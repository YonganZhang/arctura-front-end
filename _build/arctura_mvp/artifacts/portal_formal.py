"""portal_formal · Phase 12.末.C · 复用老师 studio-demo/ 顶层全局聚合产物

老师真有(我之前完全没接):
  studio-demo/ALL-MVPS-ENERGY-BOQ.json · 全 36 MVP 能耗 + BOQ 汇总
  studio-demo/ALL-MVPS-SUMMARY.md · 全 summary
  studio-demo/MVP-SPECS.md · MVP 规格清单
  studio-demo/ARCH-MVP-SPECS.md · architecture MVP 规格
  studio-demo/_qa-visual-5mvps.md · QA 视觉对比

这些是**跨 MVP 全局聚合** · 不是单 MVP 产物。worker 跑全 pipeline 时复用。
"""
from __future__ import annotations
import shutil, time
from pathlib import Path
from typing import Callable, Optional
from ..types import ArtifactResult


def _find_studio_demo() -> Optional[Path]:
    try:
        from ..paths import STARTUP_BUILDING_ROOT
        sd = STARTUP_BUILDING_ROOT / "studio-demo"
        return sd if sd.exists() else None
    except Exception:
        return None


def produce(ctx, *, on_event: Optional[Callable] = None) -> ArtifactResult:
    """全局聚合 portal · 不读 brief · copy 老师 5 顶层文件"""
    t0 = time.time()
    sb_dir = Path(ctx.get("sb_dir") or ".")
    sd = _find_studio_demo()
    if sd is None:
        return ArtifactResult(
            name="portal", status="skipped",
            timing_ms=int((time.time() - t0) * 1000),
            reason="StartUP-Building/studio-demo 不可达 · 跳过聚合产物",
        )

    portal_dir = sb_dir / "_portal"
    portal_dir.mkdir(parents=True, exist_ok=True)
    files = ["ALL-MVPS-ENERGY-BOQ.json", "ALL-MVPS-SUMMARY.md",
             "MVP-SPECS.md", "ARCH-MVP-SPECS.md", "_qa-visual-5mvps.md"]
    copied = []
    for f in files:
        src = sd / f
        if src.exists():
            shutil.copy2(src, portal_dir / f)
            copied.append(f)

    if on_event:
        on_event("portal_v3_reused", {"copied": len(copied), "src": str(sd)})

    return ArtifactResult(
        name="portal", status="done" if copied else "skipped",
        timing_ms=int((time.time() - t0) * 1000),
        output_path=str(portal_dir),
        meta={
            "engine": "formal",
            "mode": "v3_golden_reuse",
            "files_count": len(copied),
            "copied": copied,
            "policy": "v3 全局聚合 · 复用老师 studio-demo/ 顶层产物",
        },
    )
