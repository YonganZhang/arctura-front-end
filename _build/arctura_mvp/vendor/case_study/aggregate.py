#!/usr/bin/env python3
"""aggregate.py — P11 Case Study step 4: cross-MVP rollup + 2 dashboards.

Spec: playbooks/case-study-autogen-pipeline.md §5 (rollup schema) · §6.3 (dashboard MDs)
Usage: python3 aggregate.py [--root <StartUP-Building>]
"""
from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path


HKT = timezone(timedelta(hours=8))
TRADITIONAL_WEEKS_DEFAULT = 3
TRADITIONAL_HOURS = TRADITIONAL_WEEKS_DEFAULT * 5 * 8  # weekdays × 8h


def _load_all_metrics(root: Path) -> list[dict]:
    paths = sorted(
        glob.glob(str(root / "studio-demo" / "mvp" / "*" / "case-study" / "metrics.json"))
        + glob.glob(str(root / "studio-demo" / "arch-mvp" / "*" / "case-study" / "metrics.json"))
    )
    out: list[dict] = []
    for p in paths:
        try:
            out.append(json.loads(Path(p).read_text()))
        except (json.JSONDecodeError, OSError):
            continue
    return out


def _sum_nonnull(items: list, key_path: list[str]) -> float:
    total = 0.0
    for it in items:
        v = it
        for k in key_path:
            if not isinstance(v, dict):
                v = None
                break
            v = v.get(k)
        if isinstance(v, (int, float)):
            total += v
    return total


def _count_nonnull(items: list, key_path: list[str]) -> int:
    n = 0
    for it in items:
        v = it
        for k in key_path:
            if not isinstance(v, dict):
                v = None
                break
            v = v.get(k)
        if isinstance(v, (int, float)):
            n += 1
    return n


def _avg(items: list, key_path: list[str]) -> float | None:
    total = _sum_nonnull(items, key_path)
    n = _count_nonnull(items, key_path)
    return total / n if n else None


def _parse_pass_rate(s: str | None) -> float | None:
    if not isinstance(s, str):
        return None
    m = re.match(r"\s*(\d+)\s*/\s*(\d+)\s*", s)
    if not m:
        return None
    num, denom = int(m.group(1)), int(m.group(2))
    return num / denom if denom else None


def compute_rollup(metrics_list: list[dict]) -> dict:
    n_total = len(metrics_list)
    tier_counts = Counter(m.get("tier") for m in metrics_list)
    code_counts = Counter(
        m["metrics"].get("compliance_code") for m in metrics_list
        if m["metrics"].get("compliance_code")
    )
    pass_rates = [_parse_pass_rate(m["metrics"].get("compliance_pass_rate")) for m in metrics_list]
    pass_rates = [r for r in pass_rates if r is not None]

    hours_saved = 0.0
    for m in metrics_list:
        dmin = m["metrics"].get("design_duration_min")
        if isinstance(dmin, (int, float)):
            hours_saved += TRADITIONAL_HOURS - dmin / 60.0

    return {
        "n_mvps_total": n_total,
        "n_mvps_with_metrics": n_total,
        "n_mvps_with_energy": _count_nonnull(metrics_list, ["metrics", "eui_kwh_m2_yr"]),
        "n_mvps_with_boq": _count_nonnull(metrics_list, ["metrics", "boq_total_hkd"]),
        "n_mvps_with_compliance": sum(1 for m in metrics_list if m["metrics"].get("compliance_code")),
        "sum_area_sqm": _sum_nonnull(metrics_list, ["space", "area_sqm"]),
        "sum_blender_objects": int(_sum_nonnull(metrics_list, ["deliverables", "blender_objects"])),
        "sum_ifc_products": int(_sum_nonnull(metrics_list, ["deliverables", "ifc_products"])),
        "sum_stakeholder_decks": int(_sum_nonnull(metrics_list, ["deliverables", "n_stakeholder_decks"])),
        "avg_design_duration_min": _avg(metrics_list, ["metrics", "design_duration_min"]),
        "sum_boq_total_hkd": _sum_nonnull(metrics_list, ["metrics", "boq_total_hkd"]),
        "avg_eui_kwh_m2_yr": _avg(metrics_list, ["metrics", "eui_kwh_m2_yr"]),
        "sum_co2_saved_t_yr": _sum_nonnull(metrics_list, ["metrics", "co2_saved_t_yr"]),
        "compliance_pass_rate_avg": sum(pass_rates) / len(pass_rates) if pass_rates else None,
        "tier_breakdown": dict(tier_counts),
        "compliance_code_breakdown": dict(code_counts),
        "hours_saved_vs_traditional": round(hours_saved, 1),
        "generated_at": datetime.now(HKT).isoformat(timespec="seconds"),
    }


def _rel_to_cs_dir(root: Path, mvp_folder: Path) -> str:
    return str(mvp_folder.relative_to(root))


