#!/usr/bin/env python3
"""
build_variants.py — 为 8 个多方案 MVP 聚合 variant 数据 + 转 WebP

Input:
  - $SB_ROOT/studio-demo/{mvp,arch-mvp}/<slug>/variants/v*/
    每个 variant 目录含：brief.json · room.json · renders/*.png · hero.png · floorplan.png · moodboard.png · energy/boq-HK.md · energy/compliance-HK.md

Output:
  - Arctura-Front-end/assets/mvps/<slug>/variants/<vid>/*.webp
      ├── thumb.webp (400×240 裁剪 · 卡片用)
      ├── hero.webp
      ├── renders/*.webp
      ├── floorplan.webp
      └── moodboard.webp
  - Arctura-Front-end/data/mvps/<slug>/variants/<vid>.json
      每个 variant 的 override JSON（project / zones / renders / pricing / energy / compliance）

Usage:
  $PY _build/build_variants.py
"""

import json
import os
import sys
from pathlib import Path

# 复用 build_mvp_data 里的 parse 函数
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_mvp_data import (
    SB_ROOT, FE_ROOT, OUT_MVPS,
    safe_read_json, safe_read_text,
    parse_boq_md, parse_compliance_md,
    default_editable, categorize_mvp,
)

try:
    from PIL import Image, ImageOps
except ImportError:
    print("❌ 需要 Pillow: pip install --user Pillow")
    sys.exit(1)

OUT_ASSETS = FE_ROOT / "assets" / "mvps"
OUT_VARIANTS_DATA = OUT_MVPS  # /data/mvps/<slug>/variants/<vid>.json
WEBP_QUALITY = 80
THUMB_SIZE = (400, 240)


def to_webp(src: Path, dst: Path, quality: int = WEBP_QUALITY, crop_to: tuple | None = None) -> bool:
    if not src.exists():
        return False
    if dst.exists() and dst.stat().st_mtime > src.stat().st_mtime:
        return True  # 已最新
    dst.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as img:
        img = ImageOps.exif_transpose(img)
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGB")
        if crop_to:
            img = ImageOps.fit(img, crop_to, method=Image.Resampling.LANCZOS)
        img.save(dst, "WEBP", quality=quality, method=6)
    return True


def find_hero_src(variant_dir: Path) -> Path | None:
    """找 variant 的 hero · 优先级：hero.png > renders/01_hero_corner.png > renders/01_*.png > 第一张 render"""
    for name in ("hero.png", "render.png"):
        p = variant_dir / name
        if p.exists():
            return p
    rdir = variant_dir / "renders"
    if rdir.is_dir():
        for name in ("01_hero_corner.png", "01_hero.png", "hero.png"):
            p = rdir / name
            if p.exists():
                return p
        pngs = sorted(rdir.glob("*.png"))
        if pngs:
            return pngs[0]
    # arch variants 可能是 interior.png / massing.png
    for name in ("interior.png", "massing.png"):
        p = variant_dir / name
        if p.exists():
            return p
    return None


def optimize_variant_images(variant_dir: Path, out_dir: Path) -> dict:
    """转 variant 的所有 PNG → WebP · 返回统计 + renders 清单"""
    stats = {"renders": [], "hero": False, "thumb": False, "floorplan": False, "moodboard": False}
    out_dir.mkdir(parents=True, exist_ok=True)

    # renders/*.png
    rdir = variant_dir / "renders"
    if rdir.is_dir():
        (out_dir / "renders").mkdir(exist_ok=True)
        for png in sorted(rdir.glob("*.png")):
            dst = out_dir / "renders" / (png.stem + ".webp")
            if to_webp(png, dst):
                stats["renders"].append({
                    "id": png.stem.split("_", 1)[0] if "_" in png.stem else png.stem,
                    "file": f"/assets/mvps/{out_dir.parent.parent.name}/variants/{out_dir.name}/renders/{png.stem}.webp",
                    "title": png.stem.replace("_", " ").replace("-", " ").title(),
                    "tag": png.stem,
                })

    # hero + thumb
    hero_src = find_hero_src(variant_dir)
    if hero_src:
        if to_webp(hero_src, out_dir / "hero.webp"):
            stats["hero"] = True
        if to_webp(hero_src, out_dir / "thumb.webp", quality=75, crop_to=THUMB_SIZE):
            stats["thumb"] = True

    # floorplan / moodboard
    for name in ("floorplan", "moodboard"):
        src = variant_dir / f"{name}.png"
        if src.exists():
            if to_webp(src, out_dir / f"{name}.webp"):
                stats[name] = True

    return stats


