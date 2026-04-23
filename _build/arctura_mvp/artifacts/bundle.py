"""bundle artifact · ZIP 所有产物到 assets/mvps/<slug>/bundle.zip
Phase 7.4 · 顶层加 _TODO-INDEX.md 聚合所有 skipped artifact 的说明
"""
from __future__ import annotations
import json
import time
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from ..types import ArtifactResult


def _collect_todo_files(sb_dir: Path) -> list[Path]:
    """扫 sb_dir 下所有 _TODO-*.md · 按名字排序"""
    if not sb_dir.exists():
        return []
    return sorted(sb_dir.glob("_TODO-*.md"))


def _build_todo_index(slug: str, todo_files: list[Path], project) -> str:
    """生成顶层 _TODO-INDEX.md · 客户打开 bundle 第一眼看到缺啥"""
    if not todo_files:
        return f"""# {slug} · 交付清单

**Tier**: {project.tier}
**状态**: 产出齐全（本 tier 所有 artifact 都真产了）
**生成**: {datetime.utcnow().isoformat()}Z
"""

    missing_names = [p.stem.replace("_TODO-", "") for p in todo_files]
    lines = [
        f"# {slug} · 未完成清单",
        "",
        f"**Tier**: {project.tier}",
        f"**缺 {len(todo_files)} 项**: {', '.join(missing_names)}",
        f"**生成**: {datetime.utcnow().isoformat()}Z",
        "",
        "## 为什么有这份清单",
        "",
        "本 bundle.zip 是 Arctura-Front-end LIGHT pipeline 产的 demo 骨架。",
        "严老师 spec（StartUP-Building/CLAUDE.md L393-420）要求的部分产物需要 Mac/Blender/OpenStudio 等 FULL 环境 · 本机不跑。",
        "",
        "下面列清单 · 每条都有对应 `_TODO-<name>.md` 详情。",
        "",
        "## 未完成清单",
        "",
    ]
    for p in todo_files:
        name = p.stem.replace("_TODO-", "")
        lines.append(f"- **{name}** · 详情见 [{p.name}](./{p.name})")

    lines += [
        "",
        "## 下一步",
        "",
        "1. 把此项目 brief/scene 推到 `StartUP-Building/studio-demo/mvp/" + slug + "/`",
        "2. 在 Mac（或能装 Blender+OpenStudio 的 Linux）上跑 `playbooks/` 下对应 pipeline",
        "3. 真产物产出后 · 覆盖对应 `_TODO-*.md` 文件",
        "",
        "---",
        "*本 README 由 bundle.py::_build_todo_index 自动生成 · 勿手改*",
    ]
    return "\n".join(lines)


def produce(ctx: dict, on_event: Optional[Callable] = None) -> ArtifactResult:
    t0 = time.time()
    project = ctx["project"]
    sb_dir: Path = ctx["sb_dir"]
    fe_root: Path = ctx["fe_root"]
    slug = project.slug

    fe_mvp_assets = fe_root / "assets" / "mvps" / slug
    fe_mvp_assets.mkdir(parents=True, exist_ok=True)
    bundle_path = fe_mvp_assets / "bundle.zip"

    # 收 skipped artifact 的 _TODO 文件（在 sb_dir 根）· 顶层 INDEX 聚合
    todo_files = _collect_todo_files(sb_dir)
    todo_index_content = _build_todo_index(slug, todo_files, project)

    file_count = 0
    written = set()   # 记所有已加入 zip 的 arc 路径 · 防 sb_dir rglob 重复
    with zipfile.ZipFile(bundle_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # 0. 顶层 README · 客户解压第一眼看
        arc = f"{slug}/_TODO-INDEX.md"
        zf.writestr(arc, todo_index_content)
        written.add(arc); file_count += 1

        # 1. brief/scene dump
        if project.brief:
            arc = f"{slug}/brief.json"
            zf.writestr(arc, json.dumps(project.brief, ensure_ascii=False, indent=2))
            written.add(arc); file_count += 1
        if project.scene:
            arc = f"{slug}/scene.json"
            zf.writestr(arc, json.dumps(project.scene, ensure_ascii=False, indent=2))
            written.add(arc); file_count += 1
        # 2. Project meta
        from dataclasses import asdict
        arc = f"{slug}/project.json"
        zf.writestr(arc, json.dumps(asdict(project), ensure_ascii=False, indent=2))
        written.add(arc); file_count += 1

        # 3. sb_dir 下所有真产物（moodboard/floorplan/README 等）· 跳 renders 子目录（步 4 独占）
        if sb_dir.exists():
            for p in sb_dir.rglob("*"):
                if not p.is_file():
                    continue
                rel = p.relative_to(sb_dir)
                if rel.parts and rel.parts[0] == "renders":
                    continue  # 留给 fe_mvp_assets/renders/
                arc = f"{slug}/{rel}"
                if arc in written: continue
                zf.write(p, arcname=arc)
                written.add(arc)
                file_count += 1

        # 4. 渲染图（在 fe_mvp_assets/renders/ 下）· 权威路径
        renders_dir = fe_mvp_assets / "renders"
        if renders_dir.exists():
            for p in renders_dir.glob("*.png"):
                arc = f"{slug}/renders/{p.name}"
                if arc in written: continue
                zf.write(p, arcname=arc)
                written.add(arc)
                file_count += 1

    # 不再内部 emit artifact_done · 由 pipeline 统一 emit（避免重复）
    return ArtifactResult(
        name="bundle", status="done",
        timing_ms=int((time.time()-t0)*1000),
        output_path=f"/assets/mvps/{slug}/bundle.zip",
        meta={
            "files": file_count,
            "size_kb": round(bundle_path.stat().st_size / 1024, 1),
            "unimplemented_count": len(todo_files),
            "unimplemented_names": [p.stem.replace("_TODO-", "") for p in todo_files],
        },
    )
