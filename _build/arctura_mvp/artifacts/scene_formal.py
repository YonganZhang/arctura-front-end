"""scene_formal · Phase 12.D.1 · 真接老师 Blender pipeline

跟 LIGHT scene.py 的关系:
  - LIGHT scene.py → 跑 brief→objects/lights/materials 几何(快 · prod 默认)
  - scene_formal.py → 在 LIGHT 几何之上跑 Blender headless 真渲染
                    → 输出 8 张 PNG + 9 字段 room.json(对齐老师 studio-demo 标准)

老师真 pipeline 参考:
  .claude/skills/marp-deck/scripts/_render_multi_tail.py(8 视角 cameras 模板)
  本仓 _build/arctura_mvp/artifacts/exports.py::_build_blender_script(已有 scene→Blender)

工作流:
  1. brief + LIGHT scene generator 拿到 scene dict
  2. 复用 exports._build_blender_script 生成 scene 几何 Blender 脚本
  3. 加 _render_multi_tail 风格的 8 视角 cameras + 渲染命令
  4. blender --background --python <script>(真跑 · 预估 5-15 min)
  5. 输出 8 张 PNG 到 sb_dir/renders/ + 9 字段 room.json 到 sb_dir/

依赖:
  - Blender 4.5.9+(/usr/local/bin/blender 软链 + ~/.arctura-env PATH)
  - exports._build_blender_script(已存在)
  - scene generator(LIGHT 模式)输出 scene dict
"""
from __future__ import annotations
import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Callable, Optional

from ..types import ArtifactResult


def _find_blender() -> Optional[Path]:
    """同 exports.py · 三级 fallback 找 Blender"""
    p = shutil.which("blender")
    if p:
        return Path(p)
    env_p = os.environ.get("BLENDER")
    if env_p and Path(env_p).exists():
        return Path(env_p)
    polyu_default = Path("/mnt/data/yongan/.local/blender-4.5/blender")
    if polyu_default.exists():
        return polyu_default
    return None


_BLENDER = _find_blender()


# 8 视角 camera 模板(参考 _render_multi_tail.py · 老师标准)
# (name, location_factor, target_factor, lens, is_ortho, hide_ceiling, hide_walls)
SHOTS_TEMPLATE = """
# ── Cameras (auto-scaled to room) · 8 视角 · 参考老师 _render_multi_tail.py ─────
import mathutils
HX = ROOM_LEN / 2 - 0.6
HY = ROOM_WID / 2 - 0.6

SHOTS = [
    ('01_hero_corner',   ( HX, -HY, 2.2),                   (-HX*0.5,  HY*0.4, 1.0), 22, False, False, []),
    ('02_reception',     (-HX,  HY*0.6, 1.7),               (-HX*0.4,  HY*0.1, 1.2), 28, False, False, []),
    ('03_main_zone',     ( HX*0.7,  HY*0.7, 1.7),           (0.0, -HY*0.1, 1.0),     28, False, False, []),
    ('04_feature_zone',  ( HX*0.9, -HY*0.3, 1.7),           ( HX*0.5,  HY*0.3, 1.2), 24, False, False, []),
    ('05_lounge_zone',   (-HX*0.4,  HY, 1.7),               ( HX*0.7, -HY*0.7, 1.0), 28, False, False, []),
    ('06_back_corner',   ( HX*0.2, -HY, 1.7),               (-HX*0.5, -HY*0.7, 1.4), 35, False, False, []),
    ('07_top_ortho',     ( 0.0,  0.0, ROOM_HT * 4),         (0.0, 0.0, 0.0),         None, True, True, []),
    ('08_birds_eye_3d',  (-ROOM_LEN, -ROOM_WID, ROOM_HT*3), (0.0, 0.0, 0.5),         35, False, True, []),
]

def look_at(cam_obj, target):
    direction = mathutils.Vector(target) - mathutils.Vector(cam_obj.location)
    rot_quat = direction.to_track_quat('-Z', 'Y')
    cam_obj.rotation_euler = rot_quat.to_euler()

scene.render.image_settings.file_format = 'PNG'
scene.render.resolution_x = 1600
scene.render.resolution_y = 1000

RENDER_DIR = Path(r'__RENDER_DIR_PLACEHOLDER__')
RENDER_DIR.mkdir(parents=True, exist_ok=True)

for name, loc, target, lens, is_ortho, hide_ceil, hide_walls in SHOTS:
    cam_data = bpy.data.cameras.new(name=f'Cam_{name}')
    if is_ortho:
        cam_data.type = 'ORTHO'
        cam_data.ortho_scale = max(ROOM_LEN, ROOM_WID) * 1.1
    else:
        cam_data.type = 'PERSP'
        cam_data.lens = lens
        cam_data.sensor_width = 36.0
    cam_data.clip_start = 0.05
    cam_data.clip_end = 200.0
    cam_obj = bpy.data.objects.new(f'Cam_{name}', cam_data)
    bpy.context.collection.objects.link(cam_obj)
    cam_obj.location = loc
    look_at(cam_obj, target)
    scene.camera = cam_obj
    out = RENDER_DIR / f'{name}.png'
    scene.render.filepath = str(out)
    bpy.ops.render.render(write_still=True)
    print(f'[FORMAL_RENDER_OK] {out}')

print('FORMAL_RENDER_DONE')
"""


