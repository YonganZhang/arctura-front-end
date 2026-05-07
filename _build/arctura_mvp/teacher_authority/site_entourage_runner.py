"""site-entourage thin runner · arch-mvp 配景(老师 P2 子系统)

老师 6 真 CLI(playbooks/scripts/site-entourage/):
  apply_measured_dims · batch_dryrun · populate_site · qa_visualize ·
  render_entourage · verify_os3d_orientation

跟 mesh_library_runner 同模式 · 0 算法 · subprocess 直调老师 CLI。
"""
from __future__ import annotations
import shutil, subprocess, sys, time
from pathlib import Path
from typing import Optional

from ..paths import PLAYBOOKS_SCRIPTS

_SE = PLAYBOOKS_SCRIPTS / "site-entourage"
_PY = sys.executable


def _find_blender() -> Optional[str]:
    p = shutil.which("blender")
    if p:
        return p
    polyu = "/mnt/data/yongan/.local/blender-4.5/blender"
    return polyu if Path(polyu).exists() else None


def _run(step: str, cmd: list, *, timeout: int = 300) -> dict:
    t0 = time.time()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return {"step": step, "ok": proc.returncode == 0,
                "duration_ms": int((time.time() - t0) * 1000),
                "stderr_tail": (proc.stderr or "")[-300:]}
    except Exception as e:
        return {"step": step, "ok": False,
                "duration_ms": int((time.time() - t0) * 1000),
                "stderr_tail": str(e)[:300]}


def populate_site(mvp_dir: Path) -> dict:
    return _run("populate_site",
                [_PY, str(_SE / "populate_site.py"), str(mvp_dir)],
                timeout=120)


def render_entourage(mvp_dir: Path) -> dict:
    blender = _find_blender()
    if not blender:
        return {"step": "render_entourage", "ok": False, "stderr_tail": "Blender 未装"}
    return _run("render_entourage",
                [blender, "-b", "--python", str(_SE / "render_entourage.py"),
                 "--", str(mvp_dir)],
                timeout=600)


def qa_visualize(mvp_dir: Path) -> dict:
    return _run("qa_visualize",
                [_PY, str(_SE / "qa_visualize.py"), str(mvp_dir)],
                timeout=60)


def apply_measured_dims(catalog_path: Path) -> dict:
    return _run("apply_measured_dims",
                [_PY, str(_SE / "apply_measured_dims.py"), str(catalog_path)],
                timeout=60)


def verify_runner() -> dict:
    return {
        "populate_site":             (_SE / "populate_site.py").exists(),
        "render_entourage":          (_SE / "render_entourage.py").exists(),
        "qa_visualize":              (_SE / "qa_visualize.py").exists(),
        "apply_measured_dims":       (_SE / "apply_measured_dims.py").exists(),
        "batch_dryrun":              (_SE / "batch_dryrun.py").exists(),
        "verify_os3d_orientation":   (_SE / "verify_os3d_orientation.py").exists(),
        "blender":                   _find_blender() is not None,
    }


if __name__ == "__main__":
    import json
    print(json.dumps(verify_runner(), indent=2, ensure_ascii=False))
