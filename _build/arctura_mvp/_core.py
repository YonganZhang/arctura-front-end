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


TTL_DRAFT = 7 * 86400          # empty/briefing/planning 7 天
TTL_LIVE = None                # live/saved PERSIST


def _project_key(slug: str) -> str:
    return f"project:{slug}"


def _index_key() -> str:
    return "projects:index"


def _session_projects_key(anon_id: str) -> str:
    return f"session:{anon_id}:projects"


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
    # state 字段需要保留 str · dataclass 接受
    return Project(**d)


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
