"""T23.1 · tiers.resolve_tier · select 解糖 + 继承链"""
from _build.arctura_mvp.tiers import (
    resolve_tier, pick_engine, list_tiers_for_ui,
    TIER_CONFIG, TIER_ALIASES, all_tier_ids,
)


def test_concept_has_4_artifacts():
    r = resolve_tier("concept")
    assert set(r["artifacts"]) == {"scene", "moodboard", "floorplan", "renders"}
    assert r["render_engine_default"] == "fast"
    assert r["variant_count"] == 1


def test_deliver_inherits_concept_and_adds_deck():
    r = resolve_tier("deliver")
    assert "scene" in r["artifacts"]        # 继承
    assert "deck_client" in r["artifacts"]  # 新加
    assert "client_readme" in r["artifacts"]
    assert r["render_engine_default"] == "fast"


def test_quote_inherits_deliver_adds_energy():
    r = resolve_tier("quote")
    assert "deck_client" in r["artifacts"]   # 来自 deliver
    assert "energy_report" in r["artifacts"] # 新加
    assert r["render_engine_default"] == "fast"


def test_full_adds_exports_and_switches_to_formal():
    r = resolve_tier("full")
    assert "exports" in r["artifacts"]
    assert "energy_report" in r["artifacts"]  # 继承
    assert r["render_engine_default"] == "formal"  # ★ 档位自动切 formal


def test_select_is_full_plus_variants_with_count_3():
    r = resolve_tier("select")
    # 甄选 = 全案 + variants 产物 · variant_count=3
    assert "variants" in r["artifacts"]
    assert "exports" in r["artifacts"]       # 来自 full
    assert "scene" in r["artifacts"]         # 继承到底
    assert r["variant_count"] == 3
    assert r["render_engine_default"] == "formal"


def test_pick_engine_override_beats_default():
    assert pick_engine("concept") == "fast"
    assert pick_engine("concept", override="formal") == "formal"   # override 胜出
    assert pick_engine("full") == "formal"
    assert pick_engine("full", override="fast") == "fast"          # 全案也能用 fast


def test_list_tiers_for_ui_has_5_entries_sorted():
    uis = list_tiers_for_ui()
    assert len(uis) == 5
    ids = [t["id"] for t in uis]
    assert ids == ["concept", "deliver", "quote", "full", "select"]
    # select 的 variant_count
    sel = next(t for t in uis if t["id"] == "select")
    assert sel["variant_count"] == 3


def test_all_tier_ids_covers_base_and_alias():
    ids = all_tier_ids()
    assert "concept" in ids and "full" in ids and "select" in ids
