#!/usr/bin/env python3
"""extract_metrics.py — P11 Case Study step 1: MVP folder → metrics.json + thumbs/.

Spec: playbooks/case-study-autogen-pipeline.md §3, §5, §8
Usage: python3 extract_metrics.py <MVP-folder>
"""
from __future__ import annotations

import argparse
import csv
import glob
import json
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

from PIL import Image


HKT = timezone(timedelta(hours=8))


def _slugify_folder_name(name: str) -> str:
    return re.sub(r"[-_]+", " ", name).strip().title()


def _first_existing(*paths: Path) -> Path | None:
    for p in paths:
        if p and p.exists() and p.is_file():
            return p
    return None


def _glob_rel(folder: Path, pattern: str) -> list[str]:
    return sorted(str(p.relative_to(folder)) for p in folder.glob(pattern))


def _read_brief(folder: Path) -> dict | None:
    p = folder / "brief.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def _interior_space(brief: dict) -> dict:
    s = brief.get("space") or {}
    dims = s.get("dimensions_m") or {}
    return {
        "type": s.get("type"),
        "area_sqm": s.get("area_sqm"),
        "n_floors": s.get("n_floors", 1),
        "dimensions_m": {
            "length": dims.get("length"),
            "width": dims.get("width"),
            "height": dims.get("height"),
        },
    }


def _architecture_space(brief: dict) -> dict:
    b = brief.get("building") or {}
    site = brief.get("site") or {}
    footprint = b.get("footprint_m") or {}
    return {
        "type": brief.get("building_type"),
        "area_sqm": b.get("gross_floor_area_sqm") or site.get("lot_area_sqm"),
        "n_floors": b.get("floors", 1),
        "dimensions_m": {
            "length": footprint.get("length"),
            "width": footprint.get("width"),
            "height": b.get("total_height_m"),
        },
    }


def _style(brief: dict) -> dict:
    st = brief.get("style")
    if isinstance(st, str):
        kws = [s.strip() for s in re.split(r"[/,、·•]", st) if s.strip()]
        return {"keywords": kws, "palette_hex": []}
    if not isinstance(st, dict):
        return {"keywords": [], "palette_hex": []}
    palette = st.get("palette")
    palette_hex: list[str] = []
    if isinstance(palette, dict):
        palette_hex = [v for v in palette.values() if isinstance(v, str) and v.startswith("#")][:4]
    elif isinstance(palette, list):
        palette_hex = [v for v in palette if isinstance(v, str) and v.startswith("#")][:4]
    kws = st.get("keywords")
    if not isinstance(kws, list):
        kws = []
    return {"keywords": kws, "palette_hex": palette_hex}


def _timeline_weeks(brief: dict) -> int | None:
    if brief.get("timeline_weeks") is not None:
        return brief["timeline_weeks"]
    months = brief.get("timeline_months")
    if months is not None:
        return int(round(months * 4.33))
    return None


def _functional_zones(brief: dict) -> list[str]:
    zones = brief.get("functional_zones")
    if isinstance(zones, list):
        return [z["name"] if isinstance(z, dict) and "name" in z else str(z) for z in zones]
    program = brief.get("program")
    if isinstance(program, list):
        return [p.get("name", str(p)) if isinstance(p, dict) else str(p) for p in program]
    return []


def _pick_hero(folder: Path, tier: str) -> str | None:
    candidates = (
        [folder / "renders" / "01_hero_corner.png",
         folder / "render.png",
         folder / "renders" / "08_birds_eye_3d.png"]
        if tier == "interior"
        else [folder / "street.png",
              folder / "massing.png",
              folder / "renders" / "01_hero_corner.png",
              folder / "interior.png"]
    )
    found = _first_existing(*candidates)
    return str(found.relative_to(folder)) if found else None


