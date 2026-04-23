"""exports · GLB/OBJ/FBX/IFC4 enriched · spec L403 · Phase 7.4 待实装 skeleton"""
from ._unimplemented import produce_stub


def produce(ctx, on_event=None):
    return produce_stub(
        name="exports",
        spec_line="L403",
        what_missing="exports/<slug>.glb + .obj + .fbx + .ifc4（含属性+材质+着色·enriched）",
        full_pipeline_hint=(
            "严老师仓现成 pipeline（LIGHT 无法接 · 真产需 Blender 4.2 + IfcOpenShell）：\n"
            "  • P0 IFC enrich：playbooks/ifc-enrichment/\n"
            "  • P0 IFC audit：playbooks/ifc-audit/\n"
            "  • 入口：`cd $BLENDER_H && python3 -m cli_anything.blender.blender_cli model enrich-ifc ...`\n"
            "  • 验证：playbooks/scripts/verify_ifc_enriched.py\n"
            "  • 本机 Blender 已装（~/.local/blender/blender-4.2.3-linux-x64/blender）\n"
            "  • 缺的是 cli-anything/blender/agent-harness 的本机 deploy · 下一步可补\n"
            "  • 或走 Mac（严老师原本的 dev 环境）"
        ),
        ctx=ctx, on_event=on_event,
    )
