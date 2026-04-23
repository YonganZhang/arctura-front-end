#!/usr/bin/env python3
"""render_templates.py — P11 Case Study step 3: metrics + narratives → 3 .md files.

Spec: playbooks/case-study-autogen-pipeline.md §4
Usage: python3 render_templates.py <MVP-folder> [--template portfolio|impact|sales|all]
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path


def _fmt_money_hkd(v: float | None) -> str:
    return f"HK$ {int(round(v)):,}" if isinstance(v, (int, float)) else "—"


def _fmt_area(v: float | int | None) -> str:
    return f"{v:g} m²" if isinstance(v, (int, float)) else "—"


def _fmt_eui(v: float | None) -> str:
    return f"{v:.1f} kWh/m²·yr" if isinstance(v, (int, float)) else "未模拟"


def _fmt_compliance(code: str | None, rate: str | None) -> str:
    if code and rate:
        return f"{rate} ({code})"
    return "—"


def _read_narrative(cs_dir: Path, template: str) -> str:
    p = cs_dir / f"narrative-{template}.txt"
    if p.exists():
        return p.read_text().strip()
    return f"_[narrative-{template}.txt 未生成 — 跑 narrate.py 填充]_"


def _thumbs_exist(cs_dir: Path, name: str) -> bool:
    return (cs_dir / "thumbs" / name).exists()


def render_portfolio(metrics: dict, cs_dir: Path, mvp_name: str) -> str:
    narrative = _read_narrative(cs_dir, "portfolio")
    m = metrics
    area = m["space"].get("area_sqm")
    boq = m["metrics"].get("boq_total_hkd")
    eui = m["metrics"].get("eui_kwh_m2_yr")
    code = m["metrics"].get("compliance_code")
    rate = m["metrics"].get("compliance_pass_rate")
    keywords = ", ".join(m["style"].get("keywords", [])[:4])

    n_plans = len(m["deliverables"].get("plans_svg", []))
    n_elev = len(m["deliverables"].get("elevations", []))
    n_section = len(m["deliverables"].get("sections", []))
    n_decks = m["deliverables"].get("n_stakeholder_decks", 0)

    card_sources = m["deliverables"].get("card_sources", [])
    card_imgs = []
    for cs_entry in card_sources:
        card_name = cs_entry["card"]  # "card-1"
        label = cs_entry.get("label", card_name)
        if _thumbs_exist(cs_dir, f"{card_name}.jpg"):
            card_imgs.append(f"![{label}](thumbs/{card_name}.jpg)")
    if not card_imgs:
        for i in range(1, 5):
            if _thumbs_exist(cs_dir, f"card-{i}.jpg"):
                card_imgs.append(f"![card-{i}](thumbs/card-{i}.jpg)")
    cards_line = "\n\n".join(f"**{ci+1}.** {img}" for ci, img in enumerate(card_imgs)) if card_imgs else "_[缩略图未生成]_"

    return f"""---
layout: portfolio
id: {m["id"]}
tier: {m["tier"]}
tags: [{keywords}]
cover: thumbs/hero.jpg
---

# {m["scenario_cn"]}

![hero](thumbs/hero.jpg)

## 核心指标

| 面积 | 造价 | EUI | 合规 |
|:-:|:-:|:-:|:-:|
| {_fmt_area(area)} | {_fmt_money_hkd(boq)} | {_fmt_eui(eui)} | {_fmt_compliance(code, rate)} |

## 方案亮点

{narrative}

## 作品展示

{cards_line}

## 交付清单

- 3D 模型 · {len(m["deliverables"].get("exports", []))} 件套（{" / ".join(e.upper() for e in m["deliverables"].get("exports", []))}）
- 图纸 · {n_plans} 张平面 · {n_elev} 立面 · {n_section} 剖面
- {n_decks} 份角色定制方案书
- Blender scene: {m["deliverables"].get("blender_objects", 0)} objects · IFC4 products: {m["deliverables"].get("ifc_products", 0)}

[联系我们 · 要类似方案 →](mailto:studio@example.com?subject={m["id"]})
"""


def render_impact(metrics: dict, cs_dir: Path, mvp_name: str) -> str:
    narrative = _read_narrative(cs_dir, "impact")
    m = metrics
    area = m["space"].get("area_sqm")
    design_min = m["metrics"].get("design_duration_min")
    rate = m["metrics"].get("compliance_pass_rate") or "—"
    code = m["metrics"].get("compliance_code") or "—"
    eui = m["metrics"].get("eui_kwh_m2_yr")
    co2 = m["metrics"].get("co2_saved_t_yr")
    n_plans = len(m["deliverables"].get("plans_svg", []))
    n_elev = len(m["deliverables"].get("elevations", []))
    n_section = len(m["deliverables"].get("sections", []))
    n_draw = n_plans + n_elev + n_section
    n_decks = m["deliverables"].get("n_stakeholder_decks", 0)
    blender_objs = m["deliverables"].get("blender_objects", 0)
    ifc_products = m["deliverables"].get("ifc_products", 0)

    if design_min:
        ratio = f"{(3 * 5 * 8 * 60) // design_min}×" if design_min else "—"
    else:
        ratio = "—"

    return f"""---
