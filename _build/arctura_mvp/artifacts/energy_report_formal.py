"""energy_report_formal · Phase 12.D.3 · 真直接 import 老师 cli_anything.openstudio.core

跟 LIGHT energy_report.py 区别:
  - LIGHT: subprocess 调 cli-anything-openstudio CLI(间接)· EUI=None(没真跑 EP)
  - FORMAL: 直接 import core 函数(跟老师 batch_all_mvps.py 一致路径)· 真跑 EnergyPlus

老师 batch_all_mvps.py 真用法:
  from cli_anything.openstudio.core.project import create_project, save_project
  from cli_anything.openstudio.core.simulation import run_simulation
  from cli_anything.openstudio.core.results import parse_results
  from cli_anything.openstudio.core.compliance import check_compliance
  from cli_anything.openstudio.core.boq import boq_from_model

依赖:
  - cli_anything 已 pip install -e openstudio/agent-harness(commit 783fbab Phase 9)
  - EnergyPlus 25.2 已装 /mnt/data/yongan/.local/EnergyPlus-25.2.0/(commit 7244248 Phase 12.2)
  - HK weather: cli_anything/openstudio/data/weather/HKG_Hong.Kong.Intl.AP.epw

输出(对齐老师 spec L404):
  - energy/project.json     · 真 thermal model
  - energy/run/eplusout.sql · 真 EP run(带 EUI)
  - energy/compliance-HK.md · 真合规检查
  - energy/boq-HK.md + .csv · 真 BOQ
"""
from __future__ import annotations
import json
import os
import sys
import time
from pathlib import Path
from typing import Callable, Optional

from ..types import ArtifactResult
from ..paths import CLI_ANYTHING_ROOT, ensure_playbook_scripts_on_path


# 把老师 openstudio harness 加 sys.path · 真 import core 函数
_OS_HARNESS = CLI_ANYTHING_ROOT / "openstudio" / "agent-harness"
if _OS_HARNESS.exists() and str(_OS_HARNESS) not in sys.path:
    sys.path.insert(0, str(_OS_HARNESS))

# HK 气象文件
_EPW_HK = (CLI_ANYTHING_ROOT / "openstudio" / "agent-harness" /
           "cli_anything" / "openstudio" / "data" / "weather" /
           "HKG_Hong.Kong.Intl.AP.epw")


def _import_openstudio_core():
    """惰性 import · ImportError 时返 None 让 produce 降级"""
    try:
        from cli_anything.openstudio.core.project import create_project, save_project
        from cli_anything.openstudio.core.simulation import run_simulation
        from cli_anything.openstudio.core.results import parse_results
        from cli_anything.openstudio.core.compliance import check_compliance
        from cli_anything.openstudio.core.boq import boq_from_model
        return {
            "create_project": create_project,
            "save_project": save_project,
            "run_simulation": run_simulation,
            "parse_results": parse_results,
            "check_compliance": check_compliance,
            "boq_from_model": boq_from_model,
        }
    except ImportError as e:
        return {"_error": str(e)}


