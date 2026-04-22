"""Project State Machine · 5 states · 合法 transitions 白名单

对齐 arctura-phase6-complete-plan-v3-2026-04-22.md §1。
saved 被砍 · pending_count 驱动 UI（Delta #10）。
"""
from __future__ import annotations
from typing import Literal

ProjectState = Literal["empty", "briefing", "planning", "generating", "live"]

TRANSITIONS: dict[ProjectState, set[ProjectState]] = {
    "empty": {"briefing"},
    "briefing": {"briefing", "planning"},
    "planning": {"planning", "generating", "briefing"},
    "generating": {"live", "planning"},       # 成功 live · 失败回 planning
    "live": {"live", "briefing", "planning"}, # 精修 · regenerate · 改档
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
