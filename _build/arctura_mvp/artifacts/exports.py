"""exports · BIM 5 件套 真产（Phase 9）

spec L403 · GLB / OBJ / FBX / IFC4 / DXF（enriched · 含属性+材质+着色）

实装（LIGHT 模式）：
  1. 从 project.scene 组 Blender Python 脚本 · 建 primitives + materials
  2. 调 Blender headless 跑 5 个 export（GLB / OBJ / FBX · 可选 IFC/DXF）
  3. 写 sb_dir/exports/{slug}.{glb,obj,fbx}
  4. 失败降级 skipped + 错误信息

LIGHT 不产 DXF（需 Pascal Editor · P2 建筑级）· 不产 真 IFC4（enriched 需 Blender-BIM · 先不做）
"""
from __future__ import annotations
import json
import shutil
import subprocess
import time
from pathlib import Path
from typing import Callable, Optional

from ..types import ArtifactResult
from ..paths import CLI_ANYTHING_ROOT
import sys

# 严老师 ifc_export 纯 Python（只依赖 ifcopenshell）· 直接 import
_BLENDER_HARNESS = CLI_ANYTHING_ROOT / "blender" / "agent-harness"
if _BLENDER_HARNESS.exists() and str(_BLENDER_HARNESS) not in sys.path:
    sys.path.insert(0, str(_BLENDER_HARNESS))

_BLENDER = Path.home() / ".local" / "blender" / "blender-4.2.3-linux-x64" / "blender"


def _build_blender_script(scene: dict, out_dir: Path, slug: str) -> str:
    """生成 Blender Python 脚本 · 从 scene 建 geometry · export 3 格式"""
    assemblies = scene.get("assemblies") or []
    bounds = scene.get("bounds") or {"w": 6, "d": 5, "h": 3}
    materials = scene.get("materials") or {}

    # 把 scene 数据 dump 到脚本里（json 安全）
    scene_json = json.dumps({
        "bounds": bounds,
        "assemblies": [{
            "id": a.get("id", f"asm_{i}"),
            "type": a.get("type", "box"),
            "pos": a.get("pos", [0, 0, 0]),
            "size": a.get("size", [1, 1, 1]),
            "rotation": a.get("rotation", [0, 0, 0]),
            "material_id": a.get("material_id_primary") or a.get("material_id", "default"),
            "label_en": a.get("label_en", a.get("type", "obj")),
        } for i, a in enumerate(assemblies)],
        "materials": {
            k: {"base_color": v.get("base_color", "#CCCCCC")}
            for k, v in materials.items()
        },
    }, ensure_ascii=False)

    return f'''
import bpy, json, math
scene = json.loads({scene_json!r})
# 清空默认 cube/light/camera
for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)

# 建地板
b = scene["bounds"]
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
floor = bpy.context.active_object
floor.scale = (b["w"], b["d"], 1)
floor.name = "Floor"

# 材质字典 · hex → RGBA
def hex_to_rgba(h):
    h = h.lstrip("#")
    return (int(h[0:2], 16)/255, int(h[2:4], 16)/255, int(h[4:6], 16)/255, 1.0)

mat_cache = {{}}
def get_mat(mat_id):
    if mat_id in mat_cache:
        return mat_cache[mat_id]
    mat = bpy.data.materials.new(name=mat_id)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    color = scene["materials"].get(mat_id, {{}}).get("base_color", "#CCCCCC")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = hex_to_rgba(color)
    mat_cache[mat_id] = mat
    return mat

# 建 assemblies · primitives
for a in scene["assemblies"]:
    sz = a["size"]
    pos = a["pos"]
    bpy.ops.mesh.primitive_cube_add(size=1, location=(pos[0], pos[1], pos[2] + sz[2]/2))
    obj = bpy.context.active_object
    obj.scale = (sz[0]/2, sz[1]/2, sz[2]/2)
    obj.name = a["id"]
    rot = a.get("rotation", [0,0,0])
    obj.rotation_euler = (math.radians(rot[0]), math.radians(rot[1]), math.radians(rot[2]))
    mat = get_mat(a["material_id"])
    if not obj.data.materials:
        obj.data.materials.append(mat)

# apply scale 让几何 baked
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

# Export GLB
bpy.ops.export_scene.gltf(
    filepath=r"{out_dir}/{slug}.glb",
    export_format="GLB",
    export_apply=True,
    use_selection=False,
)

# Export OBJ
bpy.ops.wm.obj_export(
    filepath=r"{out_dir}/{slug}.obj",
    export_selected_objects=False,
    apply_modifiers=True,
)

# Export FBX
bpy.ops.export_scene.fbx(
    filepath=r"{out_dir}/{slug}.fbx",
    use_selection=False,
    apply_scale_options="FBX_SCALE_UNITS",
)

print("EXPORTS_OK")
'''


