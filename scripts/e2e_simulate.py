#!/usr/bin/env python3
"""e2e 自动化测试 · 模拟用户从 brief 一句话 → 全产物链接

用户场景:
  python3 scripts/e2e_simulate.py "想要一个公主房 18 平米 粉色公主风"
  python3 scripts/e2e_simulate.py "校长办公室 30 平 庄重经典 含会客区" --tier full --engine path_a
  python3 scripts/e2e_simulate.py "天台 50 平 改造成休闲花园"

流程(走 prod API · 模拟前端真用户):
  1. POST /api/projects · 创 anon project + 拿 cookie
  2. POST /api/brief/chat · 一句话喂给 LLM brief 引擎(老师 from-text 模式)· 多轮直到 ready
  3. PATCH /api/projects/<slug> · 设 tier + render_engine
  4. POST /api/mvp/create · enqueue worker
  5. GET /api/jobs/<id>/stream(SSE)· 监听到 done
  6. 输出 prod 链接 · /project/<slug>

中间所有步骤打印日志到 stdout + /tmp/e2e_<slug>.log
"""
from __future__ import annotations
import argparse
import http.cookiejar as cj
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

PROD_BASE = os.environ.get("ARCTURA_PROD_BASE", "https://arctura-front-end.vercel.app")


# ───────── HTTP 简化 helper(带 cookie 持久) ─────────

_cookie_jar = cj.CookieJar()
_opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(_cookie_jar))


def _http(method: str, path: str, body: dict | None = None,
          *, timeout: int = 30, stream: bool = False):
    url = PROD_BASE + path
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json" if not stream else "text/event-stream")
    return _opener.open(req, timeout=timeout)


def _http_json(method: str, path: str, body: dict | None = None, *, timeout: int = 30) -> dict:
    resp = _http(method, path, body, timeout=timeout)
    raw = resp.read().decode()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"_raw": raw[:500], "_status": resp.status}


def _log(label: str, msg: str = "", *, file=sys.stdout, log_file=None):
    line = f"[{datetime.now().strftime('%H:%M:%S')}] {label} {msg}"
    print(line, flush=True, file=file)
    if log_file:
        log_file.write(line + "\n")
        log_file.flush()


# ───────── 1-5 步真模拟 ─────────

def step1_create_project(log_file) -> tuple[str, int]:
    """创 empty project + anon cookie"""
    _log("STEP 1", "创 empty project (POST /api/projects)", log_file=log_file)
    r = _http_json("POST", "/api/projects", {})
    if "slug" not in r:
        raise RuntimeError(f"创 project 失败: {r}")
    slug = r["slug"]
    version = r.get("version", 0)
    _log("  ✓", f"slug={slug} · version={version} · state={r.get('state')}", log_file=log_file)
    return slug, version


def _consume_sse(resp, log_file, *, on_event=None, max_seconds: int = 60):
    """通用 SSE 流解析 · event/data 格式 · 返事件清单"""
    events = []
    buffer = ""
    t0 = time.time()
    while time.time() - t0 < max_seconds:
        try:
            chunk = resp.read(4096).decode(errors="replace")
        except Exception:
            break
        if not chunk:
            break
        buffer += chunk
        while "\n\n" in buffer:
            block, buffer = buffer.split("\n\n", 1)
            event_name = "message"
            data = ""
            for line in block.split("\n"):
                if line.startswith("event:"):
                    event_name = line[6:].strip()
                elif line.startswith("data:"):
                    data += line[5:].strip()
            if not data:
                continue
            try:
                payload = json.loads(data)
            except json.JSONDecodeError:
                payload = {"_raw": data}
            events.append({"event": event_name, "data": payload})
            if on_event:
                on_event(event_name, payload)
            if event_name in ("complete", "error"):
                return events
    return events


