"""Fast renderer · spawn `node _build/capture_renders.mjs` · Playwright 截 Three.js canvas

设计：
- Python 不重写 Playwright 逻辑 · 直接调已有的 mjs 脚本
- 输入 ctx: {slug, base_url} · 输出 {name, path}[] + 耗时
- 要求 prod 前端已部署（capture 去 fetch 活页面）· dev 可传 base_url=localhost
"""
from __future__ import annotations
import subprocess
import time
from pathlib import Path
from typing import Callable, Optional

_REPO_ROOT = Path(__file__).resolve().parents[3]
_CAPTURE_SCRIPT = _REPO_ROOT / "_build" / "capture_renders.mjs"


def render(ctx: dict, *, on_event: Optional[Callable] = None) -> dict:
    """Fast render · Three.js 8 张截图

    ctx: {slug, base_url?, timeout_s?}
    returns: {produced: [{name, path}], skipped: [...], errors: [...], timing_ms: int}
    """
    slug = ctx["slug"]
    base_url = ctx.get("base_url", "https://arctura-front-end.vercel.app")
    timeout_s = ctx.get("timeout_s", 120)

    if on_event:
        on_event("artifact_start", {"name": "renders", "engine": "fast"})

    t0 = time.time()
    try:
        cmd = [
            "node", str(_CAPTURE_SCRIPT),
            "--slug", slug,
            "--url", base_url,
        ]
        result = subprocess.run(
            cmd, cwd=str(_REPO_ROOT),
            timeout=timeout_s, capture_output=True, text=True,
        )
        elapsed_ms = int((time.time() - t0) * 1000)

        if result.returncode != 0:
            err_tail = result.stderr[-500:] if result.stderr else "no stderr"
            return {
                "produced": [],
                "skipped": [],
                "errors": [{"name": "renders", "exception": "subprocess_fail",
                           "trace_tail": err_tail}],
                "timing_ms": elapsed_ms,
            }

        # 扫描产物目录
        renders_dir = _REPO_ROOT / "assets" / "mvps" / slug / "renders"
        pngs = sorted(renders_dir.glob("*.png"))
        produced = [
            {"name": p.stem, "path": f"/assets/mvps/{slug}/renders/{p.name}"}
            for p in pngs
        ]
        if on_event:
            on_event("artifact_done", {"name": "renders", "count": len(produced),
                                        "timing_ms": elapsed_ms})
        return {
            "produced": produced,
            "skipped": [],
            "errors": [],
            "timing_ms": elapsed_ms,
        }
    except subprocess.TimeoutExpired:
        return {
            "produced": [],
            "skipped": [],
            "errors": [{"name": "renders", "exception": "timeout",
                       "trace_tail": f"exceed {timeout_s}s"}],
            "timing_ms": int((time.time() - t0) * 1000),
        }
    except Exception as e:
        return {
            "produced": [],
            "skipped": [],
            "errors": [{"name": "renders", "exception": type(e).__name__,
                       "trace_tail": str(e)[:300]}],
            "timing_ms": int((time.time() - t0) * 1000),
        }


if __name__ == "__main__":
    import sys, json
    slug = sys.argv[1] if len(sys.argv) > 1 else "50-principal-office"
    r = render({"slug": slug}, on_event=lambda e, d: print(f"[{e}] {d}"))
    print(json.dumps(r, indent=2, ensure_ascii=False))
