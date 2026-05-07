---
framework: RAE-Impact-Case-Study
id: 01-study-room
scenario: 极简书房改造 v1
date: 2026-04-17
linked_playbooks: [studio-copilot-pipeline, architecture-pipeline, energy-simulation-pipeline, compliance-pipeline]
---

# Impact Case Study — 极简书房改造 v1

## 1. Problem Statement

A 15 m² residential study conversion in Hong Kong traditionally spans 2–4 weeks and HK$ 40k–120k across three vendors — designer, drafter, and BIM handoff — with energy and compliance concerns typically surfacing mid-construction. For this Japandi-referenced study, the end-to-end pipeline produced 21 scene objects, 8 stakeholder-role decks, HK$ 254k BoQ, and a 7/9 pass against HK BEC 2021 in a single marginal-cost run. The remainder of this case traces how brief intake, parametric BIM generation, simulation, and code verification were chained into one workflow.

## 2. Approach

An end-to-end AI pipeline (see linked playbooks) chains: design intent → 3D model
(21 objects) → construction drawings → BIM (IFC4, 0 products)
→ energy simulation (EnergyPlus) → compliance (HK) → BoQ.

Key technical contributions:
- Parametric Blender scene generation with 0 IFC-classified elements
- Automated HK compliance verification
- Multi-region BoQ (HK / CN / INTL)

## 3. Deliverables

| Artefact | Count | Format |
|---|:-:|---|
| 3D scene objects | 21 | .blend / .json |
| IFC products | 0 | IFC4 |
| Drawings | 1 | SVG / DXF |
| Stakeholder decks | 8 | PPTX / ODP |
| Exports | 0 |  |

## 4. Impact Metrics

- **Time compression**: 2–4 weeks → — minutes (— speedup)
- **Cost compression**: HK$ 40k–120k → ~HK$ 2k (marginal compute + review)
- **Coverage**: 7/8 pass rate against HK
- **Energy signal**: EUI = 41.2 kWh/m²·yr; CO₂ offset vs baseline = pending tCO₂/yr
- **Scope**: — · client type: 张先生

## 5. Evidence

- Client testimonial: _[placeholder — pending client interview, see playbooks/CLIENT-INTERVIEW-TEMPLATE.md]_
- Third-party citation: _[placeholder — pending publication / conference]_
- Public artefacts: [portfolio page](../portfolio/01-study-room.md) · [repo link placeholder]
