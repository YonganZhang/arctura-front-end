"""老师 client-portal/render_from_json.py thin runner · 客户改后动态重渲染

老师真 CLI:
  blender --background --python render_from_json.py -- <room.json> <render_dir>

跟 _render_multi.py(静态)区别:
  1. 读 ALL object 位置/scale/rotation from room.json(支持编辑器加的对象)
  2. 支持 catalog_id + material.color
  3. 重渲染 8 视角

我们 chat-edit 客户改 brief → 改 room.json → 调此脚本即可重渲染。
"""
from __future__ import annotations
import shutil, subprocess, time
from pathlib import Path
from typing import Optional

from ..paths import STARTUP_BUILDING_ROOT


_RENDER_FROM_JSON = STARTUP_BUILDING_ROOT / "studio-demo" / "client-portal" / "render_from_json.py"


def _find_blender() -> Optional[str]:
    p = shutil.which("blender")
    if p:
        return p
    polyu = "/mnt/data/yongan/.local/blender-4.5/blender"
    return polyu if Path(polyu).exists() else None


def render_from_json(room_json_path: Path, render_dir: Path,
                     *, timeout: int = 600) -> dict:
    """老师真 CLI subprocess · 0 算法重写"""
    blender = _find_blender()
    if not blender:
        return {"ok": False, "error": "Blender 未装"}
    if not _RENDER_FROM_JSON.exists():
        return {"ok": False, "error": f"老师 render_from_json.py 缺: {_RENDER_FROM_JSON}"}
    render_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    try:
        proc = subprocess.run(
            [blender, "-b", "--python", str(_RENDER_FROM_JSON),
             "--", str(room_json_path), str(render_dir)],
            capture_output=True, text=True, timeout=timeout,
        )
        renders = sorted(render_dir.glob("*.png"))
        return {
            "ok": proc.returncode == 0 and bool(renders),
            "duration_ms": int((time.time() - t0) * 1000),
            "renders_count": len(renders),
            "stdout_tail": (proc.stdout or "")[-500:],
            "stderr_tail": (proc.stderr or "")[-300:],
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"timeout {timeout}s"}
    except Exception as e:
        return {"ok": False, "error": str(e)[:300]}


def verify_runner() -> dict:
    return {
        "render_from_json.py": _RENDER_FROM_JSON.exists(),
        "blender_available": _find_blender() is not None,
    }


if __name__ == "__main__":
    import json
    print(json.dumps(verify_runner(), indent=2, ensure_ascii=False))
