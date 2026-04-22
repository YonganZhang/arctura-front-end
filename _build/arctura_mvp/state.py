"""Project State Machine · 从 schemas/state-machine.json load · 单一真源

对齐 JS 侧 api/projects/[slug].js 加载同一 JSON · 改一处就行。
"""
from __future__ import annotations
from typing import Literal
import json
from pathlib import Path

ProjectState = Literal["empty", "briefing", "planning", "generating", "live"]

_SCHEMA_PATH = Path(__file__).parent / "schemas" / "state-machine.json"


def _load() -> dict:
    return json.loads(_SCHEMA_PATH.read_text())


_SCHEMA = _load()
STATES = _SCHEMA["states"]
# transitions: dict[state, set[state]]（JSON 是 list · 转 set 更好查）
TRANSITIONS: dict[ProjectState, set[ProjectState]] = {
    s: set(allowed) for s, allowed in _SCHEMA["transitions"].items()
}


def validate_transition(from_s: ProjectState, to_s: ProjectState) -> None:
    if to_s not in TRANSITIONS.get(from_s, set()):
        raise ValueError(f"Illegal state transition: {from_s} → {to_s}")


def can_edit(state: ProjectState) -> bool:
    return state == "live"


def can_save(state: ProjectState, pending_count: int) -> bool:
    return state == "live" and pending_count > 0


def is_terminal(state: ProjectState) -> bool:
    return state == "live"