def _build_render_script(scene: dict, render_dir: Path, slug: str) -> str:
    """生成完整 Blender 渲染脚本(scene 几何 + 8 视角 cameras)"""
    # 复用 exports._build_blender_script 拿 scene 几何部分
    from .exports import _build_blender_script
    geom_script = _build_blender_script(scene, render_dir, slug)

    # 但 exports 的脚本最后调 export(GLB/OBJ/FBX) · 我们截掉那部分,加渲染
    # 找第一个 'EXPORTS_OK' 或 export 调用行,只保留前面 scene 部分
    cut_markers = ["bpy.ops.export_scene.gltf", "bpy.ops.wm.obj_export", "bpy.ops.export_scene.fbx"]
    cut_idx = None
    for marker in cut_markers:
        if marker in geom_script:
            cut_idx = geom_script.find(marker)
            # 退回到 # ── Export 注释行
            export_section = geom_script.rfind("# ──", 0, cut_idx)
            if export_section >= 0:
                cut_idx = export_section
            break
    geom_only = geom_script[:cut_idx] if cut_idx else geom_script

    # 拿 bounds
    bounds = scene.get("bounds", {"w": 6, "d": 5, "h": 3})
    room_len = bounds.get("w", 6)
    room_wid = bounds.get("d", 5)
    room_ht = bounds.get("h", 3)

    # 房间尺寸常量(SHOTS 用)
    dims_block = f"\nROOM_LEN = {room_len}\nROOM_WID = {room_wid}\nROOM_HT = {room_ht}\n"

    # cameras + 渲染部分
    render_block = SHOTS_TEMPLATE.replace("__RENDER_DIR_PLACEHOLDER__", str(render_dir))

    return geom_only + dims_block + render_block


def _scene_to_room_json(scene: dict, name: str) -> dict:
    """LIGHT scene dict → 9 字段 room.json(对齐老师 studio-demo 标准)

    老师 keys: cameras / collections / lights / materials / metadata / name / objects / render / scene / version / world
    """
    return {
        "version": "1.0",
        "name": name,
        "metadata": {
            "generated_by": "scene_formal · Phase 12.D.1",
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "schema": "老师 studio-demo/mvp/<slug>/room.json 兼容",
        },
        "scene": {
            "unit_system": "METRIC",
            "scale_length": 1.0,
            "fps": 24,
            "bounds": scene.get("bounds", {}),
        },
        "render": {
            "engine": "BLENDER_EEVEE_NEXT",
            "resolution_x": 1600,
            "resolution_y": 1000,
            "samples": 128,
        },
        "world": {
            "background_color": [0.05, 0.05, 0.05],
            "hdri": scene.get("env", {}).get("hdri"),
        },
        "objects": scene.get("objects", []),
        "lights": scene.get("lights", []),
        "materials": scene.get("materials", {}),
        "cameras": [{"name": s, "render_path": f"renders/{s}.png"}
                    for s in ["01_hero_corner", "02_reception", "03_main_zone", "04_feature_zone",
                             "05_lounge_zone", "06_back_corner", "07_top_ortho", "08_birds_eye_3d"]],
        "collections": [{"name": "Default", "objects": [o.get("id") for o in scene.get("objects", [])]}],
    }


