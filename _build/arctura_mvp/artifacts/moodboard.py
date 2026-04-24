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
    # Phase 9 · 对齐 spec L397 · 6 色板（暖冷中 · 深浅错位）
    # 优先用 brief.style.palette · 不足 6 补默认 · 按 style.keywords 选默认套
    if len(swatches) < 6:
        # 从 keywords 推 default palette preset
        kw_set = set((brief.get("style", {}) or {}).get("keywords", []))
        preset = _pick_palette_preset(kw_set)
        # 补到 6 · 去重（按 hex.upper）
        seen = {s["hex"].upper() for s in swatches if "hex" in s}
        for p in preset:
            if len(swatches) >= 6:
                break
            if p["hex"].upper() not in seen:
                swatches.append(p)
                seen.add(p["hex"].upper())

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


# Phase 9 · 6 色 palette presets · 严老师 22-audit handbook 对齐 · 暖冷中深浅各取
_PALETTE_PRESETS = {
    "japandi": [  # 日式/侘寂/极简
        {"name": "oak_light", "hex": "#D7C4A8"},
        {"name": "charcoal", "hex": "#2A2A2A"},
        {"name": "linen_cream", "hex": "#F5F1E8"},
        {"name": "warm_brown", "hex": "#8A7A5C"},
        {"name": "moss_green", "hex": "#4F6245"},
        {"name": "indigo", "hex": "#2D3748"},
    ],
    "minimalist": [  # 北欧/极简
        {"name": "pure_white", "hex": "#F8F8F6"},
        {"name": "ash_grey", "hex": "#BCBCB8"},
        {"name": "charcoal", "hex": "#2A2A2A"},
        {"name": "oak_light", "hex": "#D7C4A8"},
        {"name": "dusty_blue", "hex": "#8DA7B5"},
        {"name": "accent_red", "hex": "#C44536"},
    ],
    "industrial": [  # 工业/Loft
        {"name": "concrete", "hex": "#8A857E"},
        {"name": "steel_dark", "hex": "#33363A"},
        {"name": "aged_wood", "hex": "#6B5D4E"},
        {"name": "rust", "hex": "#B8523F"},
        {"name": "black_iron", "hex": "#1A1A1A"},
        {"name": "canvas", "hex": "#8E8678"},
    ],
    "modern_chinese": [  # 新中式/禅意
        {"name": "chinese_ink", "hex": "#2C3539"},
        {"name": "aged_paper", "hex": "#E8DCC8"},
        {"name": "tea_green", "hex": "#6A7F56"},
        {"name": "wood_redbrown", "hex": "#8B6914"},
        {"name": "gold_accent", "hex": "#D4A017"},
        {"name": "stone_grey", "hex": "#9E9183"},
    ],
    "default": [  # 通用中性
        {"name": "primary", "hex": "#D7C4A8"},
        {"name": "secondary", "hex": "#8A7A5C"},
        {"name": "accent", "hex": "#2A2A2A"},
        {"name": "wall", "hex": "#F5F1E8"},
        {"name": "neutral_mid", "hex": "#A8A298"},
        {"name": "warm_accent", "hex": "#B88A5E"},
    ],
}


def _pick_palette_preset(keywords_set: set) -> list:
    """按 keywords 选 preset · 不 match 返 default"""
    kw = {str(k).lower() for k in keywords_set}
    if any(k in kw for k in ("日式", "japandi", "japanese", "侘寂", "wabi-sabi", "禅")):
        if any(k in kw for k in ("中式", "新中式", "chinese")):
            return _PALETTE_PRESETS["modern_chinese"]
        return _PALETTE_PRESETS["japandi"]
    if any(k in kw for k in ("极简", "minimal", "minimalist", "北欧", "scandinavian", "nordic")):
        return _PALETTE_PRESETS["minimalist"]
    if any(k in kw for k in ("工业", "industrial", "loft")):
        return _PALETTE_PRESETS["industrial"]
    if any(k in kw for k in ("中式", "新中式", "chinese")):
        return _PALETTE_PRESETS["modern_chinese"]
    return _PALETTE_PRESETS["default"]


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
