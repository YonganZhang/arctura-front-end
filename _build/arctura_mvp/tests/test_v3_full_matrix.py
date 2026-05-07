"""v3 全 artifact 矩阵 · 锁住 100% 老师权威不变式

测试案例设计(4 维度覆盖):
  M1 · 24 case 矩阵: 4 MVP × 6 artifact 必须 status=done + mode=v3_golden_reuse
       (锁住没掉到 LIGHT/降级 · 真复用老师产物)
  M2 · brief 不命中表 → 不应 v3 reuse · 走 fallback(锁住命中表精准性)
  M3 · ARCTURA_FORMAL_USE_GOLDEN=0 全禁 · 全 fallback(锁住可降级开关)
  M4 · 空 brief / type 缺 → 不 v3(锁住边界鲁棒性)

任一维度失守 → CI 红 · 立即可定位类型(矩阵/精准/开关/边界)。
"""
from __future__ import annotations
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from _build.arctura_mvp.artifacts.scene_formal import produce as scene
from _build.arctura_mvp.artifacts.moodboard_formal import produce as moodboard
from _build.arctura_mvp.artifacts.floorplan_formal import produce as floorplan
from _build.arctura_mvp.artifacts.deck_client_formal import produce as deck_client
from _build.arctura_mvp.artifacts.energy_report_formal import produce as energy_report
from _build.arctura_mvp.artifacts.case_study_formal import produce as case_study
from _build.arctura_mvp.artifacts.client_readme_formal import produce as client_readme
from _build.arctura_mvp.artifacts.exports_formal import produce as exports
from _build.arctura_mvp.artifacts.ai_renders_formal import produce as ai_renders


_MVP_TYPES = [
    ("01-study-room", "study"),
    ("03-coffee-shop", "cafe"),
    ("05-fitness-studio", "fitness"),
    ("13-ai-startup-office", "office"),
]
# Phase 12.末.B 修漏后矩阵 · 主体 6 artifact 全 MVP 必命中 v3
_ARTIFACTS = [
    ("scene", scene, 1),         # 主返 room.json · 文件数语义不同(整 dirs renders/)
    ("moodboard", moodboard, 2), # json + png
    ("floorplan", floorplan, 3), # svg + png + inkscape-cli.json(dxf 03/05/13 才有)
    ("deck_client", deck_client, 1),  # files 计 1 dir · decks 整目录(9 stakeholder × 2)
    ("energy_report", energy_report, 1),  # 整 dirs energy/ 含 ep_output 14 文件
    ("case_study", case_study, 1),  # 整 dirs case-study/ 含 narrative + metrics + thumbs
]

# 选择性命中 · 不是所有 MVP 都有(老师真 GitHub 状态)
# (artifact, fn, mvp_with_truth, expected_min_top_files)
_PARTIAL_ARTIFACTS = [
    # client_readme: 老师 05/13 真有 · 01/03 没 → 后两 fallback LIGHT(也算正确不挂)
    ("client_readme", client_readme, {"05-fitness-studio", "13-ai-startup-office"}),
    # exports: 03/05/13 真有(.glb/.fbx/.ifc/.obj/.mtl + dxf + 3 export script + 1 floorplan.dxf · = 9 文件 + 没整 sub) · 01-study-room 没
    ("exports", exports, {"03-coffee-shop", "05-fitness-studio", "13-ai-startup-office"}),
    # ai_renders: 只 03-coffee-shop 真有 SDXL multi-version + compare_*.png
    ("ai_renders", ai_renders, {"03-coffee-shop"}),
]


def _make_project(slug, space_type):
    return SimpleNamespace(
        brief={"space": {"type": space_type, "dimensions_m": {"length": 5, "width": 4, "height": 3}}},
        slug=slug, display_name=slug, scene={}, artifacts={},
    )


