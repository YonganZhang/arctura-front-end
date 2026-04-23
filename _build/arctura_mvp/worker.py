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

from . import _core
from . import pipeline
from .store import kv, keys as K
from .types import utc_now

POLL_INTERVAL = 2  # 无 job 时每 2s poll · Upstash REST 没 blocking pop
MAX_EVENT_LIST = 500  # job:<id>:events 最多留 500 事件


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


def run_one(job: dict):
    """跑一个 job · 不抛异常"""
    job_id = job["id"]
    slug = job["slug"]

    def on_event(evt, data):
        push_event(job_id, evt, data)

    _set_job_status(job_id, "running", {"started_at": time.time()})

    try:
        project = _core.get_project(slug)
        if not project:
            on_event("error", {"message": f"project {slug} not found"})
            _set_job_status(job_id, "error", {"error": "project not found"})
            return

        # 推进 state → generating（如未进）
        if project.state != "generating":
            project.state = "generating"
            _core.put_project(project, expected_version=project.version)

        on_event("job_picked", {"job_id": job_id, "slug": slug, "tier": job["tier"]})

        # 跑 pipeline
        result = pipeline.run(project, on_event=on_event)

        # 更新 project · 写 artifacts · state=live
        project = _core.get_project(slug)  # 拿最新 version
        project.artifacts = asdict(result).get("artifacts") or {
            "produced": result.produced,
            "skipped": result.skipped,
            "errors": result.errors,
            "partial": result.partial,
            "timing_ms": result.timing_ms,
            "urls": result.urls,
        }
        project.state = "live"
        project.render_engine = result.render_engine
        project.active_job_id = None   # Phase 7.1 · 生命周期闭合
        _core.put_project(project, expected_version=project.version)

        on_event("done", {"job_id": job_id, "state": "live",
                            "produced": result.produced, "partial": result.partial,
                            "urls": result.urls})
        _set_job_status(job_id, "done", {
            "finished_at": time.time(),
            "produced": result.produced,
            "partial": result.partial,
        })
    except Exception as e:
        trace = traceback.format_exc()[-400:]
        on_event("fatal", {"job_id": job_id, "exception": type(e).__name__, "trace_tail": trace})
        _set_job_status(job_id, "error", {
            "finished_at": time.time(),
            "exception": type(e).__name__,
            "trace_tail": trace,
        })
        # 最佳努力清 active_job_id · 失败也不抛
        try:
            p = _core.get_project(slug)
            if p and p.active_job_id == job_id:
                p.active_job_id = None
                _core.put_project(p, expected_version=p.version)
        except Exception:
            pass


def main_loop(max_iter: int = None):
    """poll jobs:queue · iter_count 控制跑几轮（None 永远）· 手动测时限量"""
    print(f"[worker] started · polling {K.jobs_queue()} every {POLL_INTERVAL}s")
    it = 0
    while True:
        if max_iter is not None and it >= max_iter:
            break
        it += 1
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
