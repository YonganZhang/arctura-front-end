"""worker pipeline orchestrator · 模仿老师 batch_all_mvps.py 7 步骤结构

老师 batch_all_mvps.py 真权威结构(Pipeline flow per MVP):
  1. _find_ifc(exports/) → auto enrich-ifc(add properties/materials)
  2. create_project from enriched IFC + brief.json(merged thermal model)
  3. run_simulation(EnergyPlus)
  4. parse_results(EUI 等)
  5. check_compliance(HK/CN/ASHRAE)
  6. boq_from_model(HK 价表)
  7. render_report + render_csv(boq-HK.md / .csv)

老师用 cli_anything.openstudio.core.{project,simulation,results,compliance,boq} 真 import。
我们已 pip install -e openstudio harness · 完整 cli_anything 可 import。

本模块 = thin orchestrator(0 算法)· 我们 worker.py 的 run_one 应**直接复用老师函数链**,
不重写。
"""
from __future__ import annotations
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# 老师真 import 路径(老师 batch_all_mvps L20-L24)
try:
    from cli_anything.openstudio.core.project import create_project, save_project
    from cli_anything.openstudio.core.simulation import run_simulation
    from cli_anything.openstudio.core.results import parse_results
    from cli_anything.openstudio.core.compliance import check_compliance
    from cli_anything.openstudio.core.boq import boq_from_model, render_report as render_boq_md, render_csv as render_boq_csv
    _OS_AVAILABLE = True
except ImportError:
    _OS_AVAILABLE = False


@dataclass
class TeacherStepResult:
    step: str
    ok: bool
    duration_ms: int
    payload: dict = field(default_factory=dict)
    error: Optional[str] = None

    def to_meta(self) -> dict:
        return {"step": self.step, "ok": self.ok, "duration_ms": self.duration_ms,
                "error": self.error[-200:] if self.error else None}


def _step(name: str, fn, *args, **kwargs) -> TeacherStepResult:
    t0 = time.time()
    try:
        out = fn(*args, **kwargs)
        return TeacherStepResult(name, True, int((time.time()-t0)*1000), payload={"out": out})
    except Exception as e:
        return TeacherStepResult(name, False, int((time.time()-t0)*1000), error=str(e)[:500])


def find_ifc(mvp_folder: Path) -> Optional[Path]:
    """老师 _find_ifc · 从 exports/ 找 IFC"""
    exports = mvp_folder / "exports"
    if not exports.is_dir():
        return None
    ifcs = sorted(exports.glob("*.ifc"))
    return ifcs[0] if ifcs else None


def run_teacher_7step_pipeline(
    mvp_folder: Path,
    *,
    weather_epw: Optional[Path] = None,
    region: str = "HK",
    code: str = "HK",
) -> dict:
    """老师 batch_all_mvps run_one · 7 步骤完整 pipeline

    返:{ok, total_duration_ms, results: {eui_kwh_m2_yr, boq_grand_total, ...}, steps: [...]}
    """
    if not _OS_AVAILABLE:
        return {"ok": False, "error": "cli_anything.openstudio 未装(pip install -e openstudio harness)",
                "steps": []}

    mvp_folder = Path(mvp_folder)
    brief_path = mvp_folder / "brief.json"
    if not brief_path.exists():
        return {"ok": False, "error": f"brief.json 缺: {brief_path}", "steps": []}

    steps: list[TeacherStepResult] = []
    results: dict = {}

    # Step 1 · IFC enrich(老师 _auto_enrich · 我们暂跳过 enrich · 用现有 IFC)
    ifc = find_ifc(mvp_folder)
    steps.append(TeacherStepResult("find_ifc", ifc is not None, 0,
                                   payload={"ifc": str(ifc) if ifc else None}))

    # Step 2 · create_project(brief + IFC → project.json)
    s2 = _step("create_project", lambda: create_project(
        brief_path=str(brief_path),
        ifc_path=str(ifc) if ifc else None,
        out_dir=str(mvp_folder / "energy"),
    ))
    steps.append(s2)
    if not s2.ok:
        return _summary(steps, results, fatal_at="create_project")
    proj = s2.payload.get("out")

    # Step 3 · run_simulation(EnergyPlus)
    weather = weather_epw or _default_weather()
    s3 = _step("run_simulation", lambda: run_simulation(proj, weather=str(weather))
               if weather else (_skip("weather 缺"),))
    steps.append(s3)

    # Step 4 · parse_results(EUI)
    s4 = _step("parse_results", lambda: parse_results(proj))
    steps.append(s4)
    if s4.ok and s4.payload.get("out"):
        r = s4.payload["out"]
        results["eui_kwh_m2_yr"] = getattr(r, "eui_kwh_m2_yr", None) or (r.get("eui_kwh_m2_yr") if isinstance(r, dict) else None)

    # Step 5 · check_compliance
    s5 = _step("check_compliance", lambda: check_compliance(proj, code=code))
    steps.append(s5)

    # Step 6 · boq_from_model
    s6 = _step("boq_from_model", lambda: boq_from_model(proj, region=region))
    steps.append(s6)
    if s6.ok and s6.payload.get("out"):
        boq = s6.payload["out"]
        results["boq_grand_total"] = getattr(boq, "grand_total", None)
        results["boq_cost_per_m2"] = getattr(boq, "cost_per_m2", None)
        results["boq_currency"] = getattr(boq, "currency", None)

    # Step 7 · render boq-HK.{md,csv}
    if s6.ok and s6.payload.get("out"):
        boq = s6.payload["out"]
        energy_dir = mvp_folder / "energy"
        energy_dir.mkdir(exist_ok=True)
        try:
            (energy_dir / f"boq-{region}.md").write_text(render_boq_md(boq))
            (energy_dir / f"boq-{region}.csv").write_text(render_boq_csv(boq))
            steps.append(TeacherStepResult("render_boq", True, 0,
                                           payload={"md": str(energy_dir / f"boq-{region}.md"),
                                                    "csv": str(energy_dir / f"boq-{region}.csv")}))
        except Exception as e:
            steps.append(TeacherStepResult("render_boq", False, 0, error=str(e)[:200]))

    return _summary(steps, results)


def _default_weather() -> Optional[Path]:
    """老师 batch_all_mvps L26 默认 HK weather"""
    p = Path("/mnt/data/yongan/projects/自己-公司项目-b46280/Building-CLI-Anything/CLI-Anything/openstudio/agent-harness/cli_anything/openstudio/data/weather/HKG_Hong.Kong.Intl.AP.epw")
    return p if p.exists() else None


def _skip(reason: str) -> dict:
    return {"_skipped": True, "reason": reason}


def _summary(steps, results, *, fatal_at=None) -> dict:
    return {
        "ok": fatal_at is None and all(s.ok or s.payload.get("out", {}).get("_skipped") for s in steps if s.step != "find_ifc"),
        "fatal_at": fatal_at,
        "total_duration_ms": sum(s.duration_ms for s in steps),
        "steps": [s.to_meta() for s in steps],
        "results": results,
    }


def verify_runner() -> dict:
    return {
        "openstudio_available": _OS_AVAILABLE,
        "default_weather_exists": _default_weather() is not None,
    }


if __name__ == "__main__":
    import json
    print(json.dumps(verify_runner(), indent=2, ensure_ascii=False))
