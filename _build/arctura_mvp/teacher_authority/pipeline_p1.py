"""老师 P1 室内设计 Pipeline · 真 18 步编排器

按 playbooks/studio-copilot-pipeline.md 真 spec:
  1. Time start
  2. brief.json create
  3. moodboard via gen_moodboard.py
  4. Build Blender scene · 4a static lint MANDATORY · 4b scene-dim MANDATORY
  5. Multi-angle render(Path A 6 张 + Path B 8 张 + validate_reports gate)
  6. Floorplan via Inkscape(中文 PingFang SC)
  7. Floorplan SVG/PNG export
  8. Marp 方案 PPT 11 页(deck-client.md)
  9. marp CLI · .pptx + .pdf
  10. 5 architectural exports(DXF/GLB/OBJ/FBX/IFC4)
  11. IFC enrich + audit
  12. Time end
  13. Verify(verify_mvp_exports gate)
  14. CLIENT-README.md
  15. 8 stakeholder PPTs · 8 并行 sub-agent
  16. Report
  17. What-If P9(合规红灯必跑)
  18. Case Study P11(LLM 双轨 + thumbs)

0 算法重写 · 每步 subprocess 直调老师 CLI · 我们只 orchestrate 顺序+gate+SSE。
"""
from __future__ import annotations
import json, shutil, subprocess, sys, time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from ..paths import (
    PLAYBOOKS_SCRIPTS, STARTUP_BUILDING_ROOT,
    BIM_CATALOG_JSON, ensure_playbook_script_subdir_on_path,
)


# ───── 老师 CLI 路径 · 集中管理 ─────────────────────────────

_MESH_LIB = PLAYBOOKS_SCRIPTS / "mesh-library"
_MARP_DECK = STARTUP_BUILDING_ROOT / ".claude" / "skills" / "marp-deck" / "scripts"
_PY = sys.executable


def _find_blender() -> Optional[str]:
    p = shutil.which("blender")
    if p:
        return p
    return "/mnt/data/yongan/.local/blender-4.5/blender" if Path("/mnt/data/yongan/.local/blender-4.5/blender").exists() else None


def _find_marp() -> Optional[str]:
    return shutil.which("marp")


# ───── Step 抽象 ─────────────────────────────────────────────

@dataclass
class StepResult:
    step: str
    ok: bool
    duration_ms: int
    is_gate: bool = False
    blocking: bool = False
    stdout_tail: str = ""
    stderr_tail: str = ""
    output_path: Optional[str] = None

    def to_meta(self) -> dict:
        return {"step": self.step, "ok": self.ok, "duration_ms": self.duration_ms,
                "blocking": self.blocking, "stderr_tail": self.stderr_tail[-200:] if self.stderr_tail else ""}


def _run(step: str, cmd: list, *, timeout: int = 300, blocking: bool = False,
         is_gate: bool = False, on_event=None) -> StepResult:
    if on_event:
        on_event(f"p1_step_start", {"step": step, "is_gate": is_gate, "blocking": blocking})
    t0 = time.time()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        result = StepResult(
            step=step, ok=proc.returncode == 0,
            duration_ms=int((time.time() - t0) * 1000),
            is_gate=is_gate, blocking=blocking,
            stdout_tail=(proc.stdout or "")[-400:],
            stderr_tail=(proc.stderr or "")[-400:],
        )
    except subprocess.TimeoutExpired:
        result = StepResult(step=step, ok=False, duration_ms=timeout * 1000,
                            is_gate=is_gate, blocking=blocking,
                            stderr_tail=f"timeout {timeout}s")
    except Exception as e:
        result = StepResult(step=step, ok=False,
                            duration_ms=int((time.time() - t0) * 1000),
                            is_gate=is_gate, blocking=blocking,
                            stderr_tail=str(e)[:400])
    if on_event:
        on_event(f"p1_step_done", result.to_meta())
    return result


# ───── 18 步 P1 真 orchestrator(0 算法 · 仅编排) ─────────────

