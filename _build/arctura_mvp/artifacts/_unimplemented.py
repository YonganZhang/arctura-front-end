"""通用 skeleton for 无 LIGHT producer 的产物（Phase 8 · 9.4 收敛）

pipeline 遇到 get_artifact(name)=None 时调 produce_for_spec(name, ctx, ...) ·
从 product_registry 查 spec_ref / full_hint 自动写 _TODO-<name>.md · 统一逻辑

当前 fallback 覆盖（`light_producer=None` in product_registry.py）：
  - `stakeholder_decks` (FULL-only · 按需 addon · 不在默认 tier)
  - `whatif` (FULL-only · 按需 addon · 不在默认 tier)

其余 13 产物（brief/scene/moodboard/floorplan/renders/deck_client/client_readme/
energy_report/exports/variants/case_study/ai_renders/bundle）均有 LIGHT 真产 ·
不走此 fallback（详见 artifacts/<name>.py）。
"""
from __future__ import annotations
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from ..types import ArtifactResult
from ..product_registry import PRODUCTS, ProductSpec


def produce_for_spec(
    name: str,
    ctx: dict,
    on_event: Optional[Callable] = None,
) -> ArtifactResult:
    """registry-driven skeleton · 所有 FULL-only 产物共用

    行为：
      - 返 ArtifactResult(status="skipped", reason=..., meta={unimplemented: True, ...})
      - 写 sb_dir/_TODO-<name>.md · 含 spec 引用 · 补齐方法
    """
    t0 = time.time()
    project = ctx["project"]
    sb_dir: Path = ctx["sb_dir"]
    sb_dir.mkdir(parents=True, exist_ok=True)

    spec: Optional[ProductSpec] = PRODUCTS.get(name)
    if spec is None:
        return ArtifactResult(
            name=name, status="error",
            timing_ms=int((time.time()-t0)*1000),
            error={"name": "unknown_artifact",
                   "trace_tail": f"artifact {name!r} 不在 product_registry 中"},
        )

    reason = (
        f"LIGHT 模式不产 {name} · 严老师 spec {spec.spec_ref} · "
        f"真交付走 {spec.full_pipeline}"
    )

    # 写 _TODO-<name>.md · 全从 registry 字段派生 · 无手写内容
    todo_path = sb_dir / f"_TODO-{name}.md"
    todo_content = f"""# TODO · {name}（{spec.name}）

**Spec 引用**: StartUP-Building/CLAUDE.md {spec.spec_ref}
**产物编号**: {spec.id if spec.id else "—（aux）"}
**Tier**: {project.tier}
**Slug**: {project.slug}

## 缺什么

{spec.name}（{spec.lang_hint_en}）

## 为什么没产

本机跑的是 Arctura-Front-end LIGHT pipeline · 仅产 LIGHT-compatible 产物。
{spec.name} 需 FULL 环境 · 对应严老师 pipeline：**{spec.full_pipeline}**

## 真产需要

{spec.full_hint or '—（见 StartUP-Building/playbooks/ 对应 pipeline md）'}

## 补齐入口

1. 把 brief/scene 推到 `StartUP-Building/studio-demo/mvp/{project.slug}/`
2. 跑对应 pipeline（见 `StartUP-Building/playbooks/`）
3. 真产物产出后覆盖本 _TODO 文件

## 依赖

本产物依赖：{', '.join(spec.depends_on) if spec.depends_on else '—'}

---
*此文件由 product_registry 自动生成 · {datetime.utcnow().isoformat()}Z*
"""
    todo_path.write_text(todo_content, encoding="utf-8")

    return ArtifactResult(
        name=name,
        status="skipped",
        timing_ms=int((time.time() - t0) * 1000),
        reason=reason,
        meta={
            "unimplemented": True,
            "product_id": spec.id,
            "spec_ref": spec.spec_ref,
            "full_pipeline": spec.full_pipeline,
            "todo_file": f"_TODO-{name}.md",
            "light_mode": True,
            "depends_on": spec.depends_on,
        },
    )
