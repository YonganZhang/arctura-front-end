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
    (r"^Shelf\d+$", "custom"),            # 子 shelf 是扁薄搁板 · 走 primitive box 保持 Blender z 坐标
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

# Assembly 识别表（Phase 3 升级 · 替代 PROCEDURAL_CHILDREN 硬跳过）
# 父 name 正则 · 匹配到就是一个 assembly 主 part；子 name 正则列表 · 匹配的 object 归入同 assembly
# 跟 Phase 2 差异：**parts 不再被跳过**，全部保留在 scene.objects；另外建 assemblies[] 把 primary + children 组成"逻辑家具"
ASSEMBLY_PATTERNS: list[dict] = [
    {"parent": r"^Chair(?!Back)",     "type": "chair_standard", "children": [r"^ChairBack", r"^ChairLeg", r"^ChairSeat"]},
    {"parent": r"^ArmChair$",         "type": "chair_lounge",   "children": [r"^ArmBack", r"^ArmSeat", r"^ArmRest"]},
    {"parent": r"^Desk(?!Leg)",       "type": "desk_standard",  "children": [r"^DeskLeg"]},
    {"parent": r"^LampPole",          "type": "lamp_floor",     "children": [r"^LampShade", r"^LampBase"]},
    {"parent": r"^FloorLamp(?!Base|Post|Shade)$", "type": "lamp_floor",
                                       "children": [r"^FloorLampBase", r"^FloorLampPost", r"^FloorLampShade"]},
    {"parent": r"^Bookshelf",         "type": "shelf_open",     "children": [r"^Shelf\d+", r"^BookshelfSide", r"^BookshelfBack"]},
    {"parent": r"^Sofa(?!Arm|Back|Cushion|Leg)", "type": "sofa_2seat",
                                       "children": [r"^SofaArm", r"^SofaCushion", r"^SofaBack", r"^SofaLeg"]},
    {"parent": r"^Bed(?!side|Frame|Leg|Headboard)", "type": "bed_queen",
                                       "children": [r"^BedFrame", r"^BedLeg", r"^BedHeadboard", r"^Mattress"]},
    {"parent": r"^(Cabinet|Closet|Wardrobe)(?!Door|Handle|Drawer)", "type": "closet_tall",
                                       "children": [r"^CabinetDoor", r"^CabinetHandle", r"^CabinetDrawer",
                                                    r"^ClosetDoor", r"^ClosetHandle"]},
    {"parent": r"^Table(?!Leg|Base|Coffee|Dining)", "type": "table_dining",
                                       "children": [r"^TableLeg", r"^TableBase"]},
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


# ───────── Assembly 识别 · Phase 3 (替代 find_child_ids_to_skip 硬跳过) ─────────

def _make_asm_id(index: int, type_: str) -> str:
    """生成 assembly id · 保证唯一且可读"""
    return f"asm_{type_}_{index}"


def _obj_id_from_name(name: str) -> str:
    """复刻 object_from_blender 的 id 规则 · 用于回指"""
    return f"obj_{re.sub(r'[^a-zA-Z0-9_]', '_', name.lower())}"


def _bbox_from_parts(parts: list[dict]) -> tuple[list[float], list[float]]:
    """算聚合包围盒 · 返回 (center_pos, size)"""
    if not parts:
        return [0, 0, 0], [0.1, 0.1, 0.1]
    xs, ys, zs = [], [], []
    for p in parts:
        px, py, pz = p["pos"]
        hw, hd, hh = p["size"][0] / 2, p["size"][1] / 2, p["size"][2] / 2
        xs += [px - hw, px + hw]; ys += [py - hd, py + hd]; zs += [pz - hh, pz + hh]
    min_x, max_x = min(xs), max(xs); min_y, max_y = min(ys), max(ys); min_z, max_z = min(zs), max(zs)
    center = [round((min_x+max_x)/2, 3), round((min_y+max_y)/2, 3), round((min_z+max_z)/2, 3)]
    size = [round(max(max_x-min_x, 0.05), 3), round(max(max_y-min_y, 0.05), 3), round(max(max_z-min_z, 0.05), 3)]
    return center, size


def build_assemblies(scene_objects: list[dict], blender_objects: list[dict]) -> list[dict]:
    """
    从 scene.objects（已 flatten）+ 原 Blender 命名信息 生成 assemblies[]。

    策略：
    1. 命名匹配优先：ASSEMBLY_PATTERNS 里的 parent name → 主 part；children name → 加入同 asm
    2. 空间近邻 fallback：名字不匹配的父家具（已有 non-custom type）· 找 1m 内未归属的 custom/零件 object · 按类型合理拉入
    3. 剩下没归属的 object（独立体：Rug, Laptop, Monitor 等）· 每个自成 assembly（single_object）· 方便 AI 操作
    返回 assemblies 列表 · 同时 mutate scene_objects 给每个 object 打 assembly_id
    """
    # 建立 object.id → scene object 的反查（scene_objects 是 build 后的形态 · 含 id/pos/size/type）
    obj_by_id = {o["id"]: o for o in scene_objects}

    # 建立 Blender name → scene object 反查（scene.id 是从 name 派生的 obj_<lower>）
    # Blender id 不稳定地 survive 到 scene · 改用 name 作 key
    name_to_obj: dict[str, dict] = {}
    for bo in blender_objects:
        name = bo.get("name", "")
        if not name:
            continue
        scene_obj_id = _obj_id_from_name(name)
        so = obj_by_id.get(scene_obj_id)
        if so:
            name_to_obj[name] = so

    assemblies: list[dict] = []
    assigned_ids: set[str] = set()
    asm_idx = 1

    # ── Pass 1：命名匹配 ──
    for pat in ASSEMBLY_PATTERNS:
        parent_re = re.compile(pat["parent"])
        child_res = [re.compile(c) for c in pat["children"]]
        # 找所有父 match
        parent_names = [n for n in name_to_obj.keys() if parent_re.match(n)]
        for pname in parent_names:
            primary = name_to_obj[pname]
            if primary["id"] in assigned_ids:
                continue
            # 找对应的 children
            part_ids = [primary["id"]]
            for cname, cobj in name_to_obj.items():
                if cname == pname or cobj["id"] in assigned_ids:
                    continue
                if any(rx.match(cname) for rx in child_res):
                    part_ids.append(cobj["id"])
            # 聚合 bbox
            parts_resolved = [obj_by_id[pid] for pid in part_ids if pid in obj_by_id]
            center, size = _bbox_from_parts(parts_resolved)
            asm_id = _make_asm_id(asm_idx, pat["type"]); asm_idx += 1
            entry = {
                "id": asm_id,
                "type": pat["type"],
                "pos": [primary["pos"][0], primary["pos"][1], 0],  # 底贴地（procedural 以 z=0 为原点）
                "rotation": primary.get("rotation", [0, 0, 0]),
                "size": size,
                "part_ids": part_ids,
                "primary_part_id": primary["id"],
                "material_id_primary": primary.get("material_id", "default"),
                "label_en": primary.get("label_en", pname),
                "label_zh": primary.get("label_zh", pname),
                "_generated_by": "naming_regex",
            }
            if primary.get("zone"):
                entry["zone"] = primary["zone"]
            assemblies.append(entry)
            for pid in part_ids:
                assigned_ids.add(pid)

    # ── Pass 2：空间 fallback ·未命中的 non-custom 父自成 assembly（每个 non-custom object 至少是一个 assembly）──
    # 对每个 non-custom 且未归属的 object · 单独成一个 assembly
    for o in scene_objects:
        if o["id"] in assigned_ids:
            continue
        if o.get("type") in (None, "custom"):
            continue
        # 尝试空间近邻：找 1m 内的 custom object 拉入
        part_ids = [o["id"]]
        for other in scene_objects:
            if other["id"] in assigned_ids or other["id"] == o["id"]:
                continue
            if other.get("type") not in (None, "custom"):
                continue  # 只拉 custom 零件
            d = math.hypot(other["pos"][0] - o["pos"][0], other["pos"][1] - o["pos"][1])
            if d <= 1.0:  # 1m 阈值
                # 简单名字启发 · custom 物体名要跟父类有语义相关（或直接包含父的 type 关键字）
                pname = o.get("label_en", "")
                cname = other.get("label_en", "")
                # 粗略：只要距离近又都在地面区域（不拉 laptop 之类会误伤）
                if cname and pname and (cname.lower().startswith(pname.lower()) or pname.lower() in cname.lower()):
                    part_ids.append(other["id"])
        parts_resolved = [obj_by_id[pid] for pid in part_ids]
        center, size = _bbox_from_parts(parts_resolved)
        asm_id = _make_asm_id(asm_idx, o.get("type", "custom")); asm_idx += 1
        entry = {
            "id": asm_id,
            "type": o.get("type", "custom"),
            "pos": [o["pos"][0], o["pos"][1], 0],
            "rotation": o.get("rotation", [0, 0, 0]),
            "size": size,
            "part_ids": part_ids,
            "primary_part_id": o["id"],
            "material_id_primary": o.get("material_id", "default"),
            "_generated_by": "spatial_fallback" if len(part_ids) > 1 else "single_object",
        }
        if o.get("zone"):    entry["zone"] = o["zone"]
        if o.get("label_en"): entry["label_en"] = o["label_en"]
        if o.get("label_zh"): entry["label_zh"] = o["label_zh"]
        assemblies.append(entry)
        for pid in part_ids:
            assigned_ids.add(pid)

    # ── Pass 3：独立 custom objects（Rug / Laptop / Monitor 等）自成 single_object assembly ──
    for o in scene_objects:
        if o["id"] in assigned_ids:
            continue
        asm_id = _make_asm_id(asm_idx, o.get("type", "custom")); asm_idx += 1
        entry = {
            "id": asm_id,
            "type": o.get("type", "custom"),
            "pos": [o["pos"][0], o["pos"][1], o["pos"][2]],  # custom 保留源 z · 避免 Rug 被拍扁
            "rotation": o.get("rotation", [0, 0, 0]),
            "size": list(o["size"]),
            "part_ids": [o["id"]],
            "primary_part_id": o["id"],
            "material_id_primary": o.get("material_id", "default"),
            "_generated_by": "single_object",
        }
        if o.get("zone"):    entry["zone"] = o["zone"]
        if o.get("label_en"): entry["label_en"] = o["label_en"]
        if o.get("label_zh"): entry["label_zh"] = o["label_zh"]
        assemblies.append(entry)
        assigned_ids.add(o["id"])

    # 最后 · 把 assembly_id 写回每个 scene object
    for asm in assemblies:
        for pid in asm["part_ids"]:
            if pid in obj_by_id:
                obj_by_id[pid]["assembly_id"] = asm["id"]

    return assemblies


def auto_complete_shell(scene: dict, blender_objects: list[dict], material_id_by_idx: dict) -> None:
    """
    如果墙 < 4 OR 无 ceiling · 按 bounds 合成
    复用已有的墙材质 / 地板材质（fallback default）
    mutates scene · 加的项有 _auto=True 标记
    """
    bounds = scene.get("bounds")
    if not bounds:
        return

    # 材质选择：优先已有 wall material_id · 否则用 default
    wall_material_id = "default"
    if scene.get("walls"):
        wall_material_id = scene["walls"][0].get("material_id", "default")
    else:
        # 找 Blender 里任何名为 Wall 的 material
        for i, mat_id in material_id_by_idx.items():
            if "wall" in mat_id.lower():
                wall_material_id = mat_id
                break

    ceiling_material_id = "default"
    for i, mat_id in material_id_by_idx.items():
        if any(k in mat_id.lower() for k in ("ceiling", "wall", "plaster")):
            ceiling_material_id = mat_id
            break

    w, d, h = bounds["w"], bounds["d"], bounds["h"]
    hw, hd = w / 2, d / 2

    # 生成 4 面外墙（方向顺时针：N, E, S, W）· 只加缺的
    # 判断方位：已有墙的 start/end 中点大致在房间哪一侧
    existing_sides = set()
    for wall in scene.get("walls", []):
        mx = (wall["start"][0] + wall["end"][0]) / 2
        my = (wall["start"][1] + wall["end"][1]) / 2
        # 最靠近哪条边？
        d_n = abs(my - hd)
        d_s = abs(my - (-hd))
        d_e = abs(mx - hw)
        d_w = abs(mx - (-hw))
        closest = min(d_n, d_s, d_e, d_w)
        if closest == d_n: existing_sides.add("N")
        elif closest == d_s: existing_sides.add("S")
        elif closest == d_e: existing_sides.add("E")
        elif closest == d_w: existing_sides.add("W")

    WALL_DEFS = {
        "N": {"start": [-hw, hd, 0], "end": [hw, hd, 0]},
        "S": {"start": [-hw, -hd, 0], "end": [hw, -hd, 0]},
        "E": {"start": [hw, -hd, 0], "end": [hw, hd, 0]},
        "W": {"start": [-hw, -hd, 0], "end": [-hw, hd, 0]},
    }

    added_walls = 0
    for side in ("N", "S", "E", "W"):
        if side in existing_sides:
            continue
        w_def = WALL_DEFS[side]
        scene.setdefault("walls", []).append({
            "id": f"wall_auto_{side}",
            "name": f"AutoWall_{side}",
            "start": w_def["start"],
            "end": w_def["end"],
            "height": h,
            "thickness": 0.1,
            "material_id": wall_material_id,
            "_auto": True,
        })
        added_walls += 1

    # 天花板：无则合成
    if "ceiling" not in scene:
        scene["ceiling"] = {
            "material_id": ceiling_material_id,
            "thickness": 0.05,
            "height": h,
            "_auto": True,
        }

    # 地板：无则合成
    if "floor" not in scene:
        floor_material_id = "default"
        for i, mat_id in material_id_by_idx.items():
            if any(k in mat_id.lower() for k in ("floor", "wood", "tile")):
                floor_material_id = mat_id
                break
        scene["floor"] = {
            "material_id": floor_material_id,
            "thickness": 0.02,
            "_auto": True,
        }


def clamp_objects_to_bounds(scene: dict) -> int:
    """把任何超出 bounds 的 object 拉回来 · 返回修正数"""
    bounds = scene.get("bounds", {})
    if not bounds:
        return 0
    w, d, h = bounds["w"], bounds["d"], bounds["h"]
    wall_margin = 0.08  # 离墙至少 8cm
    fixed = 0
    for o in scene.get("objects", []):
        pos = o.get("pos", [0, 0, 0])
        size = o.get("size", [0.1, 0.1, 0.1])
        # x · 沿宽度 · [-w/2, w/2] 内减 wall_margin
        hx = size[0] / 2
        min_x = -w / 2 + wall_margin + hx
        max_x =  w / 2 - wall_margin - hx
        new_x = max(min_x, min(max_x, pos[0]))
        # y · 沿深度
        hy = size[1] / 2
        min_y = -d / 2 + wall_margin + hy
        max_y =  d / 2 - wall_margin - hy
        new_y = max(min_y, min(max_y, pos[1]))
        # z · 不能小于 0（地板下）· 也不能顶天花板
        hz = size[2] / 2
        center_z = pos[2]
        # 只 clamp 明显越界的 · 对 pos.z ≈ 0 的（底贴地）放过
        if center_z + hz > h - 0.02:
            center_z = h - 0.02 - hz
        if abs(new_x - pos[0]) > 0.001 or abs(new_y - pos[1]) > 0.001 or abs(center_z - pos[2]) > 0.001:
            o["pos"] = [round(new_x, 3), round(new_y, 3), round(center_z, 3)]
            fixed += 1
    return fixed


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

    all_blender_objects = room.get("objects", [])
    # Phase 3: 不再跳零件 · 全部保留在 scene.objects · assembly 层负责聚合渲染

    for o in all_blender_objects:
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

    # ───────── Post-process · 永远保证 scene 视觉完整 + 逻辑正确 ─────────
    # 1. 补齐墙 / 天花板 / 地板（如果源 Blender 数据缺）
    auto_complete_shell(scene, all_blender_objects, material_id_by_idx)
    # 2. clamp 越界 object · 避免穿墙 / 穿天花
    n_clamped = clamp_objects_to_bounds(scene)
    if n_clamped:
        scene.setdefault("_postprocess", {})["clamped"] = n_clamped
    auto_walls = sum(1 for w in scene.get("walls", []) if w.get("_auto"))
    if auto_walls:
        scene.setdefault("_postprocess", {})["auto_walls"] = auto_walls

    # 3. Phase 3 · 建 assemblies 层（每 object 归属 assembly · 删 / 移 作用于 assembly）
    scene["assemblies"] = build_assemblies(scene.get("objects", []), all_blender_objects)
    scene.setdefault("_postprocess", {})["assembly_count"] = len(scene["assemblies"])

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
