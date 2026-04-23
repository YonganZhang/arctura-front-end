"""Formal renderer · Blender Eevee · 待实装

已装：~/.local/blender/blender-4.2.3-linux-x64/blender
计划：scene.json → Blender Python scene → 8 张 Eevee 渲染 → 写 assets/mvps/<slug>/renders-formal/
当前：占位 · 降级 fall back 到 fast 并标注
"""
from __future__ import annotations
from pathlib import Path
import shutil
from typing import Callable, Optional

BLENDER_BIN = Path.home() / ".local" / "blender" / "blender-4.2.3-linux-x64" / "blender"


def is_available() -> bool:
    return BLENDER_BIN.exists() and shutil.which(str(BLENDER_BIN)) is not None


def render(ctx: dict, *, on_event: Optional[Callable] = None) -> dict:
    if on_event:
        on_event("artifact_start", {"name": "renders", "engine": "formal",
                                      "note": "Phase 7 · 待实装 · 降级 fast"})
    # 降级到 fast
    from . import fast
    r = fast.render(ctx, on_event=on_event)
    # 标注是 degraded
    r["_degraded_from"] = "formal"
    return r
