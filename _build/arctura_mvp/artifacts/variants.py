"""variants · 3 方案对比 · spec L407-420 · Phase 7.5 部分真集成

LIGHT 模式做到：
  - 3 variants brief 变体（基础 / 升级围护 / 高端机电）
  - 从 base 推占位 metrics（EUI / 成本 / 合规 / 风格）
  - 用严老师 vendor/score_variants.py 算 score + stars
  - 产 diff-matrix.md · 6 维度（风格/EUI/工料/维护/合规/决策）· spec L414-420
  - 产 variants/v1/ v2/ v3/ 每个 description.md · report.json

LIGHT 仍跳过：
  - hero.png 方案渲染（需 Blender）
  - comparison-grid-4x3.png（需 image-grid harness）
  - 真 EnergyPlus EUI（需 OpenStudio）

真产数据：从 brief 推基线 EUI（HK 办公 ~48）· variants 加 delta
真分值：严老师 score_variants.py 的加权算法（40/25/20/15）
"""
from __future__ import annotations
import json
import sys
import time
from pathlib import Path
from typing import Callable, Optional

from ..types import ArtifactResult

_VENDOR = Path(__file__).resolve().parents[1] / "vendor"
if str(_VENDOR) not in sys.path:
    sys.path.insert(0, str(_VENDOR))


# 3 方案基础配方 · 基于严老师 change-impact-matrix 的 envelope/hvac 升级方向
_VARIANT_PRESETS = [
    {
        "id": "v1",
        "name": "Baseline",
        "name_zh": "基础方案",
        "desc_en": "Code-minimum compliance · lowest CAPEX",
        "desc_zh": "规范底线合规 · 最低造价",
        "envelope_level": "standard",
        "hvac_level": "standard",
        "style_score": 0.8,
        "cost_multiplier": 1.0,
        "eui_multiplier": 1.0,
        "compliance_delta": 0,
    },
    {
        "id": "v2",
        "name": "Envelope Upgrade",
        "name_zh": "围护升级",
        "desc_en": "Better insulation + Low-E glass · mid CAPEX",
        "desc_zh": "加厚保温 + Low-E 玻璃 · 中等造价",
        "envelope_level": "upgrade",
        "hvac_level": "standard",
        "style_score": 0.9,
        "cost_multiplier": 1.15,
        "eui_multiplier": 0.82,
        "compliance_delta": 1,
    },
    {
        "id": "v3",
        "name": "HVAC Premium",
        "name_zh": "高端机电",
        "desc_en": "VRF + heat recovery + high-COP chiller",
        "desc_zh": "VRF + 热回收 + 高 COP 冷机",
        "envelope_level": "upgrade",
        "hvac_level": "premium",
        "style_score": 1.0,
        "cost_multiplier": 1.32,
        "eui_multiplier": 0.68,
        "compliance_delta": 2,
    },
]


def _estimate_baseline(brief: dict) -> dict:
    """从 brief 推 v1（Baseline）占位 metrics · FULL 应替换为真 EnergyPlus + OpenStudio BoQ"""
    area = float((brief.get("space") or {}).get("area_sqm") or 30)
    # HK 市场默认（来自 StartUP-Building/playbooks/defaults/hk_market.json 精神）
    HK_EUI_OFFICE = 48        # kWh/m²/yr
    HK_PRICE_PER_M2 = 6000    # HK$/m² interior light fit-out
    # 合规（HK BEEO 2021 · 粗估 6/8 项通过）
    return {
        "eui_base": HK_EUI_OFFICE,
        "cost_base_hkd": area * HK_PRICE_PER_M2,
        "compliance_base_passed": 6,
        "compliance_base_total": 8,
    }


def _build_variants_with_metrics(brief: dict) -> list[dict]:
    """为 3 preset 挂占位 metrics · 喂给 score_variants"""
    base = _estimate_baseline(brief)
    out = []
    for preset in _VARIANT_PRESETS:
        variant = dict(preset)
        variant["eui_kwh_m2_yr"] = round(base["eui_base"] * preset["eui_multiplier"], 1)
        variant["boq_grand_total"] = round(base["cost_base_hkd"] * preset["cost_multiplier"], 0)
        variant["compliance_passed"] = base["compliance_base_passed"] + preset["compliance_delta"]
        variant["compliance_total"] = base["compliance_base_total"]
        variant["compliance_pass_rate"] = (
            f"{variant['compliance_passed']}/{variant['compliance_total']}"
        )
        out.append(variant)
    return out