# ── M1 · 24 case 矩阵 ─────────────────────────────────
@pytest.mark.parametrize("slug,stype", _MVP_TYPES)
@pytest.mark.parametrize("name,fn,min_files", _ARTIFACTS)
def test_m1_full_matrix_v3_reused(slug, stype, name, fn, min_files, tmp_path):
    project = _make_project(slug, stype)
    res = fn({"project": project, "sb_dir": tmp_path})

    assert res.status == "done", f"[{slug}/{name}] 应 done · 实际 {res.status}"
    meta = res.meta or {}
    assert meta.get("mode") == "v3_golden_reuse", \
        f"[{slug}/{name}] 应 v3_golden_reuse · 实际 mode={meta.get('mode')} (掉降级 / fallback?)"
    files_count = meta.get("files_count") or meta.get("renders_count") or 0
    assert files_count >= min_files, \
        f"[{slug}/{name}] 应 ≥{min_files} 文件 · 实际 {files_count}"


# ── M1b · 选择性命中(老师真 GitHub 状态) ────────────────
@pytest.mark.parametrize("slug,stype", _MVP_TYPES)
@pytest.mark.parametrize("name,fn,mvp_with_truth", _PARTIAL_ARTIFACTS)
def test_m1b_partial_artifacts_v3(slug, stype, name, fn, mvp_with_truth, tmp_path):
    """老师真有的 MVP → v3 命中 · 其他 → 落 fallback(都不应 error/skipped)"""
    project = _make_project(slug, stype)
    res = fn({"project": project, "sb_dir": tmp_path})
    assert res.status in ("done", "skipped"), \
        f"[{slug}/{name}] 不应 error · 实际 {res.status} {res.error}"
    if slug in mvp_with_truth:
        meta = res.meta or {}
        assert meta.get("mode") == "v3_golden_reuse", \
            f"[{slug}/{name}] 老师真有 → 应 v3 · 实际 mode={meta.get('mode')}"


# ── M2 · brief 不命中表 → 不 v3 ─────────────────────────
def test_m2_unknown_type_skips_v3(tmp_path):
    """brief.space.type='outdoor_garden'(不在 _TYPE_TO_SLUG 表)→ 不应 v3"""
    project = _make_project("test-unknown", "outdoor_garden")
    res = moodboard({"project": project, "sb_dir": tmp_path})
    assert (res.meta or {}).get("mode") != "v3_golden_reuse", \
        f"未知 type 不应触发 v3 · 实际 mode={(res.meta or {}).get('mode')}"


# ── M3 · 全局禁用开关 ──────────────────────────────────
def test_m3_env_disable_blocks_v3(tmp_path, monkeypatch):
    monkeypatch.setenv("ARCTURA_FORMAL_USE_GOLDEN", "0")
    project = _make_project("01-study-room", "study")
    for name, fn, _ in _ARTIFACTS:
        sub = tmp_path / name
        sub.mkdir()
        res = fn({"project": project, "sb_dir": sub})
        mode = (res.meta or {}).get("mode")
        assert mode != "v3_golden_reuse", \
            f"[{name}] 禁开关下不应 v3 · 实际 {mode}"


# ── M4 · 边界鲁棒性 ────────────────────────────────────
def test_m4_empty_brief_no_v3(tmp_path):
    """brief 完全空 → 不 v3 · 走 skipped/fallback"""
    project = SimpleNamespace(brief={}, slug="empty", display_name="e", scene={})
    res = moodboard({"project": project, "sb_dir": tmp_path})
    assert (res.meta or {}).get("mode") != "v3_golden_reuse"


def test_m4_brief_no_space_type(tmp_path):
    """brief.space 无 type → 不 v3"""
    project = SimpleNamespace(
        brief={"space": {"area_sqm": 20}},  # 缺 type
        slug="no-type", display_name="x", scene={},
    )
    res = moodboard({"project": project, "sb_dir": tmp_path})
    assert (res.meta or {}).get("mode") != "v3_golden_reuse"
