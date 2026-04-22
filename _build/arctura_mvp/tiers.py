"""Arctura Step 0b 产物档位 · 单一真源 · 5 档

对齐 StartUP-Building/CLAUDE.md L366-L375 + L405-L434 必含产物清单。
修改这里 · pipeline / artifact dispatch / UI 选择器自动同步。
"""
from __future__ import annotations
from typing import Literal, Optional

TierId = Literal["concept", "deliver", "quote", "full", "select"]
RenderEngine = Literal["fast", "formal"]

# 4 档基础 · select 是 (full, variant_count=3) 的 alias
TIER_CONFIG: dict[str, dict] = {
    "concept": {
        "label_zh": "概念",
        "label_en": "Concept",
        "order": 1,
        "desc_zh": "brief + 3D + 渲染 + 平面图",
        "artifacts": ["scene", "moodboard", "floorplan", "renders"],
        "render_engine_default": "fast",
        "estimated_min": {"fast": 3, "formal": 15},
    },
    "deliver": {
        "label_zh": "交付",
        "label_en": "Deliver",
        "order": 2,
        "desc_zh": "+方案 PPT + 客户文档",
        "inherits": "concept",
        "add_artifacts": ["deck_client", "client_readme"],
        "render_engine_default": "fast",
        "estimated_min": {"fast": 6, "formal": 20},
    },
    "quote": {
        "label_zh": "报价",
        "label_en": "Quote",
        "order": 3,
        "desc_zh": "+能耗 + 工料报价 + 合规",
        "inherits": "deliver",
        "add_artifacts": ["energy_report"],
        "render_engine_default": "fast",
        "estimated_min": {"fast": 8, "formal": 25},
    },
    "full": {
        "label_zh": "全案",
        "label_en": "Full",
        "order": 4,
        "desc_zh": "+BIM 导出 GLB/FBX/IFC + IFC 质检",
        "inherits": "quote",
        "add_artifacts": ["exports"],
        "render_engine_default": "formal",  # 全案档 · 默认正式渲染
        "estimated_min": {"fast": 12, "formal": 40},
    },
}

# select 档 = (full, 3) 的命名糖 · 独立常量
TIER_ALIASES: dict[str, dict] = {
    "select": {
        "label_zh": "甄选",
        "label_en": "Select",
        "order": 5,
        "desc_zh": "3 方案 × 全案 + 对比拼图 + 决策矩阵",
        "base": "full",
        "variant_count": 3,
        "add_artifacts": ["variants"],  # 甄选专属 · 整个 variants/ 目录
        "render_engine_default": "formal",
        "estimated_min": {"formal": 120},  # 3 × full
    },
}

# OPT_ADDONS（按需追加项 · CLAUDE.md L375）· 当前不参与 resolve · 保留等 Phase 7 接入


def resolve_tier(tier: TierId, variant_count: int = 1) -> dict:
    """展开 tier 到最终产物集 + 引擎 · select 解糖"""
    if tier in TIER_ALIASES:
        alias = TIER_ALIASES[tier]
        base = resolve_tier(alias["base"], alias["variant_count"])
        base["artifacts"] = base["artifacts"] + alias["add_artifacts"]
        base["tier_id"] = tier
        base["variant_count"] = alias["variant_count"]
        base["estimated_min"] = alias["estimated_min"]
        return base
    cfg = TIER_CONFIG[tier]
    if "inherits" in cfg:
        parent = resolve_tier(cfg["inherits"])
        artifacts = parent["artifacts"] + cfg.get("add_artifacts", [])
    else:
        artifacts = list(cfg["artifacts"])
    return {
        "tier_id": tier,
        "variant_count": variant_count,
        "artifacts": artifacts,
        "render_engine_default": cfg["render_engine_default"],
        "estimated_min": cfg.get("estimated_min", {}),
        "label_zh": cfg["label_zh"],
    }


def pick_engine(tier: TierId, override: Optional[RenderEngine] = None) -> RenderEngine:
    """档位 → 渲染引擎 · override 允许 · 默认推导"""
    if override:
        return override
    return resolve_tier(tier)["render_engine_default"]


def all_tier_ids() -> list[str]:
    return list(TIER_CONFIG.keys()) + list(TIER_ALIASES.keys())


def list_tiers_for_ui() -> list[dict]:
    """前端 TierPicker 用 · 5 档完整信息"""
    out = []
    for tier in TIER_CONFIG:
        cfg = TIER_CONFIG[tier]
        out.append({
            "id": tier,
            "label_zh": cfg["label_zh"],
            "order": cfg["order"],
            "desc_zh": cfg["desc_zh"],
            "artifacts": resolve_tier(tier)["artifacts"],
            "render_engine": cfg["render_engine_default"],
            "estimated_min": cfg["estimated_min"],
        })
    for alias_id, alias in TIER_ALIASES.items():
        base = resolve_tier(alias_id)
        out.append({
            "id": alias_id,
            "label_zh": alias["label_zh"],
            "order": alias["order"],
            "desc_zh": alias["desc_zh"],
            "artifacts": base["artifacts"],
            "render_engine": alias["render_engine_default"],
            "estimated_min": alias["estimated_min"],
            "variant_count": alias["variant_count"],
        })
    return sorted(out, key=lambda x: x["order"])
