"""exports_formal · Phase 12.末.B · v3 复用老师真 exports/

老师 03/05/13 MVP 真有 exports/:
  <slug>.{glb,fbx,ifc,obj,mtl} · floorplan.dxf · _export_*_script.py 3 个

01-study-room 老师没 exports/ · v3 不命中 → 落 LIGHT(Blender headless 真产 GLB/OBJ/FBX)
"""
from __future__ import annotations
from pathlib import Path
from typing import Callable, Optional
from ..types import ArtifactResult


def produce(ctx, *, on_event: Optional[Callable] = None) -> ArtifactResult:
    # v3 · 整目录 copy 老师真 exports/(模型 5 格式 + dxf + 3 export 脚本)
    from ..teacher_authority.v3_reuse import try_reuse
    project = ctx.get("project")
    sb_dir = Path(ctx.get("sb_dir") or ".")
    _v3 = try_reuse(
        project.brief if project else {}, "exports", sb_dir,
        dirs=["exports"],
        on_event=on_event,
    )
    if _v3:
        return _v3

    # 老师没真 exports(01-study-room) → 落 LIGHT
    if on_event:
        on_event("exports_formal_fallback_light", {
            "reason": "v3 不命中(老师 01-study-room 没 exports/)",
        })
    from .exports import produce as _light_produce
    result = _light_produce(ctx, on_event=on_event)
    if result.meta is None:
        result.meta = {}
    result.meta["engine"] = "formal"
    return result