def step2_brief_chat(slug: str, brief_oneliner: str, log_file,
                     max_turns: int = 5) -> dict:
    """模拟用户跟 LLM 多轮对话 · SSE stream · 多轮直到 ready_for_tier"""
    _log("STEP 2", f"brief chat 一句话: {brief_oneliner!r}", log_file=log_file)

    msg = brief_oneliner
    final_brief = {}
    completeness = 0.0
    ready = False
    for turn in range(1, max_turns + 1):
        _log(f"  turn {turn}", f"user → {msg[:80]!r}", log_file=log_file)
        try:
            resp = _http("POST", "/api/brief/chat", {
                "slug": slug,
                "user_message": msg,
            }, timeout=120, stream=True)
        except Exception as e:
            _log("  ✗", f"chat connect 失败: {e}", log_file=log_file)
            break

        reply_text = ""
        last_brief_update = None

        def _on_event(name, payload):
            nonlocal reply_text, last_brief_update
            if name == "reply":
                reply_text += payload.get("text", "") or ""
            elif name == "brief_update":
                last_brief_update = payload

        events = _consume_sse(resp, log_file, on_event=_on_event, max_seconds=90)
        try:
            resp.close()
        except Exception:
            pass

        if last_brief_update:
            final_brief = last_brief_update.get("brief") or final_brief
            completeness = last_brief_update.get("completeness", completeness)
            ready = last_brief_update.get("ready_for_tier", False)
            missing = last_brief_update.get("missing", [])
        else:
            missing = []

        _log(f"  ←",
             f"AI reply {len(reply_text)} chars · completeness={completeness:.2f} · ready={ready} · missing={missing[:3]}",
             log_file=log_file)
        if reply_text:
            _log("    quote", f"{reply_text[:160].strip()!r}", log_file=log_file)

        if ready or completeness >= 0.5:
            _log("  ✓", f"brief ready · completeness={completeness:.2f}", log_file=log_file)
            return final_brief

        # 还差字段 · 模拟用户用默认值快推进
        if missing:
            msg = f"以上字段都用合理默认值就行(我接受 {missing[0]} 等用默认),继续推进到下一步。"
        else:
            msg = "好的,以上信息够了,用默认值补齐其他字段,推进到选档位。"
    _log("  ⚠", f"brief 未 ready 但用尽 {max_turns} turn · 强行推进", log_file=log_file)
    return final_brief


def step3_set_tier(slug: str, tier: str, engine: str, log_file) -> int:
    """PATCH 设 tier + render_engine + state=planning"""
    _log("STEP 3", f"set tier={tier} · engine={engine} · state=planning", log_file=log_file)
    # 先拿当前 version
    proj = _http_json("GET", f"/api/projects/{slug}")
    version = proj.get("version", 0)
    # PATCH set tier(同时推 state planning)
    r = _http_json("PATCH", f"/api/projects/{slug}", {
        "tier": tier,
        "render_engine": engine,
        "state": "planning",
        "version": version,
    })
    new_version = r.get("version", version + 1)
    _log("  ✓", f"version {version} → {new_version} · state={r.get('state')}", log_file=log_file)
    return new_version


def step4_enqueue(slug: str, version: int, log_file) -> tuple[str, str]:
    """POST /api/mvp/create · 真 enqueue worker"""
    _log("STEP 4", f"enqueue (POST /api/mvp/create)", log_file=log_file)
    r = _http_json("POST", "/api/mvp/create", {"slug": slug, "version": version})
    if "job_id" not in r:
        raise RuntimeError(f"enqueue 失败: {r}")
    job_id = r["job_id"]
    stream_url = r.get("stream_url", f"/api/jobs/{job_id}/stream")
    _log("  ✓", f"job_id={job_id} · stream={stream_url}", log_file=log_file)
    return job_id, stream_url


def step5_listen_sse(stream_url: str, log_file, *, timeout: int = 600) -> dict:
    """监听 SSE 直到 done / error / timeout · 复用通用 _consume_sse"""
    _log("STEP 5", f"监听 SSE → {stream_url}", log_file=log_file)
    try:
        resp = _http("GET", stream_url, stream=True, timeout=timeout)
    except Exception as e:
        _log("  ✗", f"SSE 连失败: {e}", log_file=log_file)
        return {"_error": str(e)}

    t_start = time.time()
    artifacts_done = []
    final_state = {"value": None}
    error_data = {"value": None}

    def _on_event(name, payload):
        elapsed = int(time.time() - t_start)
        data = payload if isinstance(payload, dict) else {}
        nm = data.get("name") or data.get("step") or ""
        ms = data.get("timing_ms") or data.get("duration_ms") or ""
        _log(f"  +{elapsed}s", f"{name} {nm} {ms}".rstrip(), log_file=log_file)
        if name == "artifact_done":
            artifacts_done.append({"name": nm, "ms": ms})
        elif name in ("done", "complete"):
            final_state["value"] = data.get("state") or "live"
        elif name in ("error", "fatal", "artifact_error"):
            # artifact_error 只记 · 不 fatal · 老师 spec 允许部分 artifact 失败
            if name == "artifact_error":
                _log("  ⚠", f"artifact_error: {nm} · 继续", log_file=log_file)
            else:
                error_data["value"] = data

    _consume_sse(resp, log_file, on_event=_on_event, max_seconds=timeout)
    try:
        resp.close()
    except Exception:
        pass

    elapsed = int(time.time() - t_start)
    if final_state["value"]:
        _log("  ✓", f"DONE · state={final_state['value']} · {elapsed}s · {len(artifacts_done)} artifacts",
             log_file=log_file)
        return {"ok": True, "elapsed_s": elapsed, "state": final_state["value"],
                "artifacts_done": artifacts_done}
    if error_data["value"]:
        _log("  ✗", f"FAIL · {error_data['value']}", log_file=log_file)
        return {"ok": False, "elapsed_s": elapsed, "error": error_data["value"],
                "artifacts_done": artifacts_done}
    _log("  ⚠", f"timeout/EOF · {len(artifacts_done)} artifacts", log_file=log_file)
    return {"ok": False, "elapsed_s": elapsed, "error": "timeout_or_eof",
            "artifacts_done": artifacts_done}