def _all_visual_sources(folder: Path) -> list[str]:
    """Collect all visual assets, ordered by priority for card thumbnails.

    Priority tiers (higher = better for portfolio cards):
      T1: 3D renders (renders/*.png, render.png, street.png, massing.png, interior.png)
      T2: elevations (elev-*.png) — architectural perspective, good visual diversity
      T3: sections (section-*.png) — cross-section views
      T4: floor plans (floor-*.png, floorplan.png, site-plan.png)
      T5: moodboard (moodboard.png) — color reference, last resort
    """
    tiers: list[list[str]] = [[], [], [], [], []]
    # T1: 3D renders
    for pat in ("renders/*.png", "render.png", "street.png", "massing.png", "interior.png"):
        tiers[0].extend(_glob_rel(folder, pat))
    # T2: elevations
    tiers[1].extend(_glob_rel(folder, "elev-*.png"))
    # T3: sections
    tiers[2].extend(_glob_rel(folder, "section-*.png"))
    # T4: floor plans
    for pat in ("floorplan.png", "floor-*.png", "site-plan.png"):
        tiers[3].extend(_glob_rel(folder, pat))
    # T5: moodboard
    tiers[4].extend(_glob_rel(folder, "moodboard.png"))

    seen: set[str] = set()
    out: list[str] = []
    for tier in tiers:
        for r in tier:
            if r not in seen:
                seen.add(r)
                out.append(r)
    return out


def _exports(folder: Path) -> list[str]:
    exp_dir = folder / "exports"
    if not exp_dir.is_dir():
        return []
    return sorted({p.suffix.lstrip(".").lower() for p in exp_dir.iterdir()
                   if p.suffix.lower() in {".dxf", ".glb", ".obj", ".fbx", ".ifc"}})


def _boq_total(csv_path: Path) -> float | None:
    if not csv_path.exists():
        return None
    try:
        with csv_path.open() as f:
            reader = csv.reader(f)
            last_total: float | None = None
            for row in reader:
                if row and row[-2:] and "Grand Total" in " ".join(row):
                    try:
                        last_total = float(row[-1])
                    except ValueError:
                        pass
            return last_total
    except OSError:
        return None


def _compliance(folder: Path) -> tuple[str | None, str | None]:
    """Return (compliance_code, 'passed/total' string)."""
    energy_dir = folder / "energy"
    if not energy_dir.is_dir():
        return None, None
    for md in sorted(energy_dir.glob("compliance-*.md")):
        code_m = re.match(r"compliance-(.+)\.md$", md.name)
        if not code_m:
            continue
        code = code_m.group(1)
        try:
            text = md.read_text()
        except OSError:
            continue
        score_m = re.search(r"(\d+)\s*/\s*(\d+)\s+passed", text)
        if score_m:
            return code, f"{score_m.group(1)}/{score_m.group(2)}"
        score_m = re.search(r"\*\*Score\*\*:\s*(\d+)/(\d+)", text)
        if score_m:
            return code, f"{score_m.group(1)}/{score_m.group(2)}"
    return None, None


def _eui(folder: Path) -> float | None:
    pj = folder / "energy" / "project.json"
    if pj.exists():
        try:
            data = json.loads(pj.read_text())
            eui = (data.get("results") or {}).get("eui_kwh_m2_yr")
            if isinstance(eui, (int, float)):
                return float(eui)
        except (json.JSONDecodeError, OSError):
            pass
    return None


def _design_duration_min(folder: Path) -> int | None:
    readme = folder / "CLIENT-README.md"
    if not readme.exists():
        return None
    try:
        text = readme.read_text()
    except OSError:
        return None
    m = re.search(r"总用时[^\d]{0,10}(\d+)\s*分", text)
    if m:
        return int(m.group(1))
    m = re.search(r"(\d+)\s*minutes?\b", text)
    return int(m.group(1)) if m else None


