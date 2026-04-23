"""LIGHT 模式未实装 artifact 的骨架（Phase 7.4 · 对齐严老师 spec L388-390）

严老师 spec 要求："做不到就说" · "不得用文字描述代替实际产物" · "禁止静默跳过"
所以未实装的 artifact 必须显式：
  1. 返回 status="skipped" + reason 说明为什么（不是 "Phase 7+ 补" · 而是"LIGHT 模式 · 需 FULL"）
  2. 写 _TODO-<name>.md 到 sb_dir · 说明缺什么、如何补
  3. bundle.py 会把所有 _TODO-*.md 打包 + 顶层 _TODO-INDEX.md

设计：
- 单一 produce_stub() 工厂函数 · 每个 artifact 模块调一下就好
- meta 带 "unimplemented": True · 前端按此高亮
"""
from __future__ import annotations
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from ..types import ArtifactResult


def produce_stub(
    name: str,
    spec_line: str,
    what_missing: str,
    full_pipeline_hint: str,
    ctx: dict,
    on_event: Optional[Callable] = None,
) -> ArtifactResult:
    """通用 stub · 返 skipped + 写 _TODO-<name>.md

    Args:
        name · artifact 名
        spec_line · spec 里的引用（如 "L401"）
        what_missing · 缺什么产物（用户/客户看）
        full_pipeline_hint · FULL pipeline 用什么产（tech 说明）
    """
    t0 = time.time()
    project = ctx["project"]
    sb_dir: Path = ctx["sb_dir"]
    sb_dir.mkdir(parents=True, exist_ok=True)

    reason = (f"LIGHT 模式本机不产 {name} · 严老师 spec {spec_line} "
              f"要求的 {what_missing}。真交付需走 FULL pipeline："
              f"{full_pipeline_hint}")

    # 写 _TODO 文件（bundle 打包时会收） · 客户看得到
    todo_path = sb_dir / f"_TODO-{name}.md"
    todo_content = f"""# TODO · {name}（未产出）

**Spec 引用**: StartUP-Building/CLAUDE.md {spec_line}
**当前档位**: {project.tier}
**项目 slug**: {project.slug}
**缺什么**: {what_missing}

## 为什么没产

本机跑的是 LIGHT pipeline（Arctura-Front-end demo 骨架）· 仅产：
- scene（3D 场景 JSON）
- moodboard（色板 PNG）
- floorplan（平面图 SVG + PNG）
- renders（Three.js Playwright 截图 · 非真 Blender）
- bundle（打包 zip）

## 真产需要

{full_pipeline_hint}

## 下一步

1. 把此项目推到 `StartUP-Building/studio-demo/mvp/{project.slug}/` 目录
2. 走对应 pipeline（见 `StartUP-Building/playbooks/`）
3. 产物归属规则见 StartUP-Building/CLAUDE.md 归属表

---
*生成时间: {datetime.utcnow().isoformat()}Z*
"""
    todo_path.write_text(todo_content)

    return ArtifactResult(
        name=name,
        status="skipped",
        timing_ms=int((time.time() - t0) * 1000),
        reason=reason,
        meta={
            "unimplemented": True,
            "spec_line": spec_line,
            "todo_file": str(todo_path.relative_to(sb_dir.parent.parent)),
            "light_mode": True,
        },
    )
