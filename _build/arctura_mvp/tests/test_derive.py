"""Phase 11.3 · derive() 纯函数单测 · ADR-001 §"derive 是纯函数" 锁定行为"""
import copy
import pytest
from _build.arctura_mvp.derive import derive, DERIVE_SCHEMA_VERSION


def _brief(area=30, type_="office", insul=None, density=None):
    b = {
        "project": {"name_cn": "T", "name_en": "T"},
        "space": {"area_sqm": area, "type": type_},
        "style": {"keywords": ["极简"]},
        "functional_zones": [{"name": "工作区"}],
    }
    if insul is not None:
        b["envelope"] = {"insulation_mm": insul}
    if density is not None:
        b.setdefault("lighting", {})["density_wperm2"] = density
    return b


# ───── 纯函数性 ─────

def test_derive_does_not_mutate_input():
    """derive 必须不改入参 brief（纯函数契约）"""
    b = _brief()
    snapshot = copy.deepcopy(b)
    derive(b)
    assert b == snapshot, "derive 修改了入参 brief"


def test_derive_same_input_same_output():
    """同输入永远同输出 · _signatures 也一致"""
    b = _brief(area=40, type_="cafe")
    a = derive(b)
    c = derive(b)
    assert a.scene == c.scene
    assert a.editable == c.editable
    assert a.derived_metrics == c.derived_metrics
    assert a._signatures == c._signatures


def test_derive_different_brief_different_signature():
    a = derive(_brief(area=30))
    b = derive(_brief(area=80))
    assert a._signatures["brief_sha"] != b._signatures["brief_sha"]


def test_derive_overrides_change_signature_not_brief():
    base = derive(_brief())
    with_ov = derive(_brief(), overrides={"layout": {"x": {"target": "assembly", "target_id": "asm_desk_1", "pos": [1, 2, 0]}}})
    assert base._signatures["brief_sha"] == with_ov._signatures["brief_sha"]
    assert base._signatures["overrides_sha"] != with_ov._signatures["overrides_sha"]


# ───── editable 派生 ─────

def test_editable_uses_brief_envelope():
    b = derive(_brief(insul=80, density=10))
    assert b.editable["insulation_mm"] == 80
    assert b.editable["lighting_density_w_m2"] == 10


def test_editable_falls_back_when_brief_silent():
    b = derive(_brief())
    assert b.editable["insulation_mm"] == 60   # default
    assert b.editable["wwr"] == 0.25


# ───── derived_metrics ─────

def test_metrics_heuristic_used_when_no_artifacts():
    b = derive(_brief(area=30))
    m = b.derived_metrics
    assert m["_source"] == "derive_heuristic"
    assert m["eui_kwh_m2_yr"] > 0
    assert m["cost_total"] > 0
    assert m["co2_t_per_yr"] > 0


def test_metrics_real_overrides_heuristic():
    """artifacts_index 提供真 EUI · 应替换启发式"""
    b = derive(_brief(), artifacts_index={"metrics": {"eui_kwh_m2_yr": 38.2}})
    assert b.derived_metrics["eui_kwh_m2_yr"] == 38.2
    assert b.derived_metrics["_source"] == "energyplus"


def test_metrics_higher_insulation_lower_eui():
    """启发式：保温越好 EUI 越低（虽简陋 · 但方向对）"""
    low = derive(_brief(insul=40))
    high = derive(_brief(insul=120))
    assert high.derived_metrics["eui_kwh_m2_yr"] < low.derived_metrics["eui_kwh_m2_yr"]


# ───── overrides 应用 ─────

def test_layout_override_moves_assembly():
    b1 = derive(_brief(type_="office"))
    target_asm = b1.scene["assemblies"][0]
    target_id = target_asm["id"]
    b2 = derive(
        _brief(type_="office"),
        overrides={"layout": {"o1": {"target": "assembly", "target_id": target_id, "pos": [9.9, 9.9, 0]}}},
    )
    moved = next(a for a in b2.scene["assemblies"] if a["id"] == target_id)
    assert moved["pos"] == [9.9, 9.9, 0]


def test_orphan_layout_does_not_crash():
    """target_id 不在 base scene 里 · 不抛 · 静默跳过"""
    b = derive(
        _brief(),
        overrides={"layout": {"o1": {"target": "assembly", "target_id": "asm_does_not_exist", "pos": [1, 1, 0]}}},
    )
    assert b.scene is not None


def test_appearance_override_changes_floor_material():
    b = derive(
        _brief(),
        overrides={"appearance": {"floor": {"material_id": "concrete"}}},
    )
    assert b.scene["floor"]["material_id"] == "concrete"


def test_lighting_intensity_scale_applied():
    base = derive(_brief())
    light_id = base.scene["lights"][0]["id"]
    base_intensity = base.scene["lights"][0]["intensity"]
    b = derive(
        _brief(),
        overrides={"lighting": {light_id: {"intensity_scale": 0.5}}},
    )
    light = next(l for l in b.scene["lights"] if l["id"] == light_id)
    assert abs(light["intensity"] - base_intensity * 0.5) < 0.01


