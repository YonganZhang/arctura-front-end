"""Phase 7.1 · scene generator 单测"""
import pytest
from _build.arctura_mvp.generators import build_scene_from_brief


# ───────── 公共 helpers ─────────

def _minimum_brief():
    return {
        "project": "T",
        "space": {"area_sqm": 20, "type": "study"},
        "style": {"keywords": ["极简", "暖木"]},
        "functional_zones": [{"name": "工作区"}],
    }


def _required_scene_keys():
    return {"schema_version", "unit", "bounds", "walls", "objects",
            "assemblies", "lights", "materials", "env", "floor",
            "camera_default", "ceiling"}


# ───────── 1. 最小 brief 能生成合法 scene ─────────

def test_build_scene_from_minimum_brief():
    scene = build_scene_from_brief(_minimum_brief(), "test-slug")
    # 顶层 keys 齐
    assert _required_scene_keys().issubset(scene.keys())
    # bounds 非零
    assert scene["bounds"]["w"] > 0
    assert scene["bounds"]["d"] > 0
    assert scene["bounds"]["h"] > 0
    # walls 有 4 面
    assert len(scene["walls"]) == 4
    # assemblies 非空
    assert len(scene["assemblies"]) >= 1
    # objects 和 assemblies 数对等
    assert len(scene["objects"]) == len(scene["assemblies"])
    # lights 非空
    assert len(scene["lights"]) >= 1


# ───────── 2. must_have 清单被吃进去 ─────────

def test_build_scene_with_must_have():
    brief = _minimum_brief()
    brief["must_have"] = ["desk", "chair", "bookshelf"]
    scene = build_scene_from_brief(brief, "t")
    types = {a["type"] for a in scene["assemblies"]}
    # desk / chair / shelf 对应 desk_standard / chair_standard / shelf_open
    assert "desk_standard" in types
    assert "chair_standard" in types
    assert "shelf_open" in types


# ───────── 3. style.keywords 影响色板 ─────────

def test_build_scene_style_keywords_affect_palette():
    b1 = _minimum_brief(); b1["style"]["keywords"] = ["日式", "japandi"]
    b2 = _minimum_brief(); b2["style"]["keywords"] = ["工业", "industrial"]
    s1 = build_scene_from_brief(b1, "t")
    s2 = build_scene_from_brief(b2, "t")
    # 日式的 wall 和工业的 wall 颜色必不同
    assert s1["materials"]["wall"]["base_color"] != s2["materials"]["wall"]["base_color"]
    # 工业风该暗 · 日式偏暖米
    assert s1["materials"]["wall"]["base_color"].upper().startswith("#F")  # 浅
    assert s2["materials"]["wall"]["base_color"].upper().startswith("#8")  # 灰暗


# ───────── 4. area 影响 bounds ─────────

def test_build_scene_area_affects_bounds():
    small = _minimum_brief(); small["space"]["area_sqm"] = 10
    large = _minimum_brief(); large["space"]["area_sqm"] = 50
    s_small = build_scene_from_brief(small, "t")
    s_large = build_scene_from_brief(large, "t")
    # 50㎡ 房间的 bounds 必明显大
    small_area = s_small["bounds"]["w"] * s_small["bounds"]["d"]
    large_area = s_large["bounds"]["w"] * s_large["bounds"]["d"]
    assert large_area > small_area * 3  # 5x 面积差 · 至少 3x
    # 大房间层高 3.0 · 小房间 2.8
    assert s_large["bounds"]["h"] == 3.0
    assert s_small["bounds"]["h"] == 2.8


# ───────── 5. functional_zones 多 → 家具多 · 不重叠 ─────────

def test_build_scene_functional_zones_to_assemblies():
    brief = _minimum_brief()
    brief["functional_zones"] = [
        {"name": "工作区"}, {"name": "阅读区"}, {"name": "休息区"}, {"name": "收纳区"}
    ]
    scene = build_scene_from_brief(brief, "t")
    # 至少 3 个 assemblies · 多 zone 应触发额外 default
    assert len(scene["assemblies"]) >= 3

    # 检查布局不重叠（AABB 距离 · 相同 z 层）
    asms = scene["assemblies"]
    ground = [a for a in asms if abs(a["pos"][2]) < 0.01]   # 只检查地面层
    for i, a in enumerate(ground):
        for j in range(i + 1, len(ground)):
            b = ground[j]
            ax, ay, _ = a["pos"]; aw, ad, _ = a["size"]
            bx, by, _ = b["pos"]; bw, bd, _ = b["size"]
            # 中心距离 > 两者半宽之和 · 或在另一轴错开
            x_gap = abs(ax - bx) - (aw + bw) / 2
            y_gap = abs(ay - by) - (ad + bd) / 2
            assert x_gap >= -0.01 or y_gap >= -0.01, \
                f"{a['id']} & {b['id']} overlap: x_gap={x_gap} y_gap={y_gap}"


# ───────── 6. 对齐 pilot 01-study-room schema ─────────

def test_build_scene_schema_compatible_with_pilot():
    """生成的 scene 顶层 keys 覆盖 pilot 必备字段（renderer 能吃）"""
    import json
    from pathlib import Path
    pilot = json.loads((Path(__file__).resolve().parents[3] /
                         "data" / "mvps" / "01-study-room.json").read_text())
    pilot_scene_keys = {k for k in pilot["scene"].keys() if not k.startswith("_")}

    scene = build_scene_from_brief(_minimum_brief(), "t")
    our_keys = set(scene.keys())

    # 必备 · 一个不能缺
    critical = {"bounds", "walls", "objects", "assemblies", "lights",
                "materials", "env", "floor", "camera_default", "ceiling"}
    assert critical.issubset(our_keys), f"missing: {critical - our_keys}"
    assert critical.issubset(pilot_scene_keys), "pilot schema changed · update test"

    # assembly 形状也必对齐 · 至少 part_ids / primary_part_id / pos / size / type / label_zh
    for a in scene["assemblies"]:
        assert {"id", "type", "pos", "size", "part_ids",
                "primary_part_id", "label_zh", "rotation"}.issubset(a.keys())


# ───────── 额外保险 · 空 brief / 面积异常都不崩 ─────────

def test_build_scene_empty_brief_raises():
    with pytest.raises(ValueError):
        build_scene_from_brief({}, "t")
    with pytest.raises(ValueError):
        build_scene_from_brief(None, "t")


def test_build_scene_invalid_area_falls_back():
    brief = _minimum_brief()
    brief["space"]["area_sqm"] = -5  # 非法
    scene = build_scene_from_brief(brief, "t")
    # 应回落到默认 20㎡ · 不抛
    assert scene["bounds"]["w"] > 0
