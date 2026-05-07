"""client_readme_formal · Phase 12.D.5

LIGHT client_readme.py 已经接老师 templates/client-readme-template.md(部分).
formal 在此基础上加 brief 全字段消费(client / business_model / functional_zones / lighting).
"""
from __future__ import annotations
from pathlib import Path
from typing import Callable, Optional
from ..types import ArtifactResult
from .client_readme import produce as _light_produce


def produce(ctx, *, on_event: Optional[Callable] = None) -> ArtifactResult:
    """formal · v3 复用老师真 CLIENT-README.md(05/13 真有)· 不命中走 LIGHT"""
    # v3 · 命中老师真 README → 直接 copy
    from ..teacher_authority.v3_reuse import try_reuse
    project = ctx.get("project")
    sb_dir = Path(ctx.get("sb_dir") or ".")
    _v3 = try_reuse(
        project.brief if project else {}, "client_readme", sb_dir,
        files=["CLIENT-README.md"],
        on_event=on_event,
    )
    if _v3:
        return _v3

    if on_event:
        on_event("client_readme_formal_start", {
            "note": "v3 不命中(老师 01/03 没真 README)· 退回 LIGHT 跑 templates 真模板"
        })
    result = _light_produce(ctx, on_event=on_event)
    if result.meta is None:
        result.meta = {}
    result.meta["engine"] = "formal"
    result.meta["template_source"] = "StartUP-Building/playbooks/templates/client-readme-template.md"
    return result
