"""Phase 7.1 · 每 artifact 返回合理 meta 字段（SSE → 前端消费）

不 mock 真落盘（用 tmp_path）· 但不 boot playwright / rsvg / PIL 的重依赖 · 所以只跑能离线跑的 artifact：
  - scene · 纯 dict 操作
  - moodboard · 有 PIL fallback（无 PIL 时 png=False · 仍 done）
  - bundle · ZIP pure-python · 无依赖

floorplan 需要 rsvg-convert · renders 需要 Playwright · 不在本套测试覆盖
（这两个的 meta 形状在 code review 保证）
"""
from __future__ import annotations
from pathlib import Path
import pytest

from _build.arctura_mvp.types import Project, ArtifactResult
from _build.arctura_mvp.artifacts import scene as scene_art
from _build.arctura_mvp.artifacts import moodboard as moodboard_art
from _build.arctura_mvp.artifacts import bundle as bundle_art


def _make_project_with_scene():
    return Project(
        slug="t-art",
        state="generating",
        display_name="Test Project",
        brief={
            "project": "T",
            "space": {"area_sqm": 20},
            "style": {"keywords": ["极简"]},
            "functional_zones": [{"name": "区"}],
        },
    )


def _make_ctx(project, tmp_path):
    sb_dir = tmp_path / "sb" / project.slug
    fe_root = tmp_path / "fe"
    sb_dir.mkdir(parents=True)
    fe_root.mkdir(parents=True)
    return {"project": project, "sb_dir": sb_dir, "fe_root": fe_root}


# ───────── scene ─────────

def test_scene_artifact_meta_on_generation(tmp_path):
    """project.scene 空 → 调 generator · 返 done + meta.generated=True · assemblies > 0"""
    p = _make_project_with_scene()
    p.scene = None   # 强制 generator 路径
    ctx = _make_ctx(p, tmp_path)

    result = scene_art.produce(ctx)

    assert isinstance(result, ArtifactResult)
    assert result.status == "done"
    assert result.meta["generated"] is True
    assert result.meta["assemblies"] >= 1
    assert result.meta["bounds"]["w"] > 0
    # project.scene 被回填
    assert p.scene is not None
    assert len(p.scene["assemblies"]) == result.meta["assemblies"]


def test_scene_artifact_meta_when_scene_already_set(tmp_path):
    """project.scene 已存在 → 不触 generator · meta.generated=False"""
    p = _make_project_with_scene()
    p.scene = {
        "schema_version": "1.0", "bounds": {"w": 5, "d": 4, "h": 2.8},
        "assemblies": [{"id": "asm_a", "type": "chair_standard",
                         "pos": [0, 0, 0], "size": [0.5, 0.5, 0.9]}],
        "objects": [], "walls": [], "lights": [], "materials": {},
    }
    ctx = _make_ctx(p, tmp_path)

    result = scene_art.produce(ctx)

    assert result.status == "done"
    assert result.meta["generated"] is False
    assert result.meta["assemblies"] == 1
    assert result.meta["bounds"]["w"] == 5


def test_scene_artifact_skipped_when_both_missing(tmp_path):
    p = Project(slug="t-empty", state="generating", brief=None, scene=None)
    ctx = _make_ctx(p, tmp_path)
    result = scene_art.produce(ctx)
    assert result.status == "skipped"
    assert "brief" in (result.reason or "")


# ───────── moodboard ─────────

def test_moodboard_artifact_meta(tmp_path):
    p = _make_project_with_scene()
    ctx = _make_ctx(p, tmp_path)
    result = moodboard_art.produce(ctx)

    assert result.status == "done"
    assert "swatches" in result.meta
    assert result.meta["swatches"] > 0
    assert isinstance(result.meta["png"], bool)


# ───────── bundle ─────────

def test_bundle_artifact_meta(tmp_path):
    """bundle 需 fe_root/assets/mvps/<slug>/ 存在 · 且 sb_dir 有内容"""
    p = _make_project_with_scene()
    ctx = _make_ctx(p, tmp_path)
    # sb_dir 塞一个虚拟产物
    (ctx["sb_dir"] / "dummy.txt").write_text("hello")

    result = bundle_art.produce(ctx)

    assert result.status == "done"
    assert result.meta["files"] >= 1
    assert result.meta["size_kb"] > 0
    # output_path 是纯路径 · 不塞 detail
    assert "(" not in (result.output_path or "")
