"""
P4 — 从 brief.json + room.json 提取设计意图，合成精确的 prompt

核心思路：尊重原始设计（风格关键词 / 色板 / 关键家具 / 参考品牌 / 灯光），
而不是用通用模板覆盖掉用户填写的设计信息。

优先级（token 预算有限，按重要性排序）：
    1. 风格关键词（最重要，决定整个美学走向）
    2. 场景类型（coffee shop / gallery / clinic...）
    3. 色板（名称化后的颜色）
    4. 关键家具（前 2-3 个 functional zone 的 key_objects）
    5. 灯光气氛
    6. 参考品牌（AI 识别度高的名牌能显著提升效果）
"""
import re
from pathlib import Path

QUALITY_SUFFIX = (
    "professional interior photography, realistic materials, "
    "detailed textures, 8k uhd, architectural digest style"
)

QUALITY_SUFFIX_ARCH = (
    "professional architectural photography, exterior building shot, "
    "realistic materials and textures, natural daylight, golden hour, "
    "landscape surrounded by nature, 8k uhd, real estate photography"
)

NEGATIVE_PROMPT = (
    "low quality, blurry, cartoon, anime, sketch, wireframe, "
    "oversaturated, distorted, deformed, text, watermark, "
    "ugly, duplicate, morbid"
)

# 建筑外立面专用 negative — 防止 AI 把建筑渲染成室内家具/玩具模型
NEGATIVE_ARCH = (
    "low quality, blurry, cartoon, anime, sketch, wireframe, "
    "oversaturated, distorted, deformed, text, watermark, "
    "ugly, duplicate, morbid, "
    "indoor, interior scene, furniture, room, sofa, bed, desk, "
    "toy model, miniature, dollhouse, tabletop, wooden flooring, parquet"
)

# 表面类型（应该后置）：floor_terrazzo → terrazzo floor
SURFACE_WORDS = {"floor", "wall", "ceiling", "surface"}

# 材质类型（描述词应该前置）：wood_warm → warm wood
MATERIAL_WORDS = {
    "wood", "metal", "brass", "copper", "stone", "marble", "glass",
    "fabric", "leather", "concrete", "terrazzo", "tile", "plaster"
}

# 核心材质原子（用于跨字段去重 + negative 自适应）
# 包括语义相近的词形，便于从短语提取
MATERIAL_ATOMS = {
    "wood", "metal", "brass", "copper", "stone", "marble", "granite",
    "glass", "fabric", "leather", "concrete", "terrazzo", "tile",
    "plaster", "bamboo", "rattan", "steel", "iron",
}

# 这些材质如果渲染到墙面容易让空间看起来错位/过度风格化
# 自适应 negative：若 prompt 里大量出现某材质，自动禁止它出现在墙面
WALL_CONTAMINATABLE = {
    "wood", "metal", "brass", "copper", "concrete", "stone",
    "marble", "tile", "bamboo", "steel", "iron",
}


def extract_atoms(phrase: str) -> set[str]:
    """从短语抽取核心材质原子（wooden → wood, brass accents → brass）"""
    if not phrase:
        return set()
    lower = phrase.lower()
    atoms = set()
    for m in MATERIAL_ATOMS:
        # 匹配 "wood" / "wooden" / "brass" 等词根
        if m in lower:
            atoms.add(m)
    return atoms

# 建筑 MVP slug / variant → 外立面场景英文短语
ARCH_SLUG_TO_SCENE = {
    # 住宅 variants
    "nordic-cabin": "nordic wooden cabin exterior",
    "neo-chinese": "neo-Chinese style house exterior",
    "mediterranean": "mediterranean villa exterior",
    # arch-mvp 标准场景
    "house": "modern single-family house exterior",
    "office-building": "modern glass office building exterior",
    "boutique-hotel": "boutique hotel exterior facade",
    "community-center": "community center building exterior",
    "modern-chinese-house": "modern Chinese residence exterior",
    "small-library": "small public library building exterior",
    "loft-coworking": "industrial loft coworking building exterior",
    "small-clinic": "small medical clinic building exterior",
    "mixed-use": "modern mixed-use building exterior",
    "sports-complex": "sports complex building exterior",
    "nt-family-house": "suburban family house exterior",
    "dongbei-village-house": "northeast Chinese village house exterior",
    "cowork-tower": "modern coworking tower exterior",
    "art-pavilion": "contemporary art pavilion exterior",
    "hillside-villa": "hillside villa exterior",
    "community-fitness": "community fitness building exterior",
    "lakeside-retreat": "lakeside residential retreat exterior",
}

