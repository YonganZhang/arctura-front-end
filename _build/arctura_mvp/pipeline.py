"""pipeline.run() · Arctura MVP 生成主调度

输入: project (KV 读到的 Project dataclass)
输出: MVPResult
副作用: 写 sb_dir + fe assets · 推 on_event 进度

错误策略:
- 单 artifact 失败 → 累加 errors · 继续
- core artifacts (scene/bundle) 失败 → partial=True 但不中断
- 致命 (project 非法 state) → 抛异常

MCP-friendly: 纯函数 · on_event hook · dry_run 支持
"""
from __future__ import annotations
import time
from dataclasses import asdict
from pathlib import Path
from typing import Callable, Optional

from .types import Project, MVPResult, ArtifactResult
from .tiers import resolve_tier
from .artifacts import get_artifact

_REPO_ROOT = Path(__file__).resolve().parents[2]  # Arctura-Front-end/
_STARTUP_BUILDING = _REPO_ROOT.parent / "StartUP-Building"


def run(project: Project, *,
        on_event: Optional[Callable[[str, dict], None]] = None,
        dry_run: bool = False,
        base_url: str = "https://arctura-front-end.vercel.app",
        render_base_url: Optional[str] = None) -> MVPResult:
    """主 pipeline · resolve tier → 遍历 artifacts → 推事件 → 返 MVPResult

    base_url · 产物里面填的公开 URL（mvp_page / bundle）· 默认 prod
    render_base_url · Playwright 调哪个 URL 去截图 · 默认 = base_url
                     worker 跑本机时应传 localhost（见 local_server.ensure_running）
    """

    def emit(evt: str, data: dict):
        if on_event:
            try: on_event(evt, data)
            except Exception: pass

    t0 = time.time()
    emit("start", {"slug": project.slug, "tier": project.tier, "dry_run": dry_run})

    if not project.tier:
        emit("error", {"message": "project.tier 未设"})
        return MVPResult(
            slug=project.slug, tier="(missing)", variant_count=1, render_engine="fast",
            errors=[{"name": "pipeline", "exception": "tier_missing",
                     "trace_tail": "project.tier must be set before pipeline.run"}],
            partial=True, timing_ms={"total": int((time.time()-t0)*1000)},
        )

    resolved = resolve_tier(project.tier, project.variant_count or 1)
    artifacts_list = resolved["artifacts"] + ["bundle"]  # bundle 永远最后
    engine = project.render_engine or resolved["render_engine_default"]

    emit("plan", {
        "artifacts": artifacts_list,
        "engine": engine,
        "estimated_min": resolved.get("estimated_min", {}).get(engine),
    })

    # 准备 ctx · 所有 artifact 共享
    sb_dir = _STARTUP_BUILDING / "studio-demo" / "mvp" / project.slug
    sb_dir.mkdir(parents=True, exist_ok=True)
    ctx = {
        "project": project,
        "tier_resolved": resolved,
        "sb_dir": sb_dir,
        "fe_root": _REPO_ROOT,
        "base_url": base_url,
        "render_base_url": render_base_url or base_url,
        "dry_run": dry_run,
    }

    produced: list[str] = []
    skipped: list[dict] = []
    errors: list[dict] = []
    per_timing: dict[str, int] = {}

    for artifact_name in artifacts_list:
        if dry_run:
            emit("artifact_skip_dry_run", {"name": artifact_name})
            skipped.append({"name": artifact_name, "reason": "dry_run"})
            continue

        handler = get_artifact(artifact_name)
        if handler is None:
            emit("artifact_skip_unimplemented", {"name": artifact_name})
            skipped.append({"name": artifact_name,
                             "reason": "artifact 未实装（Phase 7+ 补）"})
            continue

        emit("artifact_start", {"name": artifact_name})
        t_start = time.time()
        try:
            result: ArtifactResult = handler(ctx, on_event=on_event)
            per_timing[artifact_name] = result.timing_ms or int((time.time() - t_start) * 1000)
            if result.status == "done":
                produced.append(artifact_name)
                emit("artifact_done", {"name": artifact_name,
                                         "timing_ms": per_timing[artifact_name],
                                         "meta": result.meta or {},
                                         "output_path": result.output_path})
            elif result.status == "skipped":
                skipped.append({"name": artifact_name, "reason": result.reason or "skipped"})
                emit("artifact_skipped", {"name": artifact_name, "reason": result.reason})
            else:  # error
                errors.append({"name": artifact_name, **(result.error or {})})
                emit("artifact_error", {"name": artifact_name, "error": result.error})
        except Exception as e:
            import traceback
            err = {"name": artifact_name, "exception": type(e).__name__,
                   "trace_tail": traceback.format_exc()[-400:]}
            errors.append(err)
            per_timing[artifact_name] = int((time.time() - t_start) * 1000)
            emit("artifact_error", err)

    total_ms = int((time.time() - t0) * 1000)
    partial = len(errors) > 0 or len(skipped) > 0

    # 回填 project.artifacts · 调用方可 save
    slug = project.slug
    urls = {
        "mvp_page": f"{base_url}/project/{slug}",
        "bundle": f"/assets/mvps/{slug}/bundle.zip",
    }
    # 如果有 renders · 挂 hero
    renders_dir = _REPO_ROOT / "assets" / "mvps" / slug / "renders"
    if renders_dir.exists():
        pngs = sorted(renders_dir.glob("*.png"))
        if pngs:
            urls["hero_img"] = f"/assets/mvps/{slug}/renders/{pngs[0].name}"
    if (sb_dir / "floorplan.png").exists():
        urls["floorplan"] = f"/assets/mvps/{slug}/floorplan.png"
    if (sb_dir / "moodboard.png").exists():
        urls["moodboard"] = f"/assets/mvps/{slug}/moodboard.png"

    result = MVPResult(
        slug=project.slug,
        tier=project.tier,
        variant_count=project.variant_count or 1,
        render_engine=engine,
        produced=produced,
        skipped=skipped,
        errors=errors,
        partial=partial,
        urls=urls,
        timing_ms={"total": total_ms, "per_artifact": per_timing},
    )

    emit("complete", asdict(result))
    return result


def dry_run(project: Project, **kwargs) -> MVPResult:
    """dry_run = 只计划 · 不写文件"""
    return run(project, dry_run=True, **kwargs)
