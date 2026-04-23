#!/usr/bin/env python3
"""Weighted scoring for A/B/C design variants (P10)."""
from __future__ import annotations


# Default weights — tweak per client if needed
WEIGHTS = {
    "compliance": 0.40,
    "eui": 0.25,
    "cost": 0.20,
    "style": 0.15,
}

# Compliance below this threshold => auto-reject
COMPLIANCE_REJECT_THRESHOLD = 0.70


def _normalize_lower_better(values: list[float]) -> list[float]:
    """Normalize so that the lowest value scores 1.0, highest scores 0.0."""
    lo, hi = min(values), max(values)
    if hi == lo:
        return [1.0] * len(values)
    return [(hi - v) / (hi - lo) for v in values]


def _normalize_higher_better(values: list[float]) -> list[float]:
    """Normalize so that the highest value scores 1.0, lowest scores 0.0."""
    lo, hi = min(values), max(values)
    if hi == lo:
        return [1.0] * len(values)
    return [(v - lo) / (hi - lo) for v in values]


def score_variants(variants: list[dict]) -> list[dict]:
    """Add 'score' (0-10) and 'stars' (1-5) to each variant dict.

    Expected keys per variant:
      - compliance_passed: int
      - compliance_total: int   (or compliance_pass_rate str like '7/8')
      - eui_kwh_m2_yr: float
      - boq_grand_total: float  (or boq_grand_total_hkd)
      - style_score: float      (optional, default 1.0)

    Returns the same list with 'score', 'stars', 'rejected' added in-place.
    """
    if not variants:
        return variants

    # --- extract raw values ---
    pass_rates: list[float] = []
    euis: list[float] = []
    costs: list[float] = []
    styles: list[float] = []

    for v in variants:
        # compliance pass rate
        if "compliance_pass_rate" in v and isinstance(v["compliance_pass_rate"], str):
            parts = v["compliance_pass_rate"].split("/")
            pr = int(parts[0]) / int(parts[1]) if len(parts) == 2 else 0.0
        else:
            passed = v.get("compliance_passed", 0)
            total = v.get("compliance_total", 1) or 1
            pr = passed / total
        pass_rates.append(pr)

        euis.append(float(v.get("eui_kwh_m2_yr", 0)))
        costs.append(float(v.get("boq_grand_total") or v.get("boq_grand_total_hkd", 0)))
        styles.append(float(v.get("style_score", 1.0)))

    # --- normalize ---
    n_compliance = _normalize_higher_better(pass_rates)
    n_eui = _normalize_lower_better(euis)
    n_cost = _normalize_lower_better(costs)
    n_style = _normalize_higher_better(styles)

    # --- weighted score (0-10 scale) ---
    for i, v in enumerate(variants):
        raw = (
            WEIGHTS["compliance"] * n_compliance[i]
            + WEIGHTS["eui"] * n_eui[i]
            + WEIGHTS["cost"] * n_cost[i]
            + WEIGHTS["style"] * n_style[i]
        )
        v["score"] = round(raw * 10, 1)
        v["stars"] = max(1, min(5, round(raw * 5)))
        v["rejected"] = pass_rates[i] < COMPLIANCE_REJECT_THRESHOLD
        v["_pass_rate"] = pass_rates[i]

    return variants
