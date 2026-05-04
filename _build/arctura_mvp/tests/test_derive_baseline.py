"""Phase 11.2 · derive_baseline extractor 单测

read-only 工具 · 测纯函数行为：抽取规则 + diff 算法。
"""
import pytest
from _build.scripts.derive_baseline import (
    _extract_scene_subset, _extract_editable_derived,
    diff_canonical, diff_baselines,
)


# ───── 抽取 ─────

def test_scene_subset_empty():
    """空 dict · _present True 但所有 count=0（仍是 dict 输入 · 区别于 None/missing）"""
    out = _extract_scene_subset({})
    assert out["_present"] is True
    assert out["objects_count"] == 0
    assert out["main_furniture_types"] == []
    assert out["lights_count"] == 0


def test_scene_subset_none():
    """None / 非 dict · _present False"""
    assert _extract_scene_subset(None) == {"_present": False}
    assert _extract_scene_subset("not a dict") == {"_present": False}


def test_scene_subset_canonical():
    scene = {
        "bounds": {"w": 5.234, "d": 4.111, "h": 2.8},
        "objects": [{"id": "o1"}, {"id": "o2"}, {"id": "o3"}],
        "assemblies": [
            {"type": "desk_standard"},
            {"type": "book"},   # decor · 应进 decor_count 不进 main_furniture
            {"type": "vase"},   # decor
            {"type": "chair_standard"},
        ],
        "lights": [{"type": "sun"}, {"type": "area"}],
        "materials": {"woodfloor": {}, "wall": {}, "linen_cream": {}},
        "walls": [{}, {}, {}, {}],
        "_generated_by": "scene_v1",  # 应忽略
    }
    out = _extract_scene_subset(scene)
    assert out["_present"] is True
    assert out["bounds"] == {"w": 5.23, "d": 4.11, "h": 2.8}
    assert out["objects_count"] == 3
    assert out["main_furniture_types"] == ["chair_standard", "desk_standard"]
    assert out["decor_count"] == 2
    assert out["lights_count"] == 2
    assert sorted(out["lights_types"]) == ["area", "sun"]
    assert out["material_keys"] == ["linen_cream", "wall", "woodfloor"]
    assert out["walls_count"] == 4
    assert "_generated_by" not in out


def test_editable_derived_extracts_tracked_fields_only():
    payload = {
        "editable": {
            "area_m2": 30, "insulation_mm": 80,
            "_secret_internal": "should ignore",  # 不在 tracked 里
        },
        "derived": {"eui_kwh_m2_yr": 45.5, "cost_total": 100000},
    }
    out = _extract_editable_derived(payload)
    assert out["editable"] == {"area_m2": 30, "insulation_mm": 80}
    assert "_secret_internal" not in out["editable"]
    assert out["derived"]["eui_kwh_m2_yr"] == 45.5


# ───── canonical diff 算法 ─────

def test_diff_identical_no_diffs():
    assert diff_canonical({"a": 1}, {"a": 1}) == []


def test_diff_scalar_within_epsilon():
    """浮点数 epsilon 1e-3 内视为相等"""
    assert diff_canonical({"a": 1.0}, {"a": 1.0001}) == []
    diffs = diff_canonical({"a": 1.0}, {"a": 1.5})
    assert len(diffs) == 1 and diffs[0]["kind"] == "scalar_diff"


def test_diff_added_removed_keys():
    diffs = diff_canonical({"a": 1}, {"a": 1, "b": 2})
    assert any(d["kind"] == "added" and d["path"] == "b" for d in diffs)

    diffs = diff_canonical({"a": 1, "b": 2}, {"a": 1})
    assert any(d["kind"] == "removed" and d["path"] == "b" for d in diffs)


def test_diff_nested_path():
    diffs = diff_canonical(
        {"scene": {"bounds": {"w": 5}}},
        {"scene": {"bounds": {"w": 6}}},
    )
    assert len(diffs) == 1
    assert diffs[0]["path"] == "scene.bounds.w"


def test_diff_baselines_summary():
    a = {"items": {"x": {"v": 1}, "y": {"v": 2}}}
    b = {"items": {"x": {"v": 1}, "z": {"v": 9}}}
    rep = diff_baselines(a, b)
    assert rep["summary"]["identical"] == 1   # x 相同
    assert "y" in rep["summary"]["only_in_a"]
    assert "z" in rep["summary"]["only_in_b"]


def test_diff_baselines_high_risk():
    """diff 字段超过 5 个的 slug · 标 high_risk"""
    a = {"items": {"x": {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5, "f": 6}}}
    b = {"items": {"x": {"a": 11, "b": 22, "c": 33, "d": 44, "e": 55, "f": 66}}}
    rep = diff_baselines(a, b)
    assert "x" in rep["summary"]["high_risk_slugs"]


# ───── 端到端 · 真跑 disk ─────

def test_extract_real_baseline_smoke():
    """跑真 data/mvps/ · 不抛 · 至少有 1 个 entry"""
    from _build.scripts.derive_baseline import extract_baseline_from_disk
    out = extract_baseline_from_disk()
    assert "items" in out
    assert out["count"] >= 1
