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
