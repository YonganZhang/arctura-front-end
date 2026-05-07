---
framework: RAE-Impact-Case-Study
id: 13-ai-startup-office
scenario: Stack Lab · AI Startup 办公室 · v1
date: 2026-04-17
linked_playbooks: [studio-copilot-pipeline, architecture-pipeline, energy-simulation-pipeline, compliance-pipeline]
---

# Impact Case Study — Stack Lab · AI Startup 办公室 · v1

## 1. Problem Statement

A 130 m² AI startup office fit-out in Hong Kong runs 2–4 weeks and HK$ 40k–120k, with 10 dual-monitor workstations, a GPU server room needing 5 kW dedicated power and independent cooling, and isolated phone booths typically requiring separate electrical, mechanical, and acoustic coordination. For this tech-loft office, the pipeline produced 118 scene objects, 122 IFC products, 8 role-tailored decks, HK$ 1.14M BoQ, 88.1 kWh/m²·yr EUI, and a 7/9 HK BEC 2021 pass in 23 minutes. The Approach details the unified chain.

## 2. Approach

An end-to-end AI pipeline (see linked playbooks) chains: design intent → 3D model
(118 objects) → construction drawings → BIM (IFC4, 122 products)
→ energy simulation (EnergyPlus) → compliance (HK) → BoQ.

Key technical contributions:
- Parametric Blender scene generation with 122 IFC-classified elements
- Automated HK compliance verification
- Multi-region BoQ (HK / CN / INTL)

## 3. Deliverables

| Artefact | Count | Format |
|---|:-:|---|
| 3D scene objects | 118 | .blend / .json |
| IFC products | 122 | IFC4 |
| Drawings | 1 | SVG / DXF |
| Stakeholder decks | 8 | PPTX / ODP |
| Exports | 5 | DXF · FBX · GLB · IFC · OBJ |

## 4. Impact Metrics

- **Time compression**: 2–4 weeks → 23 minutes (313× speedup)
- **Cost compression**: HK$ 40k–120k → ~HK$ 2k (marginal compute + review)
- **Coverage**: 7/8 pass rate against HK
- **Energy signal**: EUI = 88.1 kWh/m²·yr; CO₂ offset vs baseline = pending tCO₂/yr
- **Scope**: 130 m² · client type: AI 创业团队 (致敬业主)

## 5. Evidence

- Client testimonial: _[placeholder — pending client interview, see playbooks/CLIENT-INTERVIEW-TEMPLATE.md]_
- Third-party citation: _[placeholder — pending publication / conference]_
- Public artefacts: [portfolio page](../portfolio/13-ai-startup-office.md) · [repo link placeholder]
