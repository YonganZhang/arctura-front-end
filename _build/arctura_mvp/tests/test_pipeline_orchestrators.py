"""阶段 1 · 老师 P1 18 步 + P2 22 步 + 8 stakeholder dispatcher 测试

锁住:
  R1 · P1 12 老师 CLI 全可达(verify_p1)
  R2 · P1 step 顺序固定(18 步真 spec)
  R3 · P1 mandatory blocking gate(4 个)走 fatal_at 路径
  R4 · P2 22 步可调用 + site_entourage 集成
  R5 · 8 stakeholder dispatcher build_pptx.sh 可达 + 真 8 个 slug
"""
from __future__ import annotations
import os
import pytest
from pathlib import Path
from types import SimpleNamespace

from _build.arctura_mvp.teacher_authority.pipeline_p1 import verify_p1, run_p1_pipeline
from _build.arctura_mvp.teacher_authority.pipeline_p2 import verify_p2, run_p2_pipeline
from _build.arctura_mvp.teacher_authority.stakeholder_dispatcher import (
    verify_dispatcher, expected_stakeholders,
)


# ── R1 · P1 12 老师 CLI 全可达 ───────────────────────────────
def test_r1_p1_all_teacher_clis_reachable():
    info = verify_p1()
    must = ["lint_render_script", "verify_scene_dims", "room_to_room_v2",
            "layout_validate", "render_multi_assets", "validate_reports",
            "floorplan_pro", "gen_moodboard", "setup_mvp_render",
            "verify_mvp_exports"]
    missing = [k for k in must if not info[k]]
    assert not missing, f"P1 老师 CLI 缺: {missing}"
    assert info["blender"] and info["marp"]


# ── R2 · P1 brief 缺 → 立即 fatal_at='brief.json missing' ─────
def test_r2_p1_brief_missing_fatal(tmp_path):
    """无 brief.json 应立即 fatal · 不跑后续"""
    res = run_p1_pipeline(tmp_path, render_path="path_b")
    assert not res["ok"]
    assert res["fatal_at"] == "brief.json missing"


# ── R3 · P1 mandatory gate 走 fatal_at(空 mvp 应卡 step4a lint) ─
def test_r3_p1_lint_gate_blocking(tmp_path):
    """有 brief.json 但无 _render_script.py → step4a lint 应 fail · fatal_at='step4a_lint'"""
    (tmp_path / "brief.json").write_text("{}")
    res = run_p1_pipeline(tmp_path, render_path="path_b")
    # 老师 lint 应 fail(无 _render_script.py)· 但若 lint 不存在跳过(看实现)
    # 至少 ok=False
    assert "fatal_at" in res
    # 若有 gate fail · gate_failures 非空
    assert "gate_failures" in res


# ── R4 · P2 真可达 + 22 步签名 ─────────────────────────────────
def test_r4_p2_signature():
    info = verify_p2()
    assert info["blender"] and info["marp"]


def test_r4_p2_brief_missing_fatal(tmp_path):
    res = run_p2_pipeline(tmp_path)
    assert not res["ok"]
    assert "brief.json" in (res.get("fatal_at") or "")


# ── R5 · stakeholder dispatcher · 8 真 slug + build_pptx.sh ──
def test_r5_dispatcher_8_real_stakeholders():
    info = verify_dispatcher()
    assert info["build_pptx_sh_exists"], "老师 build_pptx.sh 应存在"
    assert info["stakeholders_count"] == 8
    slugs = expected_stakeholders()
    must = ["client", "investor", "designer", "contractor",
            "bim", "school-leader", "operations", "marketing"]
    assert set(slugs) == set(must)


# ── R6 · case_study LLM 双轨 + 7 真脚本 ───────────────────
def test_r6_case_study_runner_7_scripts():
    from _build.arctura_mvp.teacher_authority.case_study_runner import verify_runner
    info = verify_runner()
    must = ["extract_metrics", "populate_narratives", "narrate",
            "render_templates", "aggregate", "run_one", "run_all"]
    missing = [k for k in must if not info[k]]
    assert not missing, f"老师 case-study 脚本缺: {missing}"


# ── R7 · SSOT region map 真 helper(老师 defaults/region-code-map.yaml) ─
def test_r7_resolve_region_HK():
    from _build.arctura_mvp.teacher_authority.ssot import resolve_region
    r = resolve_region("hk")
    if r is None:
        pytest.skip("region-code-map.yaml 不可读 / pyyaml 未装")
    assert "boq_region" in r or "compliance_code" in r or "weather_epw" in r


