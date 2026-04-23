"""moodboard artifact · PIL 色板拼图 + JSON"""
from __future__ import annotations
import json
import time
from pathlib import Path
from typing import Callable, Optional

from ..types import ArtifactResult


def produce(ctx: dict, on_event: Optional[Callable] = None) -> ArtifactResult:
    t0 = time.time()
    project = ctx["project"]
    sb_dir: Path = ctx["sb_dir"]
    sb_dir.mkdir(parents=True, exist_ok=True)

    brief = project.brief or {}
    palette_list = (brief.get("style", {}) or {}).get("palette") or []
    # palette 可能是 dict ({"primary":"#hex"}) 或 list ([{"name","hex"}])
    swatches = []
    if isinstance(palette_list, dict):
        swatches = [{"name": k, "hex": v} for k, v in palette_list.items()]
    elif isinstance(palette_list, list):
        for item in palette_list:
            if isinstance(item, dict) and "hex" in item:
                swatches.append(item)
    # 默认色板
    if not swatches:
        swatches = [
            {"name": "primary", "hex": "#D7C4A8"},
            {"name": "secondary", "hex": "#8A7A5C"},
            {"name": "accent", "hex": "#2A2A2A"},
            {"name": "wall", "hex": "#F5F1E8"},
        ]

    keywords = (brief.get("style", {}) or {}).get("keywords", [])
    (sb_dir / "moodboard.json").write_text(json.dumps({
        "palette": swatches, "style_keywords": keywords, "reference_images": [],
    }, ensure_ascii=False, indent=2))

    # PNG 色板（PIL · 可选）
    png_ok = False
    try:
        from PIL import Image, ImageDraw
        W, H = 1600, 900
        img = Image.new("RGB", (W, H), "#1a1511")
        draw = ImageDraw.Draw(img)
        sw_w = W // max(len(swatches), 1)
        for i, s in enumerate(swatches):
            try:
                draw.rectangle([i * sw_w, 200, (i + 1) * sw_w, H - 80], fill=s["hex"])
            except Exception:
                pass
        # 字体 fc-match 动态查（跟 materialize_full_mvp 一致）
        font = _get_cjk_font(44)
        draw.text((40, 40), project.display_name or project.slug, fill="#F5F1E8", font=font)
        img.save(sb_dir / "moodboard.png")
        png_ok = True
    except ImportError:
        pass

    return ArtifactResult(
        name="moodboard", status="done",
        timing_ms=int((time.time()-t0)*1000),
        output_path=str(sb_dir / "moodboard.json"),
        meta={"swatches": len(swatches), "png": png_ok},
    )


def _get_cjk_font(size: int):
    import os
    import subprocess
    from PIL import ImageFont
    for query in ["Noto Sans CJK SC:style=Regular", "Noto Sans CJK TC:style=Regular",
                  "WenQuanYi Zen Hei", "sans-serif:lang=zh"]:
        try:
            out = subprocess.check_output(["fc-match", "-f", "%{file}", query],
                                           stderr=subprocess.DEVNULL, timeout=3).decode().strip()
            if out and Path(out).exists():
                return ImageFont.truetype(out, size)
        except Exception:
            continue
    paths = [
        "/usr/share/fonts/google-noto-cjk/NotoSansCJKsc-Regular.otf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ]
    for fp in paths:
        if Path(fp).exists():
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                pass
    return ImageFont.load_default()
