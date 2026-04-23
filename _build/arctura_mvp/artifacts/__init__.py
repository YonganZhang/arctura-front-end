"""Artifact registry · 按名字分派 · pipeline 遍历 resolve_tier 返回的 artifacts"""
from __future__ import annotations
from typing import Callable, Optional

from ._base import Artifact


# 动态 import · 避免循环依赖
def get_artifact(name: str) -> Optional[Callable]:
    """返回 produce(ctx, on_event) callable · 或 None（未实装 · pipeline 应 skip）"""
    if name == "scene":
        from .scene import produce; return produce
    if name == "moodboard":
        from .moodboard import produce; return produce
    if name == "floorplan":
        from .floorplan import produce; return produce
    if name == "renders":
        from .renders import produce; return produce
    if name == "bundle":
        from .bundle import produce; return produce
    # 其他 artifact（deck_client / client_readme / energy_report / exports / variants / case_study）
    # Phase 7 继续补 · 当前未实装 → None → pipeline 记 skipped
    return None
