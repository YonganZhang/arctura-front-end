#!/usr/bin/env python3
"""
optimize_images.py — 把 42 MVP 的 PNG 转 WebP + 生成 400×240 thumb
原始 300 MB → WebP 80 → ~50 MB

Input:  $SB_ROOT/studio-demo/{mvp,arch-mvp}/*/ 里的 renders/*.png + floorplan.png + moodboard.png
Output: Arctura-Front-end/assets/mvps/<slug>/
        ├── thumb.webp         (400×240 crop · 卡片用)
        ├── hero.webp          (1920×1080 · 01_hero_corner)
        ├── renders/*.webp     (8 views · 原分辨率)
        ├── floorplan.webp
        └── moodboard.webp

Usage:
  source env-linux.sh
  $PY _build/optimize_images.py [--limit N]  # --limit 只处理前 N 个测试
"""

import os
import sys
import argparse
from pathlib import Path
from PIL import Image, ImageOps

SB_ROOT = Path(os.environ.get("SB_ROOT", "/root/projects/公司项目/Building-CLI-Anything/StartUP-Building"))
FE_ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = FE_ROOT / "assets" / "mvps"

WEBP_QUALITY = 80
THUMB_SIZE = (400, 240)  # 卡片尺寸 · 3:1.8 比例


def to_webp(src: Path, dst: Path, quality: int = WEBP_QUALITY, resize: tuple | None = None, crop_to: tuple | None = None):
    """PNG → WebP · 可选 resize 或中心裁剪"""
    if dst.exists() and dst.stat().st_mtime > src.stat().st_mtime:
        return False  # 已最新，跳过
    dst.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as img:
        img = ImageOps.exif_transpose(img)  # 修正方向
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGB")
        if crop_to:
            img = ImageOps.fit(img, crop_to, method=Image.Resampling.LANCZOS)
        elif resize:
            img.thumbnail(resize, Image.Resampling.LANCZOS)
        img.save(dst, "WEBP", quality=quality, method=6)
    return True


def find_hero_render(renders_dir: Path) -> Path | None:
    """首选 01_hero_corner，否则 renders 下第一张"""
    preferred = [
        "01_hero_corner.png",
        "hero.png",
        "01_hero.png",
        "render-01-hero.png",
    ]
    for name in preferred:
        p = renders_dir / name
        if p.exists():
            return p
    pngs = sorted(renders_dir.glob("*.png"))
    return pngs[0] if pngs else None


def find_fallback_hero(mvp_dir: Path) -> Path | None:
    """没 renders/ 时的兜底：顶层 render.png / variants/vN/renders/01_hero_corner.png"""
    for name in ("render.png", "render-01-hero.png", "hero.png", "interior.png", "massing.png"):
        p = mvp_dir / name
        if p.exists():
            return p
    variants_dir = mvp_dir / "variants"
    if variants_dir.is_dir():
        for v in sorted(variants_dir.iterdir()):
            if not v.is_dir() or v.name.startswith("_"):
                continue
            hero = find_hero_render(v / "renders") if (v / "renders").is_dir() else None
            if hero:
                return hero
            for name in ("hero.png", "render.png"):
                p = v / name
                if p.exists():
                    return p
        grid = sorted(variants_dir.glob("comparison-grid*.png")) + sorted(variants_dir.glob("grid-row-*.png"))
        if grid:
            return grid[0]
    return None


