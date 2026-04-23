"""T23.5 · _core.put_project / get_project / list_projects · VersionConflict
Phase 7.1 新增 · enqueue_job
"""
import json
import pytest
from _build.arctura_mvp._core import (
    put_project, get_project, list_projects, delete_project, enqueue_job,
    VersionConflict,
)
from _build.arctura_mvp.types import Project


def _make_project(slug="test-123", state="empty", owner="anon-abc"):
    return Project(slug=slug, state=state, owner=owner, display_name=f"Project {slug}")


def test_put_and_get(kv_mock):
    p = _make_project()
    returned = put_project(p)
    assert returned.version == 1
    got = get_project("test-123")
    assert got is not None
    assert got.slug == "test-123"
    assert got.display_name == "Project test-123"


def test_put_bumps_version(kv_mock):
    p = _make_project()
    p = put_project(p)
    assert p.version == 1
    p.display_name = "new"
    p = put_project(p, expected_version=1)
    assert p.version == 2


def test_version_conflict(kv_mock):
    p = _make_project()
    p = put_project(p)
    assert p.version == 1
    # 模拟：另一客户端修改到 version=2
    p.display_name = "first update"
    p = put_project(p, expected_version=1)
    assert p.version == 2
    # 现在再用 expected=1 写 · 应该 conflict
    p.display_name = "stale"
    with pytest.raises(VersionConflict):
        put_project(p, expected_version=1)


def test_get_non_existent_returns_none(kv_mock):
    assert get_project("does-not-exist") is None


def test_list_projects_returns_sorted(kv_mock):
    p1 = _make_project("p-1", state="live", owner="me")
    p2 = _make_project("p-2", state="live", owner="me")
    p3 = _make_project("p-3", state="live", owner="me")
    put_project(p1)
    put_project(p2)
    put_project(p3)
    result = list_projects(owner="me")
    # zrevrange · 最新在前
    slugs = [p["slug"] for p in result["projects"]]
    assert set(slugs) == {"p-1", "p-2", "p-3"}
    assert result["total"] == 3


def test_delete_removes_from_index(kv_mock):
    p = _make_project("p-del", owner="me")
    put_project(p)
    assert delete_project("p-del") is True
    # get 仍能读（软删 · expire 30 天）· 但索引没
    result = list_projects(owner="me")
    assert "p-del" not in [pp["slug"] for pp in result["projects"]]


def test_put_project_sets_timestamps(kv_mock):
    p = _make_project()
    assert p.created_at == ""
    p = put_project(p)
    assert p.created_at != ""
    assert p.updated_at != ""
    assert p.created_at == p.updated_at


def test_live_state_persists_no_ttl(kv_mock):
    """live 态应 PERSIST（不在 ttls）· empty 应有 TTL"""
    p_empty = _make_project("p-empty", state="empty")
    put_project(p_empty)
    assert "project:p-empty" in kv_mock.ttls

    p_live = _make_project("p-live", state="live")
    put_project(p_live)
    assert "project:p-live" not in kv_mock.ttls   # PERSIST


# ───── Phase 7.1 · enqueue_job ─────

def test_enqueue_job_happy_path(kv_mock):
    """state=planning + tier=concept → 成功入队 · rpush + set job meta + state→generating"""
    p = _make_project("p-eq", state="planning")
    p.tier = "concept"
    p.variant_count = 1
    p.render_engine = "fast"
    put_project(p)
    before_version = p.version

    result = enqueue_job("p-eq")
    # 返回形状（跟 /api/mvp/create.js 对齐）
    assert set(result.keys()) == {"job_id", "slug", "stream_url", "status"}
    assert result["slug"] == "p-eq"
    assert result["job_id"].startswith("job-")
    assert result["stream_url"] == f"/api/jobs/{result['job_id']}/stream"
    assert result["status"] == "queued"

    # KV 副作用验证
    # 1. jobs:queue 有一条
    queue = kv_mock.lrange("jobs:queue")
    assert len(queue) == 1
    job_in_queue = json.loads(queue[0])
    assert job_in_queue["id"] == result["job_id"]
    assert job_in_queue["tier"] == "concept"

    # 2. job:<id> meta 写入
    meta_raw = kv_mock.get(f"job:{result['job_id']}")
    assert meta_raw is not None
    meta = json.loads(meta_raw)
    assert meta["status"] == "queued"

    # 3. project state=generating · active_job_id 写入 · version bump
    updated = get_project("p-eq")
    assert updated.state == "generating"
    assert updated.active_job_id == result["job_id"]
    assert updated.version == before_version + 1


def test_enqueue_job_rejects_non_planning_state(kv_mock):
    p = _make_project("p-br", state="briefing")
    p.tier = "concept"
    put_project(p)
    with pytest.raises(ValueError, match="state=briefing"):
        enqueue_job("p-br")


def test_enqueue_job_rejects_missing_tier(kv_mock):
    p = _make_project("p-nt", state="planning")
    put_project(p)
    with pytest.raises(ValueError, match="tier 未设"):
        enqueue_job("p-nt")


def test_enqueue_job_version_conflict(kv_mock):
    p = _make_project("p-vc", state="planning")
    p.tier = "concept"
    put_project(p)
    with pytest.raises(ValueError, match="version conflict"):
        enqueue_job("p-vc", expected_version=99)
