"""渲染引擎 dispatch · 按档位推 fast/formal · 可 override"""
from __future__ import annotations
from typing import Optional, Callable

from ..tiers import pick_engine as _pick


def get_renderer(tier: str, override: Optional[str] = None) -> Callable:
    """返回渲染函数 · signature: (ctx) -> list[{name, path}]"""
    engine = _pick(tier, override)
    if engine == "fast":
        from . import fast
        return fast.render
    elif engine == "formal":
        from . import formal
        return formal.render
    raise ValueError(f"unknown engine: {engine}")
