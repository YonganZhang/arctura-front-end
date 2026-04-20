#!/usr/bin/env python3
"""
build_models.py — 拷 MVP 管线产的 .glb 文件到前端 assets
Blender 导出的 GLB 平均 200-750 KB · 可直接被浏览器 model-viewer 加载实现真 3D

Input:
  - $SB_ROOT/studio-demo/{mvp,arch-mvp}/<slug>/exports/*.glb
  - $SB_ROOT/studio-demo/{mvp,arch-mvp}/<slug>/variants/v*/exports/*.glb

Output:
  - Arctura-Front-end/assets/mvps/<slug>/model.glb
  - Arctura-Front-end/assets/mvps/<slug>/variants/<vid>/model.glb

跑完后 build_mvp_data.py 自动在 JSON 里挂 model_glb 路径（检测 mtime）。
"""

import os
import shutil
import sys
from pathlib import Path

SB_ROOT = Path(os.environ.get("SB_ROOT", "/root/projects/公司项目/Building-CLI-Anything/StartUP-Building"))
FE_ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = FE_ROOT / "assets" / "mvps"


def find_glb(exports_dir: Path) -> Path | None:
    """在 exports/ 目录里找最优先的 .glb · 优先匹配 slug 命名的，否则第一个"""
    if not exports_dir.is_dir():
        return None
    glbs = sorted(exports_dir.glob("*.glb"))
    if not glbs:
        return None
    # 优先匹配目录名
    slug = exports_dir.parent.name
    for g in glbs:
        if slug in g.stem:
            return g
    return glbs[0]


def copy_if_newer(src: Path, dst: Path) -> bool:
    if not src.exists():
        return False
    if dst.exists() and dst.stat().st_mtime > src.stat().st_mtime:
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return True


def process_mvp(mvp_dir: Path) -> dict:
    slug = mvp_dir.name
    stats = {"slug": slug, "base": False, "variants": []}

    # 顶层 exports/
    glb_src = find_glb(mvp_dir / "exports")
    if glb_src:
        dst = OUT_ROOT / slug / "model.glb"
        if copy_if_newer(glb_src, dst):
            stats["base"] = True

    # variants/<v>/exports/
    variants_dir = mvp_dir / "variants"
    if variants_dir.is_dir():
        for v in sorted(variants_dir.iterdir()):
            if not v.is_dir():
                continue
            if not (len(v.name) >= 3 and v.name[0] == "v" and v.name[1].isdigit()):
                continue
            vglb = find_glb(v / "exports")
            if vglb:
                vdst = OUT_ROOT / slug / "variants" / v.name / "model.glb"
                if copy_if_newer(vglb, vdst):
                    stats["variants"].append(v.name)

    return stats


def main():
    if not SB_ROOT.exists():
        print(f"❌ SB_ROOT 不存在: {SB_ROOT}")
        sys.exit(1)

    total_base = 0
    total_variant = 0
    total_bytes = 0

    for base in ("mvp", "arch-mvp"):
        base_dir = SB_ROOT / "studio-demo" / base
        if not base_dir.is_dir():
            continue
        for mvp_dir in sorted(base_dir.iterdir()):
            if not mvp_dir.is_dir() or mvp_dir.name.startswith("_"):
                continue
            stats = process_mvp(mvp_dir)
            if stats["base"] or stats["variants"]:
                parts = []
                if stats["base"]:
                    parts.append("base ✓")
                    total_base += 1
                if stats["variants"]:
                    parts.append(f"{len(stats['variants'])} variants ({', '.join(stats['variants'])})")
                    total_variant += len(stats["variants"])
                print(f"  {stats['slug']:<35} {' + '.join(parts)}")

    # 统计总大小
    for p in OUT_ROOT.rglob("model.glb"):
        total_bytes += p.stat().st_size

    print(f"\n✅ 完成 · {total_base} base + {total_variant} variants · 总 {total_bytes/1024/1024:.1f} MB")


if __name__ == "__main__":
    main()
