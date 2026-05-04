"""Phase 11.8 · LLM JSON 解析器测试 · 用真 LLM 响应 fixture 锁

跟 _tests/unit/llm-parse-json.test.mjs 跑同一份 fixture (fixtures/llm_responses.json)
两端必须产同样结果 · 防 Python/JS drift。
"""
import json
from pathlib import Path
import pytest
from _build.arctura_mvp.chat.llm_parse_json import parse_llm_json, LLMParseError

FIXTURE = Path(__file__).parent / "fixtures" / "llm_responses.json"


def _load_fixture():
    return json.loads(FIXTURE.read_text())


def _partial_match(expect, actual, path=""):
    """递归 partial match · expect 的每 key 必须在 actual 里且值匹配（actual 可有更多 key）"""
    if isinstance(expect, dict) and isinstance(actual, dict):
        for k, v in expect.items():
            assert k in actual, f"{path}: 缺字段 '{k}'"
            _partial_match(v, actual[k], f"{path}.{k}")
    else:
        assert expect == actual, f"{path}: 期望 {expect!r} 实际 {actual!r}"


@pytest.mark.parametrize("case", _load_fixture()["cases"], ids=lambda c: c["name"])
def test_parse_llm_json_real_world_cases(case):
    """每种 LLM 真实响应格式都必须能 parse"""
    result = parse_llm_json(case["raw"])

    if case.get("expect_type") == "array":
        assert isinstance(result, list)
        return

    expect = case.get("expect")
    if expect:
        _partial_match(expect, result, case["name"])


@pytest.mark.parametrize("case", _load_fixture()["expected_to_fail"], ids=lambda c: c["name"])
def test_parse_llm_json_expected_failures(case):
    """这些输入应该抛 LLMParseError · 不该静默返坏数据"""
    with pytest.raises(LLMParseError) as exc_info:
        parse_llm_json(case["raw"])
    if "expected_error" in case:
        assert case["expected_error"] in str(exc_info.value), \
            f"{case['name']}: 错误消息不含 '{case['expected_error']}'"


# ───── 边界 case ─────

def test_non_string_input_raises():
    with pytest.raises(LLMParseError, match="expected string"):
        parse_llm_json(123)
    with pytest.raises(LLMParseError, match="expected string"):
        parse_llm_json(None)


def test_pure_whitespace_raises():
    with pytest.raises(LLMParseError, match="empty content"):
        parse_llm_json("   \n\n  ")


def test_fence_content_with_leading_trailing_whitespace():
    """fence 内有大量空白也能 parse"""
    raw = "```json\n\n\n  {\"x\": 1}  \n\n\n```"
    assert parse_llm_json(raw) == {"x": 1}


def test_multiple_json_blocks_returns_first():
    """有多个 JSON 块 · 返第一个"""
    raw = "First: {\"a\": 1} Second: {\"b\": 2}"
    result = parse_llm_json(raw)
    assert result == {"a": 1}


def test_fence_with_invalid_json_falls_through_to_balanced():
    """fence 内坏 JSON 但外面有合法的 · 平衡块策略救回"""
    raw = "```json\n{not valid\n```\n\nActual: {\"good\": true}"
    result = parse_llm_json(raw)
    # 至少不抛 · 能解出 good=true
    assert result.get("good") is True


# ───── 内部 helper ─────

def test_balanced_block_handles_string_with_braces():
    from _build.arctura_mvp.chat.llm_parse_json import _find_balanced_json_block
    text = '{"x": "text with } in string", "y": 1}'
    block = _find_balanced_json_block(text)
    assert block is not None
    s, e = block
    assert text[s:e] == text   # 整个就是一个块


def test_strip_fence_handles_no_fence():
    from _build.arctura_mvp.chat.llm_parse_json import _strip_markdown_fence
    assert _strip_markdown_fence('{"x":1}') is None


def test_cleanup_handles_smart_quotes_and_trailing_comma():
    from _build.arctura_mvp.chat.llm_parse_json import _cleanup_json_string
    src = '{“x”:1, “y”:2,}'
    out = _cleanup_json_string(src)
    assert json.loads(out) == {"x": 1, "y": 2}
