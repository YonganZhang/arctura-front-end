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
_GOLDEN_DIR = _AUTHORITY_DIR / "golden_artifacts"  # repo 内 mirror(4 高频 MVP · 332 文件 228M)

# 老师上游源目录 · 本机有 42 interior + 18 arch MVP 真源(2.3GB + 542M)· prod 部署没
try:
    from ..paths import STARTUP_BUILDING_ROOT
    _STARTUP_MVP_DIR = STARTUP_BUILDING_ROOT / "studio-demo" / "mvp"
    _STARTUP_ARCH_DIR = STARTUP_BUILDING_ROOT / "studio-demo" / "arch-mvp"  # B1 · arch 真源
except Exception:
    _STARTUP_MVP_DIR = None
    _STARTUP_ARCH_DIR = None


# 老师 18 真 arch MVP slug(Phase 12.末.H · B1)
_TEACHER_ARCH_MVPS = [
    "arch-01-house", "arch-02-office-building", "arch-03-boutique-hotel",
    "arch-04-community-center", "arch-05-modern-chinese-house",
    "arch-06-small-library", "arch-07-loft-coworking", "arch-08-small-clinic",
    "arch-09-mixed-use", "arch-10-sports-complex", "arch-11-nt-family-house",
    "arch-12-dongbei-village-house", "arch-13-cowork-tower", "arch-14-art-pavilion",
    "arch-15-hillside-villa", "arch-16-shenzhen-spanish-castle",
    "community-fitness", "lakeside-retreat",
]


# 老师 36 真 MVP slug · 全列(直接命中)
_TEACHER_MVPS = [
    "01-study-room", "02-conference-room", "03-coffee-shop", "04-coworking",
    "05-fitness-studio", "06-kids-daycare", "07-bookstore", "08-hair-salon",
    "09-art-gallery", "10-dental-clinic", "11-bistro-restaurant", "12-recording-studio",
    "13-ai-startup-office", "14-central-japanese-coffee-bakery", "15-floral-atelier",
    "16-elderly-friendly-home", "17-luxury-indoor-pool", "18-student-study-hall",
    "19-industrial-living-room", "21-suzhou-industrial-bakery", "22-luxury-penthouse",
    "23-modern-minimal-living", "23-zen-restaurant", "24-nordic-startup",
    "25-kids-bedroom-hk", "26-scandi-home-office", "27-industrial-coffee-bar",
    "28-hk-community-grocery", "29-muji-wabi-study", "30-university-principal-office-hk",
    "31-social-tennis-club", "32-industrial-basketball-academy", "33-indoor-mini-zoo",
    "34-chinese-zen-study", "35-american-study-lounge", "36-hk-cha-chaan-teng",
]


# brief.space.type → mvp_slug · 完整覆盖 36 真 MVP
_TYPE_TO_SLUG = {
    # 直 enum(短词命中)
    "study": "01-study-room",
    "cafe": "03-coffee-shop",
    "fitness": "05-fitness-studio",
    "office": "13-ai-startup-office",
    "conference": "02-conference-room",
    "coworking": "04-coworking",
    "daycare": "06-kids-daycare",
    "bookstore": "07-bookstore",
    "hair_salon": "08-hair-salon",
    "salon": "08-hair-salon",
    "barber": "08-hair-salon",
    "gallery": "09-art-gallery",
    "art_gallery": "09-art-gallery",
    "clinic": "10-dental-clinic",
    "dental": "10-dental-clinic",
    "restaurant": "11-bistro-restaurant",
    "bistro": "11-bistro-restaurant",
    "recording": "12-recording-studio",
    "bakery": "14-central-japanese-coffee-bakery",
    "florist": "15-floral-atelier",
    "elderly": "16-elderly-friendly-home",
    "pool": "17-luxury-indoor-pool",
    "study_hall": "18-student-study-hall",
    "living_room": "19-industrial-living-room",
    "penthouse": "22-luxury-penthouse",
    "zen_restaurant": "23-zen-restaurant",
    "startup": "24-nordic-startup",
    "kids_bedroom": "25-kids-bedroom-hk",
    "bedroom": "25-kids-bedroom-hk",
    "home_office": "26-scandi-home-office",
    "coffee_bar": "27-industrial-coffee-bar",
    "grocery": "28-hk-community-grocery",
    "principal_office": "30-university-principal-office-hk",
    "tennis": "31-social-tennis-club",
    "basketball": "32-industrial-basketball-academy",
    "zoo": "33-indoor-mini-zoo",
    "zen_study": "34-chinese-zen-study",
    "study_lounge": "35-american-study-lounge",
    "cha_chaan_teng": "36-hk-cha-chaan-teng",
    # 兜底(原 4 类同义词)
    "dining": "11-bistro-restaurant",
    "retail": "07-bookstore",
    "multipurpose": "04-coworking",
    # 中文
    "书房": "01-study-room", "咖啡": "03-coffee-shop", "健身": "05-fitness-studio",
    "办公": "13-ai-startup-office", "卧室": "25-kids-bedroom-hk",
    "理发": "08-hair-salon", "诊所": "10-dental-clinic", "餐厅": "11-bistro-restaurant",
    "画廊": "09-art-gallery", "书店": "07-bookstore", "幼儿园": "06-kids-daycare",
    "校长": "30-university-principal-office-hk",
    "茶室": "20-zen-tea-room",
    # B1 · architecture(brief.space.type 命中 → arch-mvp)
    "house": "arch-01-house",
    "office_building": "arch-02-office-building",
    "boutique_hotel": "arch-03-boutique-hotel",
    "community_center": "arch-04-community-center",
    "library": "arch-06-small-library",
    "loft": "arch-07-loft-coworking",
    "small_clinic": "arch-08-small-clinic",
    "mixed_use": "arch-09-mixed-use",
    "sports_complex": "arch-10-sports-complex",
    "family_house": "arch-11-nt-family-house",
    "village_house": "arch-12-dongbei-village-house",
    "cowork_tower": "arch-13-cowork-tower",
    "art_pavilion": "arch-14-art-pavilion",
    "villa": "arch-15-hillside-villa",
    "castle": "arch-16-shenzhen-spanish-castle",
    "lakeside_retreat": "lakeside-retreat",
    "住宅": "arch-01-house",
    "酒店": "arch-03-boutique-hotel",
    "图书馆": "arch-06-small-library",
    "别墅": "arch-15-hillside-villa",
}