def produce(ctx: dict, on_event: Optional[Callable] = None) -> ArtifactResult:
    t0 = time.time()
    project = ctx["project"]
    sb_dir: Path = ctx["sb_dir"]

    if not project.scene:
        return ArtifactResult(
            name="exports", status="skipped",
            timing_ms=int((time.time()-t0)*1000),
            reason="scene 缺 · 无法建模 export",
        )

    if not _BLENDER.exists():
        return ArtifactResult(
            name="exports", status="skipped",
            timing_ms=int((time.time()-t0)*1000),
            reason=f"Blender 未装 · {_BLENDER}",
        )

    exports_dir = sb_dir / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)

    # 生成脚本
    script = _build_blender_script(project.scene, exports_dir, project.slug)
    script_path = exports_dir / "_export_script.py"
    script_path.write_text(script, encoding="utf-8")

    # 跑 Blender headless
    try:
        proc = subprocess.run(
            [str(_BLENDER), "-b", "-P", str(script_path)],
            capture_output=True, text=True, timeout=180,
        )
    except subprocess.TimeoutExpired:
        return ArtifactResult(
            name="exports", status="error",
            timing_ms=int((time.time()-t0)*1000),
            error={"name": "blender_timeout", "trace_tail": "exceed 180s"},
        )

    if "EXPORTS_OK" not in proc.stdout:
        return ArtifactResult(
            name="exports", status="error",
            timing_ms=int((time.time()-t0)*1000),
            error={
                "name": "blender_script_fail",
                "trace_tail": (proc.stderr or proc.stdout)[-400:],
            },
        )

    # 检查文件产出
    produced = {
        "glb": (exports_dir / f"{project.slug}.glb").exists(),
        "obj": (exports_dir / f"{project.slug}.obj").exists(),
        "fbx": (exports_dir / f"{project.slug}.fbx").exists(),
    }

    # Phase 9.2 · 加 IFC4 via 严老师 ifc_export（纯 Python · ifcopenshell）
    ifc_path = exports_dir / f"{project.slug}.ifc"
    ifc_err = None
    try:
        from cli_anything.blender.core import ifc_export
        # 组 scene 为 export_ifc 期望的 "project" dict（objects[] 每个含 name + location + bbox）
        ifc_project = _scene_to_ifc_project(project.scene, project.display_name or project.slug)
        ifc_export.export_ifc(ifc_project, str(ifc_path), overwrite=True)
        produced["ifc"] = ifc_path.exists()
    except Exception as e:
        ifc_err = str(e)[:200]
        produced["ifc"] = False

    size_kb = {
        fmt: round((exports_dir / f"{project.slug}.{fmt}").stat().st_size / 1024, 1)
        for fmt, ok in produced.items() if ok
    }
    ok_count = sum(1 for v in produced.values() if v)

    # 清临时脚本
    script_path.unlink(missing_ok=True)

    return ArtifactResult(
        name="exports", status="done" if ok_count > 0 else "error",
        timing_ms=int((time.time()-t0)*1000),
        output_path=str(exports_dir),
        meta={
            "formats": produced,
            "size_kb": size_kb,
            "count": ok_count,
            "ifc_err": ifc_err,
            "dxf_skipped": "LIGHT 不产 DXF · spec L403 要 · 需 Pascal Editor（P2 建筑级）",
        },
    )


def _scene_to_ifc_project(scene: dict, name: str) -> dict:
    """把 Arctura scene.json 转成严老师 ifc_export 期望的 project dict

    严老师 format: {name, objects: [{name, location, scale?, visible?}]}
    Arctura scene: {assemblies: [{id, type, pos, size, rotation, label_en, ...}]}
    """
    objects = []
    # 加墙 · 地板 · 天花板为 IfcWall / IfcSlab
    bounds = scene.get("bounds") or {"w": 6, "d": 5, "h": 3}
    W, D, H = bounds["w"], bounds["d"], bounds["h"]
    # 地板
    objects.append({"name": "Floor", "location": [0, 0, 0], "scale": [W, D, 0.1], "visible": True})
    # 天花板
    objects.append({"name": "Ceiling", "location": [0, 0, H], "scale": [W, D, 0.05], "visible": True})
    # 4 墙（简化）
    for i, (wx, wy, ww, wd) in enumerate([
        (-W/2, 0, 0.1, D), (W/2, 0, 0.1, D),
        (0, -D/2, W, 0.1), (0, D/2, W, 0.1),
    ]):
        objects.append({"name": f"Wall_{i+1}", "location": [wx, wy, H/2],
                        "scale": [ww, wd, H], "visible": True})
    # 家具 assemblies → IfcFurniture
    for a in (scene.get("assemblies") or []):
        objects.append({
            "name": a.get("label_en") or a.get("type") or a.get("id", "Furniture"),
            "location": list(a.get("pos", [0, 0, 0])),
            "scale": list(a.get("size", [0.5, 0.5, 0.5])),
            "visible": True,
        })
    return {"name": name, "objects": objects}
