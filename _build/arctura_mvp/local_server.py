"""本机静态 server · Worker 用（Phase 7.2）

为什么要这个：
  Worker 跑本机 · 产 data/mvps/<slug>.json 到本地文件系统
  但 Vercel serve 的是 git push 时的 static snapshot · 新 MVP 数据没 deploy 就不在 prod
  → Playwright 调 prod 会 404 · canvas 永不出现 · 超时
  ∴ Worker 起个本地 HTTP server 服当前 repo · Playwright 调 localhost 拿实时数据

特性：
  - 启 daemon thread · 不阻塞 main_loop
  - 端口冲突时自动换（默认 8787 · 可 ARCTURA_LOCAL_PORT 覆盖）
  - 实现 vercel.json 的 rewrite 规则（/project/<slug> → /project/index.html · cleanUrls）
  - 仅本机访问（bind 127.0.0.1）· 不暴露公网

使用：
  from _build.arctura_mvp.local_server import ensure_running
  url = ensure_running()   # 幂等 · 已跑就回已跑 port · 没跑就启新 thread
"""
from __future__ import annotations
import os
import re
import sys
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Optional

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_PORT = int(os.environ.get("ARCTURA_LOCAL_PORT", "8787"))
_PORT_RANGE = 30     # 端口冲突尝试 N 次

# 本机 · 起一次就够 · 幂等
_server_thread: Optional[threading.Thread] = None
_server_url: Optional[str] = None
_server_lock = threading.Lock()


# ───────── rewrite 规则（对齐 vercel.json）─────────

_REWRITES = [
    # /project/<slug> → /project/?mvp=<slug> (serving /project/index.html with query)
    (re.compile(r"^/project/([^/]+)/?$"), lambda m: f"/project/?mvp={m.group(1)}"),
    # /new → /project/
    (re.compile(r"^/new/?$"), lambda m: "/project/"),
]


class _Handler(SimpleHTTPRequestHandler):
    """rewrite 感知的静态 handler · 从 repo root serve"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(_REPO_ROOT), **kwargs)

    def do_GET(self):
        original_path = self.path
        # 先剥 query · rewrite 可能加新 query
        q_pos = self.path.find("?")
        path_part = self.path[:q_pos] if q_pos >= 0 else self.path
        query_part = self.path[q_pos:] if q_pos >= 0 else ""

        for pattern, builder in _REWRITES:
            m = pattern.match(path_part)
            if m:
                new_path = builder(m)
                # rewrite 后带 query · merge 原有 query（rewrite 优先）
                if query_part and "?" not in new_path:
                    new_path = new_path + "&" + query_part[1:] if "?" in new_path else new_path + query_part
                self.path = new_path
                break
        return super().do_GET()

    def log_message(self, fmt, *args):
        # 静默 · 避免 worker log 被 request 刷屏
        pass


def _try_start(port: int) -> Optional[tuple[ThreadingHTTPServer, int]]:
    """尝试绑定端口 · 失败返 None"""
    try:
        srv = ThreadingHTTPServer(("127.0.0.1", port), _Handler)
        return (srv, port)
    except OSError:
        return None


def ensure_running() -> str:
    """幂等启动 · 返回 base_url（如 http://127.0.0.1:8787）"""
    global _server_thread, _server_url
    with _server_lock:
        if _server_url is not None:
            return _server_url

        # 依次尝试 DEFAULT ~ DEFAULT+30
        for i in range(_PORT_RANGE):
            port = _DEFAULT_PORT + i
            r = _try_start(port)
            if r is not None:
                srv, bound_port = r
                break
        else:
            raise RuntimeError(f"无法绑定任何端口 {_DEFAULT_PORT}..{_DEFAULT_PORT+_PORT_RANGE}")

        t = threading.Thread(
            target=srv.serve_forever,
            name="arctura-local-server",
            daemon=True,
        )
        t.start()
        _server_thread = t
        _server_url = f"http://127.0.0.1:{bound_port}"
        print(f"[local-server] serving {_REPO_ROOT} @ {_server_url}", file=sys.stderr)
        return _server_url


# ───────── smoke test ─────────

if __name__ == "__main__":
    import time
    import urllib.request
    url = ensure_running()
    print(f"server: {url}")
    # 测 rewrite
    for test in ["/", "/index.html", "/project/01-study-room", "/new"]:
        try:
            resp = urllib.request.urlopen(f"{url}{test}", timeout=3)
            print(f"  {test:40s} → {resp.status}")
        except Exception as e:
            print(f"  {test:40s} → ERR {e}")
    print("press Ctrl+C to stop")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