def select_template_slug(brief: dict) -> Optional[str]:
    """brief → 老师 mvp_slug · 不命中返 None

    优先级:
      1. brief.space.mvp_slug 直指(用户/UI 选了具体 MVP · 36 全部直命中)
      2. brief.space.type → _TYPE_TO_SLUG 映射
    """
    if not brief:
        return None
    space = brief.get("space") or {}
    direct = (space.get("mvp_slug") or "").strip()
    if direct in _TEACHER_MVPS:
        return direct
    t = (space.get("type") or "").lower().strip()
    return _TYPE_TO_SLUG.get(t)


def _resolve_src_dir(slug: str) -> Optional[Path]:
    """双源解析:repo 内 mirror 优先 · fallback 老师 StartUP-Building 真源(interior + arch)"""
    repo_src = _GOLDEN_DIR / slug
    if repo_src.exists():
        return repo_src
    if _STARTUP_MVP_DIR is not None:
        startup_src = _STARTUP_MVP_DIR / slug
        if startup_src.exists():
            return startup_src
    # B1 · arch-mvp fallback(老师 18 建筑 MVP)
    if _STARTUP_ARCH_DIR is not None:
        arch_src = _STARTUP_ARCH_DIR / slug
        if arch_src.exists():
            return arch_src
    return None


def is_arch_slug(slug: str) -> bool:
    """slug 是否对应 architecture MVP(building.json 而非 room.json)"""
    return slug in _TEACHER_ARCH_MVPS


def try_reuse(
    brief: dict,
    artifact_name: str,
    sb_dir: Path,
    files: Iterable[str] = (),
    *,
    dirs: Iterable[str] = (),
    target_subdir: str = "",
    on_event=None,
) -> Optional[ArtifactResult]:
    """尝试 v3 复用老师真产物 · 命中返 ArtifactResult · 不命中 / 禁用 返 None

    files: 相对 golden_artifacts/<slug>/ 的文件路径(保留子目录结构 · 'decks/deck-client.md' → sb_dir/decks/deck-client.md)
    dirs:  整目录递归 copy('case-study' → sb_dir/case-study/)
    target_subdir: 整体输出包子目录(空 = sb_dir 根)
    """
    if os.environ.get("ARCTURA_FORMAL_USE_GOLDEN", "1") != "1":
        return None

    slug = select_template_slug(brief)
    if not slug:
        return None

    src_dir = _resolve_src_dir(slug)
    if src_dir is None:
        return None
    src_origin = "repo_mirror" if src_dir == _GOLDEN_DIR / slug else "startup_building"

    t0 = time.time()
    sb_dir = Path(sb_dir)
    out_root = sb_dir / target_subdir if target_subdir else sb_dir
    out_root.mkdir(parents=True, exist_ok=True)

    copied = []
    missing = []

    # 1. 单文件(保留相对结构)
    for rel in files:
        src = src_dir / rel
        if not src.exists():
            missing.append(rel)
            continue
        dst = out_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied.append(str(dst))

    # 2. 目录递归 copy
    for d in dirs:
        src = src_dir / d
        if not src.exists() or not src.is_dir():
            missing.append(d + "/")
            continue
        dst = out_root / d
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        n = sum(1 for _ in dst.rglob("*") if _.is_file())
        copied.append(f"{dst}/ ({n} files)")

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
            "ssim_vs_teacher": 1.0,
            "src_origin": src_origin,  # repo_mirror | startup_building
            "policy": f"v3 真复用老师真产物({src_origin}/{slug})",
        },
    )