def variant_model_glb(mvp_slug: str, vid: str) -> str | None:
    """variant 的 GLB 路径（若已 build_models.py 拷贝过）"""
    from build_mvp_data import FE_ROOT
    p = FE_ROOT / "assets" / "mvps" / mvp_slug / "variants" / vid / "model.glb"
    return f"/assets/mvps/{mvp_slug}/variants/{vid}/model.glb" if p.exists() else None


def build_variant_json(mvp_slug: str, mvp_cat: str, variant_dir: Path, img_stats: dict) -> dict:
    """每个 variant 的 override data · 只写 variant-specific 字段，前端跟 base merge"""
    vid = variant_dir.name
    brief = safe_read_json(variant_dir / "brief.json")
    metrics = safe_read_json(variant_dir / "case-study" / "metrics.json")
    boq_md = safe_read_text(variant_dir / "energy" / "boq-HK.md")
    compliance_md = safe_read_text(variant_dir / "energy" / "compliance-HK.md")

    boq_rows, boq_total, currency = parse_boq_md(boq_md)
    checks = parse_compliance_md(compliance_md)

    # 抽数值（metrics.json schema 两版：nested vs flat）
    area = ((brief.get("space", {}) or {}).get("area_sqm") or
            metrics.get("area_sqm_scene") or
            metrics.get("area_sqm") or 0)
    eui = ((metrics.get("energy", {}) or {}).get("eui_kwh_m2_yr") or
           metrics.get("eui_kwh_m2_yr") or 0)
    total_energy = ((metrics.get("energy", {}) or {}).get("total_kwh_yr") or
                    metrics.get("annual_energy_kwh") or 0)
    grand_total = ((metrics.get("boq", {}) or {}).get("grand_total") or
                   metrics.get("boq_hkd") or
                   boq_total or 0)
    per_m2 = ((metrics.get("boq", {}) or {}).get("unit_cost_per_sqm") or
              metrics.get("cost_per_m2_hkd") or
              (grand_total / area if area else 0))

    # zones
    zones = []
    for z in brief.get("functional_zones") or []:
        zones.append({
            "id": (z.get("name_en") or z.get("name") or "").lower().replace(" ", "_")[:20],
            "name": z.get("name_en") or z.get("name", ""),
            "zh": z.get("name", ""),
            "area": z.get("area_m2") or 0,
            "notes": z.get("notes", ""),
            "x": 0, "y": 0, "w": 20, "h": 20,
        })

    # style / palette
    style_raw = brief.get("style")
    style = style_raw if isinstance(style_raw, dict) else {}
    style_kw = style.get("keywords") if isinstance(style, dict) else None
    if not style_kw and isinstance(style_raw, str):
        style_kw = [style_raw]
    if not style_kw and isinstance(style_raw, list):
        style_kw = style_raw
    palette_raw = style.get("palette") if isinstance(style, dict) else None
    palette = []
    if isinstance(palette_raw, dict):
        palette = [{"name": k, "hex": v} for k, v in palette_raw.items()]
    elif isinstance(palette_raw, list):
        for p in palette_raw:
            if isinstance(p, dict): palette.append(p)
            elif isinstance(p, str) and p.startswith("#"): palette.append({"name": "", "hex": p})

    # 人读名
    project_zh = brief.get("project", "") or ""
    project_en = brief.get("project_en", "") or ""
    style_en = project_en.split("·")[-1].strip() if "·" in project_en else project_en

    return {
        "id": vid,
        "parent_slug": mvp_slug,
        "name": style_en or vid,
        "model_glb": variant_model_glb(mvp_slug, vid),
        "project": {
            "name": project_en or project_zh or vid,
            "zh": project_zh,
            "area": round(float(area)) if area else 0,
            "location": brief.get("region") or "Hong Kong",
            "budgetHKD": brief.get("budget_hkd") or 0,
            "style": ", ".join(style_kw) if isinstance(style_kw, list) else (style_kw or ""),
            "palette": palette,
        },
        "renders": img_stats["renders"],
        "floorplan": f"/assets/mvps/{mvp_slug}/variants/{vid}/floorplan.webp" if img_stats["floorplan"] else None,
        "moodboard": f"/assets/mvps/{mvp_slug}/variants/{vid}/moodboard.webp" if img_stats["moodboard"] else None,
        "hero_img": f"/assets/mvps/{mvp_slug}/variants/{vid}/hero.webp" if img_stats["hero"] else None,
        "thumb_img": f"/assets/mvps/{mvp_slug}/variants/{vid}/thumb.webp" if img_stats["thumb"] else None,
        "zones": zones,
        "pricing": {
            "HK": {
                "label": "Hong Kong",
                "currency": currency,
                "perM2": round(per_m2) if per_m2 else 0,
                "rows": boq_rows,
                "total": f"{round(grand_total):,}" if grand_total else "0",
                "totalNumber": round(grand_total) if grand_total else 0,
                "subtotal": f"{round(grand_total / 1.47):,}" if grand_total else "0",
                "mep": f"{round(grand_total / 1.47 * 0.25):,}" if grand_total else "0",
                "prelim": f"{round(grand_total / 1.47 * 0.12):,}" if grand_total else "0",
                "cont": f"{round(grand_total / 1.47 * 0.10):,}" if grand_total else "0",
            },
        },
        "energy": {
            "eui": round(float(eui), 1) if eui else 0,
            "limit": 150,
            "annual": round(float(total_energy)) if total_energy else 0,
            "engine": (metrics.get("energy", {}) or {}).get("engine", "EnergyPlus"),
        },
        "compliance": {
            "HK": {
                "code": "HK_BEEO_BEC_2021",
                "label": "HK · BEEO 2021",
                "checks": checks,
                "items": checks,   # alias
                "verdict": (metrics.get("compliance", {}) or {}).get("status") or (metrics.get("compliance_status") or "—"),
                "score": (
                    f"{sum(1 for c in checks if c.get('status') == 'pass')}/{len(checks)} passed"
                    if checks else ""
                ),
            },
        },
        "editable": default_editable(mvp_cat, area),
        "derived": {
            "eui_kwh_m2_yr": round(float(eui), 1) if eui else 0,
            "cost_total": round(float(grand_total)) if grand_total else 0,
            "cost_per_m2": round(float(per_m2)) if per_m2 else 0,
            "co2_t_per_yr": round(float(eui) * float(area) * 0.59 / 1000, 2) if (area and eui) else 0,
        },
    }


