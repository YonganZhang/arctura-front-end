"""floorplan_formal · Phase 12.D.9 · LIGHT 基础 + 老师 fix_svg_text_zorder.py 后处理"""
from __future__ import annotations
import subprocess, sys, time
from pathlib import Path
from typing import Callable, Optional
from ..types import ArtifactResult
from ..paths import PLAYBOOKS_SCRIPTS


def produce(ctx, *, on_event: Optional[Callable] = None) -> ArtifactResult:
    if on_event:
        on_event("floorplan_formal_start", {})

    # v3 · 100% 老师权威 · 命中 → copy 老师真 floorplan.{svg,png,inkscape-cli.json,dxf}
    from ..teacher_authority.v3_reuse import try_reuse
    sb_dir = Path(ctx.get("sb_dir") or ".")
    project = ctx.get("project")
    _v3 = try_reuse(
        project.brief if project else {}, "floorplan", sb_dir,
        files=["floorplan.svg", "floorplan.png",
               "floorplan.inkscape-cli.json",
               "exports/floorplan.dxf"],  # dxf 在 exports/ 下
        on_event=on_event,
    )
    if _v3:
        return _v3

    # LIGHT 先跑产 SVG
    from .floorplan import produce as _light_produce
    result = _light_produce(ctx, on_event=on_event)
    # 后处理 · 真调老师 fix_svg_text_zorder.py 修文字层级
    fix_script = PLAYBOOKS_SCRIPTS / "fix_svg_text_zorder.py"
    sb_dir = Path(ctx.get("sb_dir") or ".")
    svg_files = list(sb_dir.glob("floorplan*.svg"))
    if fix_script.exists() and svg_files:
        for svg in svg_files:
            try:
                subprocess.run([sys.executable, str(fix_script), str(svg)],
                              capture_output=True, timeout=10)
            except Exception:
                pass
        if on_event:
            on_event("floorplan_zorder_fixed", {"count": len(svg_files)})
    if result.meta is None:
        result.meta = {}
    result.meta["engine"] = "formal"
    result.meta["post_processed_by"] = "老师 fix_svg_text_zorder.py"
    return result
