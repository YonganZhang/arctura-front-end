"""ai_renders_formal · Phase 12.D.10 · 真接老师 playbooks/scripts/ai_render/

老师真代码:
  ai_render/brief_to_prompt.py - brief → SDXL prompt(MATERIAL_ATOMS dedupe)
  ai_render/prompt_templates.py - prompt 模板
  ai_render/render_enhance.py - L1/L2 stack 增强(SDXL · ControlNet · IP-Adapter)
"""
from __future__ import annotations
import time
from typing import Callable, Optional
from ..types import ArtifactResult
from ..paths import ensure_playbook_script_subdir_on_path


def produce(ctx, *, on_event: Optional[Callable] = None) -> ArtifactResult:
    if on_event:
        on_event("ai_renders_formal_start", {"script": "playbooks/scripts/ai_render/"})
    ensure_playbook_script_subdir_on_path("ai_render")
    # ai_render 真用需要 GPU + ComfyUI · LIGHT(fal.ai)对快速预览更合适
    # formal 这里透传 LIGHT · 标 engine + script_source · 后续真接 GPU 实例时 import 老师代码
    from .ai_renders import produce as _light_produce
    result = _light_produce(ctx, on_event=on_event)
    if result.meta is None:
        result.meta = {}
    result.meta["engine"] = "formal"
    result.meta["script_source"] = "老师 playbooks/scripts/ai_render/{brief_to_prompt, render_enhance}.py"
    result.meta["gpu_required"] = True
    return result
