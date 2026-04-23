"""scene artifact · 把 project.scene dump 到 sb_dir/scene.json + fe_data/mvps/<slug>.json"""
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
    fe_root: Path = ctx["fe_root"]

    scene = project.scene or {}
    if not scene:
        return ArtifactResult(
            name="scene", status="skipped", timing_ms=int((time.time()-t0)*1000),
            reason="project.scene 为空 · 需要 brief → 生成 scene 的上游步骤（Phase 7+）",
        )

    # 写 StartUP-Building 侧 · 给 bundle 打包用
    sb_dir.mkdir(parents=True, exist_ok=True)
    (sb_dir / "scene.json").write_text(json.dumps(scene, ensure_ascii=False, indent=2))

    # 写 Arctura-Front-end 侧 · 让 /project/<slug> 能用 Three.js 渲染
    fe_mvp_dir = fe_root / "data" / "mvps"
    fe_mvp_dir.mkdir(parents=True, exist_ok=True)
    # 如果还没 mvp JSON · 从 project 构造最小版本
    fe_path = fe_mvp_dir / f"{project.slug}.json"
    if not fe_path.exists():
        from dataclasses import asdict
        mvp_min = {
            "slug": project.slug,
            "cat": "workplace",
            "type": "P1-interior",
            "complete": True,
            "project": {
                "name": project.display_name,
                "zh": project.display_name,
                "area": (project.brief or {}).get("space", {}).get("area_sqm", 30),
                "location": "Hong Kong",
                "budgetHKD": (project.brief or {}).get("budget_hkd", 100000),
                "style": ", ".join((project.brief or {}).get("style", {}).get("keywords", [])) or "",
                "palette": [],
            },
            "renders": [],
            "floorplan": None, "moodboard": None, "hero_img": None, "thumb_img": None,
            "zones": [], "furniture": [],
            "pricing": {"HK": {"label": "Hong Kong", "currency": "HKD", "perM2": 0,
                               "rows": [], "total": "HKD 0"}},
            "energy": {"eui": 45, "limit": 150, "annual": 0, "engine": "EnergyPlus"},
            "compliance": {"HK": {"code": "HK_BEEO_BEC_2021", "label": "HK · BEEO 2021",
                                   "checks": [], "verdict": "pass"}},
            "variants": {"list": []},
            "timeline": [], "decks": [], "downloads": [],
            "editable": {"area_m2": 30, "insulation_mm": 60, "glazing_uvalue": 2.0,
                         "lighting_cct": 3000, "lighting_density_w_m2": 8, "wwr": 0.25, "region": "HK"},
            "derived": {"eui_kwh_m2_yr": 45, "cost_total": 0, "cost_per_m2": 0, "co2_t_per_yr": 0},
            "scene": scene,
        }
        fe_path.write_text(json.dumps(mvp_min, ensure_ascii=False, indent=2))
    else:
        # 已存在 · 只更新 scene 字段
        d = json.loads(fe_path.read_text())
        d["scene"] = scene
        fe_path.write_text(json.dumps(d, ensure_ascii=False, indent=2))

    return ArtifactResult(
        name="scene", status="done",
        timing_ms=int((time.time()-t0)*1000),
        output_path=f"{sb_dir / 'scene.json'} (assemblies={len(scene.get('assemblies', []))})",
    )
