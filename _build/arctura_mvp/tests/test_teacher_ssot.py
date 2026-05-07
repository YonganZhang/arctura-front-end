"""老师权威 SSOT 接入测试 · Phase 12.末.G

锁住:LIGHT artifact 真用老师 playbooks/{schemas,defaults,prompts} · 不再硬编码副本。

测试维度:
  S1 · 4 SSOT(schemas/defaults/prompts/templates)可读
  S2 · 老师 brief jsonschema validate 真有效
  S3 · hk_market.json 真接入 derive(LIGHT cost_per_m2)
  S4 · 5 LLM prompt 全可拉
  S5 · paths.py 注册的 14+ 路径全 exists
"""
from __future__ import annotations
import pytest

from _build.arctura_mvp.teacher_authority import ssot
from _build.arctura_mvp.paths import verify_paths


# ── S1 · SSOT 全可读 ───────────────────────────────────────
def test_s1_ssot_loaders_all_pass():
    out = ssot.verify_ssot()
    assert out["brief-interior schema"] is True or "True" in str(out["brief-interior schema"])
    assert "业态" in str(out["hk_market"])
    assert "配置" in str(out["comparison-cameras"])
    assert "资产" in str(out["site-entourage-catalog"])
    assert "chars" in str(out["prompt classify"])


# ── S2 · jsonschema validate 真生效 ─────────────────────────
def test_s2_brief_validate_minimal():
    """合法 minimal brief 应 0 错误"""
    brief = {
        "project": "test",
        "style": {"keywords": ["modern"]},
    }
    errors = ssot.validate_brief(brief, "brief-interior")
    # 老师 schema required: project + style · 应通过(jsonschema 缺则 skip)
    if errors and "jsonschema 未装" in errors[0]:
        pytest.skip("jsonschema 未装")
    assert errors == []


def test_s2_brief_validate_missing_required():
    """缺 required 应有 error"""
    brief = {"slug": "x"}  # 缺 project + style
    errors = ssot.validate_brief(brief, "brief-interior")
    if errors and "jsonschema 未装" in errors[0]:
        pytest.skip("jsonschema 未装")
    assert len(errors) >= 2  # project 和 style 都缺


# ── S3 · hk_market.json 真接入 derive ───────────────────────
def test_s3_hk_budget_per_m2():
    """9+ 业态都该有 mid 价 · 不返 None"""
    for biz in ["cafe", "restaurant", "retail", "office", "coworking",
                "clinic", "gallery", "salon", "studio"]:
        price = ssot.hk_budget_per_m2(biz, "mid")
        assert price is not None and price > 0, f"业态 {biz} 应有价 · 实际 {price}"


def test_s3_hk_budget_unknown_returns_none():
    assert ssot.hk_budget_per_m2("nonexistent_biz") is None


def test_s3_derive_uses_teacher_price_when_hk():
    """region=HK + business_type → 用老师 hk_market 价"""
    from _build.arctura_mvp.derive import _derived_metrics_from_editable as _heuristic_derived_metrics
    editable = {"area_m2": 100, "region": "HK", "business_type": "office",
                "lighting_cct": 3000, "lighting_density_w_m2": 8, "insulation_mm": 60}
    metrics = _heuristic_derived_metrics(editable, {})
    teacher_office_mid = ssot.hk_budget_per_m2("office", "mid")
    assert metrics["cost_per_m2"] == teacher_office_mid, \
        f"region=HK+office 应用老师价 {teacher_office_mid} · 实际 {metrics['cost_per_m2']}"


def test_s3_derive_falls_back_when_no_business_type():
    """无 business_type → 走 resolver 注册表 fallback"""
    from _build.arctura_mvp.derive import _derived_metrics_from_editable as _heuristic_derived_metrics
    editable = {"area_m2": 100, "region": "HK",
                "lighting_cct": 3000, "lighting_density_w_m2": 8, "insulation_mm": 60}
    metrics = _heuristic_derived_metrics(editable, {})
    assert metrics["cost_per_m2"] > 0  # fallback 也要有价


# ── S4 · LLM prompts 全可拉 ─────────────────────────────────
def test_s4_all_prompts_loadable():
    assert len(ssot.prompt_classify_brief()) > 100
    assert len(ssot.prompt_brief_from_text()) > 100
    assert len(ssot.prompt_brief_turn_based()) > 100
    assert len(ssot.prompt_vision_extract()) > 100
    assert len(ssot.prompt_client_export_guide()) > 100


# ── S5 · paths.py 14+ 注册路径全 exists ───────────────────────
def test_s5_paths_register_all_exist():
    p = verify_paths()
    must_exist = [
        "STARTUP_BUILDING_ROOT", "PLAYBOOKS_SCRIPTS",
        "PLAYBOOKS_SCHEMAS", "PLAYBOOKS_DEFAULTS",
        "PLAYBOOKS_PROMPTS", "PLAYBOOKS_TEMPLATES",
        "STUDIO_DEMO_MVP_DIR", "STUDIO_DEMO_ARCH_DIR",
        "ASSETS_FURNITURE_ROOT", "BIM_CATALOG_JSON",
        "TEACHER_MARP_DECK_SKILL", "TEACHER_CLIENT_PORTAL_SKILL",
    ]
    missing = [k for k in must_exist if not p.get(k)]
    assert not missing, f"路径缺: {missing}"


def test_s5_playbook_subdirs_all_exist():
    p = verify_paths()
    sub_keys = [k for k in p if k.startswith("PLAYBOOK_SUB_")]
    missing = [k for k, v in p.items() if k.startswith("PLAYBOOK_SUB_") and not v]
    assert sub_keys, "PLAYBOOK_SUB_* 注册为空 · 检查 PLAYBOOKS_SCRIPTS_SUBDIRS"
    assert not missing, f"老师 subdirs 缺: {missing}"