# MVP slug → 场景类型标准化
SLUG_TO_SCENE = {
    "coffee-shop": "specialty coffee shop interior",
    "coffee-bakery": "coffee bakery interior",
    "bistro-restaurant": "bistro restaurant interior",
    "conference-room": "executive conference room",
    "coworking": "coworking space interior",
    "fitness-studio": "fitness studio interior",
    "kids-daycare": "children daycare interior",
    "bookstore": "independent bookstore interior",
    "hair-salon": "modern hair salon interior",
    "art-gallery": "contemporary art gallery interior",
    "dental-clinic": "modern dental clinic interior",
    "recording-studio": "professional recording studio",
    "ai-startup-office": "tech startup office interior",
    "floral-atelier": "elegant floral atelier interior",
    "elderly-friendly-home": "accessible elderly home interior",
    "luxury-indoor-pool": "luxury indoor swimming pool",
    "student-study-hall": "university study hall interior",
    "industrial-living-room": "industrial loft living room",
    "zen-tea-room": "zen Japanese tea room",
    "study-room": "modern study room interior",
    "living-room": "modern living room interior",
    "boutique-book-cafe": "boutique book cafe interior",
    "book-cafe": "boutique book cafe interior",
    "book-store": "independent bookstore interior",
}


def humanize_palette_key(key: str) -> str:
    """
    floor_terrazzo → terrazzo floor
    wood_warm      → warm wood
    metal_black    → black metal
    wall_cream     → cream wall
    brass_accent   → brass accent
    foliage_green  → green foliage (植物)
    """
    parts = key.lower().split("_")
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        a, b = parts
        # 表面词在前 → 表面词后置（floor_terrazzo → terrazzo floor）
        if a in SURFACE_WORDS:
            return f"{b} {a}"
        # 材质词在前 → 描述词前置（wood_warm → warm wood）
        if a in MATERIAL_WORDS:
            return f"{b} {a}"
        # 默认：保持顺序
        return f"{a} {b}"
    return " ".join(parts)


def extract_style_keywords(brief: dict, max_n: int = 3) -> str:
    """提取风格关键词，用空格连接（避免 SD 解析连字符）"""
    style = brief.get("style", {})
    if isinstance(style, dict):
        keywords = style.get("keywords", [])
    elif isinstance(style, list):
        keywords = style
    else:
        return ""

    keywords = [str(k).replace("-", " ") for k in keywords[:max_n]]
    return ", ".join(keywords)


def extract_palette_descriptors(brief: dict, top_n: int = 4) -> list[str]:
    """提取色板的可读名称（前 N 个）"""
    style = brief.get("style", {})
    if not isinstance(style, dict):
        return []
    palette = style.get("palette", {})
    if not isinstance(palette, dict):
        return []
    # 取前 top_n 个（按字典顺序 = 原始顺序，通常重要的在前）
    keys = list(palette.keys())[:top_n]
    return [humanize_palette_key(k) for k in keys]


SKIP_ZONE_KEYWORDS = {
    "入口", "等候", "门口", "衣帽", "卫生间", "洗手", "厕所", "toilet",
    "entrance", "waiting", "bathroom", "restroom", "storage", "储物",
    "后厨", "备餐", "kitchen",  # 后厨对效果图不重要
}


def extract_key_objects(brief: dict, top_zones: int = 2, max_objects: int = 5) -> list[str]:
    """提取关键家具。跳过入口/卫生间/储物等辅助区域，优先主功能区"""
    zones = brief.get("functional_zones", [])
    # 按面积排序（大的 zone 更重要），并过滤掉辅助区
    main_zones = []
    for zone in zones:
        if not isinstance(zone, dict):
            continue
        name = str(zone.get("name", "")).lower()
        if any(kw in name for kw in SKIP_ZONE_KEYWORDS):
            continue
        main_zones.append(zone)
    # 按 area_m2 降序（主区域通常面积最大）
    main_zones.sort(
        key=lambda z: float(z.get("area_m2", z.get("area_sqm", 0)) or 0),
        reverse=True,
    )

    objects = []
    for zone in main_zones[:top_zones]:
        key_objs = zone.get("key_objects", [])
        for obj in key_objs:
            obj_clean = _clean_object_name(str(obj))
            if obj_clean and obj_clean not in objects:
                objects.append(obj_clean)
        if len(objects) >= max_objects:
            break
    return objects[:max_objects]


