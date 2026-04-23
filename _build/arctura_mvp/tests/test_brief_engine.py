"""T23.3 · brief_engine.step · 多轮对话 + deep_merge + PII + completeness"""
import json
import pytest
from _build.arctura_mvp.chat.brief_engine import (
    step, completeness, ready_for_tier, missing_must_fields, _deep_merge,
)


def _mock_llm_factory(script):
    """按轮次返回脚本化 LLM 响应 · script = list of dict"""
    idx = [0]
    def mock(sp, up, history=None, model=None):
        out = script[min(idx[0], len(script) - 1)]
        idx[0] += 1
        return json.dumps(out)
    return mock


# ── 基础 pure 函数 ──

def test_completeness_empty():
    assert completeness({}) == 0.0
    assert completeness(None) == 0.0


def test_completeness_only_project():
    b = {"project": "test"}
    # Phase 7.4 · must 1/5 · nice 0/15 · 0.2*0.6 = 0.12
    assert 0.11 <= completeness(b) <= 0.13


def test_completeness_full_must():
    b = {
        "project": "T",
        "space": {"area_sqm": 30},
        "headcount": 5,
        "style": {"keywords": ["a"]},
        "functional_zones": [{"name": "x"}],
    }
    # Phase 7.4 · must 5/5 · nice 0/15 · 1.0*0.6 + 0*0.4 = 0.6
    c = completeness(b)
    assert 0.55 <= c <= 0.65


def test_ready_for_tier_blocked_until_all_must():
    assert ready_for_tier({}) is False
    partial = {"project": "T", "space": {"area_sqm": 30}}
    assert ready_for_tier(partial) is False
    full_must = {
        "project": "T", "space": {"area_sqm": 30}, "headcount": 5,
        "style": {"keywords": ["a"]}, "functional_zones": [{"n": "x"}],
    }
    assert ready_for_tier(full_must) is True


def test_missing_must_fields():
    # Phase 7.4 · must_fill = project/space.area_sqm/headcount/style.keywords/functional_zones
    assert set(missing_must_fields({})) == {
        "project", "space.area_sqm", "headcount", "style.keywords", "functional_zones",
    }
    assert set(missing_must_fields({"project": "T"})) == {
        "space.area_sqm", "headcount", "style.keywords", "functional_zones",
    }


# ── deep_merge 行为锁定（跟 JS 对齐）──

def test_deep_merge_nested_dict():
    base = {"space": {"type": "office"}}
    patch = {"space": {"area_sqm": 30}}
    merged = _deep_merge(base, patch)
    assert merged["space"] == {"type": "office", "area_sqm": 30}


def test_deep_merge_list_replaces_not_concat():
    base = {"style": {"keywords": ["old1", "old2"]}}
    patch = {"style": {"keywords": ["new1"]}}
    merged = _deep_merge(base, patch)
    assert merged["style"]["keywords"] == ["new1"]  # 数组是替换


def test_deep_merge_does_not_mutate_base():
    base = {"a": {"b": 1}}
    patch = {"a": {"c": 2}}
    merged = _deep_merge(base, patch)
    assert base == {"a": {"b": 1}}  # 原对象未变


# ── step 多轮集成（用真实 22 book-cafe brief 切分）──

def test_step_3_turns_reaches_ready(brief_book_cafe):
    """用 22-boutique-book-cafe 真 brief 反推 3 轮对话"""
    target = brief_book_cafe
    # 脚本化 LLM · 3 轮逐步填（Phase 7.4 · headcount 跟 functional_zones 一起在第 3 轮填）
    script = [
        {
            "reply": "好的 · 项目名和场地类型已记",
            "brief_patch": {
                "project": target["project"],
                "space": {"type": target.get("space", {}).get("type"),
                          "area_sqm": target.get("space", {}).get("area_sqm")},
            },
            "next_question": "风格关键词",
            "pii_fields": [],
        },
        {
            "reply": "风格记好 · 问功能分区",
            "brief_patch": {
                "style": target.get("style", {"keywords": ["modern"]}),
            },
            "next_question": "功能分区",
            "pii_fields": [],
        },
        {
            "reply": "齐了 · 可以进入选档",
            "brief_patch": {
                "functional_zones": target.get("functional_zones", [{"name": "main", "area_sqm": 50}]),
                "headcount": target.get("headcount") or 8,
            },
            "next_question": "",
            "pii_fields": [],
        },
    ]
    llm = _mock_llm_factory(script)

    r1 = step("我想做一个书店咖啡馆", llm_call=llm)
    assert "project" in r1["brief"]
    assert not r1["ready_for_tier"]

    r2 = step("风格想要什么", current_brief=r1["brief"], llm_call=llm)
    assert "style" in r2["brief"] and r2["brief"]["style"]
    assert "project" in r2["brief"]  # 第一轮没丢

    r3 = step("划分 X Y Z 区", current_brief=r2["brief"], llm_call=llm)
    assert r3["ready_for_tier"] is True
    assert r3["completeness"] >= 0.6
    assert len(r3["missing"]) == 0


def test_step_pii_accumulates():
    script = [
        {"reply": "a", "brief_patch": {"client": "张校长"}, "next_question": "", "pii_fields": ["client"]},
        {"reply": "b", "brief_patch": {"budget_hkd": 200000}, "next_question": "", "pii_fields": ["budget_hkd"]},
    ]
    llm = _mock_llm_factory(script)
    r1 = step("客户是张校长", llm_call=llm)
    r2 = step("预算 20 万", current_brief=r1["brief"], llm_call=llm)
    assert "client" in r2["brief"]["_pii_fields"]
    assert "budget_hkd" in r2["brief"]["_pii_fields"]