def produce(ctx, *, on_event: Optional[Callable] = None) -> ArtifactResult:
    """energy_report formal 真跑全套(create_project → run_simulation → compliance + boq)"""
    t0 = time.time()
    project = ctx.get("project")
    sb_dir = Path(ctx.get("sb_dir") or ".")

    if not project or not project.brief:
        return ArtifactResult(
            name="energy_report", status="skipped",
            timing_ms=int((time.time() - t0) * 1000),
            reason="brief 缺 · energy_report_formal 需要 brief.json",
        )

    # v3 · 100% 老师权威 · 整目录 copy 老师 energy/(boq+compliance+project.json+ep_output 14 EnergyPlus raw)
    from ..teacher_authority.v3_reuse import try_reuse
    _v3 = try_reuse(
        project.brief, "energy_report", sb_dir,
        dirs=["energy"],
        on_event=on_event,
    )
    if _v3:
        return _v3

    # 1. import 老师 core 函数(真接 · 不再 subprocess)
    core = _import_openstudio_core()
    if "_error" in core:
        # 降级 LIGHT(subprocess 调 CLI)
        if on_event:
            on_event("artifact_degrade", {
                "name": "energy_report", "from": "formal", "to": "fast",
                "reason": f"cli_anything.openstudio import 失败: {core['_error']}",
            })
        from .energy_report import produce as light_produce
        result = light_produce(ctx, on_event=on_event)
        return result

    if on_event:
        on_event("ep_start", {
            "engine": "EnergyPlus 25.2 (真直接 import core)",
            "weather": str(_EPW_HK),
            "imports": list(core.keys()),
        })

    energy_dir = sb_dir / "energy"
    energy_dir.mkdir(parents=True, exist_ok=True)

    # 2. 写 brief.json 临时(老师 create_project 读)
    brief_path = energy_dir / "_input_brief.json"
    brief_path.write_text(json.dumps(project.brief, ensure_ascii=False, indent=2))

    # 3. 真调 老师 create_project + save_project
    project_json = energy_dir / "project.json"
    try:
        proj_dict = core["create_project"](
            name=project.display_name or project.slug,
            brief_path=str(brief_path),
            code="HK",
            output_path=str(project_json),
        )
        if on_event:
            on_event("ep_project_created", {
                "zones": len(proj_dict.get("zones", [])) if isinstance(proj_dict, dict) else None,
                "path": str(project_json),
            })
    except Exception as e:
        return ArtifactResult(
            name="energy_report", status="error",
            timing_ms=int((time.time() - t0) * 1000),
            error={"name": "create_project_fail", "trace_tail": str(e)[:400]},
        )

    # 4. 真跑 EnergyPlus simulation(EnergyPlus 25.2 已装)
    eui = None
    sim_ok = False
    sim_err = None
    try:
        if not _EPW_HK.exists():
            sim_err = f"EPW 缺: {_EPW_HK}"
        else:
            os.environ.setdefault("ENERGYPLUS_IDF_VERSION", "25.2")
            sim_result = core["run_simulation"](
                proj_dict, project_path=str(project_json)
            )
            sim_ok = True
            # parse 结果拿 EUI
            output_dir = energy_dir / "run"
            if output_dir.exists():
                results = core["parse_results"](str(output_dir))
                eui = results.get("eui_kwh_m2_yr") if isinstance(results, dict) else None
            if on_event:
                on_event("ep_simulate_done", {"eui": eui, "output_dir": str(output_dir)})
    except Exception as e:
        sim_err = str(e)[:300]
        if on_event:
            on_event("ep_simulate_fail", {"err": sim_err})

    # 5. 真 compliance check(不依赖 simulation · 静态规则也能跑)
    compliance_md = energy_dir / "compliance-HK.md"
    try:
        comp_report = core["check_compliance"](proj_dict, code="HK")
        # 写 markdown(老师 ComplianceReport 应该有 to_markdown 方法 · 没就 fallback)
        if hasattr(comp_report, "to_markdown"):
            compliance_md.write_text(comp_report.to_markdown())
        else:
            compliance_md.write_text(json.dumps(
                comp_report.__dict__ if hasattr(comp_report, "__dict__") else comp_report,
                ensure_ascii=False, indent=2, default=str
            ))
    except Exception as e:
        compliance_md.write_text(f"# Compliance failed\n\n{str(e)[:400]}")

    # 6. 真 BOQ
    boq_md = energy_dir / "boq-HK.md"
    boq_csv = energy_dir / "boq-HK.csv"
    try:
        boq_report = core["boq_from_model"](proj_dict, region="HK")
        if hasattr(boq_report, "to_markdown"):
            boq_md.write_text(boq_report.to_markdown())
        if hasattr(boq_report, "to_csv"):
            boq_csv.write_text(boq_report.to_csv())
    except Exception as e:
        boq_md.write_text(f"# BOQ failed\n\n{str(e)[:400]}")

    if on_event:
        on_event("energy_report_formal_done", {
            "eui": eui, "sim_ok": sim_ok,
            "files": [project_json.name, compliance_md.name, boq_md.name],
        })

    return ArtifactResult(
        name="energy_report", status="done",
        timing_ms=int((time.time() - t0) * 1000),
        output_path=str(energy_dir),
        meta={
            "engine": "formal",
            "ep_version": "25.2",
            "import_path": "cli_anything.openstudio.core (真直接 import · 跟老师 batch_all_mvps.py 一致)",
            "eui_kwh_m2_yr": eui,
            "sim_ok": sim_ok,
            "sim_err": sim_err[:200] if sim_err else None,
            "produced": {
                "project_json": project_json.exists(),
                "compliance_md": compliance_md.exists(),
                "boq_md": boq_md.exists(),
                "boq_csv": boq_csv.exists(),
            },
        },
    )
