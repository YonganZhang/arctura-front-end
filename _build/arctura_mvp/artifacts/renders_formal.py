"""renders_formal · Phase 12.D.2 · 读 scene_formal 已生成的 8 张 PNG

scene_formal(D.1)已经在 sb_dir/renders/ 生成 8 张真 Blender 渲染 PNG ·
renders artifact 的 formal 实装就是验产物 + 返 result · 不用重复跑 Blender。

依赖:
  - scene_formal 必须先跑 · 写 sb_dir/renders/{01_hero_corner..08_birds_eye_3d}.png
  - depends_on=["scene"] 在 product_registry 已锁

跟 LIGHT renders.py 区别:
  - LIGHT: Three.js Playwright 截 8 张近似光追(浏览器跑)
  - FORMAL: 真 Blender Eevee Next 渲染(scene_formal 已产)· 真照片级
"""
from __future__ import annotations
import time
from pathlib import Path
from typing import Callable, Optional

from ..types import ArtifactResult


EXPECTED_RENDERS = [
    "01_hero_corner",
    "02_reception",
    "03_main_zone",
    "04_feature_zone",
    "05_lounge_zone",
    "06_back_corner",
    "07_top_ortho",
    "08_birds_eye_3d",
]


def produce(ctx, *, on_event: Optional[Callable] = None) -> ArtifactResult:
    """读 scene_formal 已生成的 8 张真 PNG · 返 ArtifactResult"""
    t0 = time.time()
    sb_dir = Path(ctx.get("sb_dir") or ".")
    render_dir = sb_dir / "renders"

    if not render_dir.exists():
        return ArtifactResult(
            name="renders", status="skipped",
            timing_ms=int((time.time() - t0) * 1000),
            reason="renders/ 目录缺 · scene_formal 必须先跑 · depends_on=[scene]",
        )

    found = []
    missing = []
    for name in EXPECTED_RENDERS:
        p = render_dir / f"{name}.png"
        if p.exists() and p.stat().st_size > 1000:  # 至少 1KB · 防空 PNG
            found.append({"id": name.split("_")[0], "tag": name, "file": str(p),
                          "size_kb": round(p.stat().st_size / 1024, 1)})
        else:
            missing.append(name)

    if len(found) < 4:  # 至少 4 张才算 OK
        return ArtifactResult(
            name="renders", status="error",
            timing_ms=int((time.time() - t0) * 1000),
            error={
                "name": "insufficient_renders",
                "trace_tail": f"found {len(found)}/{len(EXPECTED_RENDERS)} · missing: {missing}",
            },
        )

    if on_event:
        on_event("renders_formal_collected", {
            "count": len(found),
            "missing_count": len(missing),
            "engine": "Blender 4.5.9 EEVEE_NEXT",
        })

    return ArtifactResult(
        name="renders", status="done",
        timing_ms=int((time.time() - t0) * 1000),
        output_path=str(render_dir),
        meta={
            "engine": "formal",
            "count": len(found),
            "files": found,
            "missing": missing,
            "blender_version": "4.5.9",
            "render_engine": "BLENDER_EEVEE_NEXT",
        },
    )