def process_mvp(mvp_dir: Path, mvp_cat: str) -> int:
    """处理单个 MVP · 返回处理的 variant 数量"""
    slug = mvp_dir.name
    variants_dir = mvp_dir / "variants"
    if not variants_dir.is_dir():
        return 0

    count = 0
    for v in sorted(variants_dir.iterdir()):
        if not v.is_dir():
            continue
        if v.name.startswith("_") or v.name.startswith("."):
            continue
        if not (len(v.name) >= 3 and v.name[0] == "v" and v.name[1].isdigit()):
            continue

        out_img_dir = OUT_ASSETS / slug / "variants" / v.name
        out_data_dir = OUT_MVPS / slug / "variants"
        out_data_dir.mkdir(parents=True, exist_ok=True)

        img_stats = optimize_variant_images(v, out_img_dir)
        vjson = build_variant_json(slug, mvp_cat, v, img_stats)
        (out_data_dir / f"{v.name}.json").write_text(
            json.dumps(vjson, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        count += 1
        renders_count = len(img_stats["renders"])
        print(f"  · {v.name:<25} renders={renders_count}  hero={'✓' if img_stats['hero'] else '✗'}  "
              f"floor={'✓' if img_stats['floorplan'] else '✗'}  mood={'✓' if img_stats['moodboard'] else '✗'}")
    return count


def main():
    if not SB_ROOT.exists():
        print(f"❌ SB_ROOT 不存在: {SB_ROOT}")
        sys.exit(1)

    total_variants = 0
    total_mvps = 0

    for base, cat_hint in [("mvp", "hospitality"), ("arch-mvp", "civic")]:
        # cat 会被具体 categorize_mvp 覆盖（这里 cat_hint 只作 fallback）
        base_dir = SB_ROOT / "studio-demo" / base
        if not base_dir.is_dir():
            continue
        for mvp_dir in sorted(base_dir.iterdir()):
            if not mvp_dir.is_dir() or mvp_dir.name.startswith("_"):
                continue
            variants_dir = mvp_dir / "variants"
            if not variants_dir.is_dir():
                continue
            # 确认至少有一个 v* 子目录
            has_v = any(
                c.is_dir() and len(c.name) >= 3 and c.name[0] == "v" and c.name[1].isdigit()
                for c in variants_dir.iterdir()
            )
            if not has_v:
                continue
            # 用 categorize_mvp 拿到真实 cat
            mvp_cat = categorize_mvp({"slug": mvp_dir.name})

            print(f"📦 {mvp_dir.name} ({mvp_cat})")
            n = process_mvp(mvp_dir, mvp_cat)
            total_variants += n
            total_mvps += 1

    print(f"\n✅ 完成 {total_mvps} 个 MVP · {total_variants} 个 variant")

    # 自动 schema 校验
    print()
    import subprocess
    r = subprocess.run(
        [sys.executable, str(Path(__file__).resolve().parent / "validate.py"), "--quiet"],
        capture_output=True, text=True,
    )
    print(r.stdout.strip())
    if r.returncode != 0:
        print(r.stderr.strip())
        print("\n❌ Schema 校验失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
