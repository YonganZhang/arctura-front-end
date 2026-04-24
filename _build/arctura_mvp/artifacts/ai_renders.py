"""ai_renders · fal.ai fast-sdxl img2img 写实化 Blender 渲染（Phase 9.1 · 2026-04-24）

spec L93-127 · P4 AI Render Enhancement · 体块 render → 写实效果图

实装（LIGHT · 本机无 GPU）：
  1. 读 renders/ 里 Playwright 产的 8 张 Three.js 截图
  2. 每张上传 fal.ai · 调 fal-ai/fast-sdxl img2img
  3. prompt 用严老师 brief_to_prompt.build_prompt()（跨字段 dedupe + 自适应 negative）
  4. 输出到 renders-ai/<原文件名>
  5. 跳俯视图（spec L128 · AI 写实化不适合）

成本参考：~$0.008/图 · 8 张 ≈ $0.06
时间参考：10-15s/图 · 并发 4 · 8 张 ≈ 30-60s

降级：
  - fal-client 未装 / FAL_KEY 缺 → skipped + _TODO
  - 单图失败继续下一张 · 不 block 整 artifact
"""
from __future__ import annotations
import concurrent.futures
import os
import time
import urllib.request
from pathlib import Path
from typing import Callable, Optional

from ..types import ArtifactResult
from ..paths import ensure_playbook_script_subdir_on_path

# 严老师 brief_to_prompt · 跨字段 dedupe + negative 自适应
ensure_playbook_script_subdir_on_path("ai_render")

_MODEL = os.environ.get("ARCTURA_FAL_MODEL", "fal-ai/fast-sdxl")
_STRENGTH = float(os.environ.get("ARCTURA_FAL_STRENGTH", "0.8"))
_STEPS = int(os.environ.get("ARCTURA_FAL_STEPS", "15"))
_MAX_PARALLEL = int(os.environ.get("ARCTURA_FAL_PARALLEL", "4"))
_SKIP_TOKENS = ("ortho", "birds_eye", "top_down", "07_top", "08_birds")


def _is_skipped_view(filename: str) -> bool:
    name = filename.lower()
    return any(tok in name for tok in _SKIP_TOKENS)


def _build_prompts(project) -> tuple[str, str]:
    """调严老师 brief_to_prompt · fallback 到最小 prompt"""
    try:
        from brief_to_prompt import build_prompt   # type: ignore
        return build_prompt(project.brief or {}, project.scene)
    except Exception:
        # 降级
        style = (project.brief or {}).get("style", {}) if project.brief else {}
        kws = ", ".join(style.get("keywords", [])[:3]) if isinstance(style, dict) else ""
        pos = f"{kws}, interior design, photo-realistic, architectural photography, 8k uhd" \
              if kws else "photo-realistic interior, 8k uhd, architectural photography"
        neg = "low quality, blurry, cartoon, wireframe, text, watermark, distorted"
        return pos, neg


def _render_one(src: Path, dst: Path, positive: str, negative: str) -> dict:
    """对单张图调 fal.ai · 成功下载保存 · 返结果 dict"""
    import fal_client
    t0 = time.time()
    try:
        img_url = fal_client.upload_file(str(src))
        result = fal_client.subscribe(
            _MODEL,
            arguments={
                "prompt": positive,
                "negative_prompt": negative,
                "image_url": img_url,
                "strength": _STRENGTH,
                "num_inference_steps": _STEPS,
                "image_size": "square_hd",
            },
            with_logs=False,
        )
        imgs = result.get("images") or []
        if not imgs:
            return {"name": src.name, "ok": False, "error": "no image returned"}
        # 下载 fal 返的图
        out_url = imgs[0]["url"]
        dst.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(out_url, dst)
        return {
            "name": src.name,
            "ok": True,
            "size_kb": round(dst.stat().st_size / 1024, 1),
            "timing_s": round(time.time() - t0, 1),
        }
    except Exception as e:
        return {"name": src.name, "ok": False, "error": str(e)[:200]}


def produce(ctx: dict, on_event: Optional[Callable] = None) -> ArtifactResult:
    t0 = time.time()
    project = ctx["project"]
    fe_root: Path = ctx["fe_root"]

    # fal-client 是否可用
    try:
        import fal_client  # noqa: F401
    except ImportError:
        return ArtifactResult(
            name="ai_renders", status="skipped",
            timing_ms=int((time.time()-t0)*1000),
            reason="fal-client 未装 · `pip install --user fal-client`",
        )

    if not os.environ.get("FAL_KEY"):
        return ArtifactResult(
            name="ai_renders", status="skipped",
            timing_ms=int((time.time()-t0)*1000),
            reason="FAL_KEY 未设 · source ~/.arctura-env 或 api-credentials.md",
        )

    # 源 renders · 跟 renders artifact 同路径
    src_dir = fe_root / "assets" / "mvps" / project.slug / "renders"
    if not src_dir.exists():
        return ArtifactResult(
            name="ai_renders", status="skipped",
            timing_ms=int((time.time()-t0)*1000),
            reason="源 renders/ 不存在 · 需先跑 renders artifact",
        )

    src_imgs = sorted([p for p in src_dir.glob("*.png") if not _is_skipped_view(p.name)])
    if not src_imgs:
        return ArtifactResult(
            name="ai_renders", status="skipped",
            timing_ms=int((time.time()-t0)*1000),
            reason=f"{src_dir} 无可用 PNG（跳俯视后 0）",
        )

    out_dir = fe_root / "assets" / "mvps" / project.slug / "renders-ai"
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1 次 prompt · 给所有图用
    positive, negative = _build_prompts(project)

    # 并发调 fal（_MAX_PARALLEL · 默认 4）
    results: list[dict] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=_MAX_PARALLEL) as ex:
        futures = {
            ex.submit(_render_one, src, out_dir / src.name, positive, negative): src
            for src in src_imgs
        }
        for future in concurrent.futures.as_completed(futures, timeout=600):
            r = future.result()
            results.append(r)
            if on_event:
                on_event(
                    "artifact_progress",
                    {"artifact": "ai_renders", "detail": r},
                )

    ok_count = sum(1 for r in results if r.get("ok"))
    if ok_count == 0:
        return ArtifactResult(
            name="ai_renders", status="error",
            timing_ms=int((time.time()-t0)*1000),
            error={
                "name": "all_fal_fail",
                "trace_tail": "; ".join(r.get("error", "") for r in results if not r.get("ok"))[:400],
            },
        )

    return ArtifactResult(
        name="ai_renders", status="done",
        timing_ms=int((time.time()-t0)*1000),
        output_path=str(out_dir),
        meta={
            "count": ok_count,
            "total_source": len(src_imgs),
            "skipped_top_views": sum(1 for p in src_dir.glob("*.png") if _is_skipped_view(p.name)),
            "model": _MODEL,
            "strength": _STRENGTH,
            "steps": _STEPS,
            "prompt_source": "严老师 brief_to_prompt.build_prompt",
            "positive_prompt_preview": positive[:180],
            "approx_cost_usd": round(ok_count * 0.008, 3),
            "failures": [r for r in results if not r.get("ok")] or None,
        },
    )
