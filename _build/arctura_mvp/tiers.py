"""Arctura Step 0b 产物档位 · 5 档

Phase 8 · 本文件已降级为 SSOT 的 thin facade · 真数据在 product_registry.py
保留 resolve_tier / pick_engine / all_tier_ids / list_tiers_for_ui 旧 API · 不 break 调用方
"""
from __future__ import annotations
from typing import Literal, Optional

from .product_registry import (
    TIER_META, PRODUCTS, all_tier_ids, list_tiers_for_ui,
    resolve_tier_artifact_names,
)

TierId = Literal["concept", "deliver", "quote", "full", "select"]
RenderEngine = Literal["fast", "formal"]


def resolve_tier(tier_id: TierId, variant_count: int = 1) -> dict:
    """展开 tier 到最终产物集 + 引擎 · 旧 API · 从 registry 推"""
    if tier_id not in TIER_META:
        raise ValueError(f"unknown tier: {tier_id}")
    meta = TIER_META[tier_id]
    # variant_count override · select 档 registry 有默认 3
    vc = variant_count if variant_count != 1 else meta.get("variant_count", 1)
    return {
        "tier_id": tier_id,
        "variant_count": vc,
        "artifacts": resolve_tier_artifact_names(tier_id),
        "render_engine_default": meta["render_engine_default"],
        "estimated_min": meta.get("estimated_min", {}),
        "label_zh": meta["label_zh"],
    }


def pick_engine(tier: TierId, override: Optional[RenderEngine] = None) -> RenderEngine:
    """tier → render engine · override 优先"""
    if override:
        return override
    return TIER_META[tier]["render_engine_default"]


# Backward compat · 旧 TIER_CONFIG / TIER_ALIASES 保留空 dict · 不再是真源
# 如有调用方读这两个 dict · 读到空会走 resolve_tier 正确路径
TIER_CONFIG: dict = {}
TIER_ALIASES: dict = {}
