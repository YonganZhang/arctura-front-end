"""energy_report · 能耗 + 合规 + BOQ（Phase 9）

spec L404 · energy/project.json + compliance-HK.md + boq-HK.md + boq-HK.csv

实装（LIGHT 模式）：
  - brief.json → cli-anything-openstudio project new --from-brief --code HK
  - project.json → cli-anything-openstudio report compliance --code HK
  - project.json → cli-anything-openstudio report boq --region HK
  - EUI 真值需 `run simulate` + EnergyPlus binary · LIGHT 跳过（标 "EUI pending"）

工件 4 份：
  1. energy/project.json · LIGHT 能产（纯 JSON 操作）
  2. compliance-HK.md · LIGHT 能产（规则检查 · 不需 EP）
  3. boq-HK.md + boq-HK.csv · LIGHT 能产（材料×单价 · 不需 EP）
  4. run/eplusout.sql · 需 EP binary · 暂跳过
"""
from __future__ import annotations
import json
import shutil
import subprocess
import time
from pathlib import Path
from typing import Callable, Optional

from ..types import ArtifactResult
from ..paths import CLI_ANYTHING_ROOT

_OS_CLI = shutil.which("cli-anything-openstudio") or "cli-anything-openstudio"
# HK 气象文件 · 严老师 openstudio harness 自带
_EPW_HK = CLI_ANYTHING_ROOT / "openstudio" / "agent-harness" / "cli_anything" / "openstudio" / "data" / "weather" / "HKG_Hong.Kong.Intl.AP.epw"


def _write_brief_json(brief: dict, path: Path):
    """写 brief 到临时 JSON · 供 openstudio_cli 读"""
    path.write_text(json.dumps(brief, ensure_ascii=False, indent=2))


def _run_os_cli(args: list[str], timeout: int = 60) -> tuple[bool, str, str]:
    """调 openstudio CLI · 返 (ok, stdout, stderr)"""
    try:
        proc = subprocess.run(
            [_OS_CLI, *args],
            capture_output=True, text=True, timeout=timeout,
        )
        return proc.returncode == 0, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired:
        return False, "", f"timeout({timeout}s)"
    except FileNotFoundError:
        return False, "", "cli-anything-openstudio not found · pip install -e openstudio/agent-harness"


def produce(ctx: dict, on_event: Optional[Callable] = None) -> ArtifactResult:
    t0 = time.time()
    project = ctx["project"]
    sb_dir: Path = ctx["sb_dir"]

    if not project.brief:
        return ArtifactResult(
            name="energy_report", status="skipped",
            timing_ms=int((time.time()-t0)*1000),
            reason="brief 缺 · 无法生成 energy project",
        )

    if not shutil.which("cli-anything-openstudio"):
        return ArtifactResult(
            name="energy_report", status="skipped",
            timing_ms=int((time.time()-t0)*1000),
            reason="cli-anything-openstudio 未装 · 见 vendor/README.md 装 harness",
        )

    energy_dir = sb_dir / "energy"
    energy_dir.mkdir(parents=True, exist_ok=True)

    # 1. 写 brief.json 临时 · openstudio CLI 读
    tmp_brief = energy_dir / "_input_brief.json"
    _write_brief_json(project.brief, tmp_brief)
    project_json = energy_dir / "project.json"

    errors = []

    # Step 1 · project new --from-brief
    ok, out, err = _run_os_cli([
        "project", "new",
        "-n", project.display_name or project.slug,
        "--from-brief", str(tmp_brief),
        "-c", "HK",
        "-o", str(project_json),
    ])
    if not ok:
        errors.append(f"project_new: {err[:200]}")
        tmp_brief.unlink(missing_ok=True)
        return ArtifactResult(
            name="energy_report", status="error",
            timing_ms=int((time.time()-t0)*1000),
            error={"name": "project_new_fail", "trace_tail": " | ".join(errors)[:300]},
        )

    # Step 1.5 · run simulate · 产 EnergyPlus results · compliance 硬依赖
    # Phase 9.3 · 装 EP 25.1 后可跑 · 无 EP 时会失败 · compliance 也就缺
    if _EPW_HK.exists() and shutil.which("energyplus"):
        ok, out, err = _run_os_cli([
            "-p", str(project_json),
            "run", "simulate",
            "--weather", str(_EPW_HK),
        ], timeout=300)   # 年度模拟 · 给 5 分钟上限
        if not ok:
            errors.append(f"simulate: {err[:200]}")

    # Step 2 · report compliance · 输出 compliance-HK.md（需 simulate 成功）
    compliance_path = energy_dir / "compliance-HK.md"
    ok, out, err = _run_os_cli([
        "-p", str(project_json),
        "report", "compliance",
        "-c", "HK",
        "-o", str(compliance_path),
    ])
    if not ok:
        errors.append(f"compliance: {err[:200]}")

    # Step 3 · report boq · 输出 boq-HK.md + .csv
    boq_md = energy_dir / "boq-HK.md"
    boq_csv = energy_dir / "boq-HK.csv"
    ok, out, err = _run_os_cli([
        "-p", str(project_json),
        "report", "boq",
        "--region", "HK",
        "-o", str(boq_md),
        "--csv", str(boq_csv),
    ])
    if not ok:
        errors.append(f"boq: {err[:200]}")

    # 清临时
    tmp_brief.unlink(missing_ok=True)

    produced = {
        "project_json": project_json.exists(),
        "compliance": compliance_path.exists(),
        "boq_md": boq_md.exists(),
        "boq_csv": boq_csv.exists(),
    }
    ok_count = sum(1 for v in produced.values() if v)
    ep_available = bool(_EPW_HK.exists() and shutil.which("energyplus"))

    return ArtifactResult(
        name="energy_report",
        status="done" if ok_count >= 2 else "error",
        timing_ms=int((time.time()-t0)*1000),
        output_path=str(energy_dir),
        meta={
            "produced": produced,
            "count": ok_count,
            "ep_available": ep_available,
            "errors": errors or None,
        },
    )
