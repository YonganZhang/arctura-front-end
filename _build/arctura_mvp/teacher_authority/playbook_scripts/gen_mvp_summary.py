"""Generate master summary Markdown from batch results."""

import json


with open("/Users/kaku/Desktop/Work/StartUP-Building/studio-demo/ALL-MVPS-ENERGY-BOQ.json") as f:
    data = json.load(f)

results = data["results"]

interior = [r for r in results if r["category"] == "interior"]
arch = [r for r in results if r["category"] == "arch"]


def fmt_row(r):
    slug = r["slug"]
    bt = r.get("building_type", "?")
    area = r.get("floor_area_m2") or r.get("boq_floor_area") or "?"
    zones = r.get("zones", "?")
    eui = r.get("eui_kwh_m2_yr")
    eui_s = f"{eui:.1f}" if eui else "—"
    verdict = r.get("compliance_verdict", "")
    passed = r.get("compliance_passed", 0)
    total = r.get("compliance_total", 0)
    emoji = "✅" if "COMPLIANT" in verdict and "NON-" not in verdict else "⚠️" if "CONDITIONAL" in verdict else "❌"
    comp_s = f"{emoji} {passed}/{total}" if total else "—"
    total_cost = r.get("boq_grand_total", 0)
    cost_per_m2 = r.get("boq_cost_per_m2", 0)
    return (f"| {slug} | {bt} | {area} | {zones} | "
            f"{eui_s} | {comp_s} | HK${total_cost:,.0f} | HK${cost_per_m2:,.0f} |")


lines = []
lines.append("# 23 MVP 全套能耗+合规+报价总览")
lines.append("")
lines.append(f"**运行时间**: {data['run_at']}")
lines.append(f"**气候**: {data['weather']} | **法规**: {data['code']} | **报价**: {data['region']} (HKD)")
lines.append("")
lines.append("## 成功率")
lines.append("")
success = sum(1 for r in results if r["status"] == "completed" and r.get("eui_kwh_m2_yr"))
with_eui = sum(1 for r in results if r.get("eui_kwh_m2_yr"))
with_boq = sum(1 for r in results if r.get("boq_grand_total"))
lines.append(f"- 全流程通过: **{success}/{len(results)}**")
lines.append(f"- EnergyPlus 成功: **{with_eui}/{len(results)}**")
lines.append(f"- BOQ 生成成功: **{with_boq}/{len(results)}**")
lines.append("")

# Interior MVPs
lines.append("## 室内 MVP (13 个)")
lines.append("")
lines.append("| 项目 | 类型 | 面积 m² | 热区 | EUI kWh/m²·yr | HK 合规 | 总价 (HKD) | 单价 (HKD/m²) |")
lines.append("|------|------|--------|------|--------------|---------|-----------|-------------|")
for r in interior:
    lines.append(fmt_row(r))
lines.append("")

# Arch MVPs
lines.append("## 建筑 MVP (10 个)")
lines.append("")
lines.append("| 项目 | 类型 | 面积 m² | 热区 | EUI kWh/m²·yr | HK 合规 | 总价 (HKD) | 单价 (HKD/m²) |")
lines.append("|------|------|--------|------|--------------|---------|-----------|-------------|")
for r in arch:
    lines.append(fmt_row(r))
lines.append("")

# Stats
euis = [r["eui_kwh_m2_yr"] for r in results if r.get("eui_kwh_m2_yr")]
costs_per_m2 = [r["boq_cost_per_m2"] for r in results if r.get("boq_cost_per_m2")]
total_costs = [r["boq_grand_total"] for r in results if r.get("boq_grand_total")]

lines.append("## 关键数据")
lines.append("")
lines.append("### EUI 范围（能耗强度）")
lines.append("")
if euis:
    lines.append(f"- 最低: **{min(euis):.1f}** kWh/m²·yr")
    lines.append(f"- 最高: **{max(euis):.1f}** kWh/m²·yr")
    lines.append(f"- 平均: **{sum(euis)/len(euis):.1f}** kWh/m²·yr")
    lines.append(f"- 中位数: **{sorted(euis)[len(euis)//2]:.1f}** kWh/m²·yr")
lines.append("")

lines.append("### 单价范围（HKD/m²）")
lines.append("")
if costs_per_m2:
    lines.append(f"- 最低: **HK${min(costs_per_m2):,.0f}/m²**")
    lines.append(f"- 最高: **HK${max(costs_per_m2):,.0f}/m²**")
    lines.append(f"- 平均: **HK${sum(costs_per_m2)/len(costs_per_m2):,.0f}/m²**")
lines.append("")

lines.append("### 合规分布")
lines.append("")
full_compliant = sum(1 for r in results if r.get("compliance_failed") == 0 and r.get("compliance_total", 0) > 0)
conditional = sum(1 for r in results if 0 < r.get("compliance_failed", 0) <= 2)
non_compliant = sum(1 for r in results if r.get("compliance_failed", 0) > 2)
lines.append(f"- ✅ 完全合规: **{full_compliant}/{len(results)}**")
lines.append(f"- ⚠️ 有条件合规: **{conditional}/{len(results)}**")
lines.append(f"- ❌ 不合规: **{non_compliant}/{len(results)}**")
lines.append("")

# Top 3 most / least efficient
lines.append("### 能效排行")
lines.append("")
sorted_by_eui = sorted([r for r in results if r.get("eui_kwh_m2_yr")], key=lambda x: x["eui_kwh_m2_yr"])
lines.append("**Top 3 最节能**:")
for r in sorted_by_eui[:3]:
    lines.append(f"- {r['slug']} — {r['eui_kwh_m2_yr']:.1f} kWh/m²·yr")
lines.append("")
lines.append("**Top 3 最费电**:")
for r in sorted_by_eui[-3:][::-1]:
    lines.append(f"- {r['slug']} — {r['eui_kwh_m2_yr']:.1f} kWh/m²·yr")
lines.append("")

# Cost rankings
lines.append("### 报价排行")
lines.append("")
sorted_by_cost = sorted([r for r in results if r.get("boq_grand_total")], key=lambda x: x["boq_grand_total"], reverse=True)
lines.append("**Top 3 总价最高**:")
for r in sorted_by_cost[:3]:
    lines.append(f"- {r['slug']} — HK${r['boq_grand_total']:,.0f}")
lines.append("")

lines.append("---")
lines.append("")
lines.append(f"*源数据: [ALL-MVPS-ENERGY-BOQ.json](ALL-MVPS-ENERGY-BOQ.json)*")
lines.append(f"*每个 MVP 的详细能耗+合规+报价: 见 `studio-demo/mvp/<NN>/energy/` 或 `studio-demo/arch-mvp/<slug>/energy/`*")

out_path = "/Users/kaku/Desktop/Work/StartUP-Building/studio-demo/ALL-MVPS-SUMMARY.md"
with open(out_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print(f"Summary saved: {out_path}")
