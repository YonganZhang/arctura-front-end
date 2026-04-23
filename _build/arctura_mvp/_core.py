"""Project CRUD · 基础设施 · store/kv 之上的类型安全层

与 v3 §2.3 KV Layout 对齐：
  project:<slug>        主 JSON · state=live PERSIST · 其他 7 天 TTL
  projects:index        ZSET score=updated_at unix
  session:<anon>:projects  单 session 的 slug list
"""
from __future__ import annotations
from dataclasses import asdict
from typing import Optional
from datetime import datetime, timezone
import time

from .types import Project, utc_now
from .store import kv
from .store import keys as K  # 单一真源 · 跟 api/_shared/kv-keys.js 对称


TTL_DRAFT = 7 * 86400          # empty/briefing/planning 7 天
TTL_LIVE = None                # live/saved PERSIST


# Backward compat · 保留函数别名（旧测试可能引用）· 统一走 K
def _project_key(slug: str) -> str: return K.project(slug)
def _index_key() -> str: return K.projects_index()
def _session_projects_key(anon_id: str) -> str: return K.session_projects(anon_id)


def _now_unix() -> int:
    return int(time.time())


# ───── Project CRUD ─────

def put_project(p: Project, *, expected_version: Optional[int] = None) -> Project:
    """写 project · optimistic lock（expected_version 不匹配 → 抛 VersionConflict）"""
    key = _project_key(p.slug)
    existing = kv.get_json(key)
    if existing is not None:
        current_version = existing.get("version", 0)
        if expected_version is not None and expected_version != current_version:
            raise VersionConflict(f"Expected version {expected_version}, got {current_version}")
        p.version = current_version + 1
    else:
        p.version = max(1, p.version or 1)
    p.updated_at = utc_now()
    if not p.created_at:
        p.created_at = p.updated_at
    # 写 project
    ttl = TTL_LIVE if p.state == "live" else TTL_DRAFT
    kv.set_json(key, asdict(p), ex=ttl)
    # live 不 TTL · 已有 TTL 的 PERSIST
    if ttl is None:
        kv.persist(key)
    # 更新 index
    kv.zadd(_index_key(), _now_unix(), p.slug)
    # 更新 session projects
    if p.owner:
        kv.zadd(_session_projects_key(p.owner), _now_unix(), p.slug)
    return p


def get_project(slug: str) -> Optional[Project]:
    d = kv.get_json(_project_key(slug))
    if d is None:
        return None
    # 容忍 future 字段 · JS edge 写入的键若 Python 未同步则忽略（避免 hard fail）
    import dataclasses as _dc, sys as _sys
    valid = {f.name for f in _dc.fields(Project)}
    unknown = set(d.keys()) - valid
    if unknown:
        # 静默 drop 但 warn · 提醒同步 types.py
        print(f"[_core] warn: project {slug} has unknown fields dropped: {sorted(unknown)}",
              file=_sys.stderr)
    filtered = {k: v for k, v in d.items() if k in valid}
    return Project(**filtered)


def list_projects(*, owner: Optional[str] = None, limit: int = 20,
                  cursor: Optional[int] = None) -> dict:
    """cursor = start offset（简版 · zset ZREVRANGE）

    Returns: {projects: list[ProjectSummary], next_cursor: int | None}
    """
    key = _session_projects_key(owner) if owner else _index_key()
    start = cursor or 0
    stop = start + limit - 1
    slugs = kv.zrevrange(key, start, stop)
    projects = []
    for slug in slugs:
        p = get_project(slug)
        if p is None:
            continue
        projects.append({
            "slug": p.slug,
            "display_name": p.display_name,
            "state": p.state,
            "tier": p.tier,
            "hero_img": (p.artifacts or {}).get("urls", {}).get("hero_img"),
            "updated_at": p.updated_at,
            "visibility": p.visibility,
        })
    total = kv.zcard(key)
    next_cursor = (start + limit) if (start + limit) < total else None
    return {"projects": projects, "next_cursor": next_cursor, "total": total}


def enqueue_job(slug: str, *, expected_version: Optional[int] = None) -> dict:
    """入队一个 MVP 生成 job · MCP + CLI 用（JS /api/mvp/create.js 独立实现 · 接口对齐）

    前置：project.state == "planning" · project.tier 已设
    副作用：rpush jobs:queue + set job meta + 推 project state→generating + 写 active_job_id
    返回：{job_id, slug, stream_url, status}
    抛 ValueError：非 planning / 缺 tier / version 冲突
    """
    import json as _json
    import secrets
    p = get_project(slug)
    if p is None:
        raise ValueError("project not found")
    if expected_version is not None and p.version != expected_version:
        raise ValueError(f"version conflict · current={p.version} expected={expected_version}")
    if p.state != "planning":
        raise ValueError(f"state={p.state} · 必须 planning 才能入队")
    if not p.tier:
        raise ValueError("tier 未设 · 先走 pick_tier")

    job_id = f"job-{secrets.token_hex(5)}"
    job = {
        "id": job_id, "slug": slug, "tier": p.tier,
        "variant_count": p.variant_count or 1,
        "render_engine": p.render_engine,
        "queued_at": utc_now(),
    }
    # 推队列 + job meta（7 天 TTL）
    kv.rpush(K.jobs_queue(), _json.dumps(job))
    kv.set_json(K.job(job_id), {**job, "status": "queued"}, ex=7 * 86400)

    # 推进 project state
    p.state = "generating"
    p.active_job_id = job_id
    put_project(p, expected_version=p.version)

    return {"job_id": job_id, "slug": slug,
            "stream_url": f"/api/jobs/{job_id}/stream", "status": "queued"}


def delete_project(slug: str) -> bool:
    """软删：从 index 移 + 加 30 天 TTL 等 grace period"""
    p = get_project(slug)
    if p is None:
        return False
    kv.zrem(_index_key(), slug)
    if p.owner:
        kv.zrem(_session_projects_key(p.owner), slug)
    kv.expire(_project_key(slug), 30 * 86400)
    return True


# ───── Errors ─────

class VersionConflict(Exception):
    pass


# ───── Self-test ─────

if __name__ == "__main__":
    import uuid
    from .types import Project
    slug = f"test-{uuid.uuid4().hex[:8]}"
    p = Project(slug=slug, state="empty", display_name="Test Project", owner="test-anon-123")
    p = put_project(p)
    assert p.version == 1
    got = get_project(slug)
    assert got is not None
    assert got.display_name == "Test Project"
    # update
    got.display_name = "Updated"
    got.state = "briefing"
    got = put_project(got, expected_version=1)
    assert got.version == 2
    assert got.state == "briefing"
    # version conflict
    try:
        got.display_name = "stale"
        put_project(got, expected_version=1)
        assert False, "should conflict"
    except VersionConflict:
        pass
    # list
    lst = list_projects(owner="test-anon-123")
    assert any(x["slug"] == slug for x in lst["projects"])
    # cleanup
    delete_project(slug)
    print(f"✓ all _core tests passed · test slug: {slug}")
