"""derive() · 语义 SSOT (brief) + 交互差量 SSOT (overrides) → 派生缓存

Phase 11.3 · ADR-001 §"derive 是纯函数" 落地。

设计契约：
  - **纯函数** · 无副作用 · 无网络 · 无 LLM · ~50ms · 同输入永远同输出
  - 输入：brief（语义意图）+ overrides（用户在 3D viewer 拖拽产生的差量）+ artifacts_index（可选 · 仅承载链接 / 指标缓存 · 不参与 scene 语义）
  - 输出：scene · editable · derived_metrics · _signatures（用于 cache invalidate）

禁止：
  - 在 derive 里调 LLM 推断 must_have（必须先在 brief_engine 跑完 LLM 再传 brief）
  - 在 derive 里查 KV / 读磁盘
  - 让 derive 修改入参（深拷贝 + 返新对象）

用法：
    from _build.arctura_mvp.derive import derive

    bundle = derive(brief, overrides={"layout": {...}}, artifacts_index={"renders": [...]})
    bundle.scene          # 3D 状态
    bundle.editable       # 用户可编辑字段（从 brief 派生）
    bundle.derived_metrics  # eui / cost / co2
    bundle._signatures    # {brief_sha, overrides_sha, schema_version}
"""
from __future__ import annotations
import copy
import hashlib
import json
from dataclasses import dataclass, field, asdict
from typing import Any, Optional

from ..generators import build_scene_from_brief
from .overrides import apply_overrides_to_scene, OVERRIDES_SCHEMA_VERSION

# 任何字段变更都必须 bump
DERIVE_SCHEMA_VERSION = "v1"


@dataclass
class DeriveBundle:
    scene: dict
    editable: dict
    derived_metrics: dict
    _signatures: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "scene": self.scene,
            "editable": self.editable,
            "derived_metrics": self.derived_metrics,
            "_signatures": self._signatures,
        }


# ───── 派生：editable（从 brief 派生 · 替代 materializer 硬编码 default）─────

# brief 字段 → editable 字段映射（ADR-001 修 fe_payload editable SSOT 不清问题）
_EDITABLE_FALLBACKS = {
    "area_m2": 30,
    "insulation_mm": 60,
    "glazing_uvalue": 2.0,
    "lighting_cct": 3000,
    "lighting_density_w_m2": 8,
    "wwr": 0.25,
    "region": "HK",
}


def _editable_from_brief(brief: dict) -> dict:
    """优先读 brief.envelope / lighting / openings · 缺则用 fallback 默认"""
    space = brief.get("space") or {}
    envelope = brief.get("envelope") or {}
    lighting = brief.get("lighting") or {}
    openings = brief.get("openings") or {}

    return {
        "area_m2": float(space.get("area_sqm") or _EDITABLE_FALLBACKS["area_m2"]),
        "insulation_mm": int(envelope.get("insulation_mm")
                              or _EDITABLE_FALLBACKS["insulation_mm"]),
        "glazing_uvalue": float(envelope.get("window_u")
                                  or _EDITABLE_FALLBACKS["glazing_uvalue"]),
        "lighting_cct": int(lighting.get("cct")
                              or _EDITABLE_FALLBACKS["lighting_cct"]),
        "lighting_density_w_m2": float(lighting.get("density_wperm2")
                                         or _EDITABLE_FALLBACKS["lighting_density_w_m2"]),
        "wwr": float(openings.get("wwr") or _EDITABLE_FALLBACKS["wwr"]),
        "region": str(brief.get("region") or _EDITABLE_FALLBACKS["region"]),
    }


# ───── 派生：metrics（eui / cost / co2 简易估算 · FULL 版用 EnergyPlus）─────

