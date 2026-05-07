"""mesh-library Path A thin runner · 一劳永逸接老师 CLI

老师 mesh-library 8 核心 CLI 都是干净 argparse / sys.argv · 直接 subprocess 调:
  - room_to_room_v2.py <mvp_dir> <catalog> [--dry-run|--force|--use-clip]
  - layout_validate.py <mvp_dir> <catalog> [--dry-run]
  - render_assets.py(Blender python · `blender -b --python ... -- <mvp_dir>`)
  - render_multi_assets.py(同上)
  - verify_scene_dims.py <mvp_dir>(Blender python)
  - qa_vision.py <mvp_dir> [--dry-run|--model]
  - lint_render_script.py <target>
  - validate_reports.py <mvp> [thresholds]

我们 0 行算法 · 仅 thin orchestrator(为什么必须写:何时跑 Path A 的"分支胶水")。
不写 wrapper · 不重新实现老师代码。
"""
from __future__ import annotations
import os, shutil, subprocess, sys, time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from ..paths import (
    PLAYBOOKS_SCRIPTS, BIM_CATALOG_JSON,
    ensure_playbook_script_subdir_on_path,
)


_MESH_LIB = PLAYBOOKS_SCRIPTS / "mesh-library"
_PY = sys.executable


def _find_blender() -> Optional[str]:
    p = shutil.which("blender")
    if p:
        return p
    polyu = "/mnt/data/yongan/.local/blender-4.5/blender"
    if Path(polyu).exists():
        return polyu
    return os.environ.get("BLENDER")


@dataclass
class StepResult:
    step: str
    ok: bool
    duration_ms: int
    cmd: list = field(default_factory=list)
    stdout_tail: str = ""
    stderr_tail: str = ""

    def to_meta(self) -> dict:
        return {"step": self.step, "ok": self.ok, "duration_ms": self.duration_ms,
                "stderr_tail": self.stderr_tail[-200:] if self.stderr_tail else ""}


def _run(step: str, cmd: list, *, timeout: int = 300) -> StepResult:
    t0 = time.time()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return StepResult(
            step=step, ok=proc.returncode == 0,
            duration_ms=int((time.time() - t0) * 1000),
            cmd=cmd,
            stdout_tail=(proc.stdout or "")[-500:],
            stderr_tail=(proc.stderr or "")[-500:],
        )
    except subprocess.TimeoutExpired:
        return StepResult(step=step, ok=False, duration_ms=timeout * 1000, cmd=cmd,
                          stderr_tail=f"timeout {timeout}s")
    except Exception as e:
        return StepResult(step=step, ok=False, duration_ms=int((time.time() - t0) * 1000),
                          cmd=cmd, stderr_tail=str(e)[:500])


# ───────── 老师 8 CLI · 一对一直调 · 0 算法 ─────────

def lint_render_script(mvp_or_script: Path) -> StepResult:
    return _run("lint_render_script",
                [_PY, str(_MESH_LIB / "lint_render_script.py"), str(mvp_or_script)],
                timeout=10)


def verify_scene_dims(mvp_dir: Path) -> StepResult:
    blender = _find_blender()
    if not blender:
        return StepResult(step="verify_scene_dims", ok=False, duration_ms=0,
                          stderr_tail="Blender 未装")
    return _run("verify_scene_dims",
                [blender, "-b", "--python", str(_MESH_LIB / "verify_scene_dims.py"),
                 "--", str(mvp_dir)],
                timeout=120)


def room_to_room_v2(mvp_dir: Path, catalog: Path = BIM_CATALOG_JSON,
                    *, force: bool = True, use_clip: bool = False) -> StepResult:
    cmd = [_PY, str(_MESH_LIB / "room_to_room_v2.py"), str(mvp_dir), str(catalog)]
    if force:
        cmd.append("--force")
    if use_clip:
        cmd.append("--use-clip")
    return _run("room_to_room_v2", cmd, timeout=180)


def layout_validate(mvp_dir: Path, catalog: Path = BIM_CATALOG_JSON,
                    *, report_path: Optional[Path] = None) -> StepResult:
    cmd = [_PY, str(_MESH_LIB / "layout_validate.py"), str(mvp_dir), str(catalog)]
    if report_path:
        cmd += ["--report", str(report_path)]
    return _run("layout_validate", cmd, timeout=60)


