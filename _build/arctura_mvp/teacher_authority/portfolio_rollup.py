"""老师 P11 全库 rollup · case-studies/ 顶层聚合

按 case-study-autogen-pipeline.md L62-66 真 spec:
  case-studies/portfolio-index.md   ← 官网总入口
  case-studies/impact-dashboard.md  ← tenure/RAE 总览
  case-studies/metrics.json         ← 全库 rollup
  case-studies/report.json          ← pipeline 执行摘要
  case-studies/{portfolio,impact,sales}/<slug>.md ← ln -s 软链回单 MVP

我们 thin runner 调老师 aggregate.py 跑全库 rollup · 0 算法重写。
"""
from __future__ import annotations
import json, os, subprocess, sys, time
from pathlib import Path
from typing import Optional

from ..paths import PLAYBOOKS_SCRIPTS, STARTUP_BUILDING_ROOT


_CS_SCRIPT = PLAYBOOKS_SCRIPTS / "case-study"
_CASE_STUDIES_DIR = STARTUP_BUILDING_ROOT / "case-studies"
_PY = sys.executable


def run_aggregate() -> dict:
    """老师 aggregate.py · 全库 rollup → case-studies/{metrics.json, report.json}"""
    t0 = time.time()
    script = _CS_SCRIPT / "aggregate.py"
    if not script.exists():
        return {"ok": False, "error": f"老师 aggregate.py 缺: {script}"}
    try:
        proc = subprocess.run(
            [_PY, str(script)],
            capture_output=True, text=True, timeout=120,
        )
        return {
            "ok": proc.returncode == 0,
            "duration_ms": int((time.time() - t0) * 1000),
            "stdout_tail": (proc.stdout or "")[-300:],
            "stderr_tail": (proc.stderr or "")[-300:],
        }
    except Exception as e:
        return {"ok": False, "error": str(e)[:300]}


def list_aggregated_artifacts() -> dict:
    """检查老师 case-studies/ 4 顶层产物 + 23 portfolio/impact/sales 软链"""
    if not _CASE_STUDIES_DIR.exists():
        return {"ok": False, "error": f"case-studies/ 不存在: {_CASE_STUDIES_DIR}"}

    out = {
        "portfolio_index_md": (_CASE_STUDIES_DIR / "portfolio-index.md").exists(),
        "impact_dashboard_md": (_CASE_STUDIES_DIR / "impact-dashboard.md").exists(),
        "metrics_json": (_CASE_STUDIES_DIR / "metrics.json").exists(),
        "report_json": (_CASE_STUDIES_DIR / "report.json").exists(),
    }

    # 数 portfolio/ impact/ sales/ 软链(老师 ln -s 软链回单 MVP case-study/*.md)
    for sub in ["portfolio", "impact", "sales"]:
        sub_dir = _CASE_STUDIES_DIR / sub
        if sub_dir.exists():
            md_count = len(list(sub_dir.glob("*.md")))
            out[f"{sub}_md_count"] = md_count
            # 数软链(老师真用 ln -s · 单点修改)
            symlinks = [f for f in sub_dir.iterdir() if f.is_symlink()]
            out[f"{sub}_symlinks_count"] = len(symlinks)
        else:
            out[f"{sub}_md_count"] = 0
            out[f"{sub}_symlinks_count"] = 0

    return out


def get_global_metrics() -> Optional[dict]:
    """读老师 case-studies/metrics.json 全库 rollup(老师 aggregate.py 输出)"""
    p = _CASE_STUDIES_DIR / "metrics.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def get_portfolio_index() -> Optional[str]:
    """读老师 case-studies/portfolio-index.md 全库官网总入口"""
    p = _CASE_STUDIES_DIR / "portfolio-index.md"
    if not p.exists():
        return None
    return p.read_text(encoding="utf-8")


def get_impact_dashboard() -> Optional[str]:
    """读老师 case-studies/impact-dashboard.md(tenure/RAE 总览)"""
    p = _CASE_STUDIES_DIR / "impact-dashboard.md"
    if not p.exists():
        return None
    return p.read_text(encoding="utf-8")


def verify_runner() -> dict:
    """全库 rollup 自检"""
    return {
        "case_studies_dir_exists": _CASE_STUDIES_DIR.exists(),
        "aggregate_script": (_CS_SCRIPT / "aggregate.py").exists(),
        **list_aggregated_artifacts(),
    }


if __name__ == "__main__":
    print(json.dumps(verify_runner(), indent=2, ensure_ascii=False))