def _derived_metrics_from_editable(editable: dict, brief: dict) -> dict:
    """轻量启发式 · 只在没有真 EnergyPlus 输出时给前端展示用

    真值由 worker 的 energy_report artifact 算 · 写入 artifacts_index.metrics
    derive() 这里给"看着合理"的占位值 · 不会覆盖 artifacts_index 提供的真值
    """
    area = editable.get("area_m2", 30)
    cct = editable.get("lighting_cct", 3000)
    density = editable.get("lighting_density_w_m2", 8)
    insul = editable.get("insulation_mm", 60)
    region = editable.get("region", "HK")

    # 启发式 · 不是真模拟（HK ~45 baseline · 加密插值 · 只为前端 UI 展示）
    base_eui = 45.0
    eui = base_eui - (insul - 60) * 0.15 + (density - 8) * 1.5
    eui = max(20.0, round(eui, 1))

    # 单方价 (HK$/m²)：HK ~3500 · CN ~2200 · INTL ~4500
    cost_per_m2 = {"HK": 3500, "CN": 2200, "INTL": 4500}.get(region, 3500)
    cost_total = round(area * cost_per_m2)
    co2 = round(eui * area * 0.4 / 1000, 2)   # CO2 ton/yr (HK 排放因子 0.4)

    return {
        "eui_kwh_m2_yr": eui,
        "cost_total": cost_total,
        "cost_per_m2": cost_per_m2,
        "co2_t_per_yr": co2,
        "_source": "derive_heuristic",   # 区分真 EnergyPlus 输出（_source: "energyplus"）
    }


# ───── signatures · cache key ─────

def _stable_json_hash(obj: Any) -> str:
    """canonical · sort keys · 浮点稳定"""
    s = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(s.encode()).hexdigest()[:16]


def _compute_signatures(brief: dict, overrides: Optional[dict],
                        artifacts_index: Optional[dict]) -> dict:
    return {
        "brief_sha": _stable_json_hash(brief or {}),
        "overrides_sha": _stable_json_hash(overrides or {}),
        "artifacts_sha": _stable_json_hash(artifacts_index or {}),
        "derive_schema_version": DERIVE_SCHEMA_VERSION,
        "overrides_schema_version": OVERRIDES_SCHEMA_VERSION,
    }


# ───── 主入口 ─────

def derive(brief: dict,
           overrides: Optional[dict] = None,
           artifacts_index: Optional[dict] = None,
           *,
           slug: str = "derive") -> DeriveBundle:
    """brief + overrides → scene + editable + derived_metrics

    artifacts_index（可选）：worker 跑出的真 artifact 链接 + metrics
                            如有 metrics.eui_kwh_m2_yr 真值 · 替换启发式占位

    slug 仅给 scene generator 当标识用 · 不影响 derive 输出（纯函数性 OK）
    """
    if not brief:
        raise ValueError("brief 为空 · 无法 derive")

    # 深拷贝所有入参 · 防意外修改入参（Codex 三审 #1：原本只 brief 深拷贝）
    brief_copy = copy.deepcopy(brief)
    overrides = copy.deepcopy(overrides) if overrides else {}
    artifacts_index = copy.deepcopy(artifacts_index) if artifacts_index else {}

    # 1. scene · base 由 generator 出 · 然后应用 overrides
    base_scene = build_scene_from_brief(brief_copy, slug)
    scene = apply_overrides_to_scene(base_scene, overrides)

    # 2. editable · brief 派生
    editable = _editable_from_brief(brief_copy)

    # 3. derived metrics · 优先用 artifacts_index 真值
    real_metrics = (artifacts_index.get("metrics") or {}) if isinstance(artifacts_index, dict) else {}
    if isinstance(real_metrics, dict) and "eui_kwh_m2_yr" in real_metrics:
        # 真 EnergyPlus 跑过 · 用真值 · 标 source
        derived_metrics = {
            **_derived_metrics_from_editable(editable, brief_copy),
            **real_metrics,
            "_source": "energyplus",
        }
    else:
        derived_metrics = _derived_metrics_from_editable(editable, brief_copy)

    return DeriveBundle(
        scene=scene,
        editable=editable,
        derived_metrics=derived_metrics,
        _signatures=_compute_signatures(brief_copy, overrides, artifacts_index),
    )


__all__ = ["derive", "DeriveBundle", "DERIVE_SCHEMA_VERSION"]
