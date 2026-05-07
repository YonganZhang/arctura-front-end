"""8 stakeholder marp PPTs · 并行 dispatcher

老师 marp-deck SKILL.md 真 spec(L60-90):
  client / investor / designer / contractor / bim / school-leader / operations / marketing
  各自不同 hero image + tone + 页数范围
  build_pptx.sh 批量转换

我们 worker 调老师 build_pptx.sh · 8 个 deck-{stakeholder}.md → .pptx
0 算法重写 · subprocess 调老师真 CLI。
"""
from __future__ import annotations
import shutil, subprocess, time
from pathlib import Path
from typing import Callable, Optional

from ..paths import STARTUP_BUILDING_ROOT


_BUILD_PPTX_SH = STARTUP_BUILDING_ROOT / ".claude" / "skills" / "marp-deck" / "scripts" / "build_pptx.sh"

_STAKEHOLDERS = ["client", "investor", "designer", "contractor",
                 "bim", "school-leader", "operations", "marketing"]


def dispatch_stakeholder_decks(mvp_dir: Path, *, with_pdf: bool = True,
                                on_event: Optional[Callable] = None) -> dict:
    """老师 build_pptx.sh 批量转换 8 stakeholder · subprocess 直调

    前置:mvp_dir/decks/deck-{stakeholder}.md 已存在(LLM 写)
    输出:mvp_dir/decks/deck-{stakeholder}.{pptx,pdf}
    """
    if not _BUILD_PPTX_SH.exists():
        return {"ok": False, "error": f"老师 build_pptx.sh 缺: {_BUILD_PPTX_SH}"}

    decks_dir = mvp_dir / "decks"
    if not decks_dir.exists():
        return {"ok": False, "error": f"decks/ 不存在: {decks_dir}"}

    if on_event:
        on_event("stakeholder_dispatch_start", {"mvp_dir": str(mvp_dir),
                                                "stakeholders": _STAKEHOLDERS})

    t0 = time.time()
    cmd = ["bash", str(_BUILD_PPTX_SH), str(mvp_dir)]
    if with_pdf:
        cmd.append("--pdf")
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        ok = proc.returncode == 0
    except Exception as e:
        return {"ok": False, "error": str(e)[:300],
                "duration_ms": int((time.time() - t0) * 1000)}

    # 数实际生成的 pptx(老师 build_pptx.sh 自动跑 8 个)
    pptx_files = sorted(decks_dir.glob("deck-*.pptx"))
    pdf_files = sorted(decks_dir.glob("deck-*.pdf")) if with_pdf else []

    result = {
        "ok": ok and len(pptx_files) >= 1,
        "duration_ms": int((time.time() - t0) * 1000),
        "pptx_count": len(pptx_files),
        "pdf_count": len(pdf_files),
        "stakeholders_generated": [p.stem.replace("deck-", "") for p in pptx_files],
        "stderr_tail": (proc.stderr or "")[-300:],
    }
    if on_event:
        on_event("stakeholder_dispatch_done", result)
    return result


def expected_stakeholders() -> list[str]:
    """老师 8 真 stakeholder slug"""
    return list(_STAKEHOLDERS)


def verify_dispatcher() -> dict:
    return {
        "build_pptx_sh_exists": _BUILD_PPTX_SH.exists(),
        "stakeholders_count": len(_STAKEHOLDERS),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(verify_dispatcher(), indent=2, ensure_ascii=False))
