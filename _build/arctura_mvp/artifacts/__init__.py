"""Artifact registry · Phase 8 · 全从 product_registry 派生

规则：
  - 有 light_producer (`artifacts/<name>.py`) → 动态 import 它
  - light_producer=None → pipeline 层 fallback 到通用 skeleton（`_unimplemented.produce_stub`）
    · 走 registry 的 spec_ref + full_hint 统一生成 _TODO-<name>.md
"""
from __future__ import annotations
from typing import Callable, Optional

from ._base import Artifact
from ..product_registry import PRODUCTS


def get_artifact(name: str) -> Optional[Callable]:
    """name → produce(ctx, on_event) · 从 registry 派生

    返 None 表示 "无 LIGHT producer" · pipeline 层走 _unimplemented.produce_stub 兜底
    """
    spec = PRODUCTS.get(name)
    if spec is None:
        return None
    if spec.light_producer is None:
        return None   # 无 LIGHT 实装 · pipeline 走 unimplemented fallback
    # 动态 import 对应 artifact 模块
    try:
        module = __import__(
            f"_build.arctura_mvp.artifacts.{spec.light_producer}",
            fromlist=["produce"],
        )
    except ImportError:
        return None
    return getattr(module, "produce", None)


def get_unimplemented_fallback() -> Callable:
    """pipeline 未实装时走这个 · 用 registry spec 自动生成 _TODO"""
    from ._unimplemented import produce_for_spec
    return produce_for_spec
