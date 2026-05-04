"""Phase 8 · product_registry SSOT 单测 · Phase 11.5 加 kind 字段测试"""
import pytest
from _build.arctura_mvp.product_registry import (
    PRODUCTS, TIER_META, _PRODUCTS_LIST,
    resolve_tier_products, resolve_tier_artifact_names,
    list_tiers_for_ui, get_spec_for_artifact, all_tier_ids,
    _validate,
    resolve_tier_products_by_kind, list_kinds,
)


# ───── Phase 11.5 · kind 字段（ADR-001 §"4 层缓存模型"）─────

def test_kind_taxonomy_uses_only_4_values():
    """所有 ProductSpec.kind 必须 ∈ {input, derive_input, fast_artifact, slow_artifact}"""
    allowed = {"input", "derive_input", "fast_artifact", "slow_artifact"}
    actual = list_kinds()
    assert actual.issubset(allowed), f"未知 kind: {actual - allowed}"


def test_brief_is_input_kind():
    """brief 是用户编辑的输入 · 不是 artifact"""
    assert PRODUCTS["brief"].kind == "input"


def test_scene_is_derive_input():
    """scene 是 derive 函数的输入 · 由 brief+overrides 派生 · 不需 worker"""
    assert PRODUCTS["scene"].kind == "derive_input"


def test_slow_artifacts_are_default():
    """renders/deck_client/energy_report/exports/case_study 是 worker 跑的慢产物"""
    for key in ["renders", "deck_client", "energy_report", "exports", "case_study"]:
        assert PRODUCTS[key].kind == "slow_artifact", \
            f"{key}.kind 期望 slow_artifact · 实际 {PRODUCTS[key].kind}"


def test_resolve_tier_products_by_kind_filters():
    """full 档的 slow_artifact 应包含 renders 等 · 不应含 brief/scene"""
    slow = resolve_tier_products_by_kind("full", "slow_artifact")
    keys = {p.key for p in slow}
    assert "renders" in keys
    assert "brief" not in keys
    assert "scene" not in keys


def test_resolve_tier_derive_input_minimal():
    """concept 档的 derive_input 至少含 scene"""
    derive_inputs = resolve_tier_products_by_kind("concept", "derive_input")
    keys = {p.key for p in derive_inputs}
    assert "scene" in keys



# ───── 1. registry 一致性（核心保护）─────

def test_registry_self_validates():
    """product_registry._validate() 不报错 · 内含 6 项校验"""
    errors = _validate()
    assert errors == [], f"registry 不一致：{errors}"


# ───── 2. id 范围跟 spec 对齐 ─────

def test_product_ids_in_range_1_to_16():
    ids = [p.id for p in _PRODUCTS_LIST if p.id is not None]
    assert all(1 <= i <= 16 for i in ids), ids
    assert len(ids) == len(set(ids)), f"duplicate ids: {ids}"


def test_variants_and_bundle_no_id():
    """variants / bundle 不是产物编号（aux） · id=None"""
    assert PRODUCTS["variants"].id is None
    assert PRODUCTS["bundle"].id is None


# ───── 3. 5 档产物数量跟 spec 对齐 ─────

def test_tier_concept_produces_6():
    """concept = brief + scene + moodboard + floorplan + renders + bundle = 6"""
    products = resolve_tier_products("concept")
    assert len(products) == 6
    names = {p.key for p in products}
    assert names == {"brief", "scene", "moodboard", "floorplan", "renders", "bundle"}


def test_tier_deliver_adds_2():
    """deliver = concept + deck_client + client_readme · 8 产物"""
    base = set(p.key for p in resolve_tier_products("concept"))
    deliver = set(p.key for p in resolve_tier_products("deliver"))
    added = deliver - base
    assert added == {"deck_client", "client_readme"}


def test_tier_quote_adds_energy():
    """quote = deliver + energy_report · 9 产物"""
    deliver = set(p.key for p in resolve_tier_products("deliver"))
    quote = set(p.key for p in resolve_tier_products("quote"))
    assert quote - deliver == {"energy_report"}


def test_tier_full_adds_exports_and_case_study():
    """full = quote + exports + case_study · 11 产物"""
    quote = set(p.key for p in resolve_tier_products("quote"))
    full = set(p.key for p in resolve_tier_products("full"))
    assert full - quote == {"exports", "case_study"}


def test_tier_select_adds_variants():
    """select = full + variants · 12 产物"""
    full = set(p.key for p in resolve_tier_products("full"))
    select = set(p.key for p in resolve_tier_products("select"))
    assert select - full == {"variants"}


# ───── 4. LIGHT 可产物清单 ─────

def test_light_producer_modules_exist():
    """每个声明 light_producer 的都得有对应 artifacts/<name>.py · _validate 已查 · 这里再显式"""
    from pathlib import Path
    art_dir = Path(__file__).resolve().parents[1] / "artifacts"
    for spec in _PRODUCTS_LIST:
        if spec.light_producer:
            assert (art_dir / f"{spec.light_producer}.py").exists(), \
                f"{spec.key} · light_producer {spec.light_producer} 模块不存在"


def test_full_only_products_have_full_hint():
    """FULL-only 的必须写明如何补齐 · 防未来忘"""
    for spec in _PRODUCTS_LIST:
        if spec.light_producer is None and spec.key not in ("brief",):
            # brief 不走 artifact pipeline · 其他 LIGHT 无法产的都要有 hint
            assert spec.full_hint, f"{spec.key} · LIGHT 无法产但 full_hint 为空"


# ───── 5. 依赖顺序 ─────

def test_dependency_order_bundle_last():
    """bundle 永远在最后 · 包前面所有产物"""
    for tier in ["concept", "deliver", "quote", "full", "select"]:
        arts = resolve_tier_artifact_names(tier)
        assert arts[-1] == "bundle", f"{tier} bundle 不在最后: {arts}"


def test_dependencies_exist():
    """每 depends_on 指向的 key 都真存在"""
    for spec in _PRODUCTS_LIST:
        for dep in spec.depends_on:
            assert dep in PRODUCTS, f"{spec.key} depends_on={dep} 不存在"


# ───── 6. 前端 UI 数据 ─────

def test_list_tiers_for_ui_returns_5_sorted():
    tiers = list_tiers_for_ui()
    assert len(tiers) == 5
    orders = [t["order"] for t in tiers]
    assert orders == sorted(orders)
    # 必要字段
    for t in tiers:
        assert t["id"] and t["label_zh"] and t["artifacts"]


def test_all_tier_ids_sorted():
    ids = all_tier_ids()
    assert ids == ["concept", "deliver", "quote", "full", "select"]


# ───── 7. Addon 产物不默认加入任何档 ─────

def test_addons_not_in_default_tiers():
    """严老师 spec L368-375 按需追加项 · tier 不默认含 · 客户/销售明说"""
    for spec in _PRODUCTS_LIST:
        if spec.addon:
            assert len(spec.tiers) == 0, \
                f"{spec.key} 是 addon 但默认挂在 tier={spec.tiers}"


# ───── 8. get_spec_for_artifact API ─────

def test_get_spec_for_artifact():
    spec = get_spec_for_artifact("scene")
    assert spec is not None and spec.key == "scene"
    assert get_spec_for_artifact("unknown") is None


def test_get_spec_covers_all_light_producers():
    """每个 light_producer 都能 get_spec_for_artifact 找到"""
    for spec in _PRODUCTS_LIST:
        if spec.light_producer:
            found = get_spec_for_artifact(spec.light_producer)
            assert found is not None, f"{spec.light_producer} 找不到 spec"
