#!/usr/bin/env python3
"""build_scene.py — 把上游 Blender `room.json` 转成 Arctura `scene` 结构

上游 room.json（StartUP-Building 产出）= 完整 3D 场景（20+ object · 材质 · 灯光 · 相机）
下游 Arctura data/mvps/<slug>.json.scene = 前端 Three.js renderer 吃的结构化数据

本脚本独立可跑：
  python3 _build/build_scene.py --mvp 01-study-room          # pilot · 写到 data/mvps/
  python3 _build/build_scene.py --mvp 01-study-room --dry    # 只打印不写
  python3 _build/build_scene.py --all                         # 所有 interior MVP

依赖 _build/schemas/scene.schema.json 做验证（jsonschema）
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Optional

try:
    from jsonschema import Draft202012Validator
except ImportError:
    print("❌ 需要 jsonschema 4.17+: pip install --user 'jsonschema>=4.17'")
    sys.exit(2)

# ───────── 路径 ─────────
FE_ROOT = Path(__file__).resolve().parent.parent
SB_ROOT = FE_ROOT.parent / "StartUP-Building"
MVP_SRC = SB_ROOT / "studio-demo" / "mvp"
DATA_DST = FE_ROOT / "data" / "mvps"
SCHEMA_PATH = Path(__file__).resolve().parent / "schemas" / "scene.schema.json"

# ───────── Name → 分类正则（基于 42 MVP 的 Blender 命名采样）─────────
# 墙：Wall 前缀 + 方位 / Wall 结尾（Back/Left/Green/Logo/Book...）/ _Wall_ / Wall_X
# 注意不用 re.I 避免误伤 "Wallpaper" 等
WALL_RX = re.compile(
    r"(?:^|_)Wall(?=$|[_A-Z\d])"      # Wall, Wall_X, WallEast, Meeting_Wall
    r"|"
    r"[A-Za-z]+Wall\d*(?=$|_)"          # BackWall, GreenWall, BookWall, ShowerWall1, Meeting_GlassWall_
)
# 地板：Floor 前后都可，但排除 FloorLamp*
FLOOR_RX = re.compile(
    r"^Floor(?:Main|Yoga|Mat|\d*)?$"
    r"|"
    r"^[A-Z][a-zA-Z]*Floor\d*$"         # ShowerFloor1 / BathFloor 等
    r"|"
    r"^(?:Ground|Site_Ground|Deck|Slab_F\d|Slab_Existing|Slab_New)$"
)
CEILING_RX = re.compile(r"^Ceiling\d*$|^Slab_Roof$|^Roof(_.*)?$|^Eave|^Parapet")

# ───────── Name → 家具库 type 推断 ─────────
# 顺序重要：先匹配具体，再通用
TYPE_PATTERNS: list[tuple[str, str]] = [
    (r"^Bookshelf$", "shelf_open"),
    (r"^Shelf\d+$", "shelf_open"),        # 子 shelf 也归 shelf_open（renderer 会当成 primitive 处理）
    (r"^Shelves?$", "shelf_open"),
    (r"^Rack", "shelf_open"),
    (r"^Desk(?!Leg)(_.*)?$", "desk_standard"),
    (r"^WritingDesk", "desk_standard"),
    (r"^Counter(?!Leg)", "desk_standard"),
    (r"^DeskLeg", "custom"),              # 腿兜底为 box
    (r"^Chair(?!Back)(_.*)?$", "chair_standard"),
    (r"^DiningChair", "chair_standard"),
    (r"^ChairBack$", "custom"),
    (r"^ArmChair", "chair_lounge"),
    (r"^Arm(Back|Rest)", "custom"),
    (r"^Sofa3|^Sofa_3", "sofa_3seat"),
    (r"^Sofa2|^Sofa_2", "sofa_2seat"),
    (r"^Sofa", "sofa_2seat"),
    (r"^Couch", "sofa_2seat"),
    (r"^Bed(?!side)", "bed_queen"),
    (r"^TableCoffee|^CoffeeTable|^Table_Coffee", "table_coffee"),
    (r"^TableDining|^DiningTable|^Table_Dining", "table_dining"),
    (r"^Table(?!Leg)", "table_dining"),
    (r"^(Cabinet|Closet|Wardrobe|Storage)", "closet_tall"),
    (r"^LampPole", "lamp_floor"),
    (r"^FloorLamp", "lamp_floor"),
    (r"^PendantLamp|^Pendant(?!Light)", "lamp_pendant"),
    (r"^LampShade", "custom"),
    (r"^Lamp", "lamp_floor"),
]

# 中文 label 映射（pilot 01-study-room 的 name → 中文）
CH_LABELS: dict[str, str] = {
    "Floor": "地板", "BackWall": "后墙", "LeftWall": "左墙", "RightWall": "右墙",
    "FrontWall": "前墙", "Ceiling": "天花",
    "Bookshelf": "书墙", "Shelf0": "搁板 1", "Shelf1": "搁板 2",
    "Shelf2": "搁板 3", "Shelf3": "搁板 4",
    "Desk": "书桌", "DeskLegL": "桌腿（左）", "DeskLegR": "桌腿（右）",
    "Chair": "办公椅", "ChairBack": "椅背",
    "ArmChair": "休闲椅", "ArmBack": "休闲椅靠背",
    "LampPole": "落地灯", "LampShade": "灯罩",
    "Rug": "地毯", "Cabinet": "收纳柜",
    "Laptop": "笔记本", "Monitor": "显示器",
    "Counter": "操作台", "Table": "桌子", "Chair1": "椅 1", "Chair2": "椅 2",
    "Sofa": "沙发", "Bed": "床",
}


# ───────── 纯函数 utilities ─────────

def lin_to_srgb(c: float) -> int:
    """Blender linear 0-1 → sRGB 0-255"""
    c = max(0.0, min(1.0, c))
    if c <= 0.0031308:
        return round(c * 12.92 * 255)
    return round((1.055 * (c ** (1 / 2.4)) - 0.055) * 255)


def rgb_to_hex(rgb: list[float]) -> str:
    r, g, b = rgb[0], rgb[1], rgb[2]
    return f"#{lin_to_srgb(r):02X}{lin_to_srgb(g):02X}{lin_to_srgb(b):02X}"


def infer_type(name: str) -> str:
    for pat, t in TYPE_PATTERNS:
        if re.match(pat, name, re.I):
            return t
    return "custom"


def normalize_material_name(n: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", (n or "").lower()).strip("_") or "unnamed"


def convert_material(m: dict) -> dict:
    out: dict = {
        "base_color": rgb_to_hex(m.get("color", [0.8, 0.8, 0.8, 1])),
        "roughness": round(m.get("roughness", 0.7), 3),
        "metallic": round(m.get("metallic", 0.0), 3),
        "label": m.get("name", ""),
    }
    em = m.get("emission_color", [0, 0, 0, 0])
    if len(em) >= 3 and (em[0] + em[1] + em[2]) > 0 and m.get("emission_strength", 0) > 0:
        out["emissive"] = rgb_to_hex(em)
        out["emissive_intensity"] = round(m["emission_strength"], 3)
    return out


def light_intensity_from_power(type_: str, power: float) -> float:
    """粗略 W → Three.js intensity · 各 type 系数不同"""
    factor = {"sun": 1.0, "area": 0.05, "point": 0.5, "pendant": 0.8, "spot": 0.5, "directional": 1.0}.get(type_, 1.0)
    return round(power * factor, 3)


def convert_light(l: dict) -> dict:
    bl_type = l.get("type", "POINT").upper()
    type_map = {"SUN": "sun", "AREA": "area", "POINT": "point", "SPOT": "spot"}
    arc_type = type_map.get(bl_type, "point")
    out: dict = {
        "id": f"{arc_type}_{(l.get('id', 0) or 0) + 1}",
        "type": arc_type,
    }
    if arc_type == "sun":
        rot = l.get("rotation", [0, 0, 0])
        # Blender sun 的 rotation 是欧拉（度）· 简化：pitch=rot[0], yaw=rot[2]
        # 默认向下 -Z · rotation=[0,0,0] 时 dir=[0,0,-1]
        pitch = math.radians(rot[0])
        yaw = math.radians(rot[2])
        out["dir"] = [
            round(math.sin(yaw) * math.sin(pitch), 3),
            round(-math.cos(yaw) * math.sin(pitch), 3),
            round(-math.cos(pitch), 3),
        ]
    else:
        out["pos"] = [round(v, 3) for v in l.get("location", [0, 0, 2.5])]
    power = l.get("power", 100)
    out["power"] = round(power, 3)
    out["intensity"] = light_intensity_from_power(arc_type, power)
    color = l.get("color", [1, 1, 1])
    if len(color) >= 3:
        out["color"] = [round(c, 3) for c in color[:3]]
    # area light 附加 size
    if arc_type == "area":
        if "size" in l:
            out["size"] = l["size"]
        if "size_y" in l:
            out["size_y"] = l["size_y"]
        if "shape" in l:
            out["shape"] = l["shape"]
    return out


def compute_object_size(o: dict) -> list[float]:
    """Blender scale × mesh_params → actual size (米)"""
    scale = o.get("scale", [1, 1, 1])
    mesh_type = o.get("mesh_type", "cube")
    mp = o.get("mesh_params", {})
    mesh_size = mp.get("size", 2.0)

    if mesh_type in ("cube", "plane"):
        return [round(scale[0] * mesh_size, 3),
                round(scale[1] * mesh_size, 3),
                round(scale[2] * mesh_size, 3)]
    if mesh_type == "cylinder":
        r = mp.get("radius", 1) * max(scale[0], scale[1])
        depth = mp.get("depth", 2) * scale[2]
        return [round(r * 2, 3), round(r * 2, 3), round(depth, 3)]
    if mesh_type == "cone":
        r = mp.get("radius1", 1) * max(scale[0], scale[1])
        depth = mp.get("depth", 2) * scale[2]
        return [round(r * 2, 3), round(r * 2, 3), round(depth, 3)]
    if mesh_type == "sphere":
        r = mp.get("radius", 1) * max(scale[0], scale[1], scale[2])
        return [round(r * 2, 3), round(r * 2, 3), round(r * 2, 3)]
    if mesh_type == "torus":
        r_major = mp.get("major_radius", mp.get("radius", 1)) * max(scale[0], scale[1])
        r_minor = mp.get("minor_radius", 0.25) * scale[2]
        return [round(r_major * 2, 3), round(r_major * 2, 3), round(r_minor * 2, 3)]
    # fallback
    return [round(max(scale[0], 0.1), 3), round(max(scale[1], 0.1), 3), round(max(scale[2], 0.1), 3)]


def wall_from_blender(o: dict) -> Optional[dict]:
    """墙 = 薄矩形 cube · 取水平较短方向为 thickness，较长为 length"""
    loc = o.get("location", [0, 0, 0])
    scale = o.get("scale", [1, 1, 1])
    mesh_size = o.get("mesh_params", {}).get("size", 2.0)
    # half-extents
    hx = scale[0] * mesh_size / 2
    hy = scale[1] * mesh_size / 2
    hz = scale[2] * mesh_size / 2

    if hx < hy:
        # 墙沿 y 方向延伸，厚度在 x
        length = hy * 2
        thickness = hx * 2
        start = [round(loc[0], 3), round(loc[1] - length / 2, 3), 0]
        end = [round(loc[0], 3), round(loc[1] + length / 2, 3), 0]
    else:
        # 沿 x 延伸，厚度在 y
        length = hx * 2
        thickness = hy * 2
        start = [round(loc[0] - length / 2, 3), round(loc[1], 3), 0]
        end = [round(loc[0] + length / 2, 3), round(loc[1], 3), 0]
    if length <= 0:
        return None
    name = o.get("name", f"Wall_{o.get('id', 0)}")
    # id：wall_<后缀>
    suffix = re.sub(r"[^a-zA-Z0-9_]", "_", name.replace("Wall", "").strip("_")) or str(o.get("id", 0))
    return {
        "id": f"wall_{suffix}",
        "name": name,
        "start": start,
        "end": end,
        "height": round(hz * 2, 3),
        "thickness": round(max(thickness, 0.05), 3),
    }


def object_from_blender(o: dict, material_id_by_idx: dict) -> dict:
    name = o.get("name", f"Object_{o.get('id', 0)}")
    loc = o.get("location", [0, 0, 0])
    rot = o.get("rotation", [0, 0, 0])
    size = compute_object_size(o)
    inferred_type = infer_type(name)
    mat_id = material_id_by_idx.get(o.get("material", 0), "default")

    entry: dict = {
        "id": f"obj_{re.sub(r'[^a-zA-Z0-9_]', '_', name.lower())}",
        "type": inferred_type,
        "pos": [round(loc[0], 3), round(loc[1], 3), round(loc[2], 3)],
        "size": size,
        "material_id": mat_id,
        "label_en": name,
        "label_zh": CH_LABELS.get(name, name),
    }
    if any(abs(r) > 0.001 for r in rot):
        entry["rotation"] = [round(v, 3) for v in rot]
    if inferred_type == "custom":
        entry["mesh_type_legacy"] = o.get("mesh_type", "cube")
    return entry


# ───────── 主转换 ─────────

def build_scene_from_room(room: dict, brief: dict) -> dict:
    # 1. Materials
    blender_materials = room.get("materials", [])
    materials: dict = {}
    material_id_by_idx: dict = {}
    used = set()
    for m in blender_materials:
        base = normalize_material_name(m.get("name", f"mat_{m.get('id', 0)}"))
        mat_id = base
        i = 2
        while mat_id in used:
            mat_id = f"{base}_{i}"
            i += 1
        used.add(mat_id)
        materials[mat_id] = convert_material(m)
        material_id_by_idx[m.get("id", len(material_id_by_idx))] = mat_id
    if "default" not in materials:
        materials["default"] = {"base_color": "#CCCCCC", "roughness": 0.8,
                                "metallic": 0.0, "label": "Default"}

    # 2. Classify objects
    walls: list = []
    objects: list = []
    floor_entry: Optional[dict] = None
    ceiling_entry: Optional[dict] = None
    floor_raw: Optional[dict] = None

    for o in room.get("objects", []):
        name = o.get("name", "")
        if FLOOR_RX.match(name):
            floor_raw = o
            floor_entry = {
                "material_id": material_id_by_idx.get(o.get("material", 0), "default"),
                "thickness": 0.02,
            }
        elif CEILING_RX.match(name):
            loc = o.get("location", [0, 0, 3])
            scale = o.get("scale", [1, 1, 0.02])
            mesh_size = o.get("mesh_params", {}).get("size", 2.0)
            ceiling_height = round(loc[2] - (scale[2] * mesh_size / 2), 3)
            ceiling_entry = {
                "material_id": material_id_by_idx.get(o.get("material", 0), "default"),
                "thickness": round(scale[2] * mesh_size, 3) if scale[2] * mesh_size > 0 else 0.05,
                "height": max(ceiling_height, 0.0),
            }
        elif WALL_RX.match(name):
            w = wall_from_blender(o)
            if w:
                w["material_id"] = material_id_by_idx.get(o.get("material", 0), "default")
                walls.append(w)
        else:
            objects.append(object_from_blender(o, material_id_by_idx))

    # 3. Bounds
    if floor_raw:
        fs = floor_raw.get("scale", [2.5, 2, 1])
        fms = floor_raw.get("mesh_params", {}).get("size", 2.0)
        bounds_w = fs[0] * fms
        bounds_d = fs[1] * fms
    elif walls:
        xs = [v for w in walls for v in (w["start"][0], w["end"][0])]
        ys = [v for w in walls for v in (w["start"][1], w["end"][1])]
        bounds_w = max(xs) - min(xs) if xs else 5.0
        bounds_d = max(ys) - min(ys) if ys else 4.0
    else:
        bounds_w, bounds_d = 5.0, 4.0

    # Height from brief > walls > default
    brief_room = brief.get("room") if isinstance(brief, dict) else None
    brief_dims = (brief_room.get("dimensions_m", {}) if isinstance(brief_room, dict) else {})
    bounds_h = brief_dims.get("height") or (max((w["height"] for w in walls), default=2.8))

    # 4. Lights
    lights = [convert_light(l) for l in room.get("lights", [])]

    # 5. Camera
    camera_default: Optional[dict] = None
    cams = room.get("cameras", [])
    if cams:
        cam = cams[0]
        camera_default = {
            "pos": [round(v, 3) for v in cam.get("location", [3.8, -3.2, 1.7])],
            "lookAt": [0.0, 0.0, 1.2],  # 简化默认看向房间中心
            "fov": 50,
        }

    # 6. 组装
    scene: dict = {
        "schema_version": "1.0",
        "unit": "m",
        "bounds": {
            "w": round(bounds_w, 3),
            "d": round(bounds_d, 3),
            "h": round(bounds_h, 3),
        },
        "walls": walls,
        "objects": objects,
        "lights": lights,
        "materials": materials,
        "env": {
            "hdri": "/assets/hdri/interior_neutral_2k.hdr",
            "hdri_intensity": 1.0,
            "background_color": "#0C0D10",
        },
    }
    if floor_entry:
        scene["floor"] = floor_entry
    if ceiling_entry:
        scene["ceiling"] = ceiling_entry
    if camera_default:
        scene["camera_default"] = camera_default
    return scene


# ───────── IO + validation ─────────

_SCHEMA_CACHE: Optional[dict] = None

def get_validator() -> Draft202012Validator:
    global _SCHEMA_CACHE
    if _SCHEMA_CACHE is None:
        _SCHEMA_CACHE = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return Draft202012Validator(_SCHEMA_CACHE)


def validate_scene(scene: dict, slug: str) -> list[str]:
    v = get_validator()
    errs = sorted(v.iter_errors(scene), key=lambda e: list(e.absolute_path))
    return [f"{slug}:{'/'.join(str(p) for p in e.absolute_path) or '(root)'}  {e.message[:160]}"
            for e in errs]


def resolve_source_paths(slug: str) -> tuple[Optional[Path], Optional[Path]]:
    mvp_dir = MVP_SRC / slug
    room_path = mvp_dir / "room.json"
    brief_path = mvp_dir / "brief.json"
    if room_path.exists():
        return room_path, (brief_path if brief_path.exists() else None)
    # Fallback: variant 下
    vdir = mvp_dir / "variants"
    if vdir.is_dir():
        for v in sorted(vdir.iterdir()):
            if not v.is_dir():
                continue
            if (v / "room.json").exists():
                return v / "room.json", (v / "brief.json" if (v / "brief.json").exists() else brief_path if brief_path.exists() else None)
    return None, (brief_path if brief_path.exists() else None)


def build_for_mvp(slug: str, dry: bool = False, quiet: bool = False) -> tuple[bool, str]:
    room_path, brief_path = resolve_source_paths(slug)
    if not room_path:
        return False, f"{slug}: no room.json (not in mvp dir, not in any variant)"

    dst_path = DATA_DST / f"{slug}.json"
    if not dst_path.exists():
        return False, f"{slug}: data/mvps/{slug}.json 不存在（先跑 build_mvp_data.py）"

    try:
        room = json.loads(room_path.read_text(encoding="utf-8"))
    except Exception as e:
        return False, f"{slug}: room.json parse error: {e}"

    brief = {}
    if brief_path and brief_path.exists():
        try:
            brief = json.loads(brief_path.read_text(encoding="utf-8"))
        except Exception:
            brief = {}

    try:
        data = json.loads(dst_path.read_text(encoding="utf-8"))
    except Exception as e:
        return False, f"{slug}: data json parse error: {e}"

    scene = build_scene_from_room(room, brief)
    errs = validate_scene(scene, slug)
    if errs:
        return False, f"{slug}: scene 不过校验\n    " + "\n    ".join(errs[:10])

    summary = f"walls={len(scene['walls'])} objects={len(scene['objects'])} lights={len(scene['lights'])} materials={len(scene['materials'])} bounds={scene['bounds']['w']}×{scene['bounds']['d']}×{scene['bounds']['h']}"

    if dry:
        return True, f"{slug} [dry] · {summary}"

    data["scene"] = scene
    dst_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return True, f"{slug} written · {summary}"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mvp", help="单个 MVP slug")
    ap.add_argument("--all", action="store_true", help="批量所有 interior MVP")
    ap.add_argument("--dry", action="store_true", help="不写回，只校验+打印")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    if not (args.mvp or args.all):
        ap.print_help()
        sys.exit(1)

    if args.mvp:
        ok, msg = build_for_mvp(args.mvp, dry=args.dry, quiet=args.quiet)
        prefix = "✅" if ok else "❌"
        print(f"{prefix} {msg}")
        sys.exit(0 if ok else 1)

    # --all
    slugs = [d.name for d in sorted(MVP_SRC.iterdir()) if d.is_dir()]
    oks, fails = [], []
    for s in slugs:
        ok, msg = build_for_mvp(s, dry=args.dry, quiet=args.quiet)
        prefix = "✅" if ok else "❌"
        if not args.quiet or not ok:
            print(f"{prefix} {msg}")
        (oks if ok else fails).append(s)
    print(f"\n📊 {len(oks)} ok · {len(fails)} fail · {len(slugs)} total")
    if fails:
        print(f"   fail: {', '.join(fails)}")
    sys.exit(0 if not fails else 1)


if __name__ == "__main__":
    main()
