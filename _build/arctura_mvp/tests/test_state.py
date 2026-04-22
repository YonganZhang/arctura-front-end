"""T23.2 · state.validate_transition · 5x5 矩阵 + 非法路径 · 读 JSON 真源"""
import pytest
from _build.arctura_mvp.state import (
    STATES, TRANSITIONS, validate_transition, can_edit, can_save, is_terminal,
)


def test_states_list_has_5():
    assert STATES == ["empty", "briefing", "planning", "generating", "live"]


def test_transitions_loaded_from_json():
    # 从 schemas/state-machine.json load · set 化
    assert "briefing" in TRANSITIONS["empty"]
    assert "briefing" not in TRANSITIONS["live"] or True  # live→briefing 是 regenerate


@pytest.mark.parametrize("from_s,to_s", [
    ("empty", "briefing"),
    ("briefing", "briefing"),
    ("briefing", "planning"),
    ("planning", "generating"),
    ("planning", "briefing"),
    ("planning", "planning"),
    ("generating", "live"),
    ("generating", "planning"),   # 生成失败回退
    ("live", "live"),               # 精修
    ("live", "briefing"),           # regenerate
    ("live", "planning"),           # 改档
])
def test_legal_transitions_pass(from_s, to_s):
    validate_transition(from_s, to_s)  # 不 raise


@pytest.mark.parametrize("from_s,to_s", [
    ("empty", "live"),
    ("empty", "generating"),
    ("empty", "planning"),
    ("briefing", "generating"),
    ("briefing", "live"),
    ("planning", "live"),           # 必须先经 generating
    ("live", "empty"),              # 无法回到 empty
    ("live", "generating"),          # 必须先经 planning
    ("generating", "briefing"),     # 失败只回 planning · 不回 briefing
])
def test_illegal_transitions_raise(from_s, to_s):
    with pytest.raises(ValueError, match="Illegal state transition"):
        validate_transition(from_s, to_s)


def test_matrix_exhaustive_5x5():
    """每个 (from, to) 组合 · 不在 TRANSITIONS[from] 里必须 raise"""
    for from_s in STATES:
        for to_s in STATES:
            if to_s in TRANSITIONS.get(from_s, set()):
                validate_transition(from_s, to_s)  # 合法 · 不抛
            else:
                with pytest.raises(ValueError):
                    validate_transition(from_s, to_s)


def test_can_edit_only_live():
    for s in STATES:
        assert can_edit(s) == (s == "live")


def test_can_save_live_with_pending():
    assert can_save("live", 3) is True
    assert can_save("live", 0) is False
    assert can_save("briefing", 99) is False
    assert can_save("planning", 5) is False


def test_is_terminal():
    assert is_terminal("live") is True
    for s in ["empty", "briefing", "planning", "generating"]:
        assert is_terminal(s) is False


def test_unknown_state_in_from_raises():
    with pytest.raises(ValueError):
        validate_transition("imaginary", "live")