def _blender_objects(folder: Path) -> int:
    for name in ("room.json", "building.json"):
        p = folder / name
        if not p.exists():
            continue
        try:
            data = json.loads(p.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        objs = data.get("objects")
        if isinstance(objs, list):
            return len(objs)
    return 0


def _ifc_products(folder: Path) -> int:
    ifc_files = list((folder / "exports").glob("*.ifc")) if (folder / "exports").is_dir() else []
    if not ifc_files:
        return 0
    try:
        import ifcopenshell  # type: ignore
    except ImportError:
        count = 0
        for f in ifc_files:
            try:
                count += sum(1 for line in f.read_text(errors="ignore").splitlines()
                             if line.strip().startswith("#") and "IFCPRODUCT" in line.upper())
            except OSError:
                pass
        return count
    total = 0
    for f in ifc_files:
        try:
            model = ifcopenshell.open(str(f))
            total += len(model.by_type("IfcProduct"))
        except Exception:
            pass
    return total


def _n_decks(folder: Path) -> int:
    decks_dir = folder / "decks"
    if decks_dir.is_dir():
        return len(list(decks_dir.glob("deck-*.pptx"))) or len(list(decks_dir.glob("*.pptx")))
    root_pptx = list(folder.glob("deck*.pptx")) + list(folder.glob("*.odp"))
    return len(root_pptx)


_SOURCE_LABELS = {
    "renders/01_hero_corner.png": "主视角渲染",
    "renders/02_reception.png": "接待区",
    "renders/03_main_zone.png": "主功能区",
    "renders/04_feature_zone.png": "特色区域",
    "renders/05_lounge_zone.png": "休息区",
    "renders/06_back_corner.png": "背面透视",
    "renders/07_top_ortho.png": "俯视正交",
    "renders/08_birds_eye_3d.png": "鸟瞰透视",
    "render.png": "效果图",
    "street.png": "街景透视",
    "massing.png": "体量鸟瞰",
    "interior.png": "室内透视",
    "moodboard.png": "色彩参考",
    "floorplan.png": "平面图",
    "site-plan.png": "总平面",
}


def _label_for_source(rel_path: str) -> str:
    if rel_path in _SOURCE_LABELS:
        return _SOURCE_LABELS[rel_path]
    name = Path(rel_path).stem
    if name.startswith("elev-"):
        direction = {"N": "北", "S": "南", "E": "东", "W": "西"}.get(name.split("-")[1], name.split("-")[1])
        return f"{direction}立面"
    if name.startswith("section-"):
        return f"剖面 {name.split('-')[1]}"
    if name.startswith("floor-"):
        return f"{name.split('-')[1]} 平面"
    if name.startswith("renders/"):
        return f"渲染 {Path(name).stem}"
    return name


def _classify_visual(rel: str) -> str:
    """Classify a visual source into a type bucket."""
    name = Path(rel).stem.lower()
    if rel.startswith("renders/") or name in ("render", "street", "massing", "interior"):
        return "render"
    if name.startswith("elev-"):
        return "elevation"
    if name.startswith("section-"):
        return "section"
    if name.startswith("floor-") or name in ("floorplan", "site-plan"):
        return "plan"
    if name == "moodboard":
        return "moodboard"
    return "render"


def _round_robin_select(candidates: list[Path], folder: Path, hero_resolved: str) -> list[Path]:
    """Pick up to 4 cards with maximum type diversity (round-robin).

    Slot priority: render → elevation (1 only) → section → plan → moodboard.
    Never picks more than 1 from elevation (they look too similar).
    Falls back to remaining items if a type is empty.
    """
    TYPE_ORDER = ["render", "section", "elevation", "plan", "moodboard"]

    buckets: dict[str, list[Path]] = {t: [] for t in TYPE_ORDER}
    for p in candidates:
        rel = str(p.relative_to(folder)) if str(p).startswith(str(folder)) else p.name
        vtype = _classify_visual(rel)
        buckets.setdefault(vtype, []).append(p)

    selected: list[Path] = []
    used: set[str] = set()

    # Round 1: one from each type (order = render first, then section, elevation, plan, moodboard)
    for vtype in TYPE_ORDER:
        if len(selected) >= 4:
            break
        for p in buckets[vtype]:
            resolved = str(p.resolve())
            if resolved not in used and resolved != hero_resolved:
                selected.append(p)
                used.add(resolved)
                break

    # Round 2: fill remaining slots from any bucket (skip elevation — already got 1)
    if len(selected) < 4:
        for vtype in TYPE_ORDER:
            for p in buckets[vtype]:
                if len(selected) >= 4:
                    break
                resolved = str(p.resolve())
                if resolved not in used and resolved != hero_resolved:
                    # Skip extra elevations (they look too similar to each other)
                    if vtype == "elevation" and any(_classify_visual(str(s.relative_to(folder))) == "elevation"
                                                     for s in selected):
                        continue
                    selected.append(p)
                    used.add(resolved)

    return selected


def _make_thumbs(folder: Path, hero_rel: str | None, all_visuals: list[str]) -> list[dict]:
    """Generate hero / index / og / card-1..4 thumbnails.

    Returns list of {card, source, label} for each generated card (written into metrics.json).
    Card selection: pick up to 4 *distinct* images from all_visuals,
    skipping the hero to maximize diversity.
    """
    cs_dir = folder / "case-study" / "thumbs"
    cs_dir.mkdir(parents=True, exist_ok=True)

    hero_specs = {
        "hero.jpg":  ((1600, 900), 85),
        "index.jpg": ((480, 360), 80),
        "og.jpg":    ((1200, 630), 85),
    }

    hero_path = (folder / hero_rel) if hero_rel else None
    if hero_path and not hero_path.exists():
        hero_path = None

    # Resolve all visual source paths, dedup by resolved path
    all_paths: list[Path] = []
    seen_resolved: set[str] = set()
    for r in all_visuals:
        p = folder / r
        if p.exists():
            resolved = str(p.resolve())
            if resolved not in seen_resolved:
                seen_resolved.add(resolved)
                all_paths.append(p)

    if not all_paths and not hero_path:
        return

    # Use hero for hero/index/og
    actual_hero = hero_path or all_paths[0]
    for fname, (size, q) in hero_specs.items():
        _save_cropped(actual_hero, cs_dir / fname, size, q)

    # Cards: skip hero to avoid duplication, pick first 4 distinct alternatives
    hero_resolved = str(actual_hero.resolve())
    card_sources = [p for p in all_paths if str(p.resolve()) != hero_resolved]

    # If we got fewer than 4 alternatives and hero wasn't in the list, add hero back as last resort
    if len(card_sources) < 4 and all_paths:
        for p in all_paths:
            if p not in card_sources and len(card_sources) < 4:
                card_sources.append(p)

    # Round-robin: pick 1 from each type for maximum diversity
    card_sources = _round_robin_select(card_sources, folder, hero_resolved)

    card_map: list[dict] = []
    for i, src in enumerate(card_sources[:4], start=1):
        _save_cropped(src, cs_dir / f"card-{i}.jpg", (800, 600), 85)  # 4:3 not 1:1
        rel = str(src.relative_to(folder))
        card_map.append({"card": f"card-{i}", "source": rel, "label": _label_for_source(rel)})

    # Clean up extra cards if fewer than 4 now (previously generated)
    for i in range(len(card_sources) + 1, 5):
        stale = cs_dir / f"card-{i}.jpg"
        if stale.exists():
            stale.unlink()

    return card_map


def _save_cropped(src: Path, dst: Path, size: tuple[int, int], quality: int) -> None:
    try:
        img = Image.open(src)
    except (OSError, Image.UnidentifiedImageError):
        return
    if img.mode != "RGB":
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.convert("RGBA").split()[3] if img.mode in ("RGBA", "LA") else None)
        img = bg
    target_w, target_h = size
    src_ratio = img.width / img.height
    target_ratio = target_w / target_h
    if src_ratio > target_ratio:
        new_w = int(img.height * target_ratio)
        left = (img.width - new_w) // 2
        img = img.crop((left, 0, left + new_w, img.height))
    else:
        new_h = int(img.width / target_ratio)
        top = (img.height - new_h) // 2
        img = img.crop((0, top, img.width, top + new_h))
    img = img.resize(size, Image.LANCZOS)
    img.save(dst, "JPEG", quality=quality, optimize=True)


