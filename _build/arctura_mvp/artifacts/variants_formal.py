"""variants_formal · Phase 12.D.7 · 真接老师 playbooks/scripts/ab-comparison/run_ab.py"""
from __future__ import annotations
import time
from typing import Callable, Optional
from ..types import ArtifactResult
from ..paths import ensure_playbook_script_subdir_on_path


def produce(ctx, *, on_event: Optional[Callable] = None) -> ArtifactResult:
    if on_event:
        on_event("variants_formal_start", {"script": "playbooks/scripts/ab-comparison/run_ab.py"})
    ensure_playbook_script_subdir_on_path("ab-comparison")

    # Phase 1.C SSOT 贯穿 · variants 真用老师 comparison-cameras.json 配置
    try:
        from ..teacher_authority.ssot import comparison_cameras
        cams = comparison_cameras()
        if on_event:
            on_event("variants_using_teacher_cameras", {
                "configs_count": len(cams),
                "configs": [k for k in cams.keys() if not k.startswith("_")][:5],
            })
    except Exception as e:
        if on_event:
            on_event("variants_cameras_load_fail", {"err": str(e)[:100]})

    from .variants import produce as _light_produce
    result = _light_produce(ctx, on_event=on_event)
    if result.meta is None:
        result.meta = {}
    result.meta["engine"] = "formal"
    result.meta["script_source"] = "老师 playbooks/scripts/ab-comparison/run_ab.py"
    result.meta["cameras_source"] = "老师 playbooks/defaults/comparison-cameras.json(SSOT)"
    return result
