"""deck_client · 客户 PPT 真产（Phase 9）

spec L401 · decks/deck-client.pptx + .pdf · Marp 生成 · 11+ 页 · 仅含概念+交付层

实装思路（LIGHT 模式 · 不走 Claude skill SDK · 走 CLI）：
  1. 从 brief + scene + renders URL 组 deck-client.md（简版 · 严老师模板压缩）
  2. 调 `marp` CLI 转 .pptx + .pdf
  3. 失败降级 skipped + _TODO

LIGHT 版本**不做**：8 stakeholder 全套（只做 1 个 client deck）
  · FULL 要 8 份走严老师 .claude/skills/marp-deck SKILL + sub-agent 分别产
"""
from __future__ import annotations
import glob
import json
import os
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from ..types import ArtifactResult

_MARP_BIN = shutil.which("marp") or "marp"


def _find_chromium() -> Optional[str]:
    """Marp pptx/pdf 转换要 Chrome · 找 Playwright 装的 chromium · 或 system chrome"""
    # Playwright 默认路径
    candidates = sorted(glob.glob(
        str(Path.home() / ".cache/ms-playwright/chromium-*/chrome-linux*/chrome")
    ))
    if candidates:
        return candidates[-1]   # 最新版本
    # 系统 chrome
    for name in ("google-chrome", "chromium", "chromium-browser"):
        p = shutil.which(name)
        if p:
            return p
    return None


def _build_deck_md(project, renders_dir: Path) -> str:
    """严老师 client template 简化版 · 9 页 markdown · Marp YAML frontmatter"""
    brief = project.brief or {}
    scene = project.scene or {}
    space = brief.get("space") or {}
    style = brief.get("style") or {}
    zones = brief.get("functional_zones") or []
    palette = style.get("palette") or []
    keywords = style.get("keywords") or []
    assemblies = scene.get("assemblies") or []
    bounds = scene.get("bounds") or {}

    name = brief.get("project") or project.display_name or project.slug
    area = space.get("area_sqm") or "—"
    headcount = brief.get("headcount") or "—"
    budget = brief.get("budget_hkd")

    # hero / main / feature renders · 存在则用
    def _img(fname: str) -> Optional[str]:
        p = renders_dir / fname
        return str(p) if p.exists() else None
    hero = _img("01_hero_corner.png") or _img("01_hero.png")
    main_zone = _img("03_main_zone.png") or _img("03_back_view.png")
    feature = _img("04_feature_zone.png") or _img("04_left_side.png")
    back = _img("06_back_corner.png") or _img("06_top_down.png")
    floorplan_png = _img("../floorplan.png")
    moodboard_png = _img("../moodboard.png")

    # 色板 tags
    palette_pills = " ".join(f"`{c}`" for c in palette[:6]) if palette else "—"
    style_pills = " · ".join(keywords[:6]) if keywords else "—"

    # 功能分区表
    zones_rows = "\n".join(
        f"| {z.get('name', '—')} | {z.get('area_sqm', '—')} | —  |"
        for z in zones
    ) or "| — | — | — |"

    budget_str = f"HK$ {int(budget):,}" if isinstance(budget, (int, float)) else "—"

    # frontmatter · 最小 Marp 配置
    fm = f"""---
marp: true
theme: default
paginate: true
size: 16:9
---
"""

    pages = []
    # P1 · 封面
    pages.append(f"""{fm}
# {name}

**{area} m²** · {headcount} 人 · {style_pills}

> Arctura Labs · {datetime.now().strftime("%Y-%m-%d")}
""")

    # P2 · KPI
    pages.append(f"""# 设计概览

| 项 | 值 |
|---|---|
| 面积 | {area} m² |
| 常驻人数 | {headcount} |
| 功能分区 | {len(zones)} 区 |
| 3D 物体 | {len(assemblies)} 件 |
| 层高 | {bounds.get('h', '—')} m |

**风格关键词**：{style_pills}
""")

    # P3 · Moodboard
    if moodboard_png:
        pages.append(f"""# 风格与色板

![w:640]({moodboard_png})

**色板**：{palette_pills}
""")

    # P4 · Hero
    if hero:
        pages.append(f"""# 主视角

![w:840]({hero})
""")

    # P5 · Main zone
    if main_zone:
        pages.append(f"""# 核心区域

![w:840]({main_zone})
""")

    # P6 · Feature
    if feature:
        pages.append(f"""# 特色区域

![w:840]({feature})
""")

    # P7 · Back corner
    if back:
        pages.append(f"""# 安静角落

![w:840]({back})
""")

    # P8 · Floorplan
    if floorplan_png:
        pages.append(f"""# 平面布局

![w:960]({floorplan_png})
""")

    # P9 · Zones 表
    pages.append(f"""# 功能分区

| 区域 | 面积 (m²) | 核心配置 |
|---|---|---|
{zones_rows}
""")

    # P10 · 下一步
    pages.append(f"""# 下一步

- **预算参考**：{budget_str}
- **工期参考**：{brief.get('timeline_weeks') or '6-10'} 周
- **当前 tier**：{project.tier or '—'}

确认后可进一步出能耗报告 / 工料报价 / BIM 模型。
""")

    # Marp 用 `---` 分页
    return "\n\n---\n\n".join(pages).replace("---\nmarp: true", "---\nmarp: true")