def extract(folder: Path) -> dict:
    if not folder.is_dir():
        raise FileNotFoundError(f"MVP folder not found: {folder}")

    tier = "architecture" if folder.parent.name == "arch-mvp" else "interior"
    brief = _read_brief(folder)
    if brief is None:
        raise ValueError(f"brief.json missing or unreadable in {folder}")

    space = _architecture_space(brief) if tier == "architecture" else _interior_space(brief)
    style = _style(brief)
    hero = _pick_hero(folder, tier)
    if not hero:
        raise ValueError(f"No hero render found in {folder}")
    renders = _all_visual_sources(folder)
    plans = _glob_rel(folder, "floorplan.svg") + _glob_rel(folder, "floor-*.svg") + _glob_rel(folder, "site-plan.svg")
    elevations = _glob_rel(folder, "elev-*.svg")
    sections = _glob_rel(folder, "section-*.svg")
    exports = _exports(folder)
    blender_objects = _blender_objects(folder)
    ifc_products = _ifc_products(folder)
    n_decks = _n_decks(folder)

    boq_hkd = _boq_total(folder / "energy" / "boq-HK.csv")
    boq_cny = _boq_total(folder / "energy" / "boq-CN.csv")
    eui = _eui(folder)
    code, pass_rate = _compliance(folder)
    design_min = _design_duration_min(folder)

    coverage = {
        "brief": True,
        "renders": bool(renders),
        "plans": bool(plans or elevations),
        "exports": bool(exports),
        "decks": n_decks > 0,
        "energy": eui is not None,
        "boq": boq_hkd is not None or boq_cny is not None,
        "compliance": code is not None,
    }

    metrics = {
        "id": folder.name,
        "tier": tier,
        "scenario_cn": brief.get("project") or _slugify_folder_name(folder.name),
        "client_type": brief.get("client") or "未披露",
        "space": space,
        "style": style,
        "brief": {
            "budget_rmb": brief.get("budget_rmb"),
            "timeline_weeks": _timeline_weeks(brief),
            "functional_zones": _functional_zones(brief),
            "must_have": brief.get("must_have") if isinstance(brief.get("must_have"), list) else [],
        },
        "deliverables": {
            "hero_render": hero,
            "renders": renders,
            "plans_svg": plans,
            "elevations": elevations,
            "sections": sections,
            "exports": exports,
            "n_stakeholder_decks": n_decks,
            "blender_objects": blender_objects,
            "ifc_products": ifc_products,
        },
        "metrics": {
            "design_duration_min": design_min,
            "boq_total_hkd": boq_hkd,
            "boq_total_cny": boq_cny,
            "eui_kwh_m2_yr": eui,
            "compliance_code": code,
            "compliance_pass_rate": pass_rate,
            "co2_saved_t_yr": None,
        },
        "_coverage": coverage,
        "_generated": datetime.now(HKT).isoformat(timespec="seconds"),
    }

    cs_dir = folder / "case-study"
    cs_dir.mkdir(parents=True, exist_ok=True)
    card_map = _make_thumbs(folder, hero, renders)
    metrics["deliverables"]["card_sources"] = card_map
    (cs_dir / "metrics.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False))
    return metrics


def main() -> int:
    ap = argparse.ArgumentParser(description="Extract MVP metrics for case study")
    ap.add_argument("mvp_folder", type=Path)
    args = ap.parse_args()
    try:
        m = extract(args.mvp_folder.resolve())
    except (FileNotFoundError, ValueError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    print(f"OK: {m['id']} ({m['tier']}) → case-study/metrics.json + thumbs/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
