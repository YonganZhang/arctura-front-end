"""Formal renderer · Blender Eevee · 待实装

已装(PolyU 2026-05-07):/mnt/data/yongan/.local/blender-4.5/blender(+ /usr/local/bin/blender 软链)
计划:scene.json → Blender Python scene → 8 张 Eevee 渲染 → 写 assets/mvps/<slug>/renders-formal/
当前:占位 · 降级 fall back 到 fast 并标注
"""
from __future__ import annotations
import os
from pathlib import Path
import shutil
from typing import Callable, Optional


def _find_blender() -> Optional[Path]:
    """Phase 12.2 · 动态找 Blender(同 exports.py 逻辑 · 不硬编码 tencent-hk 旧路径)"""
    p = shutil.which("blender")
    if p:
        return Path(p)
    env_p = os.environ.get("BLENDER")
    if env_p and Path(env_p).exists():
        return Path(env_p)
    polyu_default = Path("/mnt/data/yongan/.local/blender-4.5/blender")
    if polyu_default.exists():
        return polyu_default
    return None


BLENDER_BIN = _find_blender()


def is_available() -> bool:
    return BLENDER_BIN is not None and BLENDER_BIN.exists()


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
