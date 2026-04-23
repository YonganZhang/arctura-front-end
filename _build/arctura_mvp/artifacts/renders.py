"""renders artifact · 调 renderers/ · fast or formal"""
from __future__ import annotations
import time
from typing import Callable, Optional

from ..types import ArtifactResult
from ..renderers import get_renderer
from ..tiers import pick_engine


def produce(ctx: dict, on_event: Optional[Callable] = None) -> ArtifactResult:
    t0 = time.time()
    project = ctx["project"]

    # 依赖守卫 · scene 缺 → Three.js 页面无 canvas → Playwright 必 timeout
    # 提前 skip 比 20s 超时更友好（scene 来自 brief → scene generator · 上游步骤）
    if not project.scene:
        return ArtifactResult(
            name="renders", status="skipped",
            timing_ms=int((time.time()-t0)*1000),
            reason="scene 缺 · 无法渲染（上游 brief→scene 未产出）",
        )

    tier = project.tier or "concept"
    engine_override = project.render_engine  # None 则走 tier 默认
    renderer_fn = get_renderer(tier, override=engine_override)

    # renderer 接 ctx + on_event · 返 {produced, skipped, errors, timing_ms}
    render_ctx = {
        "slug": project.slug,
        "base_url": ctx.get("base_url", "https://arctura-front-end.vercel.app"),
    }
    result = renderer_fn(render_ctx, on_event=on_event)

    if result.get("errors"):
        return ArtifactResult(
            name="renders", status="error",
            timing_ms=int((time.time()-t0)*1000),
            error=result["errors"][0],
        )

    produced_count = len(result.get("produced", []))
    if produced_count == 0:
        return ArtifactResult(
            name="renders", status="skipped",
            timing_ms=int((time.time()-t0)*1000),
            reason="未产出 render 图 · 检查前端 /project/<slug> 是否能渲染",
        )

    return ArtifactResult(
        name="renders", status="done",
        timing_ms=int((time.time()-t0)*1000),
        output_path=f"assets/mvps/{project.slug}/renders/",
        meta={
            "count": produced_count,
            "engine": engine_override or pick_engine(tier),
            "degraded_from": result.get("_degraded_from"),
        },
    )
