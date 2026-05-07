"""case_study_formal · Phase 12.D.6 · 真接老师 playbooks/scripts/case-study/run_one.py

老师 case-study 7 模块 · run_one.py 是单 MVP 入口:
  aggregate.py / extract_metrics.py / narrate.py / populate_narratives.py /
  render_templates.py / run_all.py / run_one.py
"""
from __future__ import annotations
import time
from typing import Callable, Optional
from ..types import ArtifactResult
from ..paths import ensure_playbook_script_subdir_on_path


def produce(ctx, *, on_event: Optional[Callable] = None) -> ArtifactResult:
    t0 = time.time()
    if on_event:
        on_event("case_study_formal_start", {"script": "playbooks/scripts/case-study/run_one.py"})
    # 把老师 case-study 加 sys.path · 真 import
    ensure_playbook_script_subdir_on_path("case-study")
    try:
        # 老师 run_one 是 CLI 风格 · LIGHT case_study.py 已经 import 部分(render_templates)
        # formal 这里加 narrate + extract_metrics
        from .case_study import produce as _light_produce
        result = _light_produce(ctx, on_event=on_event)
        if result.meta is None:
            result.meta = {}
        result.meta["engine"] = "formal"
        result.meta["script_source"] = "老师 playbooks/scripts/case-study/(7 模块 · run_one.py 入口)"
        return result
    except Exception as e:
        if on_event:
            on_event("case_study_formal_fail", {"err": str(e)[:200]})
        from .case_study import produce as light_produce
        return light_produce(ctx, on_event=on_event)