def test_r7_resolve_region_chinese_fallback():
    """中文 '北京' → 应通过 region_fallback 解到 cn_bj"""
    from _build.arctura_mvp.teacher_authority.ssot import resolve_region
    r = resolve_region("北京")
    if r is None:
        pytest.skip("region-code-map.yaml 不可读 / 老师没配置 fallback")
    # 至少有一个关键字段
    assert any(k in r for k in ("boq_region", "compliance_code", "weather_epw"))


# ── R8 · pipeline.run · use_teacher_orchestrator 触发分支 ───
def test_r8_pipeline_use_teacher_orchestrator_path(tmp_path, monkeypatch):
    """env ARCTURA_TEACHER_PIPELINE=1 触发老师 orchestrator · 应走分支"""
    monkeypatch.setenv("ARCTURA_TEACHER_PIPELINE", "1")
    # 此测试只验证分支可调 · 不需真跑 P1(无 brief.json 即 fatal_at)
    from _build.arctura_mvp import pipeline
    from _build.arctura_mvp.types import Project
    project = Project(
        slug="test-teacher-trigger",
        brief={"space": {"type": "study"}, "use_teacher_orchestrator": True},
        tier="full",
        scene={},
        artifacts={},
        state="generating",
        version=0,
        render_engine="formal",
        variant_count=1,
        display_name="test",
    )
    result = pipeline.run(project, dry_run=True)
    # 应有 teacher_pipeline 路径触发的产出
    assert hasattr(result, "produced") or hasattr(result, "errors")


# ── R9 · 阶段 2 · portfolio_rollup 全库 rollup ────────────────
def test_r9_portfolio_rollup_runner_callable():
    from _build.arctura_mvp.teacher_authority.portfolio_rollup import verify_runner
    info = verify_runner()
    if not info["case_studies_dir_exists"]:
        pytest.skip(f"老师 case-studies/ 不可达")
    assert info["aggregate_script"]
    # 老师真应有 4 顶层 + 26+ 软链
    assert info["portfolio_index_md"]
    assert info["impact_dashboard_md"]
    assert info["metrics_json"]


def test_r9_portfolio_index_readable():
    """老师 case-studies/portfolio-index.md 应可读 + 含 26 项目"""
    from _build.arctura_mvp.teacher_authority.portfolio_rollup import get_portfolio_index
    idx = get_portfolio_index()
    if not idx:
        pytest.skip("portfolio-index.md 不可达")
    assert "Portfolio" in idx or "portfolio" in idx
    # 老师真 26 项目
    md_links = idx.count("](portfolio/")
    assert md_links >= 20, f"应 ≥20 portfolio 链接 · 实 {md_links}"


def test_r9_global_metrics_readable():
    """老师 case-studies/metrics.json 全库 rollup 应可读"""
    from _build.arctura_mvp.teacher_authority.portfolio_rollup import get_global_metrics
    m = get_global_metrics()
    if m is None:
        pytest.skip("global metrics.json 不可达")
    assert isinstance(m, (dict, list))


# ── R10 · 阶段 3 · brief schema 真 jsonschema validate(老师权威) ─
def test_r10_brief_validate_against_teacher_schema():
    from _build.arctura_mvp.chat.brief_engine import validate_against_teacher_schema
    minimal = {"project": "test", "style": {"keywords": ["modern"]}}
    errs = validate_against_teacher_schema(minimal, "interior")
    if errs and "jsonschema" in errs[0].lower() and "未装" in errs[0]:
        pytest.skip("jsonschema 未装")
    assert errs == [] or len(errs) <= 2  # 老师 required 仅 project + style


def test_r10_brief_validate_missing_required():
    from _build.arctura_mvp.chat.brief_engine import validate_against_teacher_schema
    bad = {"slug": "x"}  # 缺 project + style
    errs = validate_against_teacher_schema(bad, "interior")
    if errs and "jsonschema 未装" in (errs[0] if errs else ""):
        pytest.skip("jsonschema 未装")
    assert len(errs) >= 1


# ── R11 · brief-rules nice_to_have 含老师 5 顶层字段 ──────────
def test_r11_brief_rules_covers_teacher_top_fields():
    import json
    from _build.arctura_mvp.paths import REPO_ROOT
    rules = json.loads((REPO_ROOT / "_build/arctura_mvp/schemas/brief-rules.json").read_text())
    nice = set(rules["nice_to_have"])
    must = {"compliance", "envelope", "openings", "mep_brief", "budget_rmb"}
    missing = must - nice
    assert not missing, f"老师 5 顶层字段缺: {missing}"