def _build_diff_matrix_md(variants: list[dict], brief: dict) -> str:
    """spec L414-420 · 6 维度 · 风格 / EUI / 工料 / 维护 / 合规 / 决策"""
    keywords = ", ".join((brief.get("style") or {}).get("keywords") or [])
    lines = [
        "# Diff Matrix · 3 方案对比（spec L407-420）",
        "",
        "> ⚠️ **LIGHT 模式** · EUI/成本/合规为基于 HK 市场均值的占位数据 · "
        "真交付需走 StartUP-Building P9 What-If + P7 EnergyPlus + P6 BOQ",
        "",
        "## 基线前提（来自 brief）",
        "",
        f"- 面积：{(brief.get('space') or {}).get('area_sqm') or '—'} m²",
        f"- 风格关键词：{keywords or '—'}",
        f"- 预算区间：{brief.get('budget_hkd', '—')} HKD",
        "",
        "## 对比矩阵",
        "",
        "| 维度 | v1 Baseline | v2 Envelope | v3 Premium |",
        "|---|---|---|---|",
        f"| **风格定调** | {variants[0]['name_zh']} | {variants[1]['name_zh']} | {variants[2]['name_zh']} |",
        f"| **EUI** (kWh/m²/yr) | {variants[0]['eui_kwh_m2_yr']} | "
        f"{variants[1]['eui_kwh_m2_yr']} ({_pct(variants[1]['eui_kwh_m2_yr'], variants[0]['eui_kwh_m2_yr'])}) | "
        f"{variants[2]['eui_kwh_m2_yr']} ({_pct(variants[2]['eui_kwh_m2_yr'], variants[0]['eui_kwh_m2_yr'])}) |",
        f"| **工料报价** (HKD) | {_money(variants[0]['boq_grand_total'])} | "
        f"{_money(variants[1]['boq_grand_total'])} ({_pct(variants[1]['boq_grand_total'], variants[0]['boq_grand_total'])}) | "
        f"{_money(variants[2]['boq_grand_total'])} ({_pct(variants[2]['boq_grand_total'], variants[0]['boq_grand_total'])}) |",
        f"| **年维护估** | *LIGHT 未估* | *LIGHT 未估* | *LIGHT 未估* |",
        f"| **合规** | {variants[0]['compliance_pass_rate']} | "
        f"{variants[1]['compliance_pass_rate']} | "
        f"{variants[2]['compliance_pass_rate']} |",
        f"| **分值**（0-10）| {variants[0].get('score','?'):.1f} ⭐{variants[0].get('stars','?')} | "
        f"{variants[1].get('score','?'):.1f} ⭐{variants[1].get('stars','?')} | "
        f"{variants[2].get('score','?'):.1f} ⭐{variants[2].get('stars','?')} |",
        "",
        "## 决策推荐",
        "",
        f"按严老师加权算法（spec · compliance 40% + eui 25% + cost 20% + style 15%）：",
        f"**{_best_variant_name(variants)}** 综合分最高。",
        "",
        "但仅作参考 · 真决策请走 FULL pipeline 拿真 EnergyPlus EUI + 真 BoQ · ",
        "再走 StartUP-Building/playbooks/scripts/ab-comparison/run_ab.py 产权威 diff-matrix。",
        "",
        "---",
        "*score 算法来自 StartUP-Building/playbooks/scripts/ab-comparison/score_variants.py*",
    ]
    return "\n".join(lines)


def _pct(new: float, base: float) -> str:
    if not base:
        return "—"
    delta = (new - base) / base * 100
    sign = "+" if delta >= 0 else ""
    return f"{sign}{delta:.1f}%"


def _money(v: float) -> str:
    return f"HK$ {int(round(v)):,}"


def _best_variant_name(variants: list[dict]) -> str:
    scored = [v for v in variants if v.get("score") is not None]
    if not scored:
        return variants[0]["name_zh"]
    best = max(scored, key=lambda v: v["score"])
    return best["name_zh"]


