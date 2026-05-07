---
framework: RAE-Impact-Case-Study
id: 05-fitness-studio
scenario: 精品健身工作室 Lift Studio · v1
date: 2026-04-17
linked_playbooks: [studio-copilot-pipeline, architecture-pipeline, energy-simulation-pipeline, compliance-pipeline]
---

# Impact Case Study — 精品健身工作室 Lift Studio · v1

## 1. Problem Statement

A 100 m² boutique fitness studio fit-out in Hong Kong runs 2–4 weeks and HK$ 40k–120k under the traditional multi-vendor path, with acoustics often surfacing only after testing. For this industrial-matte-black studio, the pipeline produced 90 scene objects, 94 IFC products, 8 role-specific decks, HK$ 1.03M BoQ, 119.6 kWh/m²·yr EUI, and a 7/9 HK BEC 2021 pass in 15 minutes of compute. Mirror-wall geometry, acoustic zoning for yoga vs strength areas, and 10 locker slots were all resolved upstream. The following sections detail the chain.

## 2. Approach

An end-to-end AI pipeline (see linked playbooks) chains: design intent → 3D model
(90 objects) → construction drawings → BIM (IFC4, 94 products)
→ energy simulation (EnergyPlus) → compliance (HK) → BoQ.

Key technical contributions:
- Parametric Blender scene generation with 94 IFC-classified elements
- Automated HK compliance verification
- Multi-region BoQ (HK / CN / INTL)

## 3. Deliverables

| Artefact | Count | Format |
|---|:-:|---|
| 3D scene objects | 90 | .blend / .json |
| IFC products | 94 | IFC4 |
| Drawings | 1 | SVG / DXF |
| Stakeholder decks | 8 | PPTX / ODP |
| Exports | 5 | DXF · FBX · GLB · IFC · OBJ |

## 4. Impact Metrics

- **Time compression**: 2–4 weeks → 15 minutes (480× speedup)
- **Cost compression**: HK$ 40k–120k → ~HK$ 2k (marginal compute + review)
- **Coverage**: 7/8 pass rate against HK
- **Energy signal**: EUI = 119.6 kWh/m²·yr; CO₂ offset vs baseline = pending tCO₂/yr
- **Scope**: 100 m² · client type: 小型精品健身品牌主理人

## 5. Evidence

- Client testimonial: _[placeholder — pending client interview, see playbooks/CLIENT-INTERVIEW-TEMPLATE.md]_
- Third-party citation: _[placeholder — pending publication / conference]_
- Public artefacts: [portfolio page](../portfolio/05-fitness-studio.md) · [repo link placeholder]
