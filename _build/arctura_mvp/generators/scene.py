"""brief → scene · 纯函数 generator（Phase 7.1）

输入：new-schema brief（space.area_sqm / style.keywords / functional_zones / 可选 must_have / style.palette）
输出：合法 scene dict · 形状对齐 pilot `01-study-room/scene.json`

核心逻辑：
  1. bounds 从 area_sqm 推
  2. 4 墙 auto
  3. assemblies 生成：must_have 清单 > space.type 兜底 > default
  4. materials 按 style.keywords 选色板
  5. 灯光 3 基础
  6. 布局：沿墙保守分布 · 避免重叠

不依赖外部服务（纯函数 · MCP-friendly · 可单测）
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Optional

from ._resolve_space_type import resolve_space_type, merge_furniture_lists

# 家具库 · 单一真源（前端 / renderer / generator 共用）
_LIB_PATH = Path(__file__).resolve().parents[3] / "data" / "furniture-library.json"


def _load_furniture_lib() -> dict:
    """读 data/furniture-library.json · 失败返空 dict（不抛）"""
    try:
        return json.loads(_LIB_PATH.read_text()).get("items", {})
    except Exception:
        return {}


# ───────── 默认家具清单（按 space.type 兜底）─────────
# 值是 furniture-library.json 的 key（当前 12 项：chair_standard / chair_lounge /
# sofa_2seat / sofa_3seat / desk_standard / table_coffee / table_dining / bed_queen /
# shelf_open / closet_tall / lamp_floor / lamp_pendant）· 不直接内联尺寸。
#
# 每个 enum（见 api/_shared/space-type-keywords.json::enum）都必须有一行 ·
# test_scene_distinguish_types.py 锁住 office vs cafe 等组合家具有别 ·
# 防止今天 bug（hybrid cafe-office → default fallback → 永远同一个 scene）。
_DEFAULTS_BY_TYPE: dict[str, list[str]] = {
    "office":       ["desk_standard", "chair_standard", "shelf_open", "lamp_floor"],
    "bedroom":      ["bed_queen", "closet_tall", "lamp_pendant"],
    "study":        ["desk_standard", "chair_standard", "shelf_open", "lamp_floor"],
    "living_room":  ["sofa_3seat", "table_coffee", "shelf_open", "lamp_floor"],
    "cafe":         ["table_dining", "chair_standard", "shelf_open", "lamp_pendant"],
    "dining":       ["table_dining", "chair_standard", "lamp_pendant"],
    "retail":       ["shelf_open", "chair_lounge", "table_coffee", "lamp_pendant"],
    "clinic":       ["desk_standard", "chair_standard", "chair_lounge", "lamp_floor"],
    "gallery":      ["chair_lounge", "shelf_open", "lamp_pendant"],
    "multipurpose": ["table_coffee", "chair_standard", "shelf_open", "lamp_floor"],
    "default":      ["chair_standard", "table_coffee", "lamp_floor"],
}

# must_have 里的通用词 → library type 映射
_MUST_HAVE_ALIASES: dict[str, str] = {
    "desk": "desk_standard", "书桌": "desk_standard", "办公桌": "desk_standard",
    "chair": "chair_standard", "椅子": "chair_standard", "办公椅": "chair_standard",
    "sofa": "sofa_3seat", "沙发": "sofa_3seat",
    "couch": "sofa_2seat",
    "bed": "bed_queen", "床": "bed_queen",
    "shelf": "shelf_open", "bookshelf": "shelf_open", "书架": "shelf_open",
    "closet": "closet_tall", "衣柜": "closet_tall", "wardrobe": "closet_tall",
    "table": "table_coffee", "茶几": "table_coffee",
    "dining_table": "table_dining", "餐桌": "table_dining",
    "lamp": "lamp_floor", "灯": "lamp_floor", "落地灯": "lamp_floor",
    "pendant": "lamp_pendant", "吊灯": "lamp_pendant",
    "lounge_chair": "chair_lounge", "休闲椅": "chair_lounge",
}


# ───────── 风格色板 · style.keywords → materials preset ─────────

_PALETTE_PRESETS: dict[str, dict] = {
    "japandi": {
        "woodfloor":  {"base_color": "#C9B38C", "roughness": 0.55, "metallic": 0.0, "label": "WoodFloor"},
        "wall":       {"base_color": "#F5F1E8", "roughness": 0.92, "metallic": 0.0, "label": "Wall"},
        "lightwood":  {"base_color": "#D7C4A8", "roughness": 0.55, "metallic": 0.0, "label": "LightOak"},
        "charcoal":   {"base_color": "#6B6F73", "roughness": 0.70, "metallic": 0.02, "label": "Charcoal"},
        "linen_cream":{"base_color": "#D9CFB8", "roughness": 0.97, "metallic": 0.0, "label": "CreamLinen"},
        "screen":     {"base_color": "#111318", "roughness": 0.25, "metallic": 0.05, "label": "Screen"},
        "default":    {"base_color": "#B8A888", "roughness": 0.6,  "metallic": 0.0, "label": "Default"},
    },
    "minimal": {
        "woodfloor":  {"base_color": "#E8E3D6", "roughness": 0.6,  "metallic": 0.0, "label": "PaleFloor"},
        "wall":       {"base_color": "#FAFAF7", "roughness": 0.95, "metallic": 0.0, "label": "Wall"},
        "lightwood":  {"base_color": "#F2EADF", "roughness": 0.5,  "metallic": 0.0, "label": "PaleWood"},
        "charcoal":   {"base_color": "#2C3539", "roughness": 0.7,  "metallic": 0.05, "label": "Charcoal"},
        "linen_cream":{"base_color": "#F0ECDF", "roughness": 0.97, "metallic": 0.0, "label": "Linen"},
        "screen":     {"base_color": "#111318", "roughness": 0.25, "metallic": 0.05, "label": "Screen"},
        "default":    {"base_color": "#E0DAD0", "roughness": 0.6,  "metallic": 0.0, "label": "Default"},
    },
    "industrial": {
        "woodfloor":  {"base_color": "#4A4540", "roughness": 0.65, "metallic": 0.0, "label": "DarkWood"},
        "wall":       {"base_color": "#8A857E", "roughness": 0.9,  "metallic": 0.0, "label": "Concrete"},
        "lightwood":  {"base_color": "#6B5D4E", "roughness": 0.6,  "metallic": 0.05, "label": "AgedWood"},
        "charcoal":   {"base_color": "#33363A", "roughness": 0.5,  "metallic": 0.2,  "label": "Steel"},
        "linen_cream":{"base_color": "#8E8678", "roughness": 0.85, "metallic": 0.0, "label": "Canvas"},
        "screen":     {"base_color": "#111318", "roughness": 0.25, "metallic": 0.1,  "label": "Screen"},
        "default":    {"base_color": "#5C564E", "roughness": 0.6,  "metallic": 0.1,  "label": "Default"},
    },
    "default": {
        "woodfloor":  {"base_color": "#C9B38C", "roughness": 0.55, "metallic": 0.0, "label": "WoodFloor"},
        "wall":       {"base_color": "#F5F1E8", "roughness": 0.92, "metallic": 0.0, "label": "Wall"},
        "lightwood":  {"base_color": "#D7C4A8", "roughness": 0.55, "metallic": 0.0, "label": "LightWood"},
        "charcoal":   {"base_color": "#767C81", "roughness": 0.6,  "metallic": 0.05, "label": "Charcoal"},
        "linen_cream":{"base_color": "#D9CFB8", "roughness": 0.97, "metallic": 0.0, "label": "Linen"},
        "screen":     {"base_color": "#111318", "roughness": 0.25, "metallic": 0.05, "label": "Screen"},
        "default":    {"base_color": "#B8A888", "roughness": 0.6,  "metallic": 0.0, "label": "Default"},
    },
}


def _pick_palette(keywords: list[str]) -> str:
    """按 style.keywords 选色板 preset key"""
    kws = {k.lower() for k in (keywords or [])}
    if any(k in kws for k in ["日式", "japandi", "japanese", "禅"]):
        return "japandi"
    if any(k in kws for k in ["极简", "minimal", "minimalist", "北欧"]):
        return "minimal"
    if any(k in kws for k in ["工业", "industrial", "loft"]):
        return "industrial"
    return "default"


# ───────── 布局 · 沿墙保守分布 ─────────

def _layout_assemblies(types: list[str], bounds: dict, lib: dict) -> list[tuple[str, list[float], list[float], list[float]]]:
    """沿墙循环放置 · 返回 [(type, pos, size, rotation), ...]

    策略（保守 · 避免重叠 · 不求美）：
      - 靠墙放一圈：desk/shelf 贴后墙 · chair/sofa 贴前墙 · table 居中 · lamp 角落
      - 留 0.3m 墙距 + 0.2m 家具间距
    """
    w = bounds["w"]
    d = bounds["d"]
    MARGIN = 0.3    # 墙距
    GAP    = 0.2    # 家具间距

    # 按功能分组
    wall_back = []   # 贴后墙（+y）
    wall_front = []  # 贴前墙（-y）
    center = []      # 居中
    corner = []      # 角落

    for t in types:
        if t in ("desk_standard", "shelf_open", "closet_tall"):
            wall_back.append(t)
        elif t in ("sofa_2seat", "sofa_3seat", "bed_queen"):
            wall_front.append(t)
        elif t in ("table_coffee", "table_dining"):
            center.append(t)
        elif t in ("lamp_floor", "lamp_pendant"):
            corner.append(t)
        elif t in ("chair_standard", "chair_lounge"):
            # chair 放 desk 前面（如果有 desk） · 否则居中
            if "desk_standard" in types:
                wall_back.append(t)  # 标记为跟 desk 一组（后处理）
            else:
                center.append(t)

    placed = []

    # 贴后墙 · 从 -w/2+MARGIN 向 +w/2 流
    x_cursor = -w/2 + MARGIN
    last_desk = None  # (x, y, size) · chair 跟随
    for t in wall_back:
        entry = lib.get(t, {})
        size = list(entry.get("default_size", [0.5, 0.5, 0.8]))
        sz_w, sz_d, sz_h = size

        if t == "chair_standard" and last_desk is not None:
            # chair 放 desk 前方（-y 方向）· 桌前沿 - GAP - chair_depth/2
            dx, dy, ds = last_desk
            desk_front_y = dy - ds[1] / 2
            chair_y = desk_front_y - GAP - sz_d / 2
            pos = [dx, round(chair_y, 2), 0]
            rot = [0, 0, 180]  # face desk
            placed.append((t, pos, size, rot))
            continue

        x = x_cursor + sz_w/2
        y = d/2 - MARGIN - sz_d/2
        z = 0 if entry.get("anchor", "bottom") == "bottom" else (bounds["h"] - sz_h)
        # shelf_open 特殊 · 挂墙（z > 0 · 后贴墙）
        if t == "shelf_open":
            z = sz_h / 2 + 0.5
            y = d/2 - sz_d/2 - 0.05  # 贴墙更紧
        placed.append((t, [round(x, 2), round(y, 2), round(z, 2)], size, [0, 0, 0]))
        if t == "desk_standard":
            last_desk = (round(x, 2), round(y, 2), size)
        x_cursor += sz_w + GAP

    # 贴前墙
    x_cursor = -w/2 + MARGIN
    for t in wall_front:
        entry = lib.get(t, {})
        size = list(entry.get("default_size", [1.6, 0.9, 0.85]))
        sz_w, sz_d, sz_h = size
        x = x_cursor + sz_w/2
        y = -d/2 + MARGIN + sz_d/2
        z = 0
        placed.append((t, [round(x, 2), round(y, 2), round(z, 2)], size, [0, 0, 0]))
        x_cursor += sz_w + GAP

    # 居中
    for i, t in enumerate(center):
        entry = lib.get(t, {})
        size = list(entry.get("default_size", [1.0, 0.6, 0.45]))
        pos = [round((i - len(center)/2) * (size[0] + GAP), 2), 0, 0]
        placed.append((t, pos, size, [0, 0, 0]))

    # Phase 9.2 · 往每个主家具加装饰小物（书/花瓶/杯等）· 推动 spec L398 "60+ objects" 接近达成
    # 每个已 placed 的 assembly 带 2-3 个装饰 · 总数 ~8 主 × 2.5 = 20 加到 clutter
    clutter = []
    _DECOR_SIZES = [  # 小物件 default_size · 米
        ("book", [0.18, 0.12, 0.03]),
        ("vase", [0.12, 0.12, 0.25]),
        ("cup", [0.08, 0.08, 0.09]),
        ("plant_small", [0.2, 0.2, 0.35]),
        ("picture_frame", [0.25, 0.04, 0.35]),
    ]
    decor_idx = 0
    for pt, ppos, psize, _ in placed:
        # Phase 9.2 · 更激进 · spec L398 要 60+ objects
        if pt in ("desk_standard", "table_coffee", "table_dining"):
            n_decor = 6   # 桌面 · 书 + 杯 + 小盆栽 + 相框 + etc
        elif pt in ("shelf_open", "closet_tall"):
            n_decor = 8   # 架子 · 满格书
        elif pt in ("sofa_2seat", "sofa_3seat", "bed_queen"):
            n_decor = 2   # 抱枕等
        elif pt in ("chair_standard", "chair_lounge", "lamp_floor"):
            n_decor = 1   # 配一本书或小物
        else:
            n_decor = 0
        for k in range(n_decor):
            dtype, dsize = _DECOR_SIZES[decor_idx % len(_DECOR_SIZES)]
            decor_idx += 1
            # 放在主家具顶上（z = 主家具高度 + decor/2）· x/y 偏移一点
            offx = (k - n_decor/2 + 0.5) * 0.3
            decor_pos = [round(ppos[0] + offx, 2), round(ppos[1], 2),
                         round(psize[2] + dsize[2]/2, 2)]
            clutter.append((dtype, decor_pos, dsize, [0, 0, 0]))

    # 角落
    corner_slots = [
        [-w/2 + MARGIN, -d/2 + MARGIN],   # 前左
        [ w/2 - MARGIN, -d/2 + MARGIN],   # 前右
        [ w/2 - MARGIN,  d/2 - MARGIN],   # 后右
        [-w/2 + MARGIN,  d/2 - MARGIN],   # 后左
    ]
    for i, t in enumerate(corner):
        entry = lib.get(t, {})
        size = list(entry.get("default_size", [0.5, 0.5, 1.6]))
        slot = corner_slots[i % 4]
        if t == "lamp_pendant":
            # 吊灯挂天花板中心
            placed.append((t, [0, 0, bounds["h"] - size[2] - 0.05], size, [0, 0, 0]))
        else:
            placed.append((t, [round(slot[0], 2), round(slot[1], 2), 0], size, [0, 0, 0]))

    # 加装饰 clutter 到 placed 尾部（spec L398 推 60+ objects · LIGHT 能做到 ~25-40）
    placed.extend(clutter)
    return placed


# ───────── 主入口 ─────────

def build_scene_from_brief(brief: dict, slug: str) -> dict:
    """brief → scene · 纯函数 · 不触 KV / 不写文件

    brief 支持字段：
      - space.area_sqm (必)
      - space.type (可选 · 默认 "default")
      - style.keywords (列表 · 影响色板)
      - style.palette (可选 · dict · 覆盖 _PALETTE_PRESETS)
      - must_have (可选 · list[str] · 直接给家具清单)
      - functional_zones (可选 · 影响家具数量)
    """
    if not brief:
        raise ValueError("brief 为空 · 无法生成 scene")
    space = brief.get("space") or {}
    area = float(space.get("area_sqm") or 20)
    if area <= 0:
        area = 20

    # 1. bounds
    w = round((area * 1.25) ** 0.5, 1)
    d = round(area / w, 1)
    h = 3.0 if area >= 25 else 2.8
    bounds = {"w": w, "d": d, "h": h}

    # 2. 4 墙 auto
    walls = [
        {"id": "wall_Back", "name": "BackWall",
         "start": [-w/2, d/2, 0], "end": [w/2, d/2, 0],
         "height": h, "thickness": 0.1, "material_id": "wall"},
        {"id": "wall_auto_S", "name": "AutoWall_S",
         "start": [-w/2, -d/2, 0], "end": [w/2, -d/2, 0],
         "height": h, "thickness": 0.1, "material_id": "wall", "_auto": True},
        {"id": "wall_auto_E", "name": "AutoWall_E",
         "start": [w/2, -d/2, 0], "end": [w/2, d/2, 0],
         "height": h, "thickness": 0.1, "material_id": "wall", "_auto": True},
        {"id": "wall_auto_W", "name": "AutoWall_W",
         "start": [-w/2, -d/2, 0], "end": [-w/2, d/2, 0],
         "height": h, "thickness": 0.1, "material_id": "wall", "_auto": True},
    ]

    # 3. 家具清单解析
    lib = _load_furniture_lib()
    must_have = brief.get("must_have") or []
    if must_have:
        types = []
        for raw in must_have:
            key = str(raw).strip().lower().replace(" ", "_")
            mapped = _MUST_HAVE_ALIASES.get(key) or _MUST_HAVE_ALIASES.get(str(raw).strip())
            if mapped:
                types.append(mapped)
            elif key in lib:
                types.append(key)
            # 不识别的静默跳过
    else:
        # 优先读 space.resolved_types（normalize-brief.js 写入的并集 · 见 ADR-001）
        # 这样 LLM 写 "hybrid cafe-office" → normalize 后 type='multipurpose' resolved_types=[cafe,office]
        # → 这里取 cafe ∪ office 并集 · 不是 multipurpose 单类型默认家具
        # 没经 normalize 的旧数据 → resolved_types 缺 → 退到 type_raw / type 现场解析
        resolved_types = space.get("resolved_types")
        if isinstance(resolved_types, list) and resolved_types:
            resolved = [str(t) for t in resolved_types if isinstance(t, str)]
        else:
            # 兜底：解析 type_raw（normalize 保留的原值）或 type 本身
            raw = space.get("type_raw") or space.get("type")
            resolved = resolve_space_type(raw)

        types = merge_furniture_lists(resolved, _DEFAULTS_BY_TYPE)
        if not types:
            types = list(_DEFAULTS_BY_TYPE["default"])

        # cap = 8：极端 type 字符串（"office cafe clinic showroom retail dining bedroom"）
        # 会拼出 11+ 件家具 · 小房间 _layout_assemblies 沿墙铺会溢出。
        # 8 是 _layout_assemblies 当前 4 + 4 + 居中 + 角落布局的安全上限。
        # TODO Step 2 hardening：改面积分档（4/6/8）· 保每个命中类型至少 1 件代表家具
        _MAX_MAIN_FURNITURE = 8
        if len(types) > _MAX_MAIN_FURNITURE:
            types = types[:_MAX_MAIN_FURNITURE]

    # 若 functional_zones 数 > 3 · 多加一组家具副本
    zones_n = len(brief.get("functional_zones") or [])
    if zones_n >= 3 and len(types) < 6:
        extra = _DEFAULTS_BY_TYPE["default"][:zones_n - len(types)]
        types = types + extra

    # 4. 布局 + 生成 objects/assemblies
    placed = _layout_assemblies(types, bounds, lib)
    objects, assemblies = [], []
    for i, (t, pos, size, rot) in enumerate(placed, 1):
        entry = lib.get(t, {})
        obj_id = f"obj_{t}_{i}"
        asm_id = f"asm_{t}_{i}"
        mat_id = entry.get("default_material_id") or "default"
        label_en = entry.get("label_en", t)
        label_zh = entry.get("label_zh", t)
        objects.append({
            "id": obj_id, "type": t, "pos": pos, "size": size, "rotation": rot,
            "material_id": mat_id, "label_en": label_en, "label_zh": label_zh,
            "assembly_id": asm_id,
        })
        assemblies.append({
            "id": asm_id, "type": t, "pos": pos, "rotation": rot, "size": size,
            "part_ids": [obj_id], "primary_part_id": obj_id,
            "material_id_primary": mat_id,
            "label_en": label_en, "label_zh": label_zh,
            "_generated_by": "scene_generator_v1",
        })

    # 5. 灯光 3 基础
    lights = [
        {"id": "sun_1", "type": "sun",
         "dir": [0.3, 0.55, -0.78], "power": 3.0, "intensity": 3.0,
         "color": [1.0, 0.95, 0.85]},
        {"id": "area_2", "type": "area",
         "pos": [0, 0.5, h - 0.2], "power": 80.0, "intensity": 5.5,
         "color": [1.0, 0.95, 0.85], "size": 1.0, "size_y": 0.8, "shape": "RECTANGLE"},
        {"id": "point_3", "type": "point",
         "pos": [w/2 - 0.5, -d/2 + 0.5, h - 1.4], "power": 45.0, "intensity": 24.0,
         "color": [1.0, 0.88, 0.7]},
    ]

    # 6. 材质 · 按 style.keywords 选 preset · palette 覆盖
    preset_key = _pick_palette((brief.get("style") or {}).get("keywords") or [])
    materials = dict(_PALETTE_PRESETS[preset_key])
    override = (brief.get("style") or {}).get("palette")
    if isinstance(override, dict):
        for k, v in override.items():
            if isinstance(v, dict):
                materials[k] = {**materials.get(k, {}), **v}
            elif isinstance(v, str):
                materials.setdefault(k, {})["base_color"] = v

    # 7. 组装最终 scene
    return {
        "schema_version": "1.0",
        "unit": "m",
        "bounds": bounds,
        "walls": walls,
        "objects": objects,
        "assemblies": assemblies,
        "lights": lights,
        "materials": materials,
        "env": {
            "hdri": "/assets/hdri/interior_neutral_2k.hdr",
            "hdri_intensity": 1.0,
            "background_color": "#E8E2D5",
        },
        "floor": {"material_id": "woodfloor", "thickness": 0.02},
        "ceiling": {"material_id": "wall", "thickness": 0.05, "height": h, "_auto": True},
        "camera_default": {
            "pos": [round(w * 0.7, 2), round(-d * 0.7, 2), round(h * 0.6, 2)],
            "lookAt": [0.0, 0.0, 1.2],
            "fov": 50,
        },
        "_generated_by": "scene_generator_v1",
        "_generated_for_slug": slug,
    }
