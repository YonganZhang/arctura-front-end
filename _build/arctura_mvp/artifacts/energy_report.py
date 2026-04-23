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
            "严老师仓现成 pipeline（LIGHT 无法接 · 真跑需 OpenStudio + EnergyPlus 26.1）：\n"
            "  • P7 Energy-Sim：playbooks/energy-simulation-pipeline.md\n"
            "  • P8 Compliance：playbooks/compliance-pipeline.md（codes.json v2 · HK BEEO 2021）\n"
            "  • P6 BOQ：playbooks/boq-pipeline.md\n"
            "  • 批量：playbooks/scripts/batch_all_mvps.py（23 个 MVP 一次跑）\n"
            "  • 气象：HKG_Hong.Kong.Intl.AP.epw\n"
            "  • 入口：`cd $OPENST_H && python3 -m cli_anything.openstudio.openstudio_cli project new ...`\n"
            "本机 Linux 可装 OpenStudio Server · 但 tencent-hk 未配 · 建议走 Mac 或 PolyU HPC"
        ),
        ctx=ctx, on_event=on_event,
    )
