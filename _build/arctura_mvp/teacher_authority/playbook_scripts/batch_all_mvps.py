"""Batch-run energy + compliance + BOQ on all 23 MVPs.

Collects results into a master JSON and Markdown summary.

Pipeline flow (per MVP):
  1. Find IFC in exports/ → auto enrich-ifc (add properties/materials)
  2. Create project from enriched IFC + brief.json (merged thermal model)
  3. Run EnergyPlus simulation
  4. Compliance check + BOQ report
"""

import json
import os
import sys
import time
import traceback
from glob import glob
from pathlib import Path

sys.path.insert(0, "/Users/kaku/Desktop/Work/CLI-Anything/openstudio/agent-harness")
sys.path.insert(0, "/Users/kaku/Desktop/Work/CLI-Anything/blender/agent-harness")

from cli_anything.openstudio.core.project import create_project, save_project
from cli_anything.openstudio.core.simulation import run_simulation
from cli_anything.openstudio.core.results import parse_results
from cli_anything.openstudio.core.compliance import check_compliance
from cli_anything.openstudio.core.boq import boq_from_model


WEATHER_HK = "/Users/kaku/Desktop/Work/CLI-Anything/openstudio/agent-harness/cli_anything/openstudio/data/weather/HKG_Hong.Kong.Intl.AP.epw"

MVPS = [
    # Interior
    ("01-study-room", "interior", "/Users/kaku/Desktop/Work/StartUP-Building/studio-demo/mvp/01-study-room"),
    ("02-conference-room", "interior", "/Users/kaku/Desktop/Work/StartUP-Building/studio-demo/mvp/02-conference-room"),
    ("03-coffee-shop", "interior", "/Users/kaku/Desktop/Work/StartUP-Building/studio-demo/mvp/03-coffee-shop"),
    ("04-coworking", "interior", "/Users/kaku/Desktop/Work/StartUP-Building/studio-demo/mvp/04-coworking"),
    ("05-fitness-studio", "interior", "/Users/kaku/Desktop/Work/StartUP-Building/studio-demo/mvp/05-fitness-studio"),
    ("06-kids-daycare", "interior", "/Users/kaku/Desktop/Work/StartUP-Building/studio-demo/mvp/06-kids-daycare"),
    ("07-bookstore", "interior", "/Users/kaku/Desktop/Work/StartUP-Building/studio-demo/mvp/07-bookstore"),
    ("08-hair-salon", "interior", "/Users/kaku/Desktop/Work/StartUP-Building/studio-demo/mvp/08-hair-salon"),
    ("09-art-gallery", "interior", "/Users/kaku/Desktop/Work/StartUP-Building/studio-demo/mvp/09-art-gallery"),
    ("10-dental-clinic", "interior", "/Users/kaku/Desktop/Work/StartUP-Building/studio-demo/mvp/10-dental-clinic"),
    ("11-bistro-restaurant", "interior", "/Users/kaku/Desktop/Work/StartUP-Building/studio-demo/mvp/11-bistro-restaurant"),
    ("12-recording-studio", "interior", "/Users/kaku/Desktop/Work/StartUP-Building/studio-demo/mvp/12-recording-studio"),
    ("13-ai-startup-office", "interior", "/Users/kaku/Desktop/Work/StartUP-Building/studio-demo/mvp/13-ai-startup-office"),
    # Architecture
    ("arch-01-house", "arch", "/Users/kaku/Desktop/Work/StartUP-Building/studio-demo/arch-mvp/arch-01-house"),
    ("arch-02-office-building", "arch", "/Users/kaku/Desktop/Work/StartUP-Building/studio-demo/arch-mvp/arch-02-office-building"),
    ("arch-03-boutique-hotel", "arch", "/Users/kaku/Desktop/Work/StartUP-Building/studio-demo/arch-mvp/arch-03-boutique-hotel"),
    ("arch-04-community-center", "arch", "/Users/kaku/Desktop/Work/StartUP-Building/studio-demo/arch-mvp/arch-04-community-center"),
    ("arch-05-modern-chinese-house", "arch", "/Users/kaku/Desktop/Work/StartUP-Building/studio-demo/arch-mvp/arch-05-modern-chinese-house"),
    ("arch-06-small-library", "arch", "/Users/kaku/Desktop/Work/StartUP-Building/studio-demo/arch-mvp/arch-06-small-library"),
    ("arch-07-loft-coworking", "arch", "/Users/kaku/Desktop/Work/StartUP-Building/studio-demo/arch-mvp/arch-07-loft-coworking"),
    ("arch-08-small-clinic", "arch", "/Users/kaku/Desktop/Work/StartUP-Building/studio-demo/arch-mvp/arch-08-small-clinic"),
    ("arch-09-mixed-use", "arch", "/Users/kaku/Desktop/Work/StartUP-Building/studio-demo/arch-mvp/arch-09-mixed-use"),
    ("arch-10-sports-complex", "arch", "/Users/kaku/Desktop/Work/StartUP-Building/studio-demo/arch-mvp/arch-10-sports-complex"),
]