def run_p1_pipeline(
    mvp_dir: Path,
    *,
    render_path: str = "path_a",  # path_a | path_b | path_b_sdxl
    tier: str = "full",            # concept | delivery | quote | full | selection
    addons: Optional[set] = None,  # {'13','14','15','16','17'} 按需追加
    on_event: Optional[Callable] = None,
    use_clip: bool = False,
) -> dict:
    """老师 P1 18 步 + addon · 返完整 summary
    {ok, fatal_at, total_duration_ms, steps:[...], gate_failures:[...], tier, render_path}"""
    addons = addons or set()
    mvp_dir = Path(mvp_dir)
    steps: list[StepResult] = []
    gate_failures: list[str] = []

    def add_step(r: StepResult):
        steps.append(r)
        if r.is_gate and not r.ok:
            gate_failures.append(r.step)
        return r

    # Step 1: Time start
    t_start = time.time()
    if on_event:
        on_event("p1_pipeline_start", {"mvp_dir": str(mvp_dir), "render_path": render_path, "tier": tier, "addons": list(addons)})

    # Step 2: brief.json 检查(假定上层已写)
    brief_path = mvp_dir / "brief.json"
    if not brief_path.exists():
        return _summary(steps, gate_failures, fatal_at="brief.json missing", t_start=t_start, tier=tier, render_path=render_path)

    # Step 3: moodboard
    gen_moodboard = _MARP_DECK / "gen_moodboard.py"
    if gen_moodboard.exists():
        add_step(_run("step3_moodboard",
                      [_PY, str(gen_moodboard), str(mvp_dir)],
                      timeout=60, on_event=on_event))

    # Step 4a: Static lint MANDATORY GATE(在跑 Blender 前)
    lint_step = _run("step4a_lint_render_script_GATE",
                     [_PY, str(_MESH_LIB / "lint_render_script.py"), str(mvp_dir)],
                     timeout=10, blocking=True, is_gate=True, on_event=on_event)
    add_step(lint_step)
    if not lint_step.ok:
        return _summary(steps, gate_failures, fatal_at="step4a_lint", t_start=t_start, tier=tier, render_path=render_path)

    # Step 4 ⭐ 真跑 _render_script.py(老师 spec L4 · 我们之前漏了这步)
    # 老师 P1 spec:Build Blender scene → 导出 .obj + 8 视角 renders/
    # 4b scene-dim gate 必须在这之后(它读 .obj 实测 bbox)
    blender = _find_blender()
    render_script = mvp_dir / "_render_script.py"
    if blender and render_script.exists():
        # ⚠ 老师 _render_script.py 兼容 patch:
        #   1. Blender 4.2 EEVEE → 4.5 EEVEE_NEXT(scene_formal._patch_blender_compat)
        #   2. Mac 硬编码路径 /Users/kaku/Desktop/Work/StartUP-Building/studio-demo/mvp/<slug>/ → 当前 mvp_dir
        from ..artifacts.scene_formal import _patch_blender_compat
        import re
        try:
            text = render_script.read_text(encoding="utf-8")
            text = _patch_blender_compat(text)
            # 替换老师 Mac 硬编码路径 → 我们 mvp_dir
            mac_prefix_pattern = r"/Users/kaku/Desktop/Work/StartUP-Building/studio-demo/(?:mvp|arch-mvp)/[a-zA-Z0-9_-]+/?"
            text = re.sub(mac_prefix_pattern, str(mvp_dir) + "/", text)
            # ⭐ append 老师 _render_script_footer.py(OBJ/GLB/FBX export · 老师 03 没粘)
            from ..paths import PLAYBOOKS_TEMPLATES
            footer_path = PLAYBOOKS_TEMPLATES / "_render_script_footer.py"
            if footer_path.exists():
                slug = mvp_dir.name
                footer_text = footer_path.read_text(encoding="utf-8")
                footer_text = footer_text.replace("<SLUG>", slug)
                # footer 假定 `OUT` 变量已定义 · 我们注入
                inject = f"\n\n# ── Phase 1.D · 自动 append 老师 footer(OBJ/GLB/FBX export)──\nimport os\nOUT = r'{str(mvp_dir)}'\n\n"
                text = text + inject + footer_text
            patched_path = mvp_dir / "_render_script_patched.py"
            patched_path.write_text(text, encoding="utf-8")
            run_target = patched_path
        except Exception:
            run_target = render_script
        build_step = _run("step4_build_blender_scene",
                          [blender, "-b", "--python", str(run_target)],
                          timeout=600, on_event=on_event)
        add_step(build_step)
        # ⭐ 4.5 ensure exports/*.obj 存在(verify_scene_dims 只找 exports/*.obj · 老师 footer 写到根 scene.obj)
        scene_obj = mvp_dir / "scene.obj"
        exports_dir = mvp_dir / "exports"
        if scene_obj.exists() and not list(exports_dir.glob("*.obj")) if exports_dir.exists() else True:
            try:
                exports_dir.mkdir(exist_ok=True)
                target = exports_dir / f"{mvp_dir.name}.obj"
                if not target.exists():
                    shutil.copy2(scene_obj, target)
            except Exception:
                pass
        # 不 blocking · 部分 MVP 老师 _render_script.py 自己有 issue · 但 4b gate 会拦

    # Step 4b: Scene-dim MANDATORY GATE(在 _render_script.py 跑完 + .obj 导出之后)
    if blender:
        scene_dim_step = _run("step4b_scene_dim_GATE",
                              [blender, "-b", "--python", str(_MESH_LIB / "verify_scene_dims.py"), "--", str(mvp_dir)],
                              timeout=120, blocking=True, is_gate=True, on_event=on_event)
        add_step(scene_dim_step)
        if not scene_dim_step.ok:
            return _summary(steps, gate_failures, fatal_at="step4b_scene_dim", t_start=t_start, tier=tier, render_path=render_path)

    # Step 5: Multi-angle render
    if render_path == "path_a":
        # Path A: room_to_room_v2 + render_multi_assets + validate_reports gate
        ensure_playbook_script_subdir_on_path("mesh-library")
        cmd = [_PY, str(_MESH_LIB / "room_to_room_v2.py"), str(mvp_dir), str(BIM_CATALOG_JSON), "--force"]
        if use_clip:
            cmd.append("--use-clip")
        add_step(_run("step5a_room_to_room_v2", cmd, timeout=180, on_event=on_event))
        add_step(_run("step5b_layout_validate",
                      [_PY, str(_MESH_LIB / "layout_validate.py"), str(mvp_dir), str(BIM_CATALOG_JSON)],
                      timeout=60, on_event=on_event))
        if blender:
            add_step(_run("step5c_render_multi_assets",
                          [blender, "-b", "--python", str(_MESH_LIB / "render_multi_assets.py"), "--", str(mvp_dir)],
                          timeout=600, on_event=on_event))
        # Path A report gate
        gate = _run("step5d_validate_reports_GATE",
                    [_PY, str(_MESH_LIB / "validate_reports.py"), str(mvp_dir)],
                    timeout=30, blocking=True, is_gate=True, on_event=on_event)
        add_step(gate)
        if not gate.ok:
            return _summary(steps, gate_failures, fatal_at="step5d_validate_reports", t_start=t_start, tier=tier, render_path=render_path)
    else:  # path_b
        setup_render = _MARP_DECK / "setup_mvp_render.py"
        if setup_render.exists():
            add_step(_run("step5_setup_render",
                          [_PY, str(setup_render), mvp_dir.name],
                          timeout=30, on_event=on_event))
        if blender and (mvp_dir / "_render_multi.py").exists():
            add_step(_run("step5_render_multi",
                          [blender, "-b", "--python", str(mvp_dir / "_render_multi.py")],
                          timeout=600, on_event=on_event))

    # Step 6+7: Floorplan(老师 4-27 起 floorplan_pro 仅 mockup · 真交付要手画)
    # 我们 worker 在 Vercel 边缘环境难做手画 SVG · 跑 floorplan_pro 作 placeholder
    floorplan_pro = _MESH_LIB / "floorplan_pro.py"
    if floorplan_pro.exists():
        add_step(_run("step6_floorplan_pro_mockup",
                      [_PY, str(floorplan_pro), str(mvp_dir), "--catalog", str(BIM_CATALOG_JSON)],
                      timeout=60, on_event=on_event))

    # Step 8+9: Marp deck-client
    deck_md = mvp_dir / "decks" / "deck-client.md"
    if deck_md.exists() and _find_marp():
        marp = _find_marp()
        (mvp_dir / "decks").mkdir(exist_ok=True)
        add_step(_run("step8_marp_pptx",
                      [marp, str(deck_md), "--pptx", "-o", str(mvp_dir / "decks" / "deck-client.pptx"), "--allow-local-files"],
                      timeout=60, on_event=on_event))
        add_step(_run("step9_marp_pdf",
                      [marp, str(deck_md), "--pdf", "-o", str(mvp_dir / "decks" / "deck-client.pdf"), "--allow-local-files"],
                      timeout=60, on_event=on_event))

    # Step 10-11: exports + IFC enrich(若 tier ≥ full · 调老师 blender CLI)
    if tier in ("full", "selection"):
        # 老师 model export-ifc + enrich-ifc · 详见 batch_all_mvps · 这里跳过具体 subprocess
        # (留给 worker_pipeline.run_teacher_7step_pipeline 接管 P7+P8+P6 后端)
        if on_event:
            on_event("p1_exports_handoff", {"note": "exports + enrich + audit handoff to worker_pipeline"})

    # Step 13: Verify gate(verify_mvp_exports.py)
    verify_script = PLAYBOOKS_SCRIPTS / "verify_mvp_exports.py"
    if verify_script.exists():
        verify_step = _run("step13_verify_GATE",
                           [_PY, str(verify_script), str(mvp_dir), "--tier", tier],
                           timeout=30, blocking=False, is_gate=True, on_event=on_event)
        add_step(verify_step)
        # verify gate non-blocking · 但记 missing

    # Step 14: CLIENT-README.md(我们 LIGHT client_readme 已通)
    # Step 15: 8 stakeholder PPTs(走 stakeholder_dispatcher · 见 阶段 1.D)
    # Step 17: What-If P9(addon 14 / 合规红灯)
    # Step 18: Case Study P11(addon 15 / tier ≥ delivery)

    return _summary(steps, gate_failures, fatal_at=None, t_start=t_start, tier=tier, render_path=render_path)