def test_tombstone_removes_assembly():
    base = derive(_brief(type_="office"))
    target_id = base.scene["assemblies"][0]["id"]
    b = derive(
        _brief(type_="office"),
        overrides={"tombstones": {"assemblies": [target_id]}},
    )
    ids = [a["id"] for a in b.scene["assemblies"]]
    assert target_id not in ids


def test_layout_added_object_python_symmetric_with_js():
    """Codex 三审 #2 修：Python _apply_layout 必须支持 target='added'（之前缺）"""
    b = derive(
        _brief(),
        overrides={"layout": {
            "ov_add_1": {
                "target": "added",
                "override_id": "ov_add_1",
                "payload": {"id": "new_lamp_x", "type": "lamp_floor", "pos": [2, 2, 0], "size": [0.4, 0.4, 1.6]},
            }
        }},
    )
    ids = [o["id"] for o in b.scene["objects"]]
    assert "new_lamp_x" in ids, f"Python derive 没把 added object 写进 scene · ids={ids[:5]}..."


def test_overrides_input_not_mutated_by_derive():
    """Codex 三审 #1 修：overrides + artifacts_index 必须深拷贝"""
    overrides = {"layout": {"o1": {"target": "assembly", "target_id": "asm_x", "pos": [1, 2, 3]}}}
    artifacts_index = {"metrics": {"eui_kwh_m2_yr": 38.2}}
    snap_o = copy.deepcopy(overrides)
    snap_a = copy.deepcopy(artifacts_index)
    derive(_brief(), overrides=overrides, artifacts_index=artifacts_index)
    assert overrides == snap_o, "overrides 被 derive 修改了"
    assert artifacts_index == snap_a, "artifacts_index 被 derive 修改了"


def test_appearance_inline_material_added():
    b = derive(
        _brief(),
        overrides={"appearance": {
            "materials_added": {"my_blue": {"base_color": "#0033FF", "roughness": 0.3}},
            "floor": {"material_id": "my_blue"},
        }},
    )
    assert "my_blue" in b.scene["materials"]
    assert b.scene["materials"]["my_blue"]["base_color"] == "#0033FF"
    assert b.scene["floor"]["material_id"] == "my_blue"


# ───── 错误处理 ─────

def test_empty_brief_raises():
    with pytest.raises(ValueError):
        derive(None)
    with pytest.raises(ValueError):
        derive({})


def test_signatures_include_schema_version():
    b = derive(_brief())
    assert b._signatures["derive_schema_version"] == DERIVE_SCHEMA_VERSION
    assert b._signatures["overrides_schema_version"] is not None


# ───── overrides validate ─────

def test_validate_overrides_unknown_namespace():
    from _build.arctura_mvp.derive.overrides import validate_overrides
    errs = validate_overrides({"unknown_ns": {}})
    assert any("unknown namespace" in e for e in errs)


def test_validate_overrides_missing_target_id():
    from _build.arctura_mvp.derive.overrides import validate_overrides
    errs = validate_overrides({"layout": {"o1": {"target": "assembly"}}})  # no target_id
    assert any("target_id" in e for e in errs)


def test_validate_overrides_clean():
    from _build.arctura_mvp.derive.overrides import validate_overrides
    assert validate_overrides({"layout": {"o1": {"target": "assembly", "target_id": "asm_x", "pos": [0, 0, 0]}}}) == []


def test_validate_overrides_added_does_not_require_target_id():
    """Codex 终审 #2：target='added' 不应要 target_id · 跟 JS 对称"""
    from _build.arctura_mvp.derive.overrides import validate_overrides
    errs = validate_overrides({
        "layout": {
            "ov_add_1": {"target": "added", "payload": {"id": "lamp_x", "type": "lamp_floor"}}
        }
    })
    assert errs == [], f"target=added 不该报 target_id 缺 · 但报: {errs}"


def test_validate_overrides_added_requires_payload_dict():
    """target='added' 必须有 payload dict · 防 LLM 漏写"""
    from _build.arctura_mvp.derive.overrides import validate_overrides
    errs = validate_overrides({"layout": {"o1": {"target": "added"}}})
    assert any("payload" in e for e in errs)


# ───── 集成：bug fix + derive 一起 work ─────

def test_hybrid_brief_derive_keeps_furniture_union():
    """Phase 11.1 bug 修后 · 通过 derive() 入口仍能保住 cafe ∪ office 家具"""
    b = derive(_brief(type_="hybrid cafe-office"))
    types = {a["type"] for a in b.scene["assemblies"]
             if a["type"] not in {"book", "vase", "cup", "plant_small", "picture_frame"}}
    assert "table_dining" in types or "desk_standard" in types
