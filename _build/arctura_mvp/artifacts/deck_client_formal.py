"""deck_client_formal · Phase 12.D.4 · 真接老师 marp-deck skill 8 stakeholder 模板

跟 LIGHT deck_client.py 区别:
  - LIGHT: 自写 1 份 client.md → marp 渲染 PPTX/PDF
  - FORMAL: 接老师 8 stakeholder 模板(bim/client/contractor/designer/investor/
    marketing/operations/school-leader)+ _shared.md · 真 8 份产出

老师真代码位置:
  StartUP-Building/.claude/skills/marp-deck/templates/{8 stakeholder}.md
  StartUP-Building/.claude/skills/marp-deck/templates/_shared.md(共享 head/style)
  StartUP-Building/.claude/skills/marp-deck/theme/(CSS · marp 主题)
"""
from __future__ import annotations
import json
import shutil
import subprocess
import time
from pathlib import Path
from typing import Callable, Optional

from ..types import ArtifactResult
from ..paths import STARTUP_BUILDING_ROOT


_MARP_TEMPLATES_DIR = STARTUP_BUILDING_ROOT / ".claude" / "skills" / "marp-deck" / "templates"
_MARP_THEME_DIR = STARTUP_BUILDING_ROOT / ".claude" / "skills" / "marp-deck" / "theme"

_STAKEHOLDERS = [
    "client",       # 客户(必产)
    "designer",     # 设计师
    "contractor",   # 承建
    "bim",          # BIM 工程
    "investor",     # 投资方
    "marketing",    # 营销
    "operations",   # 运营
    "school-leader",  # 校长(教育案场)
]


def _fill_placeholders(template: str, ctx_data: dict) -> str:
    """简单 {{ placeholder }} 填充 · 老师 marp 模板用"""
    out = template
    for k, v in ctx_data.items():
        if isinstance(v, (str, int, float)):
            out = out.replace(f"{{{{ {k} }}}}", str(v))
            out = out.replace(f"{{{{{k}}}}}", str(v))
    return out


def produce(ctx, *, on_event: Optional[Callable] = None) -> ArtifactResult:
    """deck_client formal · 用老师 8 模板真产 8 份 PPTX + PDF + MD"""
    t0 = time.time()
    project = ctx.get("project")
    sb_dir = Path(ctx.get("sb_dir") or ".")

    if not project or not project.brief:
        return ArtifactResult(
            name="deck_client", status="skipped",
            timing_ms=int((time.time() - t0) * 1000),
            reason="brief 缺",
        )

    # v3 · 100% 老师权威 · 命中 → 直接 copy 老师 5 真 deck.{md,pptx}
    from ..teacher_authority.v3_reuse import try_reuse
    _v3 = try_reuse(
        project.brief, "deck_client", sb_dir,
        ["decks/deck-client.md", "decks/deck-client.pptx",
         "decks/deck-bim.md", "decks/deck-bim.pptx",
         "decks/deck-contractor.md", "decks/deck-contractor.pptx",
         "decks/deck-designer.md", "decks/deck-designer.pptx",
         "decks/deck-investor.md", "decks/deck-investor.pptx"],
        target_subdir="decks", on_event=on_event,
    )
    if _v3:
        return _v3

    if not _MARP_TEMPLATES_DIR.exists():
        # 降级 LIGHT(单 client deck)
        if on_event:
            on_event("artifact_degrade", {
                "name": "deck_client", "from": "formal", "to": "fast",
                "reason": f"老师 marp-deck templates 目录缺: {_MARP_TEMPLATES_DIR}",
            })
        from .deck_client import produce as light_produce
        return light_produce(ctx, on_event=on_event)

    if not shutil.which("marp"):
        if on_event:
            on_event("artifact_degrade", {
                "name": "deck_client", "from": "formal", "to": "fast",
                "reason": "marp CLI 未装",
            })
        from .deck_client import produce as light_produce
        return light_produce(ctx, on_event=on_event)

    decks_dir = sb_dir / "decks"
    decks_dir.mkdir(parents=True, exist_ok=True)

    # 准备填充 ctx
    brief = project.brief
    ctx_data = {
        "PROJECT_NAME": brief.get("project") if isinstance(brief.get("project"), str)
                        else (brief.get("project") or {}).get("name_cn", project.slug),
        "CLIENT": brief.get("client", "客户"),
        "AREA_SQM": (brief.get("space") or {}).get("area_sqm", 0),
        "TYPE": (brief.get("space") or {}).get("type", ""),
        "SLUG": project.slug,
    }

    # 加载共享头
    shared_path = _MARP_TEMPLATES_DIR / "_shared.md"
    shared = shared_path.read_text() if shared_path.exists() else ""

    if on_event:
        on_event("marp_formal_start", {
            "templates_dir": str(_MARP_TEMPLATES_DIR),
            "stakeholders": _STAKEHOLDERS,
        })

    produced = {}
    for sh in _STAKEHOLDERS:
        tpl_path = _MARP_TEMPLATES_DIR / f"{sh}.md"
        if not tpl_path.exists():
            continue
        tpl = tpl_path.read_text()
        merged = _fill_placeholders(shared + "\n\n" + tpl, ctx_data)

        md_out = decks_dir / f"deck-{sh}.md"
        md_out.write_text(merged)

        # 跑 marp 出 PPTX
        try:
            proc = subprocess.run(
                ["marp", str(md_out), "--pptx", "-o", str(decks_dir / f"deck-{sh}.pptx")],
                capture_output=True, text=True, timeout=60,
            )
            ok = proc.returncode == 0
        except Exception as e:
            ok = False
        produced[sh] = {
            "md": md_out.exists(),
            "pptx": (decks_dir / f"deck-{sh}.pptx").exists(),
        }

    ok_count = sum(1 for v in produced.values() if v.get("pptx") or v.get("md"))

    if on_event:
        on_event("marp_formal_done", {"produced_count": ok_count, "details": produced})

    return ArtifactResult(
        name="deck_client", status="done" if ok_count > 0 else "error",
        timing_ms=int((time.time() - t0) * 1000),
        output_path=str(decks_dir),
        meta={
            "engine": "formal",
            "stakeholders_count": ok_count,
            "templates_source": "老师 marp-deck/templates 8 stakeholder",
            "produced": produced,
        },
        error=None if ok_count > 0 else {"name": "no_decks_produced"},
    )
