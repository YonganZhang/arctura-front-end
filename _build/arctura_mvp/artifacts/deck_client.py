"""deck_client · 客户 PPT（Marp 生成 11+ 页）· spec L401 · Phase 7.4 待实装 skeleton"""
from ._unimplemented import produce_stub


def produce(ctx, on_event=None):
    return produce_stub(
        name="deck_client",
        spec_line="L401",
        what_missing="decks/deck-client.pptx + .pdf（Marp 生成 · 11+ 页 · 仅含概念+交付层）",
        full_pipeline_hint=(
            "严老师仓现成资源（LIGHT 不接 · 因 Marp 本机未装）：\n"
            "  • Marp 模板：StartUP-Building/.claude/skills/marp-deck/（marp skill）\n"
            "  • 装 Marp：`npm i -g @marp-team/marp-cli`（本机 Linux/Mac 都能装）\n"
            "  • 实例：StartUP-Building/deliverables/HOD-BRIEFING-KT.marp.md → .marp.pptx\n"
            "  • 跑 P1/P2 pipeline 的 deck 步骤（见 studio-copilot-pipeline.md）\n"
            "下一步可在 LIGHT 补：内置 minimal Marp markdown 生成 + 调 npx marp CLI（本机 npm 可装）"
        ),
        ctx=ctx, on_event=on_event,
    )