def _find_ifc(mvp_folder: str) -> str | None:
    """Find the first .ifc file in the exports/ subdirectory."""
    exports_dir = os.path.join(mvp_folder, "exports")
    if not os.path.isdir(exports_dir):
        return None
    ifc_files = glob(os.path.join(exports_dir, "*.ifc"))
    return ifc_files[0] if ifc_files else None


def _auto_enrich(ifc_path: str, code: str = "HK",
                 profile: str = "residential") -> dict | None:
    """Auto-enrich an IFC file if it lacks PropertySets.

    Returns enrich stats dict, or None if already enriched / on error.
    """
    try:
        import ifcopenshell
        m = ifcopenshell.open(ifc_path)
        # Quick check: if any Pset_WallCommon exists, already enriched
        has_psets = any(
            "Pset_WallCommon" in (ifc_elem_psets or {})
            for w in m.by_type("IfcWall")
            for ifc_elem_psets in [_get_psets_safe(w)]
        )
        if has_psets:
            return None  # already enriched
    except Exception:
        pass

    try:
        from cli_anything.blender.core.ifc_enrich import enrich
        stats = enrich(ifc_path, code=code, profile=profile, overwrite=True)
        return stats
    except Exception as e:
        print(f"    WARN: enrich failed: {e}")
        return None


def _get_psets_safe(elem) -> dict:
    try:
        import ifcopenshell.util.element as ifc_elem
        return ifc_elem.get_psets(elem) or {}
    except Exception:
        return {}


def _guess_profile(slug: str, category: str) -> str:
    """Guess enrich profile from MVP slug."""
    slug_lower = slug.lower()
    if "office" in slug_lower or "coworking" in slug_lower:
        return "office"
    if "clinic" in slug_lower or "dental" in slug_lower:
        return "clinic"
    if "restaurant" in slug_lower or "bistro" in slug_lower or "coffee" in slug_lower:
        return "restaurant"
    if "shop" in slug_lower or "bookstore" in slug_lower or "salon" in slug_lower:
        return "retail"
    if "house" in slug_lower or "residential" in slug_lower:
        return "residential"
    if category == "interior":
        return "office"
    return "residential"


