"""deck_client · 客户 PPT（Marp 生成 11+ 页）· spec L401 · Phase 7.4 待实装 skeleton"""
from ._unimplemented import produce_stub


def produce(ctx, on_event=None):
    return produce_stub(
        name="deck_client",
        spec_line="L401",
        what_missing="decks/deck-client.pptx + .pdf（Marp 生成 · 11+ 页 · 仅含概念+交付层）",
        full_pipeline_hint=(
            "Marp CLI（`npm i -g @marp-team/marp-cli`）+ 客户 PPT 模板 "
            "`playbooks/templates/deck-client.md.tpl` · 跑 P1/P2 pipeline 的 deck 步骤 · "
            "或手跑 `materialize_full_mvp.py --slug <slug>` 产 deck"
        ),
        ctx=ctx, on_event=on_event,
    )
