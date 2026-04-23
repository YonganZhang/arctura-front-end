"""T23.4 · Python / JS brief rules 跨语言一致性锁定

防 _build/arctura_mvp/chat/brief_engine.py 跟 api/brief/chat.js 两边 drift。
两端都从 schemas/brief-rules.json load · 这个测试验证：
  (1) JSON load 无误
  (2) Python 侧 completeness / ready_for_tier 行为符合预期（JS 侧实际跑走 e2e 验证）
"""
import json
from pathlib import Path
import pytest
from _build.arctura_mvp.chat.brief_engine import (
    completeness, ready_for_tier, missing_must_fields,
    MUST_FILL_FOR_PLANNING, NICE_TO_HAVE,
)

SCHEMAS_DIR = Path(__file__).parent.parent / "schemas"
# tests/ → arctura_mvp/ → _build/ → Arctura-Front-end/ → api/_shared/
API_SHARED = Path(__file__).resolve().parents[3] / "api" / "_shared"


def test_brief_rules_json_same_between_source_and_api_copy():
    """schemas/brief-rules.json 必须与 api/_shared/brief-rules.json 一致"""
    src = json.loads((SCHEMAS_DIR / "brief-rules.json").read_text())
    api = json.loads((API_SHARED / "brief-rules.json").read_text())
    assert src == api, "brief-rules 双端 drift · 必须同步"


def test_state_machine_json_same_between_source_and_api_copy():
    src = json.loads((SCHEMAS_DIR / "state-machine.json").read_text())
    api = json.loads((API_SHARED / "state-machine.json").read_text())
    assert src == api, "state-machine 双端 drift · 必须同步"


def test_must_fill_loaded_from_json():
    rules = json.loads((SCHEMAS_DIR / "brief-rules.json").read_text())
    assert len(MUST_FILL_FOR_PLANNING) == len(rules["must_fill_for_planning"])


def test_nice_to_have_loaded_from_json():
    rules = json.loads((SCHEMAS_DIR / "brief-rules.json").read_text())
    assert len(NICE_TO_HAVE) == len(rules["nice_to_have"])


# 行为 snapshot · 输入固定 brief · 输出 completeness / ready_for_tier / missing
# 如果 weights / threshold / must/nice 改 · 这些 snapshot 必变 · 提醒同步 JS
# Phase 7.4 · must 扩到 5（加 headcount）· nice 扩到 15（加 n_floors / mep_brief 2 字段）
SNAPSHOT_CASES = [
    # 空 · 5 must 全缺
    ({}, {"completeness": 0.0, "ready": False, "missing_count": 5}),
    # 只有 project · must 1/5 · nice 0/15 · 0.2*0.6 = 0.12
    ({"project": "T"}, {"completeness": 0.12, "ready": False, "missing_count": 4}),
    # must 齐（但 nice 空）· 5/5 · nice 0/15 · 1.0*0.6 + 0 = 0.6
    ({
        "project": "T",
        "space": {"area_sqm": 30},
        "headcount": 5,
        "style": {"keywords": ["a"]},
        "functional_zones": [{"name": "x"}],
    }, {"completeness": 0.6, "ready": True, "missing_count": 0}),
    # must 齐 + 几个 nice · must 5/5 (1.0) + nice 5/15 (0.333) → 0.6 + 0.333*0.4 = 0.733 ≈ 0.73
    ({
        "project": "T", "slug": "test", "client": "c",
        "space": {"type": "x", "area_sqm": 30, "n_floors": 1},
        "headcount": 5,
        "style": {"keywords": ["a"], "palette": {"p": "#fff"}},
        "functional_zones": [{"name": "x"}],
    }, {"completeness": 0.73, "ready": True, "missing_count": 0}),
]


@pytest.mark.parametrize("brief,expected", SNAPSHOT_CASES)
def test_completeness_snapshots(brief, expected):
    c = completeness(brief)
    assert abs(c - expected["completeness"]) < 0.02, f"brief={brief} c={c}"
    assert ready_for_tier(brief) == expected["ready"]
    assert len(missing_must_fields(brief)) == expected["missing_count"]
