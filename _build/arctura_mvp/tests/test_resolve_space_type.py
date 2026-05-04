"""Phase 11.1 · _resolve_space_type 行为锁定

修今天 bug：scene generator 严格 dict lookup 对 LLM 创造性 type 全 miss
→ 全部 fallback default → "校长办公室" 跟 "咖啡厅" 生成同一个 scene。

锁定关键词包含匹配 + 取并集行为，防回归。
"""
import json
from pathlib import Path
import pytest

from _build.arctura_mvp.generators._resolve_space_type import (
    resolve_space_type, list_enum, merge_furniture_lists,
)

FIXTURE = Path(__file__).resolve().parents[3] / "api" / "_shared" / "space-type-keywords.json"


# ───────── 1. enum 全部不会 fallback 到 default ─────────

def test_all_enums_resolve_to_themselves():
    """每个 enum 写出来 · 必须解析到自己（不会 default）"""
    for std_type in list_enum():
        out = resolve_space_type(std_type)
        assert out == [std_type], f"{std_type} 解析为 {out}，应该 [{std_type}]"


# ───────── 2. 严格 enum 字符串大小写鲁棒 ─────────

@pytest.mark.parametrize("raw,expected", [
    ("Office", ["office"]),
    ("OFFICE", ["office"]),
    ("  cafe  ", ["cafe"]),
    ("Living_Room", ["living_room"]),
    ("living room", ["living_room"]),  # 空格变体也命中
])
def test_case_and_whitespace_robust(raw, expected):
    assert resolve_space_type(raw) == expected


# ───────── 3. 中英文别名命中（修 bug 主战场）─────────

@pytest.mark.parametrize("raw,expected_first", [
    ("校长办公室",       "office"),
    ("校长办公",         "office"),
    ("principal office", "office"),
    ("workspace",        "office"),
    ("咖啡厅",           "cafe"),
    ("咖啡馆",           "cafe"),
    ("coffee shop",      "cafe"),
    ("书房",             "study"),
    ("master bedroom",   "bedroom"),
    ("家庭客厅",         "living_room"),
    ("餐厅",             "dining"),
    ("零售店铺",         "retail"),
    ("dental clinic",    "clinic"),
    ("画廊",             "gallery"),
    ("showroom",         "gallery"),
    ("co-working",       "multipurpose"),
    ("多功能空间",       "multipurpose"),
])
def test_chinese_english_aliases(raw, expected_first):
    out = resolve_space_type(raw)
    assert expected_first in out, f"{raw} → {out} · 期望含 {expected_first}"


# ───────── 4. 混合场景 · 多类型并集 + 顺序稳定 ─────────

def test_hybrid_cafe_office_returns_both():
    """这是今天 bug 的精确 reproduce · LLM 写 'hybrid cafe-office' → 必须返 [cafe, office]"""
    out = resolve_space_type("hybrid cafe-office")
    assert "cafe" in out
    assert "office" in out
    # cafe 在前（"cafe-office" 里 cafe 出现位置先于 office）
    assert out.index("cafe") < out.index("office")


def test_showroom_cafe_returns_gallery_and_cafe():
    """showroom 在 gallery 关键词内 · cafe 单独命中 · 返两个"""
    out = resolve_space_type("showroom cafe")
    assert "gallery" in out
    assert "cafe" in out


def test_office_dedup_when_multiple_kws_hit_same_std():
    """'校长办公室' 同时含 '校长' 和 '办公' 都映射 office · 必须去重为 [office]"""
    assert resolve_space_type("校长办公室") == ["office"]


# ───────── 5. 兜底情况 ─────────

@pytest.mark.parametrize("raw", [None, "", "   ", "completely random gibberish xyz"])
def test_fallback_to_default(raw):
    assert resolve_space_type(raw) == ["default"]


# ───────── 6. merge_furniture_lists · 并集 + 保序 + 去重 ─────────

def test_merge_furniture_union_preserves_order_dedup():
    defaults = {
        "office": ["desk_standard", "chair_standard", "shelf_open"],
        "cafe":   ["table_dining", "chair_standard", "lamp_pendant"],
        "default": ["chair_standard"],
    }
    out = merge_furniture_lists(["cafe", "office"], defaults)
    # cafe 先 · office 接续 · chair_standard 不重复
    assert out == ["table_dining", "chair_standard", "lamp_pendant", "desk_standard", "shelf_open"]


def test_merge_furniture_unknown_falls_back_to_default():
    defaults = {"default": ["chair_standard"]}
    out = merge_furniture_lists(["unknown_type"], defaults)
    assert out == ["chair_standard"]


# ───────── 6.5 word-boundary 防误伤（Codex Step 1 三审 #6）─────────

@pytest.mark.parametrize("raw,must_not_have", [
    ("barber",            "dining"),    # 'bar' 不该命中 dining
    ("bar shop",          None),         # 词边界下 'bar' 是独立词 → dining 命中是合理
    ("studio apartment",  "office"),    # 'studio' 已删除 · 不该命中 office
    ("study apartment",   "office"),    # 'study' 不是 office 关键词 · 不该误判
    ("librarian office",  None),         # 'library' 词边界下不命中（librarian 不含独立 library）
])
def test_word_boundary_prevents_false_positive(raw, must_not_have):
    out = resolve_space_type(raw)
    if must_not_have is not None:
        assert must_not_have not in out, \
            f"'{raw}' 误命中 {must_not_have} · 实际 {out} · 词边界匹配失效"


def test_bar_word_matches_dining():
    """'cocktail bar' / 'wine bar' · 'bar' 是独立词 · 应命中 dining"""
    assert "dining" in resolve_space_type("cocktail bar")
    assert "dining" in resolve_space_type("wine bar")


# ───────── 7. fixture 跟 enum / DEFAULTS_BY_TYPE 同步 ─────────

def test_fixture_enum_matches_keywords_keys():
    """enum 列表必须跟 keywords 的 key 一致 · 防 fixture 自身 drift"""
    data = json.loads(FIXTURE.read_text())
    assert set(data["enum"]) == set(data["keywords"].keys()), \
        f"fixture enum {data['enum']} 跟 keywords keys {list(data['keywords'].keys())} drift"


def test_every_enum_has_default_furniture():
    """每个 enum 必须在 _DEFAULTS_BY_TYPE 有一行 · 防止新增 enum 但忘配家具 → fallback"""
    from _build.arctura_mvp.generators.scene import _DEFAULTS_BY_TYPE
    for std_type in list_enum():
        assert std_type in _DEFAULTS_BY_TYPE, \
            f"_DEFAULTS_BY_TYPE 缺 {std_type} 一行 · scene 生成会 fallback"
        # 至少 2 件家具 · 太少 scene 太空
        assert len(_DEFAULTS_BY_TYPE[std_type]) >= 2, \
            f"{std_type} 默认家具 {_DEFAULTS_BY_TYPE[std_type]} 太少（至少 2 件）"


def test_default_furniture_items_exist_in_library():
    """_DEFAULTS_BY_TYPE 引用的家具必须在 furniture-library 里 · 不然 generator 拿不到 size"""
    lib_path = Path(__file__).resolve().parents[3] / "data" / "furniture-library.json"
    lib = set(json.loads(lib_path.read_text())["items"].keys())
    from _build.arctura_mvp.generators.scene import _DEFAULTS_BY_TYPE
    for std_type, furniture in _DEFAULTS_BY_TYPE.items():
        for f in furniture:
            assert f in lib, f"_DEFAULTS_BY_TYPE[{std_type}] 引用 {f} 但 furniture-library 没有"
