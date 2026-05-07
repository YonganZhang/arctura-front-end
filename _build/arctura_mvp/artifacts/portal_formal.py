"""portal_formal v2 · Phase 12.末.G · 复用老师 studio-demo/ 顶层 + client-portal skill

v1 仅 copy studio-demo 顶层 5 文件(全局聚合 · ALL-MVPS-*)
v2 升级:命中老师 4 真 MVP → 调老师 client-portal skill 真生成 portal.html + _server.py
   (Fabric.js 2D 编辑器 + 3D viewer + render gallery + BOQ + 合规 + AI voice/text)
   不命中 → fallback v1 仅顶层聚合
"""
from __future__ import annotations
import shutil, subprocess, sys, time
from pathlib import Path
from typing import Callable, Optional
from ..types import ArtifactResult
from ..paths import STARTUP_BUILDING_ROOT, TEACHER_CLIENT_PORTAL_SKILL


def _find_studio_demo() -> Optional[Path]:
    sd = STARTUP_BUILDING_ROOT / "studio-demo"
    return sd if sd.exists() else None


def _try_teacher_client_portal_skill(mvp_dir: Path, on_event=None) -> Optional[dict]:
    """尝试调老师 client-portal skill 真生成 portal · 返 meta 字典或 None"""
    gen = TEACHER_CLIENT_PORTAL_SKILL / "scripts" / "generate_portal.py"
    if not gen.exists():
        return None
    if not (mvp_dir / "room.json").exists() and not (mvp_dir / "building.json").exists():
        return None  # generate_portal 需 room.json 或 building.json
    try:
        proc = subprocess.run(
            [sys.executable, str(gen), str(mvp_dir), "--no-server"],  # 不开 server · 仅生成
            capture_output=True, text=True, timeout=60,
        )
        if proc.returncode != 0:
            if on_event:
                on_event("client_portal_skill_fail", {
                    "stderr_tail": proc.stderr[-300:] if proc.stderr else "",
                })
            return None
        portal_html = mvp_dir / "portal.html"
        if not portal_html.exists():
            return None
        return {
            "portal_html": str(portal_html),
            "html_size": portal_html.stat().st_size,
            "skill_source": str(gen),
        }
    except Exception as e:
        if on_event:
            on_event("client_portal_skill_exc", {"err": str(e)[:200]})
        return None


def produce(ctx, *, on_event: Optional[Callable] = None) -> ArtifactResult:
    """portal_formal v2 · 全局聚合 + 单 MVP 真 portal(老师 client-portal skill)"""
    t0 = time.time()
    sb_dir = Path(ctx.get("sb_dir") or ".")
    sd = _find_studio_demo()
    if sd is None:
        return ArtifactResult(
            name="portal", status="skipped",
            timing_ms=int((time.time() - t0) * 1000),
            reason="StartUP-Building/studio-demo 不可达 · 跳过聚合产物",
        )

    # 1. 全局聚合(同 v1)
    portal_dir = sb_dir / "_portal"
    portal_dir.mkdir(parents=True, exist_ok=True)
    agg_files = ["ALL-MVPS-ENERGY-BOQ.json", "ALL-MVPS-SUMMARY.md",
                 "MVP-SPECS.md", "ARCH-MVP-SPECS.md", "_qa-visual-5mvps.md"]
    copied = []
    for f in agg_files:
        src = sd / f
        if src.exists():
            shutil.copy2(src, portal_dir / f)
            copied.append(f)

    # 2. v2 · 单 MVP portal(用老师 client-portal skill)
    portal_extras = {}
    project = ctx.get("project")
    if project and project.brief:
        from ..teacher_authority.v3_reuse import select_template_slug, _resolve_src_dir
        slug = select_template_slug(project.brief)
        if slug:
            mvp_src = _resolve_src_dir(slug)
            if mvp_src and (mvp_src / "room.json").exists():
                portal_extras = _try_teacher_client_portal_skill(sb_dir, on_event=on_event) or {}

    if on_event:
        on_event("portal_v2_done", {
            "agg_files": len(copied),
            "client_portal_skill_used": bool(portal_extras),
        })

    return ArtifactResult(
        name="portal", status="done" if copied else "skipped",
        timing_ms=int((time.time() - t0) * 1000),
        output_path=str(portal_dir),
        meta={
            "engine": "formal",
            "mode": "v3_golden_reuse",
            "files_count": len(copied),
            "copied": copied,
            "client_portal_skill": portal_extras or "未触发(brief 不命中或 skill 失败)",
            "policy": "v2 全局聚合 + 老师 client-portal skill 真 portal.html",
        },
    )
