"""client_readme · CLIENT-README.md 客户文档 · spec L402 · Phase 7.4 待实装 skeleton"""
from ._unimplemented import produce_stub


def produce(ctx, on_event=None):
    return produce_stub(
        name="client_readme",
        spec_line="L402",
        what_missing="CLIENT-README.md（设计统计 + 文件说明 + 利益方 + 材质清单）",
        full_pipeline_hint=(
            "模板在 `playbooks/templates/client-readme.md.tpl` · "
            "跑 `materialize_full_mvp.py --slug <slug>` 产 · "
            "或 P1/P2 pipeline 自动产"
        ),
        ctx=ctx, on_event=on_event,
    )
