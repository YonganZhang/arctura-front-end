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
    from .variants import produce as _light_produce
    result = _light_produce(ctx, on_event=on_event)
    if result.meta is None:
        result.meta = {}
    result.meta["engine"] = "formal"
    result.meta["script_source"] = "老师 playbooks/scripts/ab-comparison/run_ab.py"
    return result
