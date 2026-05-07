"""老师真权威 spec 锁定 · 防止我们偏离

按 v5 codemap 75 Pass 深审计 · 锁住老师 spec 关键不变量。
任何生成产物前调用 spec_lock 检查 · 不偏离老师权威。
"""
from __future__ import annotations
from pathlib import Path


# ═══════════ marp-deck 8 stakeholder hero(老师 SKILL.md L60-90) ═══════════

STAKEHOLDER_HERO_IMAGE = {
    "client":         "renders/01_hero_corner.png",       # 视觉效果优先
    "investor":       "renders/08_birds_eye_3d.png",      # 鸟瞰看格局
    "designer":       "renders/07_top_ortho.png",         # 顶视看尺寸
    "contractor":     "floorplan.png",                    # 平面图标注
    "bim":            "renders/08_birds_eye_3d.png",      # 鸟瞰看 schema
    "school-leader":  "renders/01_hero_corner.png",       # 创新展示
    "operations":     "renders/07_top_ortho.png",         # 顶视看动线
    "marketing":      "renders/01_hero_corner.png",       # 情感氛围
}

STAKEHOLDER_PAGE_COUNT = {
    "client": (8, 11), "investor": (10, 12), "designer": (10, 14),
    "contractor": (8, 10), "bim": (6, 8), "school-leader": (8, 10),
    "operations": (8, 10), "marketing": (6, 8),
}


# ═══════════ 关键产物必含(老师 CLAUDE.md L521-560) ═══════════

REQUIRED_ARTIFACTS_FULL_TIER = {
    "brief":          "brief.json",
    "moodboard":      "moodboard.png",
    "scene":          ["room.json", "building.json"],  # 任一即可
    "renders":        "renders/01_hero_corner.png",  # 至少必有这个 · 6 张 Path A / 8 张 Path B
    "floorplan_svg":  "floorplan.svg",
    "floorplan_png":  "floorplan.png",
    "deck_md":        "decks/deck-client.md",
    "deck_pptx":      "decks/deck-client.pptx",
    "deck_pdf":       "decks/deck-client.pdf",
    "client_readme":  "CLIENT-README.md",
    "export_glb":     "exports/*.glb",
    "export_obj":     "exports/*.obj",
    "export_fbx":     "exports/*.fbx",
    "export_ifc_raw":      "exports/*.ifc",
    "export_ifc_enriched": "exports/*-enriched.ifc",
    "energy_project":      "energy/project.json",
    "energy_compliance":   "energy/compliance-*.md",
    "energy_boq_md":       "energy/boq-*.md",
    "energy_boq_csv":      "energy/boq-*.csv",
    "qa_vision":     "qa-report.json",  # L3 全案档必跑
}

REQUIRED_CASE_STUDY_FILES = [  # case-study/ 必含 7+ 文件(L521 关键产物)
    "portfolio.md", "impact.md", "sales.md",
    "metrics.json",
    "narrative-portfolio.txt", "narrative-impact.txt", "narrative-sales.txt",
]


# ═══════════ Path A vs Path B 渲染数(老师 CLAUDE.md L521 + 实际产物) ═══════════

RENDER_PATH_SPEC = {
    "path_a": {
        "count": 6, "names": ["01_hero_corner", "02_reception", "03_main_zone",
                              "04_feature_zone", "05_lounge_zone", "06_back_corner"],
        "engine": "Blender + GLB asset",
        "source_pipeline": "render_multi_assets.py(mesh-library)",
    },
    "path_b": {
        "count": 8, "names": ["01_hero_corner", "02_reception", "03_main_zone",
                              "04_feature_zone", "05_lounge_zone", "06_back_corner",
                              "07_top_ortho", "08_birds_eye_3d"],
        "engine": "Blender + primitive cubes",
        "source_pipeline": "_render_multi.py(legacy)",
    },
    "path_b_sdxl": {
        "count": 8, "names": ["...8 张同 path_b", "+ ai_realistic.png", "+ ai_realistic_depth.png"],
        "engine": "Path B + P4 SDXL 后处理",
        "source_pipeline": "_render_multi.py + ai_render/render_enhance.py",
    },
}


