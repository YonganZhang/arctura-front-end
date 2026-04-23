"""exports · GLB/OBJ/FBX/IFC4 enriched · spec L403 · Phase 7.4 待实装 skeleton"""
from ._unimplemented import produce_stub


def produce(ctx, on_event=None):
    return produce_stub(
        name="exports",
        spec_line="L403",
        what_missing="exports/<slug>.glb + .obj + .fbx + .ifc4（含属性+材质+着色·enriched）",
        full_pipeline_hint=(
            "Blender 4.2 LTS + cli-anything/blender harness `blender_cli model enrich-ifc` + "
            "`blender_cli export` · Mac 或 Linux 装 Blender · 本机有 "
            "`~/.local/blender/blender-4.2.3-linux-x64/` 但 export 脚本未接入 pipeline"
        ),
        ctx=ctx, on_event=on_event,
    )
