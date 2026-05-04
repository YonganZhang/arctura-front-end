"""Phase 11.6 · 元测试 · 不同输入必须产不同输出（防全 fallback 塌缩）

**根因反思**：之前 scene-default-fallback bug "任何 brief 都生成同一个 scene" 没被
之前测试发现，因为单测只验"office 默认家具是 X"、"cafe 默认家具是 Y"，**没人测
"用户实际写'hybrid cafe-office' 不该塌到 default"**。

这个测试套件的 invariant：
  对一组**真实多样的输入**，scene 的关键字段必须**有视觉级差异**。
  如果某个字段（家具集合 / 色板 / bounds / 灯光）对所有输入都返同样值，
  说明上游 resolver/lookup 太宽 fallback · 不论 unit test 是否绿。

跟 test_each_enum_distinct_from_default 互补：那个只锁 enum 自己；
这个锁"用户会真写出来的脏字符串"集合输入路径。
"""
import copy
import pytest
from _build.arctura_mvp.generators import build_scene_from_brief
from _build.arctura_mvp.derive import derive

DECOR = {"book", "vase", "cup", "plant_small", "picture_frame"}


def _scene_signature(scene: dict) -> dict:
    """从 scene 抽 'visually distinguishing' 字段 · 用来对照不同输入的输出"""
    main_furniture = sorted({a["type"] for a in scene["assemblies"] if a["type"] not in DECOR})
    return {
        "bounds": (scene["bounds"]["w"], scene["bounds"]["d"], scene["bounds"]["h"]),
        "main_furniture": tuple(main_furniture),
        "wall_color": scene["materials"]["wall"]["base_color"].upper(),
        "floor_color": scene["materials"]["woodfloor"]["base_color"].upper(),
        "n_objects": len(scene["objects"]),
    }


def _brief(area=30, type_="office", keywords=None, must_have=None):
    b = {
        "project": {"name_cn": "T", "name_en": "T"},
        "space": {"area_sqm": area, "type": type_},
        "style": {"keywords": keywords or ["极简"]},
        "functional_zones": [{"name": "工作区"}],
    }
    if must_have:
        b["must_have"] = must_have
    return b


# ───────── 1. space.type 多样输入 · 主家具集合不能全相同 ─────────

REAL_USER_TYPE_INPUTS = [
    "office", "cafe", "study", "bedroom", "living_room", "dining",
    "retail", "clinic", "gallery", "multipurpose",
    # 真实 LLM 输出的脏字符串（曾导致 bug）
    "hybrid cafe-office", "校长办公室", "principal office",
    "showroom cafe", "dental clinic", "co-working space",
    "boutique retail store", "executive office",
]


def test_space_types_produce_distinct_furniture():
    """20+ 种实际输入 · 至少应有 N 种不同的主家具集合（防全塌缩）"""
    sigs = {}
    for t in REAL_USER_TYPE_INPUTS:
        s = build_scene_from_brief(_brief(type_=t), "t")
        sigs[t] = _scene_signature(s)["main_furniture"]

    distinct_furniture = set(sigs.values())
    # 20 个输入 · 至少 6 种 · 否则说明大量塌缩
    assert len(distinct_furniture) >= 6, \
        f"20 种输入只产出 {len(distinct_furniture)} 种家具组合 · 可能大量 fallback default · 详细：{sigs}"


def test_no_user_input_collapses_to_default_3():
    """任何用户输入都不该产出 default 3 件家具（这是 Phase 11.1 bug 的精确特征）"""
    DEFAULT_3 = ("chair_standard", "lamp_floor", "table_coffee")
    for t in REAL_USER_TYPE_INPUTS:
        s = build_scene_from_brief(_brief(type_=t), "t")
        sig = _scene_signature(s)["main_furniture"]
        assert sig != DEFAULT_3, \
            f"'{t}' 塌缩到 default 3 件家具 · resolver fallback 太宽"


# ───────── 2. style.keywords 多样输入 · 色板不能全相同（修 subagent #1）─────────

REAL_STYLE_KEYWORDS = [
    ["日式", "禅"],                        # japandi
    ["极简", "白色"],                       # minimal
    ["工业", "loft"],                       # industrial
    ["奶油", "cream", "复古"],              # warm（之前会 fallback）
    ["现代", "高端", "luxury"],             # modern_luxury（之前会 fallback）
    ["清新", "自然", "绿植"],               # fresh（之前会 fallback）
    ["大胆", "撞色", "vintage"],            # bold（之前会 fallback）
    ["contemporary", "elegant"],            # 英文 modern_luxury
    ["modern", "warmth", "zen"],            # 多命中（warm + japandi · 取首匹配）
]


def test_style_keywords_produce_distinct_palettes():
    """9 组实际风格关键词 · 必须命中至少 6 种不同色板（不能全 default）"""
    wall_colors = set()
    for kws in REAL_STYLE_KEYWORDS:
        s = build_scene_from_brief(_brief(keywords=kws), "t")
        wall_colors.add(_scene_signature(s)["wall_color"])

    assert len(wall_colors) >= 6, \
        f"9 组风格只命中 {len(wall_colors)} 个不同 wall_color · palette fallback 太宽"