def render_portfolio_index(rollup: dict, metrics_list: list[dict], root: Path) -> str:
    n_interior = rollup["tier_breakdown"].get("interior", 0)
    n_arch = rollup["tier_breakdown"].get("architecture", 0)
    lines = [
        "# Studio Copilot · Portfolio",
        "",
        f"{rollup['n_mvps_total']} 个已交付项目 · 覆盖 {len(rollup['tier_breakdown'])} 类业态 · "
        f"累计 {rollup['sum_area_sqm']:.0f} m²",
        "",
    ]
    for tier, label, count in (("interior", "Interior", n_interior),
                                ("architecture", "Architecture", n_arch)):
        lines.append(f"## {label} ({count})")
        lines.append("")
        for m in metrics_list:
            if m.get("tier") != tier:
                continue
            mvp_path = (root / "studio-demo" /
                        ("mvp" if tier == "interior" else "arch-mvp") / m["id"])
            area = m["space"].get("area_sqm")
            area_str = f"{area:g}m²" if area else "—"
            rel = _rel_to_cs_dir(root, mvp_path)
            lines.append(
                f"- ![{m['id']}]({rel}/case-study/thumbs/index.jpg) "
                f"[{m['scenario_cn']} · {area_str}](portfolio/{m['id']}.md)"
            )
        lines.append("")
    return "\n".join(lines)


def render_impact_dashboard(rollup: dict) -> str:
    pct = rollup.get("compliance_pass_rate_avg")
    pct_str = f"{pct:.0%}" if pct is not None else "—"
    avg_dur = rollup.get("avg_design_duration_min")
    avg_dur_str = f"{avg_dur:.1f}" if avg_dur is not None else "—"
    avg_eui = rollup.get("avg_eui_kwh_m2_yr")
    avg_eui_str = f"{avg_eui:.1f}" if avg_eui is not None else "—"

    return f"""# Impact Dashboard · Studio Copilot

> Snapshot {datetime.now(HKT).date().isoformat()} · {rollup['n_mvps_total']} projects · {rollup['sum_area_sqm']:.0f} m² served

## Scale

- {rollup['n_mvps_total']} projects delivered (interior {rollup['tier_breakdown'].get("interior", 0)} · architecture {rollup['tier_breakdown'].get("architecture", 0)})
- {rollup['sum_stakeholder_decks']} stakeholder materials · {rollup['sum_ifc_products']} IFC products

## Speed

- Avg design duration: {avg_dur_str} min (vs 2–4 weeks traditional)
- Hours saved (cumulative): {rollup['hours_saved_vs_traditional']} h

## Sustainability signal

- Avg EUI: {avg_eui_str} kWh/m²·yr across {rollup['n_mvps_with_energy']} projects
- CO₂ offset vs baseline: {rollup['sum_co2_saved_t_yr']} tCO₂/yr

## Regulatory coverage

- Compliance codes tested: {rollup['compliance_code_breakdown']}
- Avg pass rate: {pct_str}

[Full impact case studies → impact/](./impact/)
"""


def _symlink_force(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.is_symlink() or dst.exists():
        dst.unlink()
    try:
        rel = Path(*[".." for _ in dst.parent.relative_to(src.anchor).parts]) / src.relative_to(src.anchor)
        dst.symlink_to(rel)
    except ValueError:
        dst.symlink_to(src)


def _link_single_pages(root: Path, metrics_list: list[dict]) -> None:
    cs_root = root / "case-studies"
    for m in metrics_list:
        tier_dir = "mvp" if m["tier"] == "interior" else "arch-mvp"
        mvp_cs = root / "studio-demo" / tier_dir / m["id"] / "case-study"
        for template in ("portfolio", "impact", "sales"):
            src = mvp_cs / f"{template}.md"
            if src.exists():
                _symlink_force(src, cs_root / template / f"{m['id']}.md")


def aggregate(root: Path) -> dict:
    cs_root = root / "case-studies"
    cs_root.mkdir(parents=True, exist_ok=True)

    metrics_list = _load_all_metrics(root)
    if not metrics_list:
        raise RuntimeError(f"No metrics.json found under {root}/studio-demo/*. Run extract_metrics first.")

    rollup = compute_rollup(metrics_list)
    (cs_root / "metrics.json").write_text(json.dumps(rollup, indent=2, ensure_ascii=False))
    (cs_root / "portfolio-index.md").write_text(render_portfolio_index(rollup, metrics_list, root))
    (cs_root / "impact-dashboard.md").write_text(render_impact_dashboard(rollup))
    _link_single_pages(root, metrics_list)

    return rollup


def main() -> int:
    ap = argparse.ArgumentParser(description="Aggregate MVP metrics into cross-library rollup + dashboards")
    ap.add_argument("--root", type=Path,
                    default=Path("/Users/kaku/Desktop/Work/StartUP-Building"))
    args = ap.parse_args()
    try:
        rollup = aggregate(args.root.resolve())
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    print(f"OK: rollup over {rollup['n_mvps_total']} MVPs → case-studies/metrics.json + "
          "portfolio-index.md + impact-dashboard.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