# ───────── orchestrator ─────────

def run_e2e(brief_oneliner: str, *, tier: str = "full",
            engine: str = "path_a", verbose: bool = True) -> dict:
    """e2e 完整模拟 · 一句话 brief → prod 链接"""
    log_dir = Path("/tmp")
    log_path = log_dir / f"e2e_{int(time.time())}.log"
    log_file = open(log_path, "w", encoding="utf-8")

    _log("==== E2E SIMULATE ====", log_file=log_file)
    _log("BRIEF", brief_oneliner, log_file=log_file)
    _log("TIER", f"{tier} · ENGINE: {engine}", log_file=log_file)
    _log("PROD", PROD_BASE, log_file=log_file)
    _log("LOG", str(log_path), log_file=log_file)
    print()

    t0 = time.time()
    try:
        slug, _ = step1_create_project(log_file)
        step2_brief_chat(slug, brief_oneliner, log_file)
        version = step3_set_tier(slug, tier, engine, log_file)
        job_id, stream_url = step4_enqueue(slug, version, log_file)
        # SSE 用绝对 URL
        if not stream_url.startswith("http"):
            stream_url = stream_url
        result = step5_listen_sse(stream_url, log_file)

        elapsed = time.time() - t0
        prod_url = f"{PROD_BASE}/project/{slug}"
        download_url = None
        if result.get("ok"):
            try:
                proj = _http_json("GET", f"/api/projects/{slug}")
                downloads = proj.get("downloads", []) or []
                if downloads:
                    download_url = downloads[0].get("url")
            except Exception:
                pass

        print()
        print("═" * 70)
        print(f"E2E {'✓ DONE' if result.get('ok') else '✗ FAIL'} · {elapsed:.0f}s")
        print(f"  slug:        {slug}")
        print(f"  job_id:      {job_id}")
        print(f"  artifacts:   {len(result.get('artifacts_done', []))} done")
        if download_url:
            print(f"  bundle:      {download_url}")
        print(f"  💡 prod URL: {prod_url}")
        print(f"  📋 full log: {log_path}")
        print("═" * 70)
        return {"slug": slug, "prod_url": prod_url, "result": result,
                "elapsed_s": int(elapsed), "log_path": str(log_path)}
    except Exception as e:
        _log("✗ ERR", str(e)[:300], log_file=log_file)
        elapsed = time.time() - t0
        print()
        print(f"E2E ✗ ERROR · {elapsed:.0f}s · {e}")
        print(f"  full log: {log_path}")
        return {"_error": str(e), "elapsed_s": int(elapsed),
                "log_path": str(log_path)}
    finally:
        log_file.close()


def main():
    ap = argparse.ArgumentParser(description="e2e 模拟 brief → prod 链接")
    ap.add_argument("brief", help="一句话 brief · 例 '公主房 18 平米 粉色'")
    ap.add_argument("--tier", default="full",
                    choices=["concept", "deliver", "quote", "full", "select"])
    ap.add_argument("--engine", default="path_a",
                    choices=["fast", "formal", "path_a", "path_b_sdxl"])
    args = ap.parse_args()
    out = run_e2e(args.brief, tier=args.tier, engine=args.engine)
    sys.exit(0 if out.get("result", {}).get("ok") else 1)


if __name__ == "__main__":
    main()