def render_multi_assets(mvp_dir: Path) -> StepResult:
    blender = _find_blender()
    if not blender:
        return StepResult(step="render_multi_assets", ok=False, duration_ms=0,
                          stderr_tail="Blender 未装")
    return _run("render_multi_assets",
                [blender, "-b", "--python", str(_MESH_LIB / "render_multi_assets.py"),
                 "--", str(mvp_dir)],
                timeout=600)


def render_assets_single(mvp_dir: Path) -> StepResult:
    """单 hero 镜头(快速 sanity check)"""
    blender = _find_blender()
    if not blender:
        return StepResult(step="render_assets", ok=False, duration_ms=0,
                          stderr_tail="Blender 未装")
    return _run("render_assets",
                [blender, "-b", "--python", str(_MESH_LIB / "render_assets.py"),
                 "--", str(mvp_dir)],
                timeout=180)


def validate_reports(mvp_dir: Path, *,
                     max_snap_warns: int = 2, max_layout_moves: int = 6) -> StepResult:
    return _run("validate_reports",
                [_PY, str(_MESH_LIB / "validate_reports.py"), str(mvp_dir),
                 f"--max-snap-warns={max_snap_warns}",
                 f"--max-layout-moves={max_layout_moves}"],
                timeout=30)


def qa_vision(mvp_dir: Path, *, dry_run: bool = False) -> StepResult:
    cmd = [_PY, str(_MESH_LIB / "qa_vision.py"), str(mvp_dir)]
    if dry_run:
        cmd.append("--dry-run")
    return _run("qa_vision", cmd, timeout=120)


# ───────── Path A 5 步 pipeline orchestrator(0 算法 · 仅顺序+gate)─────────

def run_path_a(mvp_dir: Path, *, use_clip: bool = False,
               with_qa_vision: bool = False, with_validate_gate: bool = True) -> dict:
    """老师 Path A 真实家具 5 步 pipeline · 顺序按 mesh-library/README

    1. room_to_room_v2(primitive room.json → asset 版 room-v2.json)
    2. layout_validate(修 OOB / overlap / wall-hit)
    3. render_multi_assets(6 orbit views asset-aware)
    4. validate_reports(snap/layout/sofa 阈值阻断 · 全案档 gate)
    5. qa_vision(Layer 3 AI vision QA · 可选 · 全案档必跑)
    """
    mvp_dir = Path(mvp_dir)
    steps: list[StepResult] = []
    # 老师子目录加 sys.path · 老师可能 import 兄弟模块
    ensure_playbook_script_subdir_on_path("mesh-library")

    s1 = room_to_room_v2(mvp_dir, use_clip=use_clip); steps.append(s1)
    if not s1.ok:
        return _build_summary(steps, fatal_at="room_to_room_v2")

    s2 = layout_validate(mvp_dir); steps.append(s2)
    if not s2.ok:
        return _build_summary(steps, fatal_at="layout_validate")

    s3 = render_multi_assets(mvp_dir); steps.append(s3)
    if not s3.ok:
        return _build_summary(steps, fatal_at="render_multi_assets")

    if with_validate_gate:
        s4 = validate_reports(mvp_dir); steps.append(s4)
        if not s4.ok:
            return _build_summary(steps, fatal_at="validate_reports")

    if with_qa_vision:
        s5 = qa_vision(mvp_dir); steps.append(s5)
        # qa_vision 不阻塞 · 仅记录

    return _build_summary(steps)


def _build_summary(steps: list, fatal_at: Optional[str] = None) -> dict:
    return {
        "ok": fatal_at is None,
        "fatal_at": fatal_at,
        "steps_count": len(steps),
        "total_duration_ms": sum(s.duration_ms for s in steps),
        "steps": [s.to_meta() for s in steps],
    }


# ───────── 自检 ─────────

def verify_runner() -> dict:
    """检查所有 8 老师 CLI 真存在"""
    out = {}
    for name in ["lint_render_script", "verify_scene_dims", "room_to_room_v2",
                 "layout_validate", "render_assets", "render_multi_assets",
                 "validate_reports", "qa_vision"]:
        out[name] = (_MESH_LIB / f"{name}.py").exists()
    out["bim_catalog"] = BIM_CATALOG_JSON.exists()
    out["blender"] = _find_blender() is not None
    return out


if __name__ == "__main__":
    import json
    print(json.dumps(verify_runner(), indent=2, ensure_ascii=False))
