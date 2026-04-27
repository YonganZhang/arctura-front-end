"""MVP 生成 worker · 本机 tencent-hk 跑（systemd 或手动）

流程:
  1. brpop jobs:queue · 拿 job
  2. 读 project:<slug> · load Project
  3. 更新 state=generating · 写 KV
  4. 跑 pipeline.run · on_event push 到 job:<id>:events list
  5. 跑完: state=live · 写 artifacts · 清 queue

job 格式:
  {id, slug, tier, variant_count, render_engine?, queued_at}

运行:
  source ~/.arctura-env
  python3 -m _build.arctura_mvp.worker
"""
from __future__ import annotations
import json
import os
import sys
import time
import traceback
from dataclasses import asdict
from pathlib import Path

from . import _core
from . import pipeline
from .store import kv, keys as K
from .store.kv import KVError
from .types import utc_now
from .local_server import ensure_running as ensure_local_server
from .paths import REPO_ROOT, STARTUP_BUILDING_ROOT
from .materializer import build_fe_payload
from .blob_push import upload_mvp_assets  # Phase 9.8 · 资产走 Blob · 不再 git push

# Phase 10.5 · 写 KV final state 失败时的本地磁盘兜底（rescue 脚本可扫这里扶正）
STATE_CACHE_DIR = REPO_ROOT / "_build" / "_state-cache"


# Phase 9.4 · 发布门槛 · 关键产物清单（缺 → state=generating_failed · 不置 live）
ESSENTIAL_CORE = {"scene", "moodboard", "floorplan", "renders"}
ESSENTIAL_FULL = ESSENTIAL_CORE | {"deck_client", "client_readme", "exports", "energy_report", "case_study"}

POLL_INTERVAL = 2  # 无 job 时每 2s poll · Upstash REST 没 blocking pop
MAX_EVENT_LIST = 500  # job:<id>:events 最多留 500 事件

# Heartbeat · 每 30s 写 worker:<host>:heartbeat · TTL 120s（容忍 4 拍）
HEARTBEAT_INTERVAL = 30
HEARTBEAT_TTL = 120
HOSTNAME = os.environ.get("HOSTNAME") or os.uname().nodename

# Worker 自起一个本机 static server · Playwright 调 localhost 拿实时 MVP 数据
# 覆盖：ARCTURA_RENDER_BASE_URL env 环境变量 · 或 job dict 带 render_base_url 字段


def push_event(job_id: str, evt: str, data: dict):
    """把 on_event 推到 KV list · SSE endpoint 读"""
    payload = json.dumps({"event": evt, "data": data, "ts": time.time()}, ensure_ascii=False)
    try:
        kv.rpush(K.job_events(job_id), payload)
        # 首次推事件时设 TTL · 7 天后自动清理
        kv.expire(K.job_events(job_id), 7 * 86400)
    except Exception as e:
        print(f"[worker] push_event fail: {e}", file=sys.stderr)


def _set_job_status(job_id: str, status: str, extra: dict = None):
    """更新 job:<id> 元数据 · status = queued|running|done|error"""
    try:
        raw = kv.get(K.job(job_id))
        meta = json.loads(raw) if raw else {}
        meta["status"] = status
        meta["status_at"] = time.time()
        if extra:
            meta.update(extra)
        kv.set_json(K.job(job_id), meta, ex=7 * 86400)
    except Exception as e:
        print(f"[worker] set_job_status fail: {e}", file=sys.stderr)


def _err_dict(where: str, exc: Exception, **ctx) -> dict:
    """统一错误字典 · 给 on_event / set_job_status 共用 · 前端拿到这个 schema"""
    d = {
        "where": where,
        "code": getattr(exc, "code", None) or type(exc).__name__,
        "message": str(exc)[:500],
        "trace_tail": traceback.format_exc()[-1500:],
        "context": ctx,
    }
    if isinstance(exc, KVError):
        d["kv"] = exc.to_dict()
    return d


