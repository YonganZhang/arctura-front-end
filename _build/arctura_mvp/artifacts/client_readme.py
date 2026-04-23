"""client_readme · CLIENT-README.md 真产（Phase 7.5）

严老师 spec L402 · 用严老师 `playbooks/client-readme-template.md`（136 行模板）
填占位符 → sb_dir/CLIENT-README.md。

LIGHT 模式未产的字段（PPT 页数 / 导出文件 / 施工图等）· 标注 "— LIGHT 模式未产 · 见 _TODO-*.md"。
"""
from __future__ import annotations
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from ..types import ArtifactResult

_TEMPLATE_PATH = Path(__file__).resolve().parents[1] / "templates" / "client-readme-template.md"
# template 把真 markdown 包在 ```markdown ... ``` 里 · 要抽出来
_MARKDOWN_BLOCK_RE = re.compile(r"```markdown\n(.*?)\n```", re.DOTALL)
_LIGHT_MISSING = "— *LIGHT 模式未产*"


def _extract_template_body() -> str:
    raw = _TEMPLATE_PATH.read_text(encoding="utf-8")
    m = _MARKDOWN_BLOCK_RE.search(raw)
    return m.group(1) if m else raw


def _fill_placeholders(template: str, subs: dict) -> str:
    """替换 {key} 占位符 · 未提供的 key 保留 {key} 原样（方便人工填）"""
    def repl(match: re.Match):
        k = match.group(1)
        if k in subs and subs[k] is not None:
            return str(subs[k])
        return _LIGHT_MISSING
    # 匹配 {N}, {SIZE}, {项目中文名} 等 · 不吃 {} 空的
    return re.sub(r"\{([^{}\n]+?)\}", repl, template)


def produce(ctx: dict, on_event: Optional[Callable] = None) -> ArtifactResult:
    t0 = time.time()
    project = ctx["project"]
    sb_dir: Path = ctx["sb_dir"]
    sb_dir.mkdir(parents=True, exist_ok=True)

    brief = project.brief or {}
    scene = project.scene or {}
    artifacts = project.artifacts or {}

    # 统计（能拿到的就填 · 拿不到用 _LIGHT_MISSING）
    assemblies = scene.get("assemblies", []) or []
    objects = scene.get("objects", []) or []
    zones = brief.get("functional_zones", []) or []

    name_cn = (project.display_name or brief.get("project", project.slug))
    now_hkt = datetime.now()  # worker 在 HK server · 够准

    subs = {
        "项目中文名": name_cn,
        "YYYY-MM-DD": now_hkt.strftime("%Y-%m-%d"),
        "HH:MM:SS": now_hkt.strftime("%H:%M:%S"),
        # "N 分 N 秒" · 从 artifacts.timing_ms.total 推
        "N 分 N 秒": _fmt_duration_ms(artifacts.get("timing_ms", {}).get("total")),
        # 多处 {N} · 语义模糊 · 按出现顺序给 · re.sub 按每次替换
        # 更精确：把语义化 key 塞进 template 的一些地方
        # 这里用 sequential fallback：先填我们能填的 N · 剩下保留 {N}
        "slug": project.slug,
        "SIZE": _fmt_size_mb(artifacts),
    }

    # template 里多个 `{N}` 代表不同数字 · 先做语义化替换（按固定位置）· 再兜底通用 {N} 填充
    template = _extract_template_body()

    # 先把 3D 物体总数 / 平面图实体数 / PPT 页数 等特殊 {N} 定位替换 · 用 markdown 表格行匹配
    floorplan_entities = len(zones) + len(assemblies)
    # 总用时 "**{N} 分 {N} 秒**" 两个 {N} · 整体替换
    duration_str = _fmt_duration_ms(artifacts.get("timing_ms", {}).get("total"))
    template = template.replace("**{N} 分 {N} 秒**", f"**{duration_str}**", 1)
    template = template.replace("3D 物体总数 | {N}",
                                f"3D 物体总数 | {len(assemblies) or len(objects) or _LIGHT_MISSING}", 1)
    template = template.replace("平面图实体数 | {N}",
                                f"平面图实体数 | {floorplan_entities or _LIGHT_MISSING}", 1)
    template = template.replace("方案 PPT 页数 | {N}",
                                f"方案 PPT 页数 | {_LIGHT_MISSING}", 1)
    template = template.replace("产品内容（{N} 个文件",
                                f"产品内容（{_count_files(ctx)} 个文件", 1)
    template = template.replace("，共 {SIZE} MB）", "）", 1)

    # 再填命名占位符（{项目中文名} / {YYYY-MM-DD} / {N 分 N 秒} 等）
    filled = _fill_placeholders(template, subs)

    # 顶部加 LIGHT 模式横幅
    light_banner = (
        "> ⚠️ **LIGHT 模式输出** · 本 README 由 Arctura-Front-end LIGHT pipeline 产出 · "
        "严老师 spec 要求的 PPT / IFC / 施工 DXF 等需走 FULL pipeline · "
        "详见同目录 `_TODO-*.md` 清单\n\n"
    )
    filled = light_banner + filled

    out_path = sb_dir / "CLIENT-README.md"
    out_path.write_text(filled, encoding="utf-8")

    return ArtifactResult(
        name="client_readme",
        status="done",
        timing_ms=int((time.time() - t0) * 1000),
        output_path=str(out_path),
        meta={
            "lines": filled.count("\n"),
            "assemblies_count": len(assemblies),
            "zones_count": len(zones),
            "light_mode": True,
            "template_source": "StartUP-Building/playbooks/client-readme-template.md",
        },
    )


def _fmt_duration_ms(ms: Optional[int]) -> str:
    if ms is None:
        return _LIGHT_MISSING
    s = int(ms / 1000)
    return f"{s // 60} 分 {s % 60} 秒"


def _fmt_size_mb(artifacts: dict) -> str:
    # bundle.meta.size_kb · 但 client_readme 在 bundle 之前跑 · 拿不到
    return _LIGHT_MISSING


def _count_files(ctx: dict) -> str:
    sb_dir: Path = ctx["sb_dir"]
    if not sb_dir.exists():
        return _LIGHT_MISSING
    count = sum(1 for p in sb_dir.rglob("*") if p.is_file())
    return str(count)
