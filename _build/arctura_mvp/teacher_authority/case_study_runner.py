"""老师 P11 Case Study Auto-Gen · LLM 双轨 + thumbs + 全库 rollup

按 playbooks/case-study-autogen-pipeline.md 真 spec(L548-650):
  方式 A · Claude Native(默认 · populate_narratives.py)· 23 × 3 = 69 narrative txt
  方式 B · Gemini CLI fallback(narrate.py)· 失败降级 flash · 占位符 _[
  防覆盖 · skip-if-exists default · --overwrite 强制
  缩略图 4 规格(hero 16:9 / card 4:3 × 4 / index 4:3 / og 1.91:1)· make_thumbs.py
  全库 rollup · case-studies/{portfolio-index, impact-dashboard, metrics, report}.md
  ln -s 软链 · 单点修改

0 算法重写 · subprocess 直调老师 7 个 case-study 脚本。
"""
from __future__ import annotations
import json, subprocess, sys, time
from pathlib import Path
from typing import Callable, Optional

from ..paths import PLAYBOOKS_SCRIPTS

_CS = PLAYBOOKS_SCRIPTS / "case-study"
_PY = sys.executable


def _run(step: str, cmd: list, *, timeout: int = 120) -> dict:
    t0 = time.time()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return {"step": step, "ok": proc.returncode == 0,
                "duration_ms": int((time.time() - t0) * 1000),
                "stdout_tail": (proc.stdout or "")[-300:],
                "stderr_tail": (proc.stderr or "")[-300:]}
    except Exception as e:
        return {"step": step, "ok": False,
                "duration_ms": int((time.time() - t0) * 1000),
                "stderr_tail": str(e)[:300]}


# ───── 老师 7 case-study 脚本 thin ─────────────────────────

def extract_metrics(mvp_dir: Path) -> dict:
    """老师 extract_metrics.py · 单 MVP → metrics.json"""
    return _run("extract_metrics",
                [_PY, str(_CS / "extract_metrics.py"), str(mvp_dir)],
                timeout=30)


def populate_narratives() -> dict:
    """方式 A · Claude Native 维护的 dict 一次性写入 23×3=69 narrative txt"""
    return _run("populate_narratives",
                [_PY, str(_CS / "populate_narratives.py")],
                timeout=60)


def narrate_single(mvp_dir: Path, *, template: str = "portfolio",
                   overwrite: bool = False) -> dict:
    """方式 B · Gemini CLI fallback · skip-if-exists default · template ∈ {portfolio,impact,sales}"""
    cmd = [_PY, str(_CS / "narrate.py"),
           "--metrics", str(mvp_dir / "case-study" / "metrics.json"),
           "--template", template,
           "--output", str(mvp_dir / "case-study" / f"narrative-{template}.txt")]
    if overwrite:
        cmd.append("--overwrite")
    return _run(f"narrate_{template}", cmd, timeout=120)


def render_templates(mvp_dir: Path) -> dict:
    """老师 render_templates.py · 注入 narrative + metrics → 3 模板 md"""
    return _run("render_templates",
                [_PY, str(_CS / "render_templates.py"), str(mvp_dir)],
                timeout=30)


def make_thumbs(mvp_dir: Path) -> dict:
    """老师 thumbs 生成 inline 在 extract_metrics/run_one · 不是独立脚本
    · run_one.py 已含 4 规格 thumbs(hero/card×4/index/og)
    · 单独跑 thumbs · 调 extract_metrics(已含 thumbs 流程)"""
    return extract_metrics(mvp_dir)  # extract_metrics 已含 thumbs 副作用


def aggregate_all() -> dict:
    """老师 aggregate.py · 全库 rollup → case-studies/{metrics.json, report.json}"""
    return _run("aggregate",
                [_PY, str(_CS / "aggregate.py")],
                timeout=60)


def run_one_mvp(mvp_dir: Path, *, on_event: Optional[Callable] = None) -> dict:
    """老师 run_one.py · 单 MVP P11 全套(metrics + narrative + 3 模板 + thumbs)"""
    return _run("run_one",
                [_PY, str(_CS / "run_one.py"), str(mvp_dir)],
                timeout=180)


def run_all_mvps() -> dict:
    """老师 run_all.py · 跨 MVP 批量 + rollup"""
    return _run("run_all",
                [_PY, str(_CS / "run_all.py")],
                timeout=600)


# ───── P11 完整 orchestrator(单 MVP 顺序)─────────────────

def run_p11_for_mvp(mvp_dir: Path, *,
                    overwrite_narrative: bool = False,
                    on_event: Optional[Callable] = None) -> dict:
    """单 MVP P11 完整 5 步 · 老师真 spec 顺序:
       1. extract_metrics → metrics.json
       2. populate_narratives(Claude Native · 已写) OR narrate_single(Gemini fallback)
       3. render_templates → 3 模板 md
       4. make_thumbs → 4 规格
       5. (上层 caller 跑 aggregate_all 全库 rollup)
    """
    mvp_dir = Path(mvp_dir)
    if on_event:
        on_event("p11_start", {"mvp_dir": str(mvp_dir)})

    steps = []
    s1 = extract_metrics(mvp_dir); steps.append(s1)
    if not s1["ok"]:
        return {"ok": False, "fatal_at": "extract_metrics", "steps": steps}

    # populate_narratives 全库一次性 · 跑 1 次即可(本函数不重复跑 · caller 决定)
    # 这里默认走 narrate_single 三次(若 Claude Native 已填则 skip-if-exists 自动跳)
    for tmpl in ["portfolio", "impact", "sales"]:
        s = narrate_single(mvp_dir, template=tmpl, overwrite=overwrite_narrative)
        steps.append(s)

    s_render = render_templates(mvp_dir); steps.append(s_render)
    s_thumbs = make_thumbs(mvp_dir); steps.append(s_thumbs)

    if on_event:
        on_event("p11_done", {"steps_count": len(steps),
                              "ok": all(s["ok"] for s in steps)})

    return {"ok": all(s["ok"] for s in steps),
            "steps_count": len(steps),
            "steps": steps,
            "total_duration_ms": sum(s.get("duration_ms", 0) for s in steps)}


def verify_runner() -> dict:
    return {
        "extract_metrics":      (_CS / "extract_metrics.py").exists(),
        "populate_narratives":  (_CS / "populate_narratives.py").exists(),
        "narrate":              (_CS / "narrate.py").exists(),
        "render_templates":     (_CS / "render_templates.py").exists(),
        "make_thumbs":          (_CS / "make_thumbs.py").exists(),
        "aggregate":            (_CS / "aggregate.py").exists(),
        "run_one":              (_CS / "run_one.py").exists(),
        "run_all":              (_CS / "run_all.py").exists(),
    }


if __name__ == "__main__":
    print(json.dumps(verify_runner(), indent=2, ensure_ascii=False))