def _clean_object_name(obj: str) -> str:
    """
    清理家具描述 → 可进 prompt 的英文短语
    '4 × 圆木桌' → 'round wooden tables'
    'L 型吧台' → 'L-shaped bar'
    '咖啡机 La Marzocco' → 'La Marzocco espresso machine'
    中文直译简单映射
    """
    s = str(obj).strip()
    # 去掉数量前缀 "4 × ", "8 ×"
    s = re.sub(r"^\d+\s*[×x]\s*", "", s)
    # 去掉尺寸 "4m ", "5 层"
    s = re.sub(r"^\d+\s*[mM米层]\s*", "", s)
    s = s.strip()

    # 中文 → 英文关键词映射表
    cn_to_en = {
        "长凳": "bench", "衣帽架": "coat rack", "地垫": "door mat",
        "吧台": "bar counter", "L 型吧台": "L-shaped bar", "L型吧台": "L-shaped bar",
        "咖啡机": "espresso machine", "展示冷柜": "display cooler",
        "后吧架": "back bar shelf", "圆木桌": "round wooden tables",
        "木椅": "wooden chairs", "长木桌": "long wooden table",
        "长凳 / 高脚凳": "benches and bar stools", "高脚凳": "bar stools",
        "展示书架": "display bookshelf", "书架": "bookshelf",
        "操作台": "work counter", "水槽": "sink", "冰箱": "refrigerator",
        "洗手台": "washbasin", "隔断": "partition",
        "落地大型盆栽": "large potted plants", "盆栽": "potted plants",
        "沙发": "sofa", "茶几": "coffee table", "单椅": "armchair",
        "电视": "TV", "电视柜": "TV console", "书柜": "bookshelf",
        "餐桌": "dining table", "餐椅": "dining chairs", "地毯": "area rug",
        "吊灯": "pendant lights", "落地灯": "floor lamp", "台灯": "table lamp",
        "镜子": "mirror", "壁画": "wall art", "植物": "plants",
        "床": "bed", "床头柜": "nightstands", "衣柜": "wardrobe",
    }
    for cn, en in cn_to_en.items():
        if cn in s:
            return en

    # 如果还是中文，返回空
    if re.search(r"[\u4e00-\u9fff]", s):
        return ""
    return s.lower()


def extract_lighting(brief: dict) -> str:
    """提取灯光描述"""
    lighting = brief.get("lighting", {})
    if not isinstance(lighting, dict):
        return ""
    parts = []
    main = lighting.get("main", "")
    warmth = lighting.get("warmth", "")
    # 暖光提取
    if warmth:
        if "2700" in str(warmth) or "warm" in str(warmth).lower():
            parts.append("warm 2700K lighting")
        elif "3000" in str(warmth):
            parts.append("warm 3000K lighting")
        elif "4000" in str(warmth):
            parts.append("neutral 4000K lighting")
    # 灯具类型
    if "吊灯" in main or "pendant" in main.lower():
        if "黄铜" in main or "brass" in main.lower():
            parts.insert(0, "brass pendant lights")
        else:
            parts.insert(0, "pendant lights")
    elif "筒灯" in main or "downlight" in main.lower():
        parts.insert(0, "recessed downlights")
    return ", ".join(parts)


def extract_reference(brief: dict, max_n: int = 1) -> str:
    """提取参考品牌（AI 识别度高的，优先纯英文名）"""
    style = brief.get("style", {})
    if not isinstance(style, dict):
        return ""
    brands = style.get("reference_brands", [])
    if not brands:
        return ""
    # 优先选择纯英文/拉丁字符的品牌（CLIP 对中文识别差）
    def clean(b: str) -> str:
        b = str(b).strip()
        if b.startswith("%"):
            b = b[1:].strip()
        # 从混合字符串中提取拉丁部分："蔦屋書店 Tsutaya T-Site" → "Tsutaya T-Site"
        latin_parts = re.findall(r"[A-Za-z][A-Za-z0-9\s\-&\.']*[A-Za-z0-9]", b)
        if latin_parts:
            return max(latin_parts, key=len).strip()
        return b if not re.search(r"[\u4e00-\u9fff]", b) else ""

    cleaned = [clean(b) for b in brands]
    cleaned = [c for c in cleaned if c]
    if not cleaned:
        return ""
    return f"{cleaned[0]} aesthetic"


def extract_room_materials(room: dict | None, max_n: int = 3) -> list[str]:
    """从 room.json 提取材质名（camelCase → 空格分隔）"""
    if not room:
        return []
    materials = room.get("materials", [])
    names = []
    for mat in materials[:max_n]:
        if not isinstance(mat, dict):
            continue
        name = mat.get("name", "")
        if name:
            # TerrazzoFloor → terrazzo floor
            spaced = re.sub(r"(?<!^)(?=[A-Z])", " ", name).lower()
            names.append(spaced)
    return names


