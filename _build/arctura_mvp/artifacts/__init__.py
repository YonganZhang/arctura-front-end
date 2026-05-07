"""Artifact registry · Phase 8 · 全从 product_registry 派生

规则(Phase 12.4 加 engine routing):
  - engine="fast"(默认) · 找 light_producer (`artifacts/<name>.py`)
  - engine="formal" · 优先找 formal_producer (`artifacts/<name>_formal.py` 真接老师代码)
    · formal_producer=None → 降级 fast(并标 _degraded_from="formal")
  - light_producer=None → pipeline 层 fallback 到通用 skeleton(`_unimplemented.produce_stub`)
"""
from __future__ import annotations
from typing import Callable, Optional, Tuple

from ._base import Artifact
from ..product_registry import PRODUCTS


def get_artifact(name: str, engine: str = "fast") -> Optional[Callable]:
    """name + engine → produce(ctx, on_event)

    Phase 12.4 · engine routing:
      engine="fast" → light_producer(LIGHT 占位,快速 demo)
      engine="formal" → formal_producer(真接老师 cli_anything / playbooks/scripts) · 没实装降级 fast
    返 None 表示完全无实装 · pipeline 层走 _unimplemented.produce_stub 兜底
    """
    spec = PRODUCTS.get(name)
    if spec is None:
        return None

    # Phase 12.4 · engine = "formal" 优先用 formal_producer
    if engine == "formal" and spec.formal_producer:
        try:
            module = __import__(
                f"_build.arctura_mvp.artifacts.{spec.formal_producer}",
                fromlist=["produce"],
            )
            fn = getattr(module, "produce", None)
            if fn:
                return fn
        except ImportError:
            pass  # formal 模块 import 失败 · 降级 fast

    # 回退路径:fast / formal_producer 未实装 / formal import 失败 → light_producer
    if spec.light_producer is None:
        return None
    try:
        module = __import__(
            f"_build.arctura_mvp.artifacts.{spec.light_producer}",
            fromlist=["produce"],
        )
    except ImportError:
        return None
    return getattr(module, "produce", None)


def resolve_artifact_engine(name: str, requested_engine: str) -> Tuple[Optional[str], str]:
    """诊断用:返 (实际用 producer, 实际 engine)

    Phase 12.4 · 让 worker 日志能写 [evt] artifact_resolved · name=X · requested=formal · used=fast(degraded)
    """
    spec = PRODUCTS.get(name)
    if spec is None:
        return (None, "missing_spec")
    if requested_engine == "formal" and spec.formal_producer:
        return (spec.formal_producer, "formal")
    if spec.light_producer:
        degraded = " (degraded from formal)" if requested_engine == "formal" else ""
        return (spec.light_producer, f"fast{degraded}")
    return (None, "no_producer")


def get_unimplemented_fallback() -> Callable:
    """pipeline 未实装时走这个 · 用 registry spec 自动生成 _TODO"""
    from ._unimplemented import produce_for_spec
    return produce_for_spec
