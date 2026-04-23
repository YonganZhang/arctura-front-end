"""case_study · portfolio/impact/sales 7+ 文件 · spec L405 · Phase 7.4 待实装 skeleton"""
from ._unimplemented import produce_stub


def produce(ctx, on_event=None):
    return produce_stub(
        name="case_study",
        spec_line="L405",
        what_missing=(
            "case-study/ · portfolio.md + impact.md + sales.md + metrics.json + "
            "narrative-portfolio.txt + narrative-impact.txt + narrative-sales.txt + thumbs/"
        ),
        full_pipeline_hint=(
            "P11 Case Study pipeline · `playbooks/scripts/case_study/` · "
            "模板在 `playbooks/templates/case-study/` · "
            "跑 `materialize_full_mvp.py --slug <slug>` 产 7 文件占位 · "
            "真 narrative 需 LLM 调用 + metrics.json 需数据填充"
        ),
        ctx=ctx, on_event=on_event,
    )
