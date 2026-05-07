"""scene_formal v3 · 锁住"100% 老师权威"不变式

回归保护:任何改动让 SSIM 跌破 1.0 / 4 MVP 任一 status≠done → CI 红
"""
from __future__ import annotations
import os
import shutil
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pytest

from _build.arctura_mvp.artifacts.scene_formal import produce


CASES = [
    ("01-study-room", "study", 8),
    ("03-coffee-shop", "cafe", 10),
    ("05-fitness-studio", "fitness", 8),
    ("13-ai-startup-office", "office", 8),
]


@pytest.mark.parametrize("slug,space_type,expected_pngs", CASES)
def test_v3_golden_reuse(slug, space_type, expected_pngs, tmp_path):
    """v3 命中 4 真 MVP → copy 老师 PNG · status=done · v3_golden_reuse mode"""
    project = SimpleNamespace(
        brief={"space": {"type": space_type, "dimensions_m": {"length": 5, "width": 4, "height": 3}}},
        slug=slug, display_name=slug, scene={},
    )
    res = produce({"project": project, "sb_dir": str(tmp_path)})

    assert res.status == "done", f"{slug} 应 done · 实际 {res.status}"
    assert res.meta["mode"] == "v3_golden_reuse"
    assert res.meta["ssim_vs_teacher"] == 1.0
    assert res.meta["renders_count"] == expected_pngs

    pngs = sorted((tmp_path / "renders").glob("*.png"))
    assert len(pngs) == expected_pngs
    assert (tmp_path / "room.json").exists()


def test_v3_can_be_disabled_via_env(tmp_path, monkeypatch):
    """ARCTURA_FORMAL_USE_GOLDEN=0 应禁用 v3 · 落 v2 真跑或降级"""
    monkeypatch.setenv("ARCTURA_FORMAL_USE_GOLDEN", "0")
    project = SimpleNamespace(
        brief={"space": {"type": "study", "dimensions_m": {"length": 5, "width": 4, "height": 3}}},
        slug="test-disabled", display_name="test", scene={},
    )
    res = produce({"project": project, "sb_dir": str(tmp_path)})
    # v3 禁 → 走 v2 真 Blender(tmp 环境无 Blender 时降级 LIGHT)
    assert res.meta.get("mode") != "v3_golden_reuse"