def produce(ctx: dict, on_event: Optional[Callable] = None) -> ArtifactResult:
    t0 = time.time()
    project = ctx["project"]
    sb_dir: Path = ctx["sb_dir"]
    fe_root: Path = ctx.get("fe_root")

    if not project.brief or not project.scene:
        return ArtifactResult(
            name="deck_client", status="skipped",
            timing_ms=int((time.time()-t0)*1000),
            reason="brief 或 scene 缺 · 无法生成 deck",
        )

    # Marp 是否可用
    if not shutil.which("marp"):
        return ArtifactResult(
            name="deck_client", status="skipped",
            timing_ms=int((time.time()-t0)*1000),
            reason="marp CLI 未装 · `npm i -g @marp-team/marp-cli`",
        )

    decks_dir = sb_dir / "decks"
    decks_dir.mkdir(parents=True, exist_ok=True)

    # renders 目录（worker 在 fe_root/assets/mvps/<slug>/renders/）
    renders_dir = fe_root / "assets" / "mvps" / project.slug / "renders" if fe_root else sb_dir / "renders"

    # 1. 生成 markdown
    md_content = _build_deck_md(project, renders_dir)
    md_path = decks_dir / "deck-client.md"
    md_path.write_text(md_content, encoding="utf-8")

    # 2. 调 marp 转 pptx + pdf · CHROME_PATH 指 Playwright chromium（本机已装）
    errors = []
    pptx_path = decks_dir / "deck-client.pptx"
    pdf_path = decks_dir / "deck-client.pdf"

    env = os.environ.copy()
    chrome = _find_chromium()
    if chrome:
        env["CHROME_PATH"] = chrome

    for target in (pptx_path, pdf_path):
        try:
            subprocess.run(
                [_MARP_BIN, str(md_path), "-o", str(target), "--allow-local-files"],
                check=True, capture_output=True, text=True, timeout=120, env=env,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            errors.append(f"{target.suffix[1:]}: {(getattr(e, 'stderr', '') or str(e))[:200]}")

    pptx_ok = pptx_path.exists() and pptx_path.stat().st_size > 1000
    pdf_ok = pdf_path.exists() and pdf_path.stat().st_size > 1000

    if not (pptx_ok or pdf_ok):
        return ArtifactResult(
            name="deck_client", status="error",
            timing_ms=int((time.time()-t0)*1000),
            error={"name": "marp_fail", "trace_tail": " | ".join(errors)[:300]},
        )

    page_count = md_content.count("\n\n---\n\n") + 1  # 分页符数量 + 1
    return ArtifactResult(
        name="deck_client", status="done",
        timing_ms=int((time.time()-t0)*1000),
        output_path=str(decks_dir),
        meta={
            "pages": page_count,
            "pptx": pptx_ok,
            "pdf": pdf_ok,
            "size_kb_pptx": round(pptx_path.stat().st_size / 1024, 1) if pptx_ok else 0,
            "size_kb_pdf": round(pdf_path.stat().st_size / 1024, 1) if pdf_ok else 0,
            "errors": errors or None,
            "template_source": "CLI-Anything/.claude/skills/marp-deck (simplified · client only)",
        },
    )