def run_one(slug, category, mvp_folder):
    t0 = time.time()
    result = {
        "slug": slug,
        "category": category,
        "status": "pending",
        "error": "",
        "ifc_enriched": False,
        "data_source": "brief",
    }

    try:
        brief_path = f"{mvp_folder}/brief.json"
        if not os.path.isfile(brief_path):
            result["status"] = "no_brief"
            return result

        energy_dir = f"{mvp_folder}/energy"
        os.makedirs(energy_dir, exist_ok=True)
        project_path = f"{energy_dir}/project.json"

        # ── Step 0: Auto-enrich IFC if available ──────────────
        ifc_path = _find_ifc(mvp_folder)
        if ifc_path:
            profile = _guess_profile(slug, category)
            enrich_stats = _auto_enrich(ifc_path, code="HK", profile=profile)
            if enrich_stats:
                result["ifc_enriched"] = True
                result["enrich_stats"] = {
                    "psets_added": enrich_stats.get("psets_added", 0),
                    "materials_added": enrich_stats.get("materials_added", 0),
                }

        # ── Step 1: Create project (IFC + brief merged) ──────
        proj = create_project(
            slug,
            brief_path=brief_path,
            ifc_path=ifc_path,  # None if no IFC found
            code="HK",
            output_path=project_path,
        )
        zones = proj.get("thermal_model", {}).get("zones", [])
        result["zones"] = len(zones)
        result["building_type"] = proj.get("thermal_model", {}).get("building_type", "")
        result["data_source"] = proj.get("thermal_model", {}).get("source", "brief")

        # ── Step 2: Run simulation ────────────────────────────
        proj["weather_file"] = WEATHER_HK
        proj = run_simulation(proj, project_path=project_path)
        save_project(proj, project_path)

        sim_results = parse_results(proj["simulation"]["output_dir"])
        proj["results"] = sim_results
        save_project(proj, project_path)

        result["eui_kwh_m2_yr"] = sim_results.get("eui_kwh_m2_yr")
        result["total_energy_kwh"] = sim_results.get("total_site_energy_kwh")
        result["floor_area_m2"] = sim_results.get("floor_area_m2")
        result["sim_warnings"] = sim_results.get("warnings", 0)
        result["sim_severe"] = sim_results.get("severe_errors", 0)

        # ── Step 3: Compliance ────────────────────────────────
        comp = check_compliance(proj, code="HK")
        result["compliance_verdict"] = comp.verdict
        result["compliance_passed"] = comp.passed
        result["compliance_failed"] = comp.failed
        result["compliance_total"] = comp.total_checks

        # Save compliance report
        from cli_anything.openstudio.core.compliance import render_report as render_comp
        with open(f"{energy_dir}/compliance-HK.md", "w") as f:
            f.write(render_comp(comp))

        # ── Step 4: BOQ ───────────────────────────────────────
        boq = boq_from_model(proj, region="HK")
        result["boq_subtotal"] = boq.subtotal
        result["boq_grand_total"] = boq.grand_total
        result["boq_cost_per_m2"] = boq.cost_per_m2
        result["boq_currency"] = boq.currency
        result["boq_floor_area"] = boq.floor_area_m2

        from cli_anything.openstudio.core.boq import render_report as render_boq, render_csv
        with open(f"{energy_dir}/boq-HK.md", "w") as f:
            f.write(render_boq(boq))
        with open(f"{energy_dir}/boq-HK.csv", "w") as f:
            f.write(render_csv(boq))

        result["status"] = "completed"

    except Exception as e:
        result["status"] = "failed"
        result["error"] = f"{type(e).__name__}: {e}"
        result["traceback"] = traceback.format_exc()

    result["duration_s"] = round(time.time() - t0, 1)
    return result


def main():
    print(f"Running {len(MVPS)} MVPs through enrich → energy → compliance → BOQ...\n")

    results = []
    for slug, category, folder in MVPS:
        print(f"[{len(results)+1:2}/{len(MVPS)}] {slug} ... ", end="", flush=True)
        r = run_one(slug, category, folder)
        if r["status"] == "completed":
            src = r.get("data_source", "brief")
            enriched = " +enriched" if r.get("ifc_enriched") else ""
            print(f"OK  EUI={r.get('eui_kwh_m2_yr', '?')}  HK${r.get('boq_grand_total', 0):,.0f}  [{src}{enriched}]  ({r['duration_s']}s)")
        else:
            print(f"FAIL  {r.get('error', r['status'])}")
        results.append(r)

    # Save master JSON
    out_dir = "/Users/kaku/Desktop/Work/StartUP-Building/studio-demo"
    master_json = f"{out_dir}/ALL-MVPS-ENERGY-BOQ.json"
    with open(master_json, "w", encoding="utf-8") as f:
        json.dump({"run_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                   "weather": "HK Airport", "code": "HK", "region": "HK",
                   "results": results}, f, indent=2, ensure_ascii=False)
    print(f"\nMaster JSON: {master_json}")

    # Summary stats
    completed = [r for r in results if r["status"] == "completed"]
    ifc_enriched = sum(1 for r in completed if r.get("ifc_enriched"))
    ifc_merged = sum(1 for r in completed if r.get("data_source") in ("ifc", "ifc+brief"))
    print(f"Completed: {len(completed)}/{len(results)}")
    print(f"IFC enriched: {ifc_enriched}, IFC-merged thermal model: {ifc_merged}")

    return results


if __name__ == "__main__":
    main()