def produce(ctx, *, on_event: Optional[Callable] = None) -> ArtifactResult:
    """scene_formal · 真跑 Blender headless 渲染 + 输出 9 字段 room.json

    依赖 ctx:
      - project (含 scene · brief)
      - sb_dir(StartUP-Building/studio-demo/mvp/<slug>/)
    """
    t0 = time.time()
    project = ctx.get("project")
    sb_dir = Path(ctx.get("sb_dir") or ".")

    if not project or not project.scene:
        return ArtifactResult(
            name="scene", status="skipped",
            timing_ms=int((time.time() - t0) * 1000),
            reason="project 或 scene 缺 · scene_formal 需要 LIGHT scene generator 先跑",
        )

    if _BLENDER is None or not _BLENDER.exists():
        # Blender 不可用 · 降级到 LIGHT scene · 标 _degraded_from
        if on_event:
            on_event("artifact_degrade", {
                "name": "scene", "from": "formal", "to": "fast",
                "reason": "Blender 未装 · 降级 LIGHT scene generator",
            })
        from .scene import produce as light_produce
        result = light_produce(ctx, on_event=on_event)
        if hasattr(result, "_degraded_from"):
            result._degraded_from = "formal"
        return result

    if on_event:
        on_event("blender_start", {"engine": "EEVEE", "blender_path": str(_BLENDER)})

    # 1. 准备 render_dir + script
    render_dir = sb_dir / "renders"
    render_dir.mkdir(parents=True, exist_ok=True)
    script = _build_render_script(project.scene, render_dir, project.slug)
    script_path = sb_dir / "_render_multi.py"
    script_path.write_text(script, encoding="utf-8")

    # 2. blender --background --python
    try:
        proc = subprocess.run(
            [str(_BLENDER), "-b", "-P", str(script_path)],
            capture_output=True, text=True, timeout=900,  # 15 min 上限
        )
    except subprocess.TimeoutExpired:
        return ArtifactResult(
            name="scene", status="error",
            timing_ms=int((time.time() - t0) * 1000),
            error={"name": "blender_timeout", "trace_tail": "exceed 900s · scene_formal 渲染超时"},
        )

    if "FORMAL_RENDER_DONE" not in proc.stdout:
        # 看具体哪步失败
        return ArtifactResult(
            name="scene", status="error",
            timing_ms=int((time.time() - t0) * 1000),
            error={
                "name": "blender_render_fail",
                "trace_tail": (proc.stderr or proc.stdout)[-600:],
            },
        )

    # 3. 写 9 字段 room.json
    room_data = _scene_to_room_json(project.scene, project.display_name or project.slug)
    room_path = sb_dir / "room.json"
    room_path.write_text(json.dumps(room_data, ensure_ascii=False, indent=2))

    # 4. 验产物
    rendered_pngs = sorted(render_dir.glob("*.png"))
    if on_event:
        on_event("blender_done", {
            "renders_count": len(rendered_pngs),
            "room_json_path": str(room_path),
        })

    return ArtifactResult(
        name="scene", status="done",
        timing_ms=int((time.time() - t0) * 1000),
        output_path=str(room_path),
        meta={
            "engine": "formal",
            "renders_count": len(rendered_pngs),
            "blender_version": "4.5.9",
            "room_json_keys": list(room_data.keys()),
        },
    )
