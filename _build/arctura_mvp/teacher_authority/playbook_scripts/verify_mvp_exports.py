#!/usr/bin/env python3
"""Verify an MVP's deliverables against the 全案 checklist.

Per CLAUDE.md "关键产物必含内容", a 全案 MVP must have:
- brief.json / moodboard.png / room.json / renders ≥ 6 / floorplan.svg+png
- exports: GLB + OBJ + FBX + IFC4 (raw) + IFC4-enriched
- energy: project.json + compliance-*.md + boq-*.md (+.csv)
- decks: deck-client.md + .pptx + .pdf
- CLIENT-README.md
- case-study/ (optional but recommended)

Exit codes:
  0 — all checks pass (green)
  1 — at least one required item missing (red)

Usage:
    /opt/anaconda3/envs/mini-2025/bin/python verify_mvp_exports.py <mvp-dir> [--tier full]
        --tier concept|delivery|quote|full|selection
               full = 全案 (default), enforces BIM + compliance + IFC audit
"""

import argparse
import json
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class Check:
    name: str
    severity: str        # "required" (red), "recommended" (yellow)
    desc: str
    ok: bool = False
    detail: str = ""


def check_file(mvp: Path, rel: str, *, required=True, min_bytes=1):
    p = mvp / rel
    ok = p.exists() and p.stat().st_size >= min_bytes
    detail = f"{p.stat().st_size}b" if p.exists() else "missing"
    return ok, detail


def check_glob(mvp: Path, pattern: str, *, min_count=1):
    files = list(mvp.glob(pattern))
    return (len(files) >= min_count), f"{len(files)} file(s)"


def run_checks(mvp: Path, tier: str):
    checks: list[Check] = []

    def C(name, sev, desc, ok, detail=""):
        checks.append(Check(name, sev, desc, ok, detail))

    # ── 概念档（tier: concept+） ─────────────────────────
    ok, d = check_file(mvp, "brief.json")
    C("brief", "required", "Design brief", ok, d)

    ok, d = check_file(mvp, "room.json", min_bytes=500)
    ok2, _ = check_file(mvp, "building.json", min_bytes=500)
    C("scene_json", "required", "3D scene JSON (room.json or building.json)",
      ok or ok2, d if ok else "no room/building.json")

    ok, d = check_file(mvp, "moodboard.png")
    C("moodboard", "required", "Moodboard image", ok, d)

    ok, d = check_glob(mvp, "renders/*.png", min_count=6)
    C("renders", "required", "≥ 6 render views", ok, d)

    ok, d = check_file(mvp, "floorplan.svg")
    ok2, d2 = check_file(mvp, "floorplan.png")
    C("floorplan", "required", "Floorplan (.svg + .png)", ok and ok2,
      f"svg={d} png={d2}")

    # ── 交付档（tier: delivery+） ────────────────────────
    if tier in ("delivery", "quote", "full", "selection"):
        ok, d = check_file(mvp, "decks/deck-client.md")
        C("deck_md", "required", "Marp deck source", ok, d)
        ok, d = check_file(mvp, "decks/deck-client.pptx")
        C("deck_pptx", "required", "Client deck (PPTX)", ok, d)
        ok, d = check_file(mvp, "decks/deck-client.pdf")
        C("deck_pdf", "required", "Client deck (PDF)", ok, d)
        ok, d = check_file(mvp, "CLIENT-README.md")
        C("client_readme", "required", "CLIENT-README.md", ok, d)

    # ── 报价档（tier: quote+） ───────────────────────────
    if tier in ("quote", "full", "selection"):
        ok, d = check_file(mvp, "energy/project.json")
        C("energy_project", "required", "OpenStudio project.json", ok, d)
        ok, d = check_glob(mvp, "energy/boq-*.md")
        C("boq_md", "required", "BOQ markdown", ok, d)
        ok, d = check_glob(mvp, "energy/boq-*.csv")
        C("boq_csv", "required", "BOQ CSV", ok, d)

    # ── 全案档（tier: full+） ───────────────────────────
    if tier in ("full", "selection"):
        # Full BIM export set — per CLAUDE.md "关键产物必含内容"
        ok, d = check_glob(mvp, "exports/*.glb")
        C("export_glb", "required", "GLB export (web/portal 3D viewer)", ok, d)
        ok, d = check_glob(mvp, "exports/*.fbx")
        C("export_fbx", "required", "FBX export (Maya/Max/Unreal interop)", ok, d)

        # OBJ may be at root (legacy) or exports/
        ok1, _ = check_file(mvp, "scene.obj")
        ok2, d = check_glob(mvp, "exports/*.obj")
        C("export_obj", "required", "OBJ export", ok1 or ok2,
          "scene.obj" if ok1 else d)

        ok, d = check_glob(mvp, "exports/*.ifc")
        ifcs = list(mvp.glob("exports/*.ifc"))
        has_enriched = any("enrich" in f.name.lower() for f in ifcs)
        C("export_ifc_raw", "required", "IFC4 raw export", len(ifcs) >= 1, d)
        C("export_ifc_enriched", "required", "IFC4 enriched (属性+材质+Space)",
          has_enriched,
          "enriched ifc found" if has_enriched else "no *-enriched.ifc")

        # Compliance
        ok, d = check_glob(mvp, "energy/compliance-*.md")
        C("compliance", "required", "Compliance report", ok, d)

        # L3 vision QA — per CLAUDE.md "全案档禁止跳过 L3"
        # qa-prompt.json alone (dry-run) does NOT satisfy this; the API must
        # have actually run and produced qa-report.json.
        ok, d = check_file(mvp, "qa-report.json")
        C("qa_vision", "required",
          "L3 vision QA report (qa_vision.py output, not just qa-prompt.json)",
          ok, d)

    # ── 甄选档（tier: selection+） ──────────────────────
    if tier == "selection":
        ok, d = check_glob(mvp, "variants/v*/hero.png")
        C("variants_renders", "required", "≥3 variant renders", ok, d)
        ok, d = check_file(mvp, "variants/diff-matrix.md")
        C("diff_matrix", "required", "Variant diff matrix", ok, d)

    # ── 推荐项（recommended, yellow not red） ──────────
    if tier in ("full", "selection"):
        ok, d = check_file(mvp, "portal.html")
        C("portal", "recommended", "Interactive client portal", ok, d)
        ok, d = check_glob(mvp, "case-study/*.md", min_count=3)
        C("case_study", "recommended", "Case study docs (3 templates)", ok, d)

    return checks


