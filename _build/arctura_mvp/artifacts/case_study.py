"""case_study · portfolio/impact/sales 3 .md + metrics.json · spec L405

Phase 7.5 · 用严老师 vendor/case_study/render_templates.py
LIGHT 模式简化：
  - 我们有 brief / scene / artifacts · 直接组 metrics.json（不走 extract_metrics 扫文件夹）
  - render_templates.render_* 生成 3 文件
  - narrate 跳过（Gemini CLI 本机无 · narrative-*.txt 用占位符）
  - thumbs 跳过（BOQ/EUI/合规 占位）
FULL 模式产全套：见 StartUP-Building/playbooks/scripts/case-study/run_one.py
"""
from __future__ import annotations
import json
import sys
import time
from datetime import date
from pathlib import Path
from typing import Callable, Optional

from ..types import ArtifactResult
from ..paths import ensure_playbook_script_subdir_on_path

# Phase 9 · 直接用本机 StartUP-Building/playbooks/scripts/case-study/ · 不 vendor copy
ensure_playbook_script_subdir_on_path("case-study")


def _build_metrics(project) -> dict:
    """LIGHT 模式 metrics.json · 对齐 spec case-study-autogen §5 schema"""
    brief = project.brief or {}
    scene = project.scene or {}
    artifacts = project.artifacts or {}
    space = brief.get("space") or {}
    style = brief.get("style") or {}

    return {
        "id": project.slug,
        "tier": "interior",   # P1
        "scenario_cn": brief.get("project") or project.display_name or project.slug,
        "client_type": brief.get("client", "—"),
        "space": {
            "type": space.get("type"),
            "area_sqm": space.get("area_sqm"),
            "n_floors": space.get("n_floors", 1),
            "dimensions_m": {"length": None, "width": None, "height": None},
        },
        "style": {"keywords": style.get("keywords") or []},
        "metrics": {
            "boq_total_hkd": None,            # 需 FULL · OpenStudio report boq
            "boq_total_cny": None,
            "eui_kwh_m2_yr": None,            # 需 FULL · EnergyPlus
            "co2_saved_t_yr": None,
            "compliance_code": None,
            "compliance_pass_rate": None,
            "design_duration_min": _design_min_from_artifacts(artifacts),
        },
        "deliverables": {
            "plans_svg": ["floorplan.svg"] if (artifacts.get("produced") and "floorplan" in artifacts["produced"]) else [],
            "elevations": [],                 # 需 FULL · P1/P2
            "sections": [],
            "n_stakeholder_decks": 0,         # 需 FULL · marp-deck
            "card_sources": [],               # 缩略图对应 · LIGHT 无
            "exports": [],                    # 需 FULL · Blender
            "blender_objects": len(scene.get("objects", [])),
            "ifc_products": 0,
            "renders": (
                [f"renders/{i:02d}_*.png" for i in range(1, 9)]
                if "renders" in (artifacts.get("produced") or [])
                else []
            ),
        },
        "_light_mode": True,
        "_spec_ref": "StartUP-Building/CLAUDE.md L405 + playbooks/case-study-autogen-pipeline.md",
    }


def _design_min_from_artifacts(artifacts: dict) -> Optional[float]:
    total_ms = (artifacts.get("timing_ms") or {}).get("total")
    if not total_ms:
        return None
    return round(total_ms / 1000 / 60, 1)


def _write_placeholder_narrative(cs_dir: Path, template: str):
    """占位 narrative · FULL 需跑 narrate.py with LLM"""
    p = cs_dir / f"narrative-{template}.txt"
    p.write_text(
        f"_[narrative-{template}.txt 占位 · LIGHT 模式不调 LLM · "
        f"FULL 需走 StartUP-Building/playbooks/scripts/case-study/narrate.py]_"
    )


def produce(ctx: dict, on_event: Optional[Callable] = None) -> ArtifactResult:
    t0 = time.time()
    project = ctx["project"]
    sb_dir: Path = ctx["sb_dir"]

    if not project.brief:
        return ArtifactResult(
            name="case_study", status="skipped",
            timing_ms=int((time.time()-t0)*1000),
            reason="brief 缺 · 无法生成 case_study",
        )

    cs_dir = sb_dir / "case-study"
    cs_dir.mkdir(parents=True, exist_ok=True)
    (cs_dir / "thumbs").mkdir(exist_ok=True)

    # 1. metrics.json
    metrics = _build_metrics(project)
    (cs_dir / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2)
    )

    # 2. narrative 占位（3 份）· FULL 跑 narrate.py 填真 LLM
    for t in ("portfolio", "impact", "sales"):
        _write_placeholder_narrative(cs_dir, t)

    # 3. 渲染 3 .md 模板 · 用严老师 vendor
    # 注意：render_templates 读 folder/case-study/ 目录 · 我们传 sb_dir
    try:
        import render_templates  # vendored · stdlib only
    except ImportError as e:
        return ArtifactResult(
            name="case_study", status="error",
            timing_ms=int((time.time()-t0)*1000),
            error={"name": "vendor_import", "trace_tail": str(e)},
        )

    rendered = []
    for template in ("portfolio", "impact", "sales"):
        try:
            # render_one(folder, template) 写 folder/case-study/<template>.md
            render_templates.render_one(sb_dir, template)
            out = cs_dir / f"{template}.md"
            if out.exists():
                rendered.append(template)
        except Exception as e:
            # 单个模板失败不 abort · 其他继续
            (cs_dir / f"{template}.md").write_text(
                f"# {template}.md 渲染失败\n\n错误: {e}\n\nspec: StartUP-Building/CLAUDE.md L405"
            )

    # 顶部加 LIGHT 模式警告 banner
    for t in rendered:
        md = cs_dir / f"{t}.md"
        body = md.read_text()
        banner = (
            "> ⚠️ **LIGHT 模式输出** · 数据从 brief/scene 推 · "
            "BOQ/EUI/合规/exports 等为占位 · FULL 需走 StartUP-Building P11 pipeline\n\n"
        )
        md.write_text(banner + body)

    file_count = 1 + 3 + len(rendered)  # metrics + 3 narrative + N rendered
    return ArtifactResult(
        name="case_study",
        status="done",
        timing_ms=int((time.time()-t0)*1000),
        output_path=str(cs_dir),
        meta={
            "files": file_count,
            "rendered_templates": rendered,
            "light_mode": True,
            "metrics_empty_fields": [
                k for k, v in metrics["metrics"].items() if v is None
            ],
            "template_source": "StartUP-Building/playbooks/scripts/case-study/render_templates.py",
        },
    )