def test_no_style_keyword_collapses_to_default_palette():
    """除了显式 ['default'] 输入，其他风格关键词都不该用 default 色板（同主 bug 形状）"""
    DEFAULT_WALL = "#F5F1E8"   # default preset.wall
    suspicious = []
    for kws in REAL_STYLE_KEYWORDS:
        s = build_scene_from_brief(_brief(keywords=kws), "t")
        if _scene_signature(s)["wall_color"] == DEFAULT_WALL.upper():
            suspicious.append(kws)
    assert not suspicious, \
        f"以下风格关键词全 fallback default 色板：{suspicious}"


# ───────── 3. area 必须真影响 bounds（不能 50㎡ 跟 200㎡ 同样大）─────────

def test_area_affects_bounds_monotonic():
    sizes = [10, 30, 60, 120, 250]
    bounds_areas = []
    for a in sizes:
        s = build_scene_from_brief(_brief(area=a), "t")
        bounds_areas.append(s["bounds"]["w"] * s["bounds"]["d"])
    # 单调递增（10 < 30 < 60 < 120 < 250）
    for i in range(1, len(bounds_areas)):
        assert bounds_areas[i] > bounds_areas[i - 1], \
            f"area 单调性失败：area {sizes[i-1]}→{sizes[i]} 但 bounds {bounds_areas[i-1]}→{bounds_areas[i]}"


# ───────── 4. derive() metrics 必须有差异（防 EUI/cost 全相同）─────────

def test_derive_metrics_distinguish_briefs():
    """5 个明显不同的 brief（area+insul+region 都不同）· derive metrics 必须有差异"""
    briefs = [
        {**_brief(area=20),  "envelope": {"insulation_mm": 40},  "region": "HK"},
        {**_brief(area=80),  "envelope": {"insulation_mm": 120}, "region": "CN"},
        {**_brief(area=200), "envelope": {"insulation_mm": 80},  "region": "INTL"},
        {**_brief(area=30),  "envelope": {"insulation_mm": 60},  "region": "HK"},
        {**_brief(area=50),  "envelope": {"insulation_mm": 100}, "region": "HK"},
    ]
    eui_set = set()
    cost_set = set()
    for b in briefs:
        bundle = derive(b)
        eui_set.add(bundle.derived_metrics["eui_kwh_m2_yr"])
        cost_set.add(bundle.derived_metrics["cost_total"])
    assert len(eui_set) >= 4, f"5 brief 只产 {len(eui_set)} 种 EUI · 启发式失效"
    assert len(cost_set) >= 4, f"5 brief 只产 {len(cost_set)} 种 cost · 启发式失效"


# ───────── 5. derive() 同一 brief 多次结果稳定（纯函数）·
#            两个不同 brief 结果不能相同（防 derive 内部塌缩）─────────

def test_derive_pure_and_distinct():
    """同 brief 多次 → signatures 一致；不同 brief → signatures 必须不同"""
    b1 = _brief(area=30, type_="office")
    b2 = _brief(area=30, type_="cafe")

    a = derive(copy.deepcopy(b1))
    aa = derive(copy.deepcopy(b1))
    b = derive(copy.deepcopy(b2))

    # 纯函数性
    assert a._signatures == aa._signatures
    # 区分性
    assert a._signatures["brief_sha"] != b._signatures["brief_sha"]
    sig_a = _scene_signature(a.scene)
    sig_b = _scene_signature(b.scene)
    assert sig_a["main_furniture"] != sig_b["main_furniture"], \
        "office vs cafe 经 derive 后家具仍相同 · derive 没把 brief 区别传到 scene"


# ───────── 6. functional_zones 多 → 应有更多家具 ─────────

def test_more_zones_more_furniture():
    s_few = build_scene_from_brief({**_brief(), "functional_zones": [{"name": "z1"}]}, "t")
    s_many = build_scene_from_brief(
        {**_brief(), "functional_zones": [{"name": f"z{i}"} for i in range(6)]},
        "t",
    )
    n_few = len({a["type"] for a in s_few["assemblies"] if a["type"] not in DECOR})
    n_many = len({a["type"] for a in s_many["assemblies"] if a["type"] not in DECOR})
    assert n_many >= n_few, \
        f"6 zones 家具数 {n_many} 不大于 1 zone {n_few} · functional_zones 信号丢失"


# ───────── 7. must_have 优先级（用户显式列家具应被采纳）─────────

def test_must_have_overrides_type_default():
    """用户写 must_have=['书架','沙发']，应用 must_have 不走 type 默认"""
    s = build_scene_from_brief(
        _brief(type_="cafe", must_have=["bookshelf", "sofa", "lamp"]), "t",
    )
    types = {a["type"] for a in s["assemblies"] if a["type"] not in DECOR}
    # 必含 must_have 翻译后的家具
    assert "shelf_open" in types, f"must_have='bookshelf' 没生效 · types={types}"
    assert any(t.startswith("sofa") for t in types), f"must_have='sofa' 没生效 · types={types}"