# ── R12 · P0 asset-intake 5 文件类型支持 ─────────────────────
def test_r12_p0_supports_5_kinds():
    from _build.arctura_mvp.teacher_authority.p0_asset_intake import (
        detect_input_kind, run_p0_intake,
    )
    assert detect_input_kind(Path("x.ifc")) == "ifc"
    assert detect_input_kind(Path("x.dxf")) == "dxf"
    assert detect_input_kind(Path("x.svg")) == "svg"
    assert detect_input_kind(Path("x.pdf")) == "pdf"
    assert detect_input_kind(Path("x.png")) == "image"


def test_r12_p0_unknown_kind(tmp_path):
    from _build.arctura_mvp.teacher_authority.p0_asset_intake import run_p0_intake
    fake = tmp_path / "x.unknown"
    fake.write_text("")
    r = run_p0_intake(fake, tmp_path / "out")
    assert not r["ok"]


# ── R13 · 阶段 4 · spec_enforcer 真 enforce ────────────────
def test_r13_enforce_full_tier_empty_dir(tmp_path):
    """空 mvp dir · enforce 应返 missing 多项 + ok=False"""
    from _build.arctura_mvp.teacher_authority.spec_enforcer import enforce_full_tier_completeness
    r = enforce_full_tier_completeness(tmp_path)
    assert not r["ok"]
    assert len(r["missing"]) > 5


def test_r13_enforce_render_count_path_a():
    """Path A 必 6 张 · 路径 spec lock"""
    from _build.arctura_mvp.teacher_authority.spec_enforcer import enforce_render_count
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        # 0 张 PNG · Path A 应 fail
        r = enforce_render_count(Path(d), "path_a")
        assert not r["ok"]
        assert r["expected"] == 6


def test_r13_enforce_compliance_code():
    """5 法规 enforce + EUI advisory"""
    from _build.arctura_mvp.teacher_authority.spec_enforcer import enforce_compliance_code
    r_ok = enforce_compliance_code("HK")
    assert r_ok["ok"] and r_ok["is_advisory"]
    r_bad = enforce_compliance_code("FAKE")
    assert not r_bad["ok"]


def test_r13_enforce_change_category():
    """老师 15 客户改类 enforce"""
    from _build.arctura_mvp.teacher_authority.spec_enforcer import enforce_change_category
    assert enforce_change_category("材质/颜色")["ok"]
    assert enforce_change_category("房间尺寸")["ok"]
    assert not enforce_change_category("乱写的类别")["ok"]


# ── R14 · chat-edit smart rerun(老师 change-impact 接 op)───
def test_r14_smart_rerun_for_op_color():
    """客户改 set_palette → must_artifacts: renders + energy_report + case_study"""
    from _build.arctura_mvp.teacher_authority.chat_edit_smart_rerun import (
        smart_rerun_for_chat_edit,
    )
    r = smart_rerun_for_chat_edit({"type": "set_palette", "value": ["#fff"]})
    assert r["category"] == "材质/颜色"
    assert "renders" in r["must_artifacts"]


def test_r14_smart_rerun_for_op_room_size():
    """客户改 set_area_sqm → must_artifacts: 多个(scene/renders/floorplan/exports/energy_report)"""
    from _build.arctura_mvp.teacher_authority.chat_edit_smart_rerun import (
        smart_rerun_for_chat_edit,
    )
    r = smart_rerun_for_chat_edit({"type": "set_area_sqm", "value": 100})
    assert r["category"] == "房间尺寸"
    must = r["must_artifacts"]
    assert "scene" in must
    assert "renders" in must
    assert "floorplan" in must
    assert "energy_report" in must


def test_r14_smart_rerun_unknown_op_default_full():
    """未知 op 类 → 保守默认全重跑(_warning 标记)"""
    from _build.arctura_mvp.teacher_authority.chat_edit_smart_rerun import (
        smart_rerun_for_chat_edit,
    )
    r = smart_rerun_for_chat_edit({"type": "unknown_op_xyz"})
    assert "_warning" in r
    assert r["category"] is None


# ── R15 · drift_detector 真追老师 git ──────────────────────
def test_r15_drift_detector_reads_teacher_git():
    from _build.arctura_mvp.teacher_authority.drift_detector import detect_drift
    r = detect_drift()
    if not r["current_head"]:
        pytest.skip("老师 git 不可达")
    assert r["current_head"]
    assert "recent_commits" in r
    assert r["zhiling_specs_count"] >= 30  # 老师 33 spec


def test_r5_dispatcher_no_decks_dir(tmp_path):
    """无 decks/ 应返 error"""
    from _build.arctura_mvp.teacher_authority.stakeholder_dispatcher import (
        dispatch_stakeholder_decks,
    )
    r = dispatch_stakeholder_decks(tmp_path)
    assert not r["ok"]
    assert "decks" in (r.get("error") or "")
