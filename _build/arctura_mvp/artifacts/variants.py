"""variants · 3 方案对比拼图 + diff-matrix 6 维 · spec L407-420 · Phase 7.4 待实装 skeleton"""
from ._unimplemented import produce_stub


def produce(ctx, on_event=None):
    return produce_stub(
        name="variants",
        spec_line="L407-420",
        what_missing=(
            "variants/ · 3 方案（v1/v2/v3）× hero.png + 4 视角 renders + description.md · "
            "comparison-grid-4x3.png · grid-row-*.png × 4 · report.json · "
            "whatif-3variants.md · diff-matrix.md（6 维：风格/EUI/工料/维护/合规/决策）"
        ),
        full_pipeline_hint=(
            "Blender `_render_ab_variants.py` 渲染各方案 + P9 What-If 能耗对比 + "
            "P10 comparison grid 拼图 · 跑 `playbooks/scripts/ab_variants/` · "
            "Mac/Linux + Blender · 不在本机 LIGHT 模式"
        ),
        ctx=ctx, on_event=on_event,
    )
