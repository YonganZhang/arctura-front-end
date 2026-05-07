"""moodboard_formal · Phase 12.D.8 · 真接老师 gen_moodboard.py

老师代码: StartUP-Building/.claude/skills/marp-deck/scripts/gen_moodboard.py
工作流:
  - read brief.json · style.palette + style.keywords
  - PIL 6 swatch + 项目名 + 关键词
  - 输出 PNG · NotoSansCJK 中文(本机已软链)

跟 LIGHT moodboard.py 区别:
  - LIGHT: 自写 PIL 6 色 swatch
  - FORMAL: 调老师真 gen_moodboard.py · 字体/版式跟老师 spec 一致
"""
from __future__ import annotations
import subprocess, sys, time
from pathlib import Path
from typing import Callable, Optional
from ..types import ArtifactResult
from ..paths import STARTUP_BUILDING_ROOT


_GEN_MOODBOARD = STARTUP_BUILDING_ROOT / ".claude" / "skills" / "marp-deck" / "scripts" / "gen_moodboard.py"


def produce(ctx, *, on_event: Optional[Callable] = None) -> ArtifactResult:
    t0 = time.time()
    sb_dir = Path(ctx.get("sb_dir") or ".")

    if not _GEN_MOODBOARD.exists():
        if on_event:
            on_event("artifact_degrade", {"name": "moodboard", "from": "formal", "to": "fast",
                                          "reason": f"老师 gen_moodboard.py 缺: {_GEN_MOODBOARD}"})
        from .moodboard import produce as light_produce
        return light_produce(ctx, on_event=on_event)

    # 老师 gen_moodboard.py 用法: gen_moodboard.py <mvp-folder> · 读 mvp-folder/brief.json 写 moodboard.png
    try:
        proc = subprocess.run(
            [sys.executable, str(_GEN_MOODBOARD), str(sb_dir)],
            capture_output=True, text=True, timeout=30,
        )
        ok = proc.returncode == 0
    except Exception as e:
        if on_event:
            on_event("moodboard_formal_fail", {"err": str(e)[:200]})
        from .moodboard import produce as light_produce
        return light_produce(ctx, on_event=on_event)

    out = sb_dir / "moodboard.png"
    if not out.exists() or not ok:
        if on_event:
            on_event("artifact_degrade", {"name": "moodboard", "from": "formal", "to": "fast",
                                          "reason": "gen_moodboard 跑了但产物缺"})
        from .moodboard import produce as light_produce
        return light_produce(ctx, on_event=on_event)

    if on_event:
        on_event("moodboard_formal_done", {"path": str(out), "size_kb": round(out.stat().st_size/1024, 1)})

    return ArtifactResult(
        name="moodboard", status="done",
        timing_ms=int((time.time() - t0) * 1000),
        output_path=str(out),
        meta={"engine": "formal", "source": "老师 gen_moodboard.py", "size_kb": round(out.stat().st_size/1024, 1)},
    )