# ═══════════ Image Convention(老师 marp-deck SKILL.md L86-104) ═══════════

DECK_IMAGE_CONVENTION = {
    "default": "![center](../renders/XX_name.png)",  # 不带 width hint
    "full_img": "<!-- _class: full-img --> + ![center](...)",  # 全图页(floorplan/moodboard 单图铺页)
    "banned": "![w:1050px center]",  # 老师 2026-04-27 起禁止
    "legacy_compat_w100": "![w:100%]",  # 老师真产物仍用 · spec 已弃但兼容
}


# ═══════════ L3 AI Vision QA 输出 schema(老师 qa-report.json) ═══════════

QA_VISION_REPORT_SCHEMA = {
    "$comment": "老师 qa_vision.py 输出 qa-report.json 真权威格式 · 全案档必含",
    "issues": [
        {
            "severity": "HIGH | MED | LOW",
            "view": "01_hero_corner | 03_main_zone | ...",
            "category": "floating | sinking | clipping | orientation | pairing | scale | missing",
            "description": "string",
            "fix_hint": "string",
        }
    ],
    "verdict": "PASS | NEEDS-FIX | FAIL",
    "tier": "concept | delivery | quote | full | selection",
    "_meta": {"model": "claude-sonnet-4-5", "image_count": 8},
}


# ═══════════ change-impact-matrix 5 档客户改类(老师真权威) ═══════════

CLIENT_CHANGE_CATEGORIES = [
    "材质/颜色", "家具位置", "家具增删", "灯光氛围", "功能区调整",
    "房间尺寸", "风格大改", "换渲染风格", "HVAC/设备", "围护结构",
    "合规标准", "报价地区", "新文件", "只改描述", "要第 2/3 方案",
]


# ═══════════ 5 档 + 受众(老师 product-selector.md) ═══════════

TIER_SPEC = {
    "concept":    {"label": "概念", "audience": "内部讨论", "p1_min": 3, "p2_min": 5},
    "deliver":    {"label": "交付", "audience": "客户决策", "p1_min": 5, "p2_min": 8},
    "quote":      {"label": "报价", "audience": "客户问'多少钱'", "p1_min": 6, "p2_min": 9},
    "full":       {"label": "全案", "audience": "工程团队", "p1_min": 8, "p2_min": 12},
    "select":     {"label": "甄选", "audience": "多方案选型", "p1_min": 24, "p2_min": 36},
}


# ═══════════ 5 法规(P8 codes.json v2 · 2026-04-20) ═══════════

COMPLIANCE_CODES = ["HK", "CN_HOT", "CN_COLD", "ASHRAE", "JP"]
EUI_IS_ADVISORY = True  # 老师 P8 v2 · 禁止把 EUI 当 pass/fail 硬指标


# ═══════════ 验证 helpers(thin) ═══════════

def get_stakeholder_hero(stakeholder: str) -> str:
    """8 stakeholder → 老师真 hero image 路径"""
    return STAKEHOLDER_HERO_IMAGE.get(stakeholder, "renders/01_hero_corner.png")


def expected_render_count(render_path: str) -> int:
    return RENDER_PATH_SPEC.get(render_path, {}).get("count", 8)


def is_full_tier_complete(mvp_dir: Path) -> dict:
    """老师 verify_mvp_exports 简化 Python 版 · 不需 subprocess
    返 {ok: bool, missing: [...]}"""
    missing = []
    for key, pattern in REQUIRED_ARTIFACTS_FULL_TIER.items():
        if isinstance(pattern, list):
            if not any((mvp_dir / p).exists() for p in pattern):
                missing.append(key)
        elif "*" in pattern:
            if not list(mvp_dir.glob(pattern)):
                missing.append(key)
        else:
            if not (mvp_dir / pattern).exists():
                missing.append(key)
    case_study_dir = mvp_dir / "case-study"
    if case_study_dir.exists():
        for f in REQUIRED_CASE_STUDY_FILES:
            if not (case_study_dir / f).exists():
                missing.append(f"case-study/{f}")
    return {"ok": not missing, "missing": missing,
            "total_required": len(REQUIRED_ARTIFACTS_FULL_TIER) + len(REQUIRED_CASE_STUDY_FILES)}
