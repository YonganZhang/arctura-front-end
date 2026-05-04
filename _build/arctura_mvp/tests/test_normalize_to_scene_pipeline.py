"""集成测试：normalize-brief.js → scene generator 全链路（Codex Step 1 三审 #1 ship-blocker）

验证：normalize 写 KV 后 scene 仍然能拿到家具并集（不被 multipurpose 抹掉）。
跨语言：JS normalize 写出的形状 · Python scene generator 必须能消费。
"""
import pytest
from _build.arctura_mvp.generators import build_scene_from_brief
from _build.arctura_mvp.generators._resolve_space_type import resolve_space_type


def _simulate_js_normalize(brief):
    """Python 端 mock JS 的 normalizeBriefSpaceType 行为 · 用相同逻辑保持一致

    单一命中 → space.type = enum
    多命中 → space.type='multipurpose' · resolved_types = [...]
    全 miss → space.type='multipurpose' · resolved_types=[]
    """
    if not isinstance(brief, dict):
        return brief
    space = brief.get("space")
    if not isinstance(space, dict):
        return brief
    raw = space.get("type")
    if not isinstance(raw, str) or not raw:
        return brief

    ENUM = {"office", "cafe", "study", "bedroom", "living_room", "dining",
            "retail", "clinic", "gallery", "multipurpose"}
    trimmed = raw.strip().lower()
    if trimmed in ENUM:
        space["type"] = trimmed
        space.pop("resolved_types", None)
        return brief

    resolved = resolve_space_type(raw)
    if not resolved or (len(resolved) == 1 and resolved[0] == "default"):
        space.setdefault("type_raw", raw)
        space["type"] = "multipurpose"
        space["resolved_types"] = []
        return brief
    if len(resolved) == 1:
        if raw.strip().lower() != resolved[0]:
            space.setdefault("type_raw", raw)
        space["type"] = resolved[0]
        space.pop("resolved_types", None)
        return brief
    space.setdefault("type_raw", raw)
    space["type"] = "multipurpose"
    space["resolved_types"] = resolved
    return brief


def _brief(raw_type, area=30):
    return {
        "project": {"name_cn": "T", "name_en": "T"},
        "space": {"area_sqm": area, "type": raw_type},
        "style": {"keywords": ["极简"]},
        "functional_zones": [{"name": "工作区"}],
    }


def _furniture_types(scene):
    DECOR = {"book", "vase", "cup", "plant_small", "picture_frame"}
    return {a["type"] for a in scene["assemblies"] if a["type"] not in DECOR}


# ───────── 致命场景 · normalize 后必须仍出 cafe + office 家具 ─────────

def test_hybrid_cafe_office_after_normalize_keeps_union():
    """LLM 写 'hybrid cafe-office' → JS normalize → space.type='multipurpose' resolved_types=['cafe','office']
    → scene generator 必须读 resolved_types 并取 cafe ∪ office 家具 · 不能走 multipurpose 默认"""
    b = _brief("hybrid cafe-office")
    _simulate_js_normalize(b)
    assert b["space"]["type"] == "multipurpose"
    # resolved_types 含 cafe + office（也可能含 multipurpose 因 'hybrid' 是它的关键词）
    assert "cafe" in b["space"]["resolved_types"]
    assert "office" in b["space"]["resolved_types"]

    scene = build_scene_from_brief(b, "t")
    types = _furniture_types(scene)
    # 必须同时有 cafe 代表（table_dining）和 office 代表（desk_standard）
    assert "table_dining" in types, f"normalize 后 cafe 信号丢失 · types={types}"
    assert "desk_standard" in types, f"normalize 后 office 信号丢失 · types={types}"


def test_principal_office_after_normalize():
    """'校长办公室' → normalize → type='office' raw='校长办公室' → scene 走 office 默认"""
    b = _brief("校长办公室")
    _simulate_js_normalize(b)
    assert b["space"]["type"] == "office"
    assert b["space"]["type_raw"] == "校长办公室"

    scene = build_scene_from_brief(b, "t")
    assert "desk_standard" in _furniture_types(scene)


def test_all_miss_falls_back_to_multipurpose_enum():
    """全 miss 'alien xyz' → normalize → type='multipurpose' · strict-enum 消费方不炸"""
    b = _brief("alien xyz totally unknown")
    _simulate_js_normalize(b)
    assert b["space"]["type"] == "multipurpose"
    assert b["space"]["resolved_types"] == []
    assert b["space"]["type_raw"] == "alien xyz totally unknown"

    # scene 仍能生成（走 multipurpose 默认家具）
    scene = build_scene_from_brief(b, "t")
    assert len(_furniture_types(scene)) >= 2


def test_legacy_brief_without_normalize_still_works():
    """老数据：brief 没经过 normalize · space.type 是脏字符串 · scene 仍能恢复（兼容 type_raw fallback）"""
    b = _brief("hybrid cafe-office")  # 不经 normalize · 直接老形状
    scene = build_scene_from_brief(b, "t")
    types = _furniture_types(scene)
    # 老路径靠 type_raw or type 现场 resolve · 也能取并集
    assert "table_dining" in types or "desk_standard" in types


def test_already_enum_passthrough():
    """已是 enum 的 brief · normalize 不动家具语义"""
    b = _brief("office")
    _simulate_js_normalize(b)
    assert b["space"]["type"] == "office"
    assert "resolved_types" not in b["space"]

    scene = build_scene_from_brief(b, "t")
    assert "desk_standard" in _furniture_types(scene)