def print_report(mvp: Path, tier: str, checks: list[Check]) -> int:
    reqs = [c for c in checks if c.severity == "required"]
    recs = [c for c in checks if c.severity == "recommended"]
    req_fail = [c for c in reqs if not c.ok]
    rec_fail = [c for c in recs if not c.ok]

    print(f"\n━━━ Verify MVP: {mvp.name} · tier={tier} ━━━\n")
    print(f"{'sev':<12s} {'check':<24s} {'status':<8s} detail")
    print("─" * 78)
    for c in checks:
        status = "✓ OK" if c.ok else ("✗ MISS" if c.severity == "required" else "⚠ skip")
        print(f"{c.severity:<12s} {c.name:<24s} {status:<8s} {c.detail[:36]}")

    print("\n" + "─" * 78)
    print(f"  Required:  {len(reqs) - len(req_fail)}/{len(reqs)} pass")
    print(f"  Recommend: {len(recs) - len(rec_fail)}/{len(recs)} pass")

    if req_fail:
        print(f"\n❌ FAILED — {len(req_fail)} required items missing:")
        for c in req_fail:
            print(f"    • {c.name} ({c.desc})")
        print("\nFix these before claiming tier done. See CLAUDE.md § '关键产物必含内容'.")
        return 1

    print("\n✅ PASSED — all required items present.")
    if rec_fail:
        print(f"   (recommended: {len(rec_fail)} optional items missing)")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mvp_dir", type=Path, help="MVP directory")
    ap.add_argument("--tier", choices=["concept", "delivery", "quote", "full", "selection"],
                    default="full", help="Tier to enforce (default: full / 全案)")
    args = ap.parse_args()

    mvp = args.mvp_dir.resolve()
    if not mvp.exists() or not mvp.is_dir():
        print(f"ERROR: not a directory: {mvp}", file=sys.stderr)
        sys.exit(2)

    checks = run_checks(mvp, args.tier)
    sys.exit(print_report(mvp, args.tier, checks))


if __name__ == "__main__":
    main()