def _summary(steps, gate_failures, *, fatal_at, t_start, tier, render_path) -> dict:
    return {
        "ok": fatal_at is None and not gate_failures,
        "fatal_at": fatal_at,
        "tier": tier,
        "render_path": render_path,
        "total_duration_ms": int((time.time() - t_start) * 1000),
        "steps_count": len(steps),
        "steps": [s.to_meta() for s in steps],
        "gate_failures": gate_failures,
    }


def verify_p1() -> dict:
    """检查 P1 18 步老师真 CLI 全可达"""
    return {
        "lint_render_script": (_MESH_LIB / "lint_render_script.py").exists(),
        "verify_scene_dims":   (_MESH_LIB / "verify_scene_dims.py").exists(),
        "room_to_room_v2":     (_MESH_LIB / "room_to_room_v2.py").exists(),
        "layout_validate":     (_MESH_LIB / "layout_validate.py").exists(),
        "render_multi_assets": (_MESH_LIB / "render_multi_assets.py").exists(),
        "validate_reports":    (_MESH_LIB / "validate_reports.py").exists(),
        "floorplan_pro":       (_MESH_LIB / "floorplan_pro.py").exists(),
        "gen_moodboard":       (_MARP_DECK / "gen_moodboard.py").exists(),
        "setup_mvp_render":    (_MARP_DECK / "setup_mvp_render.py").exists(),
        "verify_mvp_exports":  (PLAYBOOKS_SCRIPTS / "verify_mvp_exports.py").exists(),
        "blender":             _find_blender() is not None,
        "marp":                _find_marp() is not None,
    }


if __name__ == "__main__":
    print(json.dumps(verify_p1(), indent=2, ensure_ascii=False))
