"""Product Registry · SSOT for 16 产物 × 5 档 × LIGHT/FULL 能力

对齐 严老师 spec：
  - StartUP-Building/CLAUDE.md L358-L420（5 档 · 必含产物清单）
  - Zhiling/docx/22-pipeline-alignment-audit-and-handbook-v4.md（产物编号体系）
  - internal-handbook-v4（产物套餐体系）

设计原则（一劳永逸）：
  - 一处改 · 全处跟（tiers.py / artifacts / MCP / 前端 展示 都从这里查）
  - 加新产物 = 加 1 行 · 不改其他文件
  - 不做抽象类 · 纯 dataclass + dict · 足够

使用：
  from _build.arctura_mvp.product_registry import PRODUCTS, resolve_tier_products

命令行自检：
  python3 -m _build.arctura_mvp.product_registry --validate
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


# ───────── 类型 ─────────

@dataclass
class ProductSpec:
    key: str                            # 稳定 ID · 跟 artifact 文件名对齐
    name: str                           # 人读 · 中英混
    id: Optional[int] = None            # 严老师编号 1-16 · None = aux（variants）
    tiers: list[str] = field(default_factory=list)   # 哪些 tier 含此产物
    light_producer: Optional[str] = None      # artifacts/<name>.py 模块 · None = LIGHT 无法产
    full_pipeline: Optional[str] = None       # 严老师 spec 中的 pipeline 编号/路径
    addon: bool = False                 # True = 按需追加项（#13-16）· 不默认加入任何 tier
    spec_ref: str = ""                  # "spec L###"
    depends_on: list[str] = field(default_factory=list)   # 上游产物 key（scene → renders）
    full_hint: str = ""                 # _TODO-*.md 里填的 FULL pipeline 补齐说明
    lang_hint_en: str = ""              # 英文名（前端双语用）


# ───────── 16 产物 + variants（aux）· 严老师 spec 权威清单 ─────────
# 顺序 = 依赖顺序（brief 最先 · bundle 最后 · 便于 pipeline 按序执行）

_PRODUCTS_LIST: list[ProductSpec] = [
    # #1 · brief · 进 concept+ 所有档
    ProductSpec(
        key="brief", id=1, name="设计简报", lang_hint_en="Brief",
        tiers=["concept", "deliver", "quote", "full", "select"],
        light_producer=None,  # brief 不是 artifact · 是 chat 产出 · 这里仅登记存在
        full_pipeline="P3 brief-intake",
        spec_ref="L393+L396",
        full_hint="P3 brief-intake（已 LIGHT 实装为 /api/brief/chat · GPT-5.4 多轮）",
    ),
    # #3 · scene (room.json / building.json)
    ProductSpec(
        key="scene", id=3, name="3D 场景", lang_hint_en="Scene (room/building)",
        tiers=["concept", "deliver", "quote", "full", "select"],
        light_producer="scene",
        full_pipeline="P1 Interior / P2 Architecture",
        spec_ref="L398",
        depends_on=["brief"],
        full_hint="真 3D 建模需 Blender Pascal Editor · LIGHT 版走 generators/scene.py · 60+ objects 需 FULL",
    ),
    # #2 · moodboard
    ProductSpec(
        key="moodboard", id=2, name="风格板", lang_hint_en="Moodboard",
        tiers=["concept", "deliver", "quote", "full", "select"],
        light_producer="moodboard",
        full_pipeline="P1/P2 moodboard step",
        spec_ref="L397",
        depends_on=["brief"],
        full_hint="FULL 版会从 brief.style 跨字段 dedupe + SDXL 风格参考图（P4）· LIGHT 只产 4 色 palette + PNG",
    ),
    # #5 · floorplan
    ProductSpec(
        key="floorplan", id=5, name="平面图", lang_hint_en="Floorplan",
        tiers=["concept", "deliver", "quote", "full", "select"],
        light_producer="floorplan",
        full_pipeline="P1/P2 floorplan SVG (含中文标注+面积+比例尺)",
        spec_ref="L400",
        depends_on=["scene"],
        full_hint="FULL 走 Inkscape CLI 出中文标注+面积+比例尺 · LIGHT 只产简版 SVG+PNG",
    ),
    # #4 · renders × 8
    ProductSpec(
        key="renders", id=4, name="渲染 × 8", lang_hint_en="Renders × 8",
        tiers=["concept", "deliver", "quote", "full", "select"],
        light_producer="renders",
        full_pipeline="P1/P2 Blender Eevee · + P4 AI 增强（可选）",
        spec_ref="L399",
        depends_on=["scene"],
        full_hint="FULL 走 Blender Eevee 出 8 张 · 可 + P4 SDXL 写实化 · LIGHT 走 Three.js Playwright 截图",
    ),
    # #6 · deck_client PPT · Phase 9 真产（Marp CLI 本机已装）
    ProductSpec(
        key="deck_client", id=6, name="方案 PPT", lang_hint_en="Client Deck (Marp)",
        tiers=["deliver", "quote", "full", "select"],
        light_producer="deck_client",   # ✅ Phase 9 · 接 marp CLI · 产 .pptx + .pdf
        full_pipeline="P1/P2 deck step · Marp CLI + .claude/skills/marp-deck (full 8 stakeholder)",
        spec_ref="L401",
        depends_on=["brief", "scene", "renders"],
        full_hint="LIGHT 版已产单份 client deck · FULL 走严老师 marp-deck skill 产 8 份 stakeholder PPT",
    ),
    # #7 · client_readme
    ProductSpec(
        key="client_readme", id=7, name="客户文档", lang_hint_en="CLIENT-README",
        tiers=["deliver", "quote", "full", "select"],
        light_producer="client_readme",
        full_pipeline="P1/P2 README step · templates/client-readme-template.md",
        spec_ref="L402",
        depends_on=["brief", "scene"],
        full_hint="LIGHT 版已用严老师 templates/client-readme-template.md 填占位符 · "
                  "FULL 会跑 materialize_full_mvp.py 带真统计",
    ),
    # #8 · energy_report (project.json + compliance + boq)
    ProductSpec(
        key="energy_report", id=8, name="能耗 + 合规 + 报价", lang_hint_en="Energy + Compliance + BOQ",
        tiers=["quote", "full", "select"],
        light_producer=None,
        full_pipeline="P7 Energy-Sim + P8 Compliance + P6 BOQ",
        spec_ref="L404",
        depends_on=["scene", "brief"],
        full_hint="需 OpenStudio + EnergyPlus 26.1 · 入口 `cd $OPENST_H && openstudio_cli project new` · "
                  "气象 HKG_Hong.Kong.Intl.AP.epw · 批量跑 playbooks/scripts/batch_all_mvps.py",
    ),
    # #10 · exports · Phase 9 真产（Blender 4.2.3 已装 · GLB/OBJ/FBX）
    ProductSpec(
        key="exports", id=10, name="BIM 导出（GLB/OBJ/FBX）", lang_hint_en="Exports (GLB/OBJ/FBX)",
        tiers=["full", "select"],
        light_producer="exports",   # ✅ Phase 9 · Blender headless 产 3 格式
        full_pipeline="P0 IFC enrich + P1/P2 export step · 加 IFC4+DXF 需 Blender-BIM + Pascal",
        spec_ref="L403",
        depends_on=["scene"],
        full_hint="LIGHT 产 3/5 格式（GLB/OBJ/FBX）· FULL 加 IFC4 enriched（Blender-BIM）+ DXF（Pascal）",
    ),
    # variants · aux for select tier
    ProductSpec(
        key="variants", id=None, name="3 方案对比", lang_hint_en="A/B/C Variants",
        tiers=["select"],
        light_producer="variants",
        full_pipeline="P10 A/B/C comparison",
        spec_ref="L407-420",
        depends_on=["scene", "brief"],
        full_hint="LIGHT 只产 diff-matrix（严老师 score_variants.py 真算 + 占位 EUI/BOQ）· "
                  "FULL 加 Blender render 每方案 hero + comparison-grid",
    ),
    # #15 · case_study (addon · select 强制加 · 其他档按需)
    ProductSpec(
        key="case_study", id=15, name="Case Study 素材", lang_hint_en="Case Study",
        tiers=["full", "select"],
        light_producer="case_study",
        full_pipeline="P11 Case Study Auto-Gen",
        spec_ref="L405",
        depends_on=["brief", "scene"],
        addon=False,   # P11 已经被 spec L405 列为 full 档必含 · 不是 addon
        full_hint="LIGHT 用严老师 render_templates.py 产 7 文件（metrics + portfolio/impact/sales）· "
                  "FULL 走 narrate.py 真 LLM · 可换 ZHIZENGZENG/Claude API 做 LIGHT polyfill",
    ),

    # addon（严老师 spec L368-375 按需追加项 · tier 不默认含 · 客户/销售明说加）
    # #13 · stakeholder_decks
    ProductSpec(
        key="stakeholder_decks", id=13, name="8 份利益方 PPT", lang_hint_en="Stakeholder Decks",
        tiers=[],  # addon 不默认 tier
        light_producer=None,
        full_pipeline="marp-deck skill",
        spec_ref="L373",
        depends_on=["deck_client"],
        addon=True,
        full_hint="需 .claude/skills/marp-deck · 一键 8 份 PPT · 本机 LIGHT 未接",
    ),
    # #14 · whatif
    ProductSpec(
        key="whatif", id=14, name="What-If 参数扫描", lang_hint_en="What-If",
        tiers=[],
        light_producer=None,
        full_pipeline="P9 What-If",
        spec_ref="L374",
        depends_on=["energy_report"],
        addon=True,
        full_hint="需 OpenStudio · `openstudio_cli report whatif --preset envelope-upgrade` 等",
    ),
    # #16 · ai_renders
    ProductSpec(
        key="ai_renders", id=16, name="AI 渲染增强", lang_hint_en="AI Renders",
        tiers=[],
        light_producer=None,
        full_pipeline="P4 SDXL/L2-C",
        spec_ref="L376",
        depends_on=["renders"],
        addon=True,
        full_hint="需 ComfyUI + SDXL · RealVisXL V4.0 + xinsir depth CN · Mac/GPU Linux",
    ),

    # bundle 永远最后 · 不在产物编号里 · 但是 artifact
    ProductSpec(
        key="bundle", id=None, name="Bundle.zip", lang_hint_en="Bundle",
        tiers=["concept", "deliver", "quote", "full", "select"],
        light_producer="bundle",
        full_pipeline="本地打包",
        spec_ref="—",
        depends_on=[],   # 真依赖所有前面产物 · 但顺序 pipeline 保证
        full_hint="LIGHT + FULL 都走同一份 bundle.py · 顶层含 _TODO-INDEX.md 清单",
    ),
]

# 查表 dict（key → spec）
PRODUCTS: dict[str, ProductSpec] = {p.key: p for p in _PRODUCTS_LIST}


# ───────── 派生 API（tiers.py / artifacts / MCP 都调这几个）─────────

# 5 档 label + 耗时 · label 跟 spec L360-366 对齐
TIER_META: dict[str, dict] = {
    "concept":  {"order": 1, "label_zh": "概念", "label_en": "Concept",
                 "desc_zh": "brief + 3D + 渲染 + 平面图",
                 "render_engine_default": "fast",
                 "estimated_min": {"fast": 3, "formal": 15}},
    "deliver":  {"order": 2, "label_zh": "交付", "label_en": "Deliver",
                 "desc_zh": "+方案 PPT + 客户文档",
                 "render_engine_default": "fast",
                 "estimated_min": {"fast": 6, "formal": 20}},
    "quote":    {"order": 3, "label_zh": "报价", "label_en": "Quote",
                 "desc_zh": "+能耗 + 工料报价 + 合规",
                 "render_engine_default": "fast",
                 "estimated_min": {"fast": 8, "formal": 25}},
    "full":     {"order": 4, "label_zh": "全案", "label_en": "Full",
                 "desc_zh": "+BIM 导出 GLB/FBX/IFC + Case Study",
                 "render_engine_default": "formal",
                 "estimated_min": {"fast": 12, "formal": 40}},
    "select":   {"order": 5, "label_zh": "甄选", "label_en": "Select",
                 "desc_zh": "3 方案 × 全案 + 对比拼图 + 决策矩阵",
                 "render_engine_default": "formal",
                 "estimated_min": {"formal": 120},
                 "variant_count": 3},
}


def resolve_tier_products(tier_id: str, *, include_addons: bool = False) -> list[ProductSpec]:
    """返回此 tier 该产的产物清单 · 按依赖顺序
    include_addons=True 时加上 addon 产物（当前无 default addon · 未来按需）
    """
    if tier_id not in TIER_META:
        raise ValueError(f"unknown tier: {tier_id}")
    products = []
    for spec in _PRODUCTS_LIST:
        if spec.addon and not include_addons:
            continue
        if tier_id in spec.tiers:
            products.append(spec)
    # bundle 永远最后
    products.sort(key=lambda s: (s.key == "bundle", _PRODUCTS_LIST.index(s)))
    return products


def resolve_tier_artifact_names(tier_id: str) -> list[str]:
    """返回此 tier 的 artifact 名称清单（用于 pipeline.run artifact 遍历）
    · 跳过 brief（不是 artifact · 是 chat 产出）· 其他按 key 返回
    · LIGHT 不可产的仍返回（artifacts/<name>.py skeleton 会写 _TODO）
    """
    out = []
    for spec in resolve_tier_products(tier_id):
        if spec.key == "brief":
            continue   # brief 不走 pipeline · 在 chat 阶段已有
        out.append(spec.key)
    return out


def get_spec_for_artifact(name: str) -> Optional[ProductSpec]:
    """artifact 名字 → ProductSpec · 用 key 匹配
    （light_producer 和 key 现都等价 · 如果将来分离可改）
    """
    return PRODUCTS.get(name)


def all_tier_ids() -> list[str]:
    return sorted(TIER_META.keys(), key=lambda t: TIER_META[t]["order"])


def list_tiers_for_ui() -> list[dict]:
    """给前端 TierPicker / MCP arctura_tier_list 用"""
    out = []
    for tier_id in all_tier_ids():
        meta = TIER_META[tier_id]
        products = resolve_tier_products(tier_id)
        out.append({
            "id": tier_id,
            "label_zh": meta["label_zh"],
            "label_en": meta["label_en"],
            "order": meta["order"],
            "desc_zh": meta["desc_zh"],
            "artifacts": [p.key for p in products],
            "product_count": len(products),
            "render_engine": meta["render_engine_default"],
            "estimated_min": meta["estimated_min"],
            **({"variant_count": meta["variant_count"]} if "variant_count" in meta else {}),
        })
    return out


# ───────── 自检 · python3 -m _build.arctura_mvp.product_registry --validate ─────────

def _validate() -> list[str]:
    """registry 一致性检查 · 返错误列表 · 空 = OK"""
    errors: list[str] = []
    # 1. key 唯一
    keys = [p.key for p in _PRODUCTS_LIST]
    if len(keys) != len(set(keys)):
        errors.append(f"duplicate product keys: {keys}")
    # 2. id 唯一（non-None）
    ids = [p.id for p in _PRODUCTS_LIST if p.id is not None]
    if len(ids) != len(set(ids)):
        errors.append(f"duplicate product ids: {ids}")
    # 3. id 范围 1-16
    for p in _PRODUCTS_LIST:
        if p.id is not None and not (1 <= p.id <= 16):
            errors.append(f"product {p.key} id={p.id} 不在 1-16")
    # 4. tier 引用合法
    for p in _PRODUCTS_LIST:
        for t in p.tiers:
            if t not in TIER_META:
                errors.append(f"product {p.key} tier={t} 未在 TIER_META")
    # 5. depends_on 引用存在
    for p in _PRODUCTS_LIST:
        for dep in p.depends_on:
            if dep not in PRODUCTS:
                errors.append(f"product {p.key} depends_on={dep} 不存在")
    # 6. LIGHT producer 模块必存在（artifacts/<name>.py）
    from pathlib import Path
    art_dir = Path(__file__).parent / "artifacts"
    for p in _PRODUCTS_LIST:
        if p.light_producer:
            mod_path = art_dir / f"{p.light_producer}.py"
            if not mod_path.exists():
                errors.append(f"product {p.key} light_producer={p.light_producer} 模块 {mod_path} 不存在")
    return errors


if __name__ == "__main__":
    import sys
    if "--validate" in sys.argv:
        errors = _validate()
        if errors:
            print(f"✗ {len(errors)} 个错误：")
            for e in errors:
                print(f"  · {e}")
            sys.exit(1)
        print("✓ product_registry 一致性 OK")
        print(f"  {len(_PRODUCTS_LIST)} 个产物 · {len(TIER_META)} 档")
        for tier in all_tier_ids():
            products = resolve_tier_products(tier)
            print(f"  {tier:8s} → {len(products):2d} artifacts: {[p.key for p in products]}")
    else:
        # 默认打印 tier 表
        import json
        print(json.dumps(list_tiers_for_ui(), ensure_ascii=False, indent=2))
