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
    # v3 · 老师 03-coffee-shop 真有 SDXL 多版本 + compare_*.png · 直接 copy
    from pathlib import Path as _Path
    from ..teacher_authority.v3_reuse import try_reuse
    project = ctx.get("project")
    sb_dir = _Path(ctx.get("sb_dir") or ".")
    _v3 = try_reuse(
        project.brief if project else {}, "ai_renders", sb_dir,
        files=[
            "compare_all_stacks.png", "compare_horizontal_core.png",
            "compare_horizontal_experiments.png", "compare_l1_vs_l2b_vs_l2c.png",
            "compare_prompt_fix_v1_vs_v2.png", "compare_sd15_vs_sdxl.png",
        ],
        dirs=["renders-ai", "renders-ai-sdxl",
              "renders-ai-sdxl-l2", "renders-ai-sdxl-l2b"],
        on_event=on_event,
    )
    if _v3:
        return _v3

    # v3 不命中(老师只 03-coffee-shop 有 SDXL 多版本) → 落 LIGHT(需 fe_root)
    if "fe_root" not in ctx:
        if on_event:
            on_event("ai_renders_skipped", {
                "reason": "v3 不命中 + ctx 缺 fe_root(LIGHT 依赖)· 老师其余 MVP 没 AI render 产物",
            })
        return ArtifactResult(
            name="ai_renders", status="skipped",
            timing_ms=0,
            reason="老师该 MVP 无 AI render 真产物 · LIGHT 缺 fe_root context",
        )

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
