"""老师 P2 建筑设计 Pipeline · 真 22 步编排器

按 playbooks/architecture-pipeline.md 真 spec:
  P1 18 步基础上 +4 步:
  - Site Plan(总平面)
  - Multi-floor Plans(N 层平面)
  - 4 Elevations(立面 N/S/E/W)
  - Section(剖面 AA)
  - 3 体量视角(massing/street/interior)
  - Site Entourage(可选 · 真实 GLB 户外)

0 算法重写 · 复用 site_entourage_runner + 老师 architecture-pipeline.md spec。
"""
from __future__ import annotations
import json, shutil, subprocess, sys, time
from pathlib import Path
from typing import Callable, Optional

from ..paths import PLAYBOOKS_SCRIPTS, STARTUP_BUILDING_ROOT
from .pipeline_p1 import StepResult, _run, _find_blender, _find_marp, _summary
from .site_entourage_runner import populate_site, render_entourage, qa_visualize

_MARP_DECK = STARTUP_BUILDING_ROOT / ".claude" / "skills" / "marp-deck" / "scripts"
_PY = sys.executable


def run_p2_pipeline(
    arch_mvp_dir: Path,
    *,
    tier: str = "full",
    addons: Optional[set] = None,
    use_site_entourage: bool = True,
    on_event: Optional[Callable] = None,
) -> dict:
    """老师 P2 22 步建筑 pipeline · 真编排"""
    addons = addons or set()
    arch_mvp_dir = Path(arch_mvp_dir)
    steps: list[StepResult] = []
    gate_failures: list[str] = []
    t_start = time.time()

    if on_event:
        on_event("p2_pipeline_start", {"arch_mvp_dir": str(arch_mvp_dir), "tier": tier})

    brief = arch_mvp_dir / "brief.json"
    if not brief.exists():
        return _summary(steps, gate_failures, fatal_at="brief.json missing",
                        t_start=t_start, tier=tier, render_path="path_b_arch")

    blender = _find_blender()

    # Step 3: moodboard
    gen_moodboard = _MARP_DECK / "gen_moodboard.py"
    if gen_moodboard.exists():
        steps.append(_run("p2_step3_moodboard",
                          [_PY, str(gen_moodboard), str(arch_mvp_dir)],
                          timeout=60, on_event=on_event))

    # Step 4: Build arch Blender scene(老师手写 _render_script.py · 我们假定已存在)
    # _render_script.py 老师 P2 是手写 80+ obj · 我们 worker 不重写 · 假定 brief 有 _render_script.py 模板

    # Step 5: Multi-angle render(massing / street / interior)
    if blender and (arch_mvp_dir / "_render_multi.py").exists():
        steps.append(_run("p2_step5_render_multi",
                          [blender, "-b", "--python", str(arch_mvp_dir / "_render_multi.py")],
                          timeout=600, on_event=on_event))

    # Step 6: Site Plan(老师真 Inkscape CLI 1:200~1:500)
    # 不直接跑 · 留给老师 _build_floorplan.sh 或手画(老师 4-27 起手画 default)
    if (arch_mvp_dir / "_build_floorplan.sh").exists():
        steps.append(_run("p2_step6_build_floorplan",
                          ["bash", str(arch_mvp_dir / "_build_floorplan.sh")],
                          timeout=120, on_event=on_event))

    # Step 6.5(可选)· Site Entourage Phase 1 populate_site
    if use_site_entourage:
        r = populate_site(arch_mvp_dir)
        steps.append(StepResult(step="p2_step65_populate_site", ok=r.get("ok", False),
                               duration_ms=r.get("duration_ms", 0),
                               stderr_tail=r.get("stderr_tail", "")))

    # Step 7-9: Multi-floor + 4 Elevations + Section
    # 老师真 CLI 是 inkscape · 我们 worker 不直接跑 · 假定 _build_*.sh 已含
    for sub in ["_build_floors.sh", "_build_elevations.sh", "_build_section.sh"]:
        sh = arch_mvp_dir / sub
        if sh.exists():
            steps.append(_run(f"p2_step{sub}",
                              ["bash", str(sh)],
                              timeout=180, on_event=on_event))

    # Step 9.5(可选)· Site Entourage render_entourage(街景)
    if use_site_entourage and blender:
        r = render_entourage(arch_mvp_dir)
        steps.append(StepResult(step="p2_step95_render_entourage", ok=r.get("ok", False),
                               duration_ms=r.get("duration_ms", 0),
                               stderr_tail=r.get("stderr_tail", "")))

    # Step 13-14: Marp deck-client + .pptx + .pdf
    deck_md = arch_mvp_dir / "decks" / "deck-client.md"
    if deck_md.exists() and _find_marp():
        marp = _find_marp()
        (arch_mvp_dir / "decks").mkdir(exist_ok=True)
        steps.append(_run("p2_step13_marp_pptx",
                          [marp, str(deck_md), "--pptx", "-o", str(arch_mvp_dir / "decks" / "deck-client.pptx"), "--allow-local-files"],
                          timeout=60, on_event=on_event))
        steps.append(_run("p2_step14_marp_pdf",
                          [marp, str(deck_md), "--pdf", "-o", str(arch_mvp_dir / "decks" / "deck-client.pdf"), "--allow-local-files"],
                          timeout=60, on_event=on_event))

    # Step 16: Verify(verify_mvp_exports gate · arch tier)
    verify_script = PLAYBOOKS_SCRIPTS / "verify_mvp_exports.py"
    if verify_script.exists():
        verify_step = _run("p2_step16_verify_GATE",
                           [_PY, str(verify_script), str(arch_mvp_dir), "--tier", tier],
                           timeout=30, is_gate=True, on_event=on_event)
        steps.append(verify_step)
        if verify_step.is_gate and not verify_step.ok:
            gate_failures.append(verify_step.step)

    return _summary(steps, gate_failures, fatal_at=None, t_start=t_start,
                    tier=tier, render_path="p2_arch")


def verify_p2() -> dict:
    return {
        "site_entourage_dir": (PLAYBOOKS_SCRIPTS / "site-entourage").exists(),
        "blender": _find_blender() is not None,
        "marp": _find_marp() is not None,
    }


if __name__ == "__main__":
    print(json.dumps(verify_p2(), indent=2, ensure_ascii=False))