def _persist_state_with_fallback(project, job_id: str, on_event) -> dict:
    """写 final state · KV 失败时**本地磁盘兜底** · 不让整个 job 进 fatal 路径

    这是 Phase 10.5 关键修复：4-25 全案 fatal 根因 = 产物全跑完 · 最后一步写 KV SSL EOF
    → 整个 run_one 进 except → user 看到失败 · 但产物在磁盘已经成功。
    """
    state_dump = asdict(project)
    STATE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = STATE_CACHE_DIR / f"{job_id}.json"
    try:
        cache_file.write_text(json.dumps(state_dump, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"[worker] state cache disk write fail (non-fatal): {e}", file=sys.stderr)

    try:
        _core.put_project(project, expected_version=project.version)
        # KV 写成功 · 删除磁盘兜底（不再需要救援）
        try:
            cache_file.unlink(missing_ok=True)
        except Exception:
            pass
        return {"persisted": "kv", "kv_ok": True}
    except Exception as e:
        # KV 失败但本地磁盘已写 · 救援脚本可扫 _state-cache/ 扶正
        err = _err_dict("worker.persist_state.put_project", e,
                        slug=project.slug, state=project.state,
                        version=project.version, cache_file=str(cache_file))
        print(f"[worker] put_project fail (state={project.state}) · 已落盘 {cache_file} · err={err['message']}",
              file=sys.stderr)
        on_event("persist_kv_fail", err)
        return {"persisted": "disk_only", "kv_ok": False, "cache_file": str(cache_file), "error": err}


def run_one(job: dict):
    """跑一个 job · 不抛异常 · 各 step 独立报错（不让 final-state KV 抖断把全 job 标 error）"""
    job_id = job["id"]
    slug = job["slug"]
    current_step = "init"  # 给 fatal handler 报"挂在哪一步"

    def on_event(evt, data):
        push_event(job_id, evt, data)

    _set_job_status(job_id, "running", {"started_at": time.time()})

    try:
        current_step = "load_project"
        project = _core.get_project(slug)
        if not project:
            on_event("error", _err_dict("worker.run_one.load_project",
                                          ValueError(f"project {slug} not found"),
                                          slug=slug, job_id=job_id))
            _set_job_status(job_id, "error", {"error": "project not found", "where": "load_project"})
            return

        # 推进 state → generating（如未进）
        current_step = "advance_state_generating"
        if project.state != "generating":
            project.state = "generating"
            _core.put_project(project, expected_version=project.version)

        on_event("job_picked", {"job_id": job_id, "slug": slug, "tier": job["tier"],
                                  "variant_count": project.variant_count,
                                  "render_engine": project.render_engine,
                                  "brief_summary": _brief_summary(project.brief)})

        current_step = "pipeline_run"

        # 跑 pipeline（可能 mutate project.scene · 见 scene artifact 生成回填）
        # render_base_url 优先级：env ARCTURA_RENDER_BASE_URL > 本机 static server > 公开 base_url
        render_base = os.environ.get("ARCTURA_RENDER_BASE_URL")
        if not render_base:
            try:
                render_base = ensure_local_server()
            except Exception as e:
                print(f"[worker] local server start fail: {e} · 退回 prod 渲染",
                      file=sys.stderr)
                render_base = None
        result = pipeline.run(project, on_event=on_event, render_base_url=render_base)
        generated_scene = project.scene   # 保留 pipeline mutate 后的结果

        # 更新 project · 写 artifacts · state=live
        current_step = "reload_project_for_state_write"
        project = _core.get_project(slug)  # 拿最新 version
        if generated_scene and not project.scene:
            project.scene = generated_scene   # pipeline 新生成的 scene · 回填到 KV
        artifacts_meta = asdict(result).get("artifacts") or {
            "produced": result.produced,
            "skipped": result.skipped,
            "errors": result.errors,
            "partial": result.partial,
            "timing_ms": result.timing_ms,
            "urls": result.urls,
        }

        # Phase 9.4 + 9.8 · Materializer · 扫磁盘真产物 → 组前端 JSON payload
        # 9.8 · 资产先上传 Vercel Blob · URL 指 CDN · 前端不等 Vercel redeploy
        current_step = "blob_upload"
        sb_dir = STARTUP_BUILDING_ROOT / "studio-demo" / "mvp" / slug
        asset_urls = None
        try:
            asset_urls = upload_mvp_assets(slug, sb_dir, REPO_ROOT)
            meta = asset_urls.get("_meta") or {}
            on_event("blob_uploaded", {
                "slug": slug,
                "uploaded": meta.get("uploaded"),
                "failed": meta.get("failed"),
                "timing_ms": meta.get("timing_ms"),
                "errors": meta.get("errors"),
            })
        except Exception as e:
            # Blob 挂了不 block · materializer 会降级走老本地路径（用户仍能看 · 只是是破图风险）
            err = _err_dict("worker.run_one.blob_upload", e,
                            slug=slug, sb_dir=str(sb_dir))
            print(f"[worker] blob upload fail: {e}", file=sys.stderr)
            on_event("blob_upload_fail", err)
            asset_urls = None

        current_step = "materialize"
        try:
            fe_payload = build_fe_payload(
                sb_dir, slug, REPO_ROOT,
                mvp_type="P1-interior",
                agg={},  # worker 不走聚合批量 · 让 materializer 读 metrics.json fallback
                asset_urls=asset_urls,  # Phase 9.8 · 有 Blob URL 就用 · 没就 fallback 老 /assets/
            )
            artifacts_meta["fe_payload"] = fe_payload
            artifacts_meta["asset_urls_source"] = "blob" if asset_urls and asset_urls.get("_meta", {}).get("uploaded") else "local"

            # 本机写盘 · 让 localhost:8787/project/<slug> 立刻能看到真内容
            fe_json = REPO_ROOT / "data" / "mvps" / f"{slug}.json"
            fe_json.parent.mkdir(parents=True, exist_ok=True)
            fe_json.write_text(
                json.dumps(fe_payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            on_event("materialized", {
                "slug": slug,
                "renders": len(fe_payload.get("renders", [])),
                "decks": len(fe_payload.get("decks", [])),
                "downloads": len(fe_payload.get("downloads", [])),
                "eui": (fe_payload.get("energy") or {}).get("eui"),
                "compliance_checks": len(((fe_payload.get("compliance") or {}).get("HK") or {}).get("checks") or []),
            })
        except Exception as e:
            # 降级 · 不 block live · 记 log + on_event 让前端能看到
            err = _err_dict("worker.run_one.materialize", e, slug=slug)
            print(f"[worker] materialize fail: {e}", file=sys.stderr)
            on_event("materialize_fail", err)

        # Phase 9.8 · 不再 git push / vercel deploy · 资产已在 Blob · KV fe_payload 已写
        # · 用户刷 /project/<slug> · KV fallback 返 fe_payload · URL 指 Blob CDN · 秒级可见
        project.artifacts = artifacts_meta

        # Phase 9.4 · 发布门槛 · 按 essential 产物 + partial/errors 判定 state
        essential = ESSENTIAL_FULL if project.tier == "full" else ESSENTIAL_CORE
        produced_set = set(result.produced or [])
        missing_essential = essential - produced_set
        if missing_essential:
            project.state = "generating_failed"
        elif result.partial or result.errors:
            project.state = "live_partial"
        else:
            project.state = "live"

        project.render_engine = result.render_engine
        project.active_job_id = None   # Phase 7.1 · 生命周期闭合

        # Phase 10.5 关键修复 · 写 final state 用磁盘兜底 · KV 失败不进 fatal 路径
        current_step = "persist_final_state"
        persist_info = _persist_state_with_fallback(project, job_id, on_event)

        # done event 永远发 · 即使 KV 写挂了 · 产物本身已经成功
        on_event("done", {"job_id": job_id, "state": project.state,
                            "produced": result.produced, "partial": result.partial,
                            "missing_essential": sorted(missing_essential) or None,
                            "urls": result.urls,
                            "persisted": persist_info.get("persisted")})
        _set_job_status(job_id, "done" if persist_info["kv_ok"] else "done_disk_only", {
            "finished_at": time.time(),
            "produced": result.produced,
            "partial": result.partial,
            "state": project.state,
            "missing_essential": sorted(missing_essential) or None,
            "persist_info": persist_info,
        })
    except Exception as e:
        # 真正的 fatal 路径 · 上面任意 step 出错（含 _persist_state_with_fallback 之外的）
        err = _err_dict(f"worker.run_one[step={current_step}]", e,
                        slug=slug, job_id=job_id, tier=job.get("tier"),
                        variant_count=job.get("variant_count"))
        on_event("fatal", err)
        _set_job_status(job_id, "error", {
            "finished_at": time.time(),
            "where": current_step,
            "exception": type(e).__name__,
            "trace_tail": err["trace_tail"],
        })
        # 最佳努力清 active_job_id · 失败也不抛
        try:
            p = _core.get_project(slug)
            if p and p.active_job_id == job_id:
                p.active_job_id = None
                _core.put_project(p, expected_version=p.version)
        except Exception:
            pass


def _brief_summary(brief) -> dict:
    """从 Project.brief 拎几个关键字段给 job_picked event · 出错时方便看输入"""
    if not brief:
        return {}
    if not isinstance(brief, dict):
        try:
            brief = asdict(brief)
        except Exception:
            return {"_error": "brief not serializable"}
    return {
        "type": brief.get("type"),
        "area_m2": brief.get("area_m2"),
        "headcount": brief.get("headcount"),
        "style": brief.get("style"),
        "must_fill_complete": brief.get("must_fill_complete"),
    }


def _beat():
    """写一次 heartbeat · TTL 120s · 加入 workers:index · 静默错"""
    try:
        kv.set(K.worker_heartbeat(HOSTNAME), str(time.time()), ex=HEARTBEAT_TTL)
        kv.zadd(K.workers_index(), time.time(), HOSTNAME)
    except Exception as e:
        print(f"[worker] heartbeat fail: {e}", file=sys.stderr)


def main_loop(max_iter: int = None):
    """poll jobs:queue · iter_count 控制跑几轮（None 永远）· 手动测时限量

    heartbeat 每 HEARTBEAT_INTERVAL s 写一次 · SSE 探活用
    """
    print(f"[worker] started · host={HOSTNAME} · polling {K.jobs_queue()} every {POLL_INTERVAL}s")
    _beat()   # 启动即刻写一次
    last_beat = time.time()
    it = 0
    while True:
        if max_iter is not None and it >= max_iter:
            break
        it += 1
        # 定时 heartbeat
        if time.time() - last_beat >= HEARTBEAT_INTERVAL:
            _beat()
            last_beat = time.time()
        try:
            # Upstash REST 不支持 brpop · 用 rpop 轮询
            raw = kv.rpop(K.jobs_queue())
            if raw is None:
                time.sleep(POLL_INTERVAL)
                continue
            job = json.loads(raw)
            print(f"[worker] picked job: {job.get('id')} · {job.get('slug')} · tier={job.get('tier')}")
            run_one(job)
        except KeyboardInterrupt:
            print("[worker] stopped by user"); break
        except Exception as e:
            print(f"[worker] loop err: {e}", file=sys.stderr)
            time.sleep(5)


if __name__ == "__main__":
    main_loop()