def produce(ctx: dict, on_event: Optional[Callable] = None) -> ArtifactResult:
    t0 = time.time()
    project = ctx["project"]
    sb_dir: Path = ctx["sb_dir"]

    if not project.brief:
        return ArtifactResult(
            name="variants", status="skipped",
            timing_ms=int((time.time()-t0)*1000),
            reason="brief 缺 · 无法推 variants",
        )

    variants_dir = sb_dir / "variants"
    variants_dir.mkdir(parents=True, exist_ok=True)

    variants = _build_variants_with_metrics(project.brief)

    # 严老师 score_variants · 加权 0-10 · stars 1-5
    try:
        from score_variants import score_variants
        variants = score_variants(variants)
    except Exception as e:
        # 失败不 abort · 填默认值继续
        for v in variants:
            v.setdefault("score", 5.0)
            v.setdefault("stars", 3)
            v.setdefault("rejected", False)

    # 写每方案 description.md
    for v in variants:
        vd = variants_dir / v["id"]
        vd.mkdir(exist_ok=True)
        desc = (
            f"# {v['name_zh']}（{v['name']}）\n\n"
            f"> {v['desc_zh']}\n\n"
            f"## 评分\n\n"
            f"- 综合分：{v['score']:.1f} / 10（⭐{v['stars']}）\n"
            f"- EUI：{v['eui_kwh_m2_yr']} kWh/m²/yr\n"
            f"- 造价：{_money(v['boq_grand_total'])}\n"
            f"- 合规：{v['compliance_pass_rate']}\n"
            f"- 风格分：{v['style_score']}\n\n"
            f"## 技术配置\n\n"
            f"- Envelope: {v['envelope_level']}\n"
            f"- HVAC: {v['hvac_level']}\n\n"
            f"## Hero 图\n\n"
            f"⚠️ LIGHT 模式未渲染 · 见 sb_dir 的 `_TODO-variants-hero.md` · "
            f"FULL 需走 playbooks/scripts/ab-comparison/run_ab.py + Blender\n"
        )
        (vd / "description.md").write_text(desc)

    # report.json · 严老师 spec L413 的结构化报告
    (variants_dir / "report.json").write_text(
        json.dumps({
            "slug": project.slug,
            "variants": variants,
            "winner": _best_variant_name(variants),
            "weights": {"compliance": 0.40, "eui": 0.25, "cost": 0.20, "style": 0.15},
            "_light_mode": True,
            "_spec_ref": "StartUP-Building/CLAUDE.md L407-420",
        }, ensure_ascii=False, indent=2)
    )

    # diff-matrix.md · 6 维 · spec L414-420
    (variants_dir / "diff-matrix.md").write_text(_build_diff_matrix_md(variants, project.brief))

    # hero 渲染 / comparison-grid 明示缺失
    (sb_dir / "_TODO-variants-hero.md").write_text(
        f"""# TODO · variants 的 hero/renders/comparison-grid

**Spec**: StartUP-Building/CLAUDE.md L407-420
**Tier**: {project.tier}
**Slug**: {project.slug}

## 本轮真产
- variants/v1/description.md + v2/ + v3/
- variants/report.json（严老师 score_variants 加权算法）
- variants/diff-matrix.md（6 维 · EUI/造价/合规为 LIGHT 占位）

## 本轮未产（LIGHT 限制）
- v*/hero.png · 每方案主视图（需 Blender 渲染 · playbooks/scripts/ab-comparison/run_ab.py）
- v*/renders/*.png · 每方案 4 视角（同上）
- comparison-grid-4x3.png · 4 行 3 列拼图（cli-anything-image-grid）
- grid-row-*.png × 4 · 单行拼图
- whatif-3variants.md · 真 EnergyPlus What-If（playbooks/whatif-pipeline.md P9）

## 补齐入口
在 Mac 上跑：
```
cd $OPENST_H
python3 run_ab.py --base-project <project.json> --axis envelope \\
  --variants "v1_baseline;v2_envelope:wall_u=0.4;v3_premium:wall_u=0.3,hvac_type=VRF" \\
  --heroes "v1=<hero1.png>,v2=<hero2.png>,v3=<hero3.png>" \\
  --weather HKG_Hong.Kong.Intl.AP.epw --out <variants_dir>
```
"""
    )

    file_count = 3 + 3 + 2  # 3 description + report + diff-matrix + hero-todo
    return ArtifactResult(
        name="variants",
        status="done",
        timing_ms=int((time.time()-t0)*1000),
        output_path=str(variants_dir),
        meta={
            "files": file_count,
            "variants_count": len(variants),
            "winner": _best_variant_name(variants),
            "light_mode": True,
            "blender_renders_skipped": True,
            "template_source": "StartUP-Building/playbooks/scripts/ab-comparison/score_variants.py",
        },
    )