def detect_scene_category(brief: dict, mvp_dir: Path | None = None) -> str:
    """返回 'architecture' 或 'interior'。依赖 brief 字段 + 目录路径。"""
    # 1. brief 明确标记
    if brief.get("building_type"):
        return "architecture"
    if isinstance(brief.get("building"), dict) and brief["building"].get("floors"):
        return "architecture"
    # 2. 目录路径线索
    if mvp_dir:
        path_str = str(mvp_dir).lower()
        if "arch-mvp" in path_str or mvp_dir.name.startswith("arch-"):
            return "architecture"
    # 3. 默认室内
    return "interior"


def infer_arch_scene(brief: dict, mvp_dir: Path | None = None) -> str:
    """
    推断建筑场景 → 英文短语
    优先级: brief.variant → brief.slug → MVP 目录 slug → building_type 回退
    """
    candidates = []
    variant = str(brief.get("variant", "")).lower()
    if variant:
        # v1-nordic-cabin → nordic-cabin
        candidates.append(re.sub(r"^v\d+-", "", variant))
        candidates.append(variant)
    slug_field = str(brief.get("slug", "")).lower()
    if slug_field:
        candidates.append(re.sub(r"^\d+-", "", slug_field))
    if mvp_dir:
        candidates.append(re.sub(r"^(arch-)?\d+-", "", mvp_dir.name.lower()))
        candidates.append(mvp_dir.name.lower())

    for slug in candidates:
        if slug in ARCH_SLUG_TO_SCENE:
            return ARCH_SLUG_TO_SCENE[slug]
        for key, val in ARCH_SLUG_TO_SCENE.items():
            if key in slug:
                return val

    # 基于 building_type 回退
    btype = str(brief.get("building_type", "")).lower()
    if btype == "residential":
        return "modern residential building exterior"
    if btype == "commercial":
        return "modern commercial building exterior"
    if btype == "office":
        return "modern office building exterior"
    if btype == "mixed":
        return "modern mixed-use building exterior"
    return "modern building exterior"


def extract_architecture_context(brief: dict) -> list[str]:
    """提取建筑上下文：层数 / 选址环境 / 建筑类型"""
    parts = []
    b = brief.get("building", {})
    if isinstance(b, dict):
        floors = b.get("floors") or b.get("stories")
        if floors:
            parts.append(f"{floors}-story building")

    site = brief.get("site", {})
    if isinstance(site, dict):
        orientation = str(site.get("orientation") or "")
        setting = str(site.get("setting") or site.get("context") or "")
        combined = f"{orientation} {setting}".lower()
        if "湖" in orientation or "lake" in combined:
            parts.append("lakeside setting")
        if "山" in orientation or "hill" in combined or "mountain" in combined:
            parts.append("hillside landscape")
        if "海" in orientation or "ocean" in combined or "seaside" in combined:
            parts.append("seaside location")
        if "森林" in orientation or "forest" in combined or "woodland" in combined:
            parts.append("forest surroundings")

    return parts


def infer_scene_type(brief: dict, mvp_dir: Path | None = None) -> str:
    """
    推断场景类型 → 英文短语
    优先级: brief.slug → MVP 目录 slug → brief.project → 回退
    """
    candidates = []
    # 1. brief.slug（最可靠）
    slug_field = str(brief.get("slug", "")).lower()
    if slug_field:
        candidates.append(re.sub(r"^\d+-", "", slug_field))
    # 2. MVP 目录名
    if mvp_dir:
        candidates.append(re.sub(r"^\d+-", "", mvp_dir.name.lower()))
    # 3. project 字段（转空格分隔）
    project = str(brief.get("project", "")).lower()
    if project:
        candidates.append(project)

    for slug in candidates:
        if slug in SLUG_TO_SCENE:
            return SLUG_TO_SCENE[slug]
        # 模糊匹配
        for key, val in SLUG_TO_SCENE.items():
            if key in slug or key.replace("-", " ") in slug:
                return val

    return "modern interior design"


def dedup_palette(palette_phrases: list[str], seen_atoms: set[str]) -> list[str]:
    """
    去重：若 palette 短语的所有原子都已在 seen_atoms 中，跳过该短语
    同时把新原子加入 seen_atoms
    """
    kept = []
    for p in palette_phrases:
        p_atoms = extract_atoms(p)
        # 纯 surface 词（如 "cream wall"、"white ceiling"）没有材质原子 → 保留
        if not p_atoms:
            kept.append(p)
            continue
        # 所有材质原子都已在 seen 里 → 重复，跳过
        if p_atoms.issubset(seen_atoms):
            continue
        kept.append(p)
        seen_atoms |= p_atoms
    return kept