framework: RAE-Impact-Case-Study
id: {m["id"]}
scenario: {m["scenario_cn"]}
date: {date.today().isoformat()}
linked_playbooks: [studio-copilot-pipeline, architecture-pipeline, energy-simulation-pipeline, compliance-pipeline]
---

# Impact Case Study — {m["scenario_cn"]}

## 1. Problem Statement

{narrative}

## 2. Approach

An end-to-end AI pipeline (see linked playbooks) chains: design intent → 3D model
({blender_objs} objects) → construction drawings → BIM (IFC4, {ifc_products} products)
→ energy simulation (EnergyPlus) → compliance ({code}) → BoQ.

Key technical contributions:
- Parametric Blender scene generation with {ifc_products} IFC-classified elements
- Automated {code} compliance verification
- Multi-region BoQ (HK / CN / INTL)

## 3. Deliverables

| Artefact | Count | Format |
|---|:-:|---|
| 3D scene objects | {blender_objs} | .blend / .json |
| IFC products | {ifc_products} | IFC4 |
| Drawings | {n_draw} | SVG / DXF |
| Stakeholder decks | {n_decks} | PPTX / ODP |
| Exports | {len(m["deliverables"].get("exports", []))} | {" · ".join(e.upper() for e in m["deliverables"].get("exports", []))} |

## 4. Impact Metrics

- **Time compression**: 2–4 weeks → {design_min if design_min else "—"} minutes ({ratio} speedup)
- **Cost compression**: HK$ 40k–120k → ~HK$ 2k (marginal compute + review)
- **Coverage**: {rate} pass rate against {code}
- **Energy signal**: EUI = {_fmt_eui(eui)}; CO₂ offset vs baseline = {co2 if co2 is not None else "pending"} tCO₂/yr
- **Scope**: {_fmt_area(area)} · client type: {m["client_type"]}

## 5. Evidence

- Client testimonial: _[placeholder — pending client interview, see playbooks/CLIENT-INTERVIEW-TEMPLATE.md]_
- Third-party citation: _[placeholder — pending publication / conference]_
- Public artefacts: [portfolio page](../portfolio/{m["id"]}.md) · [repo link placeholder]
"""


def render_sales(metrics: dict, cs_dir: Path, mvp_name: str) -> str:
    narrative = _read_narrative(cs_dir, "sales")
    m = metrics
    area = m["space"].get("area_sqm")
    design_min = m["metrics"].get("design_duration_min")
    rate = m["metrics"].get("compliance_pass_rate") or "—"
    code = m["metrics"].get("compliance_code") or "—"
    n_decks = m["deliverables"].get("n_stakeholder_decks", 0)
    n_plans = len(m["deliverables"].get("plans_svg", []))
    n_elev = len(m["deliverables"].get("elevations", []))
    n_section = len(m["deliverables"].get("sections", []))
    n_deliverables = 5 + n_plans + n_elev + n_section + n_decks

    similar_imgs = []
    for i in range(1, 4):
        if _thumbs_exist(cs_dir, f"card-{i}.jpg"):
            similar_imgs.append(f"![similar{i}](thumbs/card-{i}.jpg)")
    similar_line = " ".join(similar_imgs) if similar_imgs else ""

    return f"""---
layout: sales-one-pager
id: {m["id"]}
audience: {m["client_type"]}-prospects
---

# {m["client_type"]} · 从"需求 → 可施工方案" 10 分钟内

![hero](thumbs/hero.jpg)

{narrative}

## 实测结果（本案例）

| 设计耗时 | 交付文件 | 合规通过 |
|:-:|:-:|:-:|
| {design_min if design_min else "—"} 分钟 | {n_deliverables} 份 | {rate} ({code}) |

## 类似方案

{similar_line}

**→ 回复本邮件或扫码 contact us · 48 小时内给你的 {m["client_type"]} 出第一版。**
"""


RENDERERS = {
    "portfolio": render_portfolio,
    "impact": render_impact,
    "sales": render_sales,
}


def render_one(folder: Path, template: str) -> Path:
    cs_dir = folder / "case-study"
    metrics_path = cs_dir / "metrics.json"
    if not metrics_path.exists():
        raise FileNotFoundError(f"metrics.json not found: {metrics_path}. Run extract_metrics.py first.")
    metrics = json.loads(metrics_path.read_text())
    md = RENDERERS[template](metrics, cs_dir, folder.name)
    out = cs_dir / f"{template}.md"
    out.write_text(md)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Render 3 case-study markdown files")
    ap.add_argument("mvp_folder", type=Path)
    ap.add_argument("--template", choices=["portfolio", "impact", "sales", "all"], default="all")
    args = ap.parse_args()
    folder = args.mvp_folder.resolve()
    targets = ["portfolio", "impact", "sales"] if args.template == "all" else [args.template]
    try:
        for t in targets:
            out = render_one(folder, t)
            print(f"OK: {t} → {out.relative_to(folder)}")
    except (FileNotFoundError, ValueError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
