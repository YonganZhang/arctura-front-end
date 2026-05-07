---
framework: RAE-Impact-Case-Study
id: 03-coffee-shop
scenario: 独立精品咖啡店 Coffee Lab · v1
date: 2026-04-17
linked_playbooks: [studio-copilot-pipeline, architecture-pipeline, energy-simulation-pipeline, compliance-pipeline]
---

# Impact Case Study — 独立精品咖啡店 Coffee Lab · v1

## 1. Problem Statement

An 80 m² independent café conversion in Hong Kong typically runs 2–4 weeks and HK$ 40k–120k, split across interior design, kitchen MEP, and BIM handoff, with energy and licensing checks happening after drawings are frozen. For this industrial-wood café, the pipeline produced 78 scene objects, 82 IFC products, 8 stakeholder decks across roles from barista to landlord, an HK$ 894k BoQ, 130.5 kWh/m²·yr EUI and 7/9 HK BEC 2021 pass — all in a single marginal-cost run. The Approach section walks through how this was chained end-to-end.

## 2. Approach

An end-to-end AI pipeline (see linked playbooks) chains: design intent → 3D model
(78 objects) → construction drawings → BIM (IFC4, 82 products)
→ energy simulation (EnergyPlus) → compliance (HK) → BoQ.

Key technical contributions:
- Parametric Blender scene generation with 82 IFC-classified elements
- Automated HK compliance verification
- Multi-region BoQ (HK / CN / INTL)

## 3. Deliverables

| Artefact | Count | Format |
|---|:-:|---|
| 3D scene objects | 78 | .blend / .json |
| IFC products | 82 | IFC4 |
| Drawings | 1 | SVG / DXF |
| Stakeholder decks | 8 | PPTX / ODP |
| Exports | 5 | DXF · FBX · GLB · IFC · OBJ |

## 4. Impact Metrics

- **Time compression**: 2–4 weeks → — minutes (— speedup)
- **Cost compression**: HK$ 40k–120k → ~HK$ 2k (marginal compute + review)
- **Coverage**: 7/8 pass rate against HK
- **Energy signal**: EUI = 130.5 kWh/m²·yr; CO₂ offset vs baseline = pending tCO₂/yr
- **Scope**: 80 m² · client type: 某独立咖啡品牌主理人

## 5. Evidence

- Client testimonial: _[placeholder — pending client interview, see playbooks/CLIENT-INTERVIEW-TEMPLATE.md]_
- Third-party citation: _[placeholder — pending publication / conference]_
- Public artefacts: [portfolio page](../portfolio/03-coffee-shop.md) · [repo link placeholder]
