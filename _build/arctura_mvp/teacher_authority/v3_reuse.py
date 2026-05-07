"""v3 老师产物复用 helper · 100% 老师权威终极方案

用户原话:"100% 以我老师的代码为权威 · 直接复制他的来用就行"

每个 *_formal.py 在 produce() 顶部调:
    from ..teacher_authority.v3_reuse import try_reuse
    res = try_reuse(brief, "moodboard", sb_dir, ["moodboard.json", "moodboard.png"])
    if res: return res
    # fallback v2 真跑

逻辑:
  1. brief.space.type → mvp_slug(同 scene_formal)
  2. 检 teacher_authority/golden_artifacts/<slug>/ 有目标文件
  3. shutil.copy2 到 sb_dir(可指定子目录)· 0.01s
  4. 返 ArtifactResult(status=done, mode=v3_golden_reuse)

ARCTURA_FORMAL_USE_GOLDEN=0 全局禁用 · 落 v2。
"""
from __future__ import annotations
import os
import shutil
import time
from pathlib import Path
from typing import Iterable, Optional

from ..types import ArtifactResult


_AUTHORITY_DIR = Path(__file__).parent
_GOLDEN_DIR = _AUTHORITY_DIR / "golden_artifacts"


# 跟 scene_formal._TYPE_TO_TEMPLATE 同步 · 避免 import 循环
_TYPE_TO_SLUG = {
    "study": "01-study-room",
    "cafe": "03-coffee-shop",
    "fitness": "05-fitness-studio",
    "office": "13-ai-startup-office",
    "bedroom": "01-study-room",
    "living_room": "13-ai-startup-office",
    "dining": "03-coffee-shop",
    "retail": "03-coffee-shop",
    "gallery": "13-ai-startup-office",
    "clinic": "13-ai-startup-office",
    "multipurpose": "13-ai-startup-office",
    "书房": "01-study-room",
    "咖啡": "03-coffee-shop",
    "健身": "05-fitness-studio",
    "办公": "13-ai-startup-office",
    "卧室": "01-study-room",
}


def select_template_slug(brief: dict) -> Optional[str]:
    """brief → 老师 mvp_slug · 不命中返 None"""
    if not brief:
        return None
    space = brief.get("space") or {}
    t = (space.get("type") or "").lower().strip()
    return _TYPE_TO_SLUG.get(t)


def try_reuse(
    brief: dict,
    artifact_name: str,
    sb_dir: Path,
    files: Iterable[str],
    *,
    target_subdir: str = "",
    on_event=None,
) -> Optional[ArtifactResult]:
    """尝试 v3 复用老师真产物 · 命中返 ArtifactResult · 不命中 / 禁用 返 None

    files: 老师 golden_artifacts/<slug>/ 下相对路径(支持子目录如 'decks/deck-client.md')
    target_subdir: copy 到 sb_dir 下的子目录(空 = sb_dir 根)
    """
    if os.environ.get("ARCTURA_FORMAL_USE_GOLDEN", "1") != "1":
        return None

    slug = select_template_slug(brief)
    if not slug:
        return None

    src_dir = _GOLDEN_DIR / slug
    if not src_dir.exists():
        return None

    t0 = time.time()
    sb_dir = Path(sb_dir)
    out_root = sb_dir / target_subdir if target_subdir else sb_dir
    out_root.mkdir(parents=True, exist_ok=True)

    copied = []
    missing = []
    for rel in files:
        src = src_dir / rel
        if not src.exists():
            missing.append(rel)
            continue
        dst = out_root / Path(rel).name
        shutil.copy2(src, dst)
        copied.append(str(dst))

    if not copied:
        return None

    if on_event:
        on_event(f"{artifact_name}_v3_reused", {
            "template_slug": slug,
            "copied": len(copied),
            "missing": missing,
            "policy": "v3 · 直接复用老师真产物 · 100% 老师权威",
        })

    return ArtifactResult(
        name=artifact_name, status="done",
        timing_ms=int((time.time() - t0) * 1000),
        output_path=copied[0],
        meta={
            "engine": "formal",
            "mode": "v3_golden_reuse",
            "template_slug": slug,
            "files_count": len(copied),
            "files_missing": missing,
            "ssim_vs_teacher": 1.0,  # 字节级复用
            "policy": "v3 真复用老师 golden_artifacts/" + slug,
        },
    )