def process_mvp(mvp_dir: Path, slug: str) -> dict:
    """处理单个 MVP · 返回统计"""
    out_dir = OUT_ROOT / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "renders").mkdir(exist_ok=True)

    stats = {"slug": slug, "renders": 0, "floorplan": False, "moodboard": False, "thumb": False, "hero": False, "bytes": 0}

    # 1. 所有 renders/*.png → renders/*.webp（室内 MVP 路径）
    renders_dir = mvp_dir / "renders"
    hero_src = None
    if renders_dir.is_dir():
        for png in sorted(renders_dir.glob("*.png")):
            dst = out_dir / "renders" / (png.stem + ".webp")
            try:
                to_webp(png, dst)
                stats["renders"] += 1
                stats["bytes"] += dst.stat().st_size
            except Exception as e:
                print(f"  ⚠️  render fail {png.name}: {e}")
        hero_src = find_hero_render(renders_dir)

    # 1b. 建筑 MVP · 顶层 elev-*.png + massing.png + interior.png 当 renders
    # 不 duplicate 如果 室内 MVP 已处理
    if not hero_src:
        arch_candidates = []
        for pattern in ["interior.png", "massing.png", "elev-*.png", "floor-*.png", "site*.png"]:
            arch_candidates.extend(sorted(mvp_dir.glob(pattern)))
        for png in arch_candidates:
            dst = out_dir / "renders" / (png.stem + ".webp")
            try:
                to_webp(png, dst)
                stats["renders"] += 1
                stats["bytes"] += dst.stat().st_size
                if hero_src is None and png.name in ("interior.png", "massing.png"):
                    hero_src = png
            except Exception as e:
                print(f"  ⚠️  arch render fail {png.name}: {e}")
        # 如果还没 hero，用第一张 arch_candidates
        if hero_src is None and arch_candidates:
            hero_src = arch_candidates[0]

    # 1c. 最后兜底：顶层 render.png / variants/vN/renders/... / variants/grid-*.png
    if not hero_src:
        hero_src = find_fallback_hero(mvp_dir)
    if hero_src:
        try:
            to_webp(hero_src, out_dir / "hero.webp")
            stats["hero"] = True
            stats["bytes"] += (out_dir / "hero.webp").stat().st_size
        except Exception as e:
            print(f"  ⚠️  hero fail: {e}")

    # 3. thumb.webp（400×240 中心裁剪 · 来自 hero）
    if hero_src:
        try:
            to_webp(hero_src, out_dir / "thumb.webp", quality=75, crop_to=THUMB_SIZE)
            stats["thumb"] = True
            stats["bytes"] += (out_dir / "thumb.webp").stat().st_size
        except Exception as e:
            print(f"  ⚠️  thumb fail: {e}")

    # 4. floorplan.webp
    fp = mvp_dir / "floorplan.png"
    if fp.exists():
        try:
            to_webp(fp, out_dir / "floorplan.webp")
            stats["floorplan"] = True
            stats["bytes"] += (out_dir / "floorplan.webp").stat().st_size
        except Exception as e:
            print(f"  ⚠️  floorplan fail: {e}")

    # 5. moodboard.webp
    mb = mvp_dir / "moodboard.png"
    if mb.exists():
        try:
            to_webp(mb, out_dir / "moodboard.webp")
            stats["moodboard"] = True
            stats["bytes"] += (out_dir / "moodboard.webp").stat().st_size
        except Exception as e:
            print(f"  ⚠️  moodboard fail: {e}")

    return stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="只处理前 N 个（测试用）")
    args = ap.parse_args()

    if not SB_ROOT.exists():
        print(f"❌ SB_ROOT 不存在: {SB_ROOT}")
        sys.exit(1)

    all_mvps = []
    for base in ("mvp", "arch-mvp"):
        base_dir = SB_ROOT / "studio-demo" / base
        if base_dir.is_dir():
            for mvp_dir in sorted(base_dir.iterdir()):
                if mvp_dir.is_dir() and not mvp_dir.name.startswith("_"):
                    all_mvps.append(mvp_dir)

    if args.limit > 0:
        all_mvps = all_mvps[: args.limit]

    print(f"📦 处理 {len(all_mvps)} 个 MVP · 输出到 {OUT_ROOT}")
    OUT_ROOT.mkdir(parents=True, exist_ok=True)

    total_bytes = 0
    total_renders = 0
    total_complete = 0

    for mvp_dir in all_mvps:
        slug = mvp_dir.name
        print(f"  → {slug}", end="", flush=True)
        stats = process_mvp(mvp_dir, slug)
        total_bytes += stats["bytes"]
        total_renders += stats["renders"]
        status_parts = []
        status_parts.append(f"{stats['renders']} renders")
        if stats["hero"]:
            status_parts.append("hero")
        if stats["thumb"]:
            status_parts.append("thumb")
        if stats["floorplan"]:
            status_parts.append("floorplan")
        if stats["moodboard"]:
            status_parts.append("moodboard")
        if stats["hero"] and stats["thumb"]:
            total_complete += 1
        print(f"  · {' + '.join(status_parts) or '(空)'}  {stats['bytes']/1024/1024:.1f} MB")

    print()
    print(f"📊 完成 {total_complete}/{len(all_mvps)} MVP · {total_renders} renders · 总大小 {total_bytes/1024/1024:.1f} MB")


if __name__ == "__main__":
    main()
