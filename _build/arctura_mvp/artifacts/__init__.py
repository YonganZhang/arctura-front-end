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
    # Phase 7.4 · 6 个未实装 artifact 走 skeleton · 返 status=skipped + 写 _TODO-<name>.md
    # 不再 silent skip · 对齐 spec L388-390 "做不到就说"
    if name == "deck_client":
        from .deck_client import produce; return produce
    if name == "client_readme":
        from .client_readme import produce; return produce
    if name == "energy_report":
        from .energy_report import produce; return produce
    if name == "exports":
        from .exports import produce; return produce
    if name == "variants":
        from .variants import produce; return produce
    if name == "case_study":
        from .case_study import produce; return produce
    return None
