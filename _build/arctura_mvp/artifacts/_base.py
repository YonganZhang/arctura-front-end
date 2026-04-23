"""Artifact ABC · 所有产物生成器共用接口

设计目标：
- 每 artifact 单一职责 · 单一文件
- produce(ctx) → 标准 ArtifactResult（dataclass 见 types.py）
- on_event hook · 推 SSE / 日志
- 纯函数 · 无全局副作用 · 方便 mock / 单测
"""
from __future__ import annotations
import time
from abc import ABC, abstractmethod
from typing import Callable, Optional

from ..types import ArtifactResult


class Artifact(ABC):
    """产物生成器基类 · 所有 artifact 继承"""

    name: str = ""
    requires: list[str] = []   # 依赖的其他 artifact 名（顺序用）

    @abstractmethod
    def produce(self, ctx: dict, on_event: Optional[Callable] = None) -> ArtifactResult:
        """ctx: {project, tier_resolved, sb_dir, fe_root, ...}

        要求：
        - 成功 → ArtifactResult(status="done", output_path=..., timing_ms)
        - 做不到但明确 → status="skipped" · reason 说明
        - 异常 → status="error" · error={exception, trace_tail}
        """
        ...


def timed(fn: Callable):
    """装饰器 · 自动测耗时"""
    def wrapper(*args, **kwargs):
        t0 = time.time()
        result = fn(*args, **kwargs)
        elapsed = int((time.time() - t0) * 1000)
        if isinstance(result, ArtifactResult):
            result.timing_ms = elapsed
        elif isinstance(result, dict):
            result["timing_ms"] = elapsed
        return result
    return wrapper
