"""KV key 命名单一真源 · Python 侧

对称镜像见 api/_shared/kv-keys.js（JS Edge 侧）· 改这里必须改那里 · 有双端 snapshot 测试保护。
"""
from __future__ import annotations


def project(slug: str) -> str:
    return f"project:{slug}"


def brief_history(slug: str) -> str:
    return f"project:{slug}:brief_history"


def pending_edits(slug: str) -> str:
    return f"project:{slug}:pending_edits"


def project_overrides(slug: str) -> str:
    """Phase 11.4 · ADR-001 §"差量 SSOT" · scene-ops 拖动持久化"""
    return f"project:{slug}:overrides"


def projects_index() -> str:
    return "projects:index"


def projects_archive() -> str:
    return "projects:archive"


def session_projects(anon_id: str) -> str:
    return f"session:{anon_id}:projects"


def rate_ip(ip: str, action: str = "create") -> str:
    return f"rate:{ip}:{action}"


def rate_session(anon_id: str, action: str = "create") -> str:
    return f"rate:session:{anon_id}:{action}"


def lock(slug: str) -> str:
    return f"project:{slug}:lock"


def job(job_id: str) -> str:
    return f"job:{job_id}"


def job_events(job_id: str) -> str:
    """Worker push · SSE stream 读 · 事件列表"""
    return f"job:{job_id}:events"


def jobs_queue() -> str:
    """Worker pull 用的 list"""
    return "jobs:queue"


def worker_heartbeat(host: str) -> str:
    """Worker 探活 · 每 30s 写 timestamp · TTL 120s · Phase 7.2"""
    return f"worker:{host}:heartbeat"


def workers_index() -> str:
    """所有活跃 worker 的 hostname 集合（SET）· SSE 探活用"""
    return "workers:index"


def audit(slug: str, ts: str) -> str:
    return f"audit:{slug}:{ts}"


def migration_guard(version: str) -> str:
    return f"migration:legacy:{version}"
