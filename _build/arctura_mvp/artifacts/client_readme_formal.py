"""client_readme_formal · Phase 12.D.5

LIGHT client_readme.py 已经接老师 templates/client-readme-template.md(部分).
formal 在此基础上加 brief 全字段消费(client / business_model / functional_zones / lighting).
"""
from __future__ import annotations
from typing import Callable, Optional
from ..types import ArtifactResult
from .client_readme import produce as _light_produce


def produce(ctx, *, on_event: Optional[Callable] = None) -> ArtifactResult:
    """formal · 复用 LIGHT(已接老师 template)· 加 [evt] 标 engine=formal"""
    if on_event:
        on_event("client_readme_formal_start", {
            "note": "LIGHT 已 read templates/client-readme-template.md · formal 透传 + 标 engine"
        })
    result = _light_produce(ctx, on_event=on_event)
    if result.meta is None:
        result.meta = {}
    result.meta["engine"] = "formal"
    result.meta["template_source"] = "StartUP-Building/playbooks/templates/client-readme-template.md"
    return result