def build_wall_negative(seen_atoms: set[str]) -> str:
    """
    根据 prompt 中出现的主材质，生成"这些材质不应污染墙面"的 negative 词
    解决 SDXL 把整面墙渲染成主材质（如墙变木纹）的问题
    """
    contaminants = seen_atoms & WALL_CONTAMINATABLE
    if not contaminants:
        return ""
    parts = []
    for m in sorted(contaminants):
        parts.extend([
            f"{m} walls",
            f"{m} wall paneling",
            f"{m} cladding on walls",
        ])
    return ", ".join(parts)


def build_prompt(
    brief: dict,
    room: dict | None = None,
    mvp_dir: Path | None = None,
) -> tuple[str, str]:
    """
    从 brief + room 合成精确 prompt
    返回 (positive_prompt, negative_prompt)

    根据 brief 自动识别 interior / architecture 两套 prompt 模板

    去污染策略（v2 · 2026-04-20）:
      1. 跨字段材质原子去重（style ↔ palette），避免同一材质词重复累加 CLIP 权重
      2. 自适应 negative：主导材质自动加入"墙面禁词"，防止 wood 染墙

    Token 预算（CLIP 上限 77）：
        style(6) + scene(5) + palette(8) + objects/context(10) + lighting(4) + ref(4) + suffix(10) ≈ 47
    """
    category = detect_scene_category(brief, mvp_dir)
    style_kw = extract_style_keywords(brief, max_n=3)
    palette_raw = extract_palette_descriptors(brief, top_n=4)
    reference = extract_reference(brief)

    # === 跨字段去重：style 里的材质原子登记，palette 去重时跳过已登记的 ===
    seen_atoms = extract_atoms(style_kw)
    palette = dedup_palette(palette_raw, seen_atoms)

    parts = []

    if category == "architecture":
        # 建筑外立面模式 — 不取 functional_zones.key_objects（室内家具），改用建筑上下文
        scene = infer_arch_scene(brief, mvp_dir)
        arch_ctx = extract_architecture_context(brief)

        if style_kw:
            parts.append(style_kw)
        parts.append(scene)
        if arch_ctx:
            parts.append(", ".join(arch_ctx))
        if palette:
            parts.append(", ".join(palette))
        if reference:
            parts.append(reference)
        parts.append(QUALITY_SUFFIX_ARCH)

        # 建筑类：墙面即外立面，不做 wall 去污染（外立面本来就是材质展示）
        return ", ".join(parts), NEGATIVE_ARCH

    # 室内模式
    scene = infer_scene_type(brief, mvp_dir)
    objects = extract_key_objects(brief, top_zones=2, max_objects=4)
    lighting = extract_lighting(brief)

    # 把 objects 的材质原子也纳入 seen（用于 negative 识别）
    for obj in objects:
        seen_atoms |= extract_atoms(obj)

    if style_kw:
        parts.append(style_kw)
    parts.append(scene)
    if palette:
        parts.append(", ".join(palette))
    if objects:
        parts.append(", ".join(objects))
    if lighting:
        parts.append(lighting)
    if reference:
        parts.append(reference)
    parts.append(QUALITY_SUFFIX)

    # === 自适应 negative：禁止主材质污染墙面 ===
    wall_neg = build_wall_negative(seen_atoms)
    negative = f"{NEGATIVE_PROMPT}, {wall_neg}" if wall_neg else NEGATIVE_PROMPT

    return ", ".join(parts), negative


# --- 测试 ---
if __name__ == "__main__":
    import json
    import sys

    mvp_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
        "/Users/kaku/Desktop/Work/StartUP-Building/studio-demo/mvp/03-coffee-shop"
    )
    brief = json.loads((mvp_path / "brief.json").read_text())
    room_path = mvp_path / "room.json"
    room = json.loads(room_path.read_text()) if room_path.exists() else None

    pos, neg = build_prompt(brief, room, mvp_path)
    print(f"MVP: {mvp_path.name}")
    print(f"\n=== POSITIVE PROMPT ===\n{pos}")
    print(f"\n=== NEGATIVE PROMPT ===\n{neg}")
    # Token 估算（粗略：1 token ≈ 1 word）
    print(f"\nApprox tokens: {len(pos.split())}")
