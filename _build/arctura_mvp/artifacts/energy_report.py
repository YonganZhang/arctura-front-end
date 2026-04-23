"""energy_report · project.json + compliance-HK.md + boq-HK.md/csv · spec L404 · Phase 7.4 待实装 skeleton"""
from ._unimplemented import produce_stub


def produce(ctx, on_event=None):
    return produce_stub(
        name="energy_report",
        spec_line="L404",
        what_missing=(
            "energy/project.json + compliance-HK.md + boq-HK.md + boq-HK.csv "
            "（真 EnergyPlus 能耗模拟 + HK BEEO 2021 合规 + HK 工料报价）"
        ),
        full_pipeline_hint=(
            "OpenStudio CLI（见 CLI-Anything/openstudio）+ EnergyPlus 26.1 + "
            "`HKG_Hong.Kong.Intl.AP.epw` 气象 · 跑 P7/P8/P6 pipeline · "
            "Mac 或 Linux 装 OpenStudio · 不在本机（Arctura LIGHT 模式）"
        ),
        ctx=ctx, on_event=on_event,
    )
