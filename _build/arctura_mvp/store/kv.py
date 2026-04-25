"""Upstash Redis REST client · 纯 requests · Python 3.8+

Edge function 用 fetch 直连（见 api/projects.js）· 本文件给 worker/CLI 用。

加载 env：
  source ~/.arctura-env  # 或直接 export UPSTASH_REDIS_REST_URL / UPSTASH_REDIS_REST_TOKEN
"""
from __future__ import annotations
import os
import json as _json
import time
from typing import Any, Optional
import urllib.request
import urllib.parse
import urllib.error


class KVError(Exception):
    def __init__(self, msg, *, status=None, retryable=False):
        super().__init__(msg)
        self.status = status
        self.retryable = retryable


def _config():
    url = os.environ.get("UPSTASH_REDIS_REST_URL")
    token = os.environ.get("UPSTASH_REDIS_REST_TOKEN")
    if not url or not token:
        raise KVError("UPSTASH_REDIS_REST_URL / TOKEN 未设 · source ~/.arctura-env",
                      retryable=False)
    return url.rstrip("/"), token


def _request(path: str, *, method="GET", body=None, timeout=10, max_retries=3):
    """Upstash REST 请求 · Phase 10 加 retry · SSL EOF / 502 等 retryable 错自动重试

    Upstash 偶发 SSL UNEXPECTED_EOF · 实测每天数次 · 单点失败让 pipeline 整个垮（10/10 跑成
    最后写 KV 挂了 · 用户看 'KVError'）· 不可接受。
    指数退避 · 1s / 2s / 4s · 累计 7s · 一般够过抖动。
    """
    url, token = _config()
    full = f"{url}/{path}"
    headers = {"Authorization": f"Bearer {token}"}
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = _json.dumps(body).encode()

    last_err = None
    for attempt in range(max_retries):
        req = urllib.request.Request(full, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return _json.loads(r.read())
        except urllib.error.HTTPError as e:
            text = e.read().decode("utf-8", "replace")[:200]
            retryable = e.code in (429, 502, 503, 504)
            last_err = KVError(f"Upstash HTTP {e.code}: {text}", status=e.code, retryable=retryable)
            if not retryable or attempt == max_retries - 1:
                raise last_err
        except urllib.error.URLError as e:
            # SSL EOF / connection reset / DNS 等 · 全 retryable
            last_err = KVError(f"Upstash network: {e.reason}", retryable=True)
            if attempt == max_retries - 1:
                raise last_err
        # 指数退避 · 1s · 2s · 4s
        backoff = 2 ** attempt
        try:
            print(f"[kv] retry {attempt+1}/{max_retries} after {backoff}s · {last_err}", flush=True)
        except Exception:
            pass
        time.sleep(backoff)
    # 不应到这 · 防御性
    raise last_err or KVError("Upstash unknown error", retryable=False)


# ───── Basic KV ─────

def ping() -> bool:
    return _request("ping").get("result") == "PONG"


def get(key: str) -> Optional[str]:
    r = _request(f"get/{urllib.parse.quote(key, safe='')}")
    return r.get("result")  # None if missing


def set(key: str, value: str, *, ex: Optional[int] = None) -> bool:
    """SET key value [EX seconds]"""
    path = f"set/{urllib.parse.quote(key, safe='')}/{urllib.parse.quote(value, safe='')}"
    if ex is not None:
        path += f"?EX={ex}"
    r = _request(path)
    return r.get("result") == "OK"


def set_json(key: str, obj: Any, *, ex: Optional[int] = None) -> bool:
    return set(key, _json.dumps(obj, ensure_ascii=False), ex=ex)


def get_json(key: str) -> Optional[Any]:
    raw = get(key)
    return _json.loads(raw) if raw else None


def delete(*keys: str) -> int:
    if not keys:
        return 0
    parts = "/".join(urllib.parse.quote(k, safe="") for k in keys)
    r = _request(f"del/{parts}", method="POST")
    return r.get("result", 0)


def persist(key: str) -> bool:
    """去掉 TTL"""
    r = _request(f"persist/{urllib.parse.quote(key, safe='')}", method="POST")
    return r.get("result") == 1


def exists(*keys: str) -> int:
    parts = "/".join(urllib.parse.quote(k, safe="") for k in keys)
    r = _request(f"exists/{parts}")
    return r.get("result", 0)


def expire(key: str, seconds: int) -> bool:
    r = _request(f"expire/{urllib.parse.quote(key, safe='')}/{seconds}", method="POST")
    return r.get("result") == 1


# ───── Sorted set（projects:index / jobs queue 用）─────

def zadd(key: str, score: float, member: str) -> int:
    """ZADD key score member · 返回新加 0/1"""
    r = _request(f"zadd/{urllib.parse.quote(key, safe='')}/{score}/{urllib.parse.quote(member, safe='')}")
    return r.get("result", 0)


def zrevrange(key: str, start: int = 0, stop: int = -1, *, with_scores=False) -> list:
    """按 score 逆序 · 画廊用（最新在前）"""
    path = f"zrevrange/{urllib.parse.quote(key, safe='')}/{start}/{stop}"
    if with_scores:
        path += "?withScores=true"
    r = _request(path)
    return r.get("result", [])


def zcard(key: str) -> int:
    r = _request(f"zcard/{urllib.parse.quote(key, safe='')}")
    return r.get("result", 0)


def zrem(key: str, member: str) -> int:
    r = _request(f"zrem/{urllib.parse.quote(key, safe='')}/{urllib.parse.quote(member, safe='')}",
                 method="POST")
    return r.get("result", 0)


# ───── List（jobs queue 用 · BRPOP by worker）─────

def lpush(key: str, *values: str) -> int:
    """LPUSH key value [value...]"""
    parts = "/".join(urllib.parse.quote(v, safe="") for v in values)
    r = _request(f"lpush/{urllib.parse.quote(key, safe='')}/{parts}", method="POST")
    return r.get("result", 0)


def rpop(key: str) -> Optional[str]:
    r = _request(f"rpop/{urllib.parse.quote(key, safe='')}", method="POST")
    return r.get("result")


def rpush(key: str, value: str) -> int:
    """RPUSH key value"""
    r = _request(f"rpush/{urllib.parse.quote(key, safe='')}/{urllib.parse.quote(value, safe='')}",
                 method="POST")
    return r.get("result", 0)


def lrange(key: str, start: int = 0, stop: int = -1) -> list:
    r = _request(f"lrange/{urllib.parse.quote(key, safe='')}/{start}/{stop}")
    return r.get("result", [])


def llen(key: str) -> int:
    r = _request(f"llen/{urllib.parse.quote(key, safe='')}")
    return r.get("result", 0)


# ───── Pipeline / MULTI（two-phase commit for save）─────

def pipeline(commands: list[list]) -> list:
    """批量命令 · 单一请求 · Upstash 的 pipeline API

    commands = [["SET", "k1", "v1"], ["ZADD", "index", "100", "slug"], ...]
    """
    r = _request("pipeline", method="POST", body=commands)
    return r  # list of {result} or {error}


# ───── Rate limit helper ─────

def rate_limit_check(key: str, limit: int, window_s: int) -> bool:
    """滑动窗口近似 · 返回 True = 允许 · False = 超限"""
    count = _request(f"incr/{urllib.parse.quote(key, safe='')}", method="POST").get("result", 0)
    if count == 1:
        expire(key, window_s)
    return count <= limit


# ───── Self-test（python -m arctura_mvp.store.kv）─────

if __name__ == "__main__":
    import sys
    print(f"Config: URL={_config()[0]}")
    print(f"PING: {ping()}")
    k = f"arctura-kv-test-{int(time.time())}"
    assert set(k, "hello", ex=60)
    assert get(k) == "hello"
    assert set_json(f"{k}:json", {"a": 1, "b": "中"})
    assert get_json(f"{k}:json") == {"a": 1, "b": "中"}
    assert zadd("arctura-test-zset", 100, "slug-a") == 1
    assert zadd("arctura-test-zset", 200, "slug-b") == 1
    assert zrevrange("arctura-test-zset") == ["slug-b", "slug-a"]
    assert zcard("arctura-test-zset") == 2
    assert delete(k, f"{k}:json", "arctura-test-zset") == 3
    print("✓ all KV smoke tests passed")
