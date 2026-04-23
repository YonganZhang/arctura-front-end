"""bundle artifact · ZIP 所有产物到 assets/mvps/<slug>/bundle.zip"""
from __future__ import annotations
import json
import time
import zipfile
from pathlib import Path
from typing import Callable, Optional

from ..types import ArtifactResult


def produce(ctx: dict, on_event: Optional[Callable] = None) -> ArtifactResult:
    t0 = time.time()
    project = ctx["project"]
    sb_dir: Path = ctx["sb_dir"]
    fe_root: Path = ctx["fe_root"]
    slug = project.slug

    fe_mvp_assets = fe_root / "assets" / "mvps" / slug
    fe_mvp_assets.mkdir(parents=True, exist_ok=True)
    bundle_path = fe_mvp_assets / "bundle.zip"

    file_count = 0
    with zipfile.ZipFile(bundle_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # 1. brief/scene dump
        if project.brief:
            zf.writestr(f"{slug}/brief.json",
                         json.dumps(project.brief, ensure_ascii=False, indent=2))
            file_count += 1
        if project.scene:
            zf.writestr(f"{slug}/scene.json",
                         json.dumps(project.scene, ensure_ascii=False, indent=2))
            file_count += 1
        # 2. Project meta
        from dataclasses import asdict
        zf.writestr(f"{slug}/project.json",
                     json.dumps(asdict(project), ensure_ascii=False, indent=2))
        file_count += 1

        written = set()

        # 3. sb_dir 下所有真产物（moodboard/floorplan/README 等）· 跳 renders 子目录（步 4 独占）
        if sb_dir.exists():
            for p in sb_dir.rglob("*"):
                if not p.is_file():
                    continue
                rel = p.relative_to(sb_dir)
                if rel.parts and rel.parts[0] == "renders":
                    continue  # 留给 fe_mvp_assets/renders/
                arc = f"{slug}/{rel}"
                if arc in written: continue
                zf.write(p, arcname=arc)
                written.add(arc)
                file_count += 1

        # 4. 渲染图（在 fe_mvp_assets/renders/ 下）· 权威路径
        renders_dir = fe_mvp_assets / "renders"
        if renders_dir.exists():
            for p in renders_dir.glob("*.png"):
                arc = f"{slug}/renders/{p.name}"
                if arc in written: continue
                zf.write(p, arcname=arc)
                written.add(arc)
                file_count += 1

    # 不再内部 emit artifact_done · 由 pipeline 统一 emit（避免重复）
    return ArtifactResult(
        name="bundle", status="done",
        timing_ms=int((time.time()-t0)*1000),
        output_path=f"/assets/mvps/{slug}/bundle.zip",
        meta={
            "files": file_count,
            "size_kb": round(bundle_path.stat().st_size / 1024, 1),
        },
    )
