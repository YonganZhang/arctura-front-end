#!/usr/bin/env python3
"""Verify that an IFC file has been enriched (not a bare Blender export).

Enriched IFC must have:
  1. At least 1 IFCPROPERTYSET (property data attached to elements)
  2. At least 1 IFCRELASSOCIATESMATERIAL (material assignments)
  3. At least 1 typed element beyond IFCBUILDINGELEMENTPROXY
     (e.g. IFCFURNITURE, IFCWALL, IFCDOOR, IFCWINDOW, IFCSLAB)

Usage:
  python verify_ifc_enriched.py <path.ifc> [<path2.ifc> ...]
  python verify_ifc_enriched.py --scan-dir <mvp-dir>   # find all .ifc recursively

As a library:
  from verify_ifc_enriched import check_ifc_enriched
  issues = check_ifc_enriched("/path/to/file.ifc")
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# IFC entity types that indicate typed (non-proxy) building/furniture elements
TYPED_ELEMENT_PATTERNS = [
    "IFCWALL",
    "IFCWALLSTANDARDCASE",
    "IFCSLAB",
    "IFCDOOR",
    "IFCWINDOW",
    "IFCFURNITURE",
    "IFCFURNISHINGELEMENT",
    "IFCCOLUMN",
    "IFCBEAM",
    "IFCROOF",
    "IFCSTAIRFLIGHT",
    "IFCRAILING",
    "IFCCOVERING",
    "IFCFLOWSEGMENT",
    "IFCFLOWTERMINAL",
    "IFCBUILDINGELEMENTPART",
]

# Compile regex: match entity name at word boundary (avoid partial matches)
_TYPED_RE = re.compile(
    r"\b(" + "|".join(TYPED_ELEMENT_PATTERNS) + r")\b"
)


def check_ifc_enriched(ifc_path: str | Path) -> list[str]:
    """Check if an IFC file has been enriched.

    Returns a list of issue strings. Empty list = file is properly enriched.
    """
    ifc_path = Path(ifc_path)
    issues: list[str] = []

    if not ifc_path.exists():
        return [f"File not found: {ifc_path}"]
    if ifc_path.stat().st_size == 0:
        return [f"Empty file: {ifc_path}"]

    text = ifc_path.read_text(encoding="utf-8", errors="replace")

    # Count key enrichment markers
    n_property_set = len(re.findall(r"\bIFCPROPERTYSET\b", text))
    n_material_assoc = len(re.findall(r"\bIFCRELASSOCIATESMATERIAL\b", text))
    n_proxy = len(re.findall(r"\bIFCBUILDINGELEMENTPROXY\b", text))
    n_typed = len(_TYPED_RE.findall(text))

    fname = ifc_path.name

    # Check 1: Property sets
    if n_property_set == 0:
        issues.append(
            f"{fname}: no IFCPROPERTYSET found — element properties missing "
            f"(enrich-ifc not run)"
        )

    # Check 2: Material assignments
    if n_material_assoc == 0:
        issues.append(
            f"{fname}: no IFCRELASSOCIATESMATERIAL found — material data missing"
        )

    # Check 3: Typed elements vs proxies
    if n_typed == 0 and n_proxy > 0:
        issues.append(
            f"{fname}: all {n_proxy} elements are IFCBUILDINGELEMENTPROXY — "
            f"no typed elements (Wall/Door/Window/Furniture/Slab)"
        )

    # Check 4: Even if some typed exist, warn if proxy ratio is too high (>90%)
    total_elements = n_proxy + n_typed
    if total_elements > 0 and n_typed > 0:
        proxy_ratio = n_proxy / total_elements
        if proxy_ratio > 0.90:
            issues.append(
                f"{fname}: {n_proxy}/{total_elements} elements are still "
                f"IFCBUILDINGELEMENTPROXY ({proxy_ratio:.0%}) — "
                f"enrichment may be incomplete"
            )

    return issues


def scan_directory(dir_path: Path) -> dict[Path, list[str]]:
    """Recursively find all .ifc files and check each one.

    Returns dict mapping ifc_path -> issues (only files with issues included).
    """
    results: dict[Path, list[str]] = {}
    for ifc_file in sorted(dir_path.rglob("*.ifc")):
        issues = check_ifc_enriched(ifc_file)
        if issues:
            results[ifc_file] = issues
    return results


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(
        description="Verify IFC files have been enriched (not bare Blender export)"
    )
    ap.add_argument("files", nargs="*", type=Path, help="IFC file(s) to check")
    ap.add_argument(
        "--scan-dir", type=Path, help="Recursively scan directory for .ifc files"
    )
    args = ap.parse_args()

    all_issues: dict[str, list[str]] = {}

    if args.scan_dir:
        for fpath, issues in scan_directory(args.scan_dir).items():
            all_issues[str(fpath)] = issues

    for fpath in args.files or []:
        issues = check_ifc_enriched(fpath)
        if issues:
            all_issues[str(fpath)] = issues

    if not args.files and not args.scan_dir:
        ap.print_help()
        return 1

    if all_issues:
        total = sum(len(v) for v in all_issues.values())
        print(f"FAIL — {total} issue(s) in {len(all_issues)} file(s):", file=sys.stderr)
        for fpath, issues in all_issues.items():
            for iss in issues:
                print(f"  - {iss}", file=sys.stderr)
        return 1

    n_checked = len(list(args.scan_dir.rglob("*.ifc"))) if args.scan_dir else 0
    n_checked += len(args.files or [])
    print(f"OK — {n_checked} IFC file(s) verified as enriched")
    return 0


if __name__ == "__main__":
    sys.exit(main())
