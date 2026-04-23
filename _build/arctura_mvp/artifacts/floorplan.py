"""floorplan artifact · SVG + PNG（rsvg-convert）"""
from __future__ import annotations
import json
import shutil
import subprocess
import time
from pathlib import Path
from typing import Callable, Optional

from ..types import ArtifactResult


def produce(ctx: dict, on_event: Optional[Callable] = None) -> ArtifactResult:
    t0 = time.time()
    project = ctx["project"]
    sb_dir: Path = ctx["sb_dir"]

    scene = project.scene or {}
    if not scene:
        return ArtifactResult(name="floorplan", status="skipped",
                               timing_ms=int((time.time()-t0)*1000),
                               reason="无 scene 不能画 floorplan")

    svg = _build_svg(project, scene)
    svg_path = sb_dir / "floorplan.svg"
    svg_path.write_text(svg)

    png_path = sb_dir / "floorplan.png"
    if shutil.which("rsvg-convert"):
        subprocess.run(["rsvg-convert", "-o", str(png_path), "-w", "1200", str(svg_path)],
                       check=False, capture_output=True)

    return ArtifactResult(name="floorplan", status="done",
                           timing_ms=int((time.time()-t0)*1000),
                           output_path=f"{svg_path} (png_exists={png_path.exists()})")


def _build_svg(project, scene: dict) -> str:
    b = scene.get("bounds", {"w": 6, "d": 5, "h": 3})
    W, D = b["w"], b["d"]
    SC = 80
    PAD = 40
    vw = int(W * SC + PAD * 2)
    vh = int(D * SC + PAD * 2 + 60)

    def tx(x): return round(PAD + (x + W / 2) * SC, 1)
    def ty(y): return round(PAD + (D / 2 - y) * SC, 1)

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{vw}" height="{vh}" viewBox="0 0 {vw} {vh}" font-family="Noto Sans SC,sans-serif">']
    parts.append(f'<rect width="{vw}" height="{vh}" fill="#F5F1E8"/>')
    parts.append(f'<rect x="{PAD}" y="{PAD}" width="{W*SC}" height="{D*SC}" fill="#FAF6ED" stroke="#5D4037" stroke-width="3"/>')
    # Zones
    mvp = project.__dict__ if hasattr(project, "__dict__") else {}
    brief = (project.brief or {}) if hasattr(project, "brief") else {}
    zones = brief.get("functional_zones", []) or []
    for z in zones:
        x, y = z.get("x", 0), z.get("y", 0)
        w, h = z.get("w", 1), z.get("h", 1)
        if not (x or y or w != 1 or h != 1):
            continue  # brief 里没坐标 · 跳
        parts.append(f'<rect x="{tx(x-w/2)}" y="{ty(y+h/2)}" width="{w*SC}" height="{h*SC}" fill="#D7C4A8" opacity="0.35" stroke="#8A7A5C" stroke-dasharray="4,3"/>')
        parts.append(f'<text x="{tx(x)}" y="{ty(y)}" fill="#3E2C26" font-size="14" text-anchor="middle">{z.get("name", "")} · {z.get("area_sqm", 0)}㎡</text>')
    # Furniture assemblies
    for a in scene.get("assemblies", []):
        pos = a.get("pos", [0, 0, 0])
        sz = a.get("size", [0.5, 0.5, 0.5])
        x0 = tx(pos[0] - sz[0] / 2)
        y0 = ty(pos[1] + sz[1] / 2)
        parts.append(f'<rect x="{x0}" y="{y0}" width="{sz[0]*SC}" height="{sz[1]*SC}" fill="#8A7A5C" opacity="0.7" stroke="#3E2C26"/>')
        parts.append(f'<text x="{tx(pos[0])}" y="{ty(pos[1])+4}" fill="#F5F1E8" font-size="10" text-anchor="middle">{a.get("label_zh","")}</text>')
    # Title + scale
    parts.append(f'<text x="{PAD}" y="{PAD-10}" fill="#3E2C26" font-size="16" font-weight="700">{project.display_name} · 平面图</text>')
    parts.append(f'<text x="{vw-PAD}" y="{PAD-10}" fill="#3E2C26" font-size="12" text-anchor="end">比例 1:50 · {W}m × {D}m</text>')
    sbar_y = vh - 30
    parts.append(f'<line x1="{PAD}" y1="{sbar_y}" x2="{PAD+SC}" y2="{sbar_y}" stroke="#3E2C26" stroke-width="2"/>')
    parts.append(f'<text x="{PAD+SC/2}" y="{sbar_y-6}" fill="#3E2C26" font-size="10" text-anchor="middle">1m</text>')
    parts.append('</svg>')
    return "".join(parts)
