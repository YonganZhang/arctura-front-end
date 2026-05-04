"""materializer · 扫磁盘 MVP 产物 → 构前端 data/mvps/<slug>.json（Phase 9.4）

Context:
  Phase 9.3 worker 产 11 个真产物落 StartUP-Building/studio-demo/mvp/<slug>/ 磁盘 ·
  但前端 /project/<slug> 只吃 Arctura-Front-end/data/mvps/<slug>.json · 这个 JSON
  之前由 save.js 硬编码空壳 (`renders:[], decks:[], energy.eui:45`)
  → 磁盘真产物展示不出来（Codex 2026-04-24 审查发现）。

  此模块把 build_mvp_data.py 里的扫盘逻辑抽出 · 让 worker 跑完 pipeline 直接
  建完整前端 JSON · 前端立刻看到真 renders / 真 EUI / 真 PPT 链接。

入口:
  build_fe_payload(mvp_dir, slug, fe_root, mvp_type, agg) -> dict
    返回对齐 pilot 01-study-room.json schema 的完整前端 JSON
    worker 用 · save.js 用（via project.artifacts.fe_payload）

  build_mvp_record(mvp_dir, mvp_type, agg, fe_root) -> (index_entry, full_data)
    返回 tuple · build_mvp_data.py 批量 CLI 用

纯函数 · 不依赖全局 FE_ROOT/SB_ROOT · 可被 worker / save.js-via-kv / CLI 共用。
"""
from __future__ import annotations
import json
import re
from pathlib import Path
from typing import Optional


# ───────── 默认可编辑字段 ─────────

def default_editable(mvp_cat: str, area_m2: float) -> dict:
    """chat 能改这些字段 · 驱动 derived (eui/cost) 重算

    lighting density 按场景粗略设（W/m²）· 工程合理值。
    Phase 11.7 改走 resolver 注册表 · 修 LLM 推 'wellness center'/'校长办公室' 等
    脏 mvp_cat 之前 fallback 8 W/m² 的塌缩盲点。
    """
    from .resolvers import get as get_resolver, LIGHTING_DENSITY_W_M2_BY_CAT
    cat_canonical = get_resolver("building_category").resolve_first(mvp_cat)
    return {
        "area_m2": round(float(area_m2)) if area_m2 else 40,
        "insulation_mm": 60,        # XPS 墙体保温
        "glazing_uvalue": 2.0,      # W/m²K · 双玻默认
        "lighting_cct": 3000,       # K · 2700=warm / 3000=neutral / 4000=cool
        "lighting_density_w_m2": LIGHTING_DENSITY_W_M2_BY_CAT[cat_canonical],
        "wwr": 0.25,                # window-to-wall ratio
        "region": "HK",             # 合规地区：HK / CN / US / JP
    }


# ───────── I/O helpers ─────────

def safe_read_json(p: Path) -> dict:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def safe_read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except Exception:
        return ""


def _first_str(*candidates):
    """返回第一个非空 str · 跳过 None/dict/list/空串"""
    for c in candidates:
        if isinstance(c, str) and c.strip():
            return c
    return None


# ───────── BOQ / compliance 解析 ─────────

def parse_boq_md(md: str) -> tuple[list[dict], float, str]:
    """从 boq-HK.md 解析表格行 + 总价 + 币种

    支持两种表头：
      - 老 5 列: `| Cat | Desc | Sub | Qty | Amt |`
      - 严老师 openstudio 7 列: `| # | Category | Description | Qty | Unit | Unit Price | Total |`
    Grand Total 从 "Grand Total" 行抽 · fallback 累加 line items
    """
    rows = []
    total = 0
    currency = "HK$"
    if "¥" in md or "RMB" in md:
        currency = "¥"
    elif "US$" in md:
        currency = "US$"

    # 优先抓 "Grand Total" 明示行（严老师 openstudio 格式）
    import re as _re
    m = _re.search(r"\*\*Grand Total\*\*\s*\|\s*\*\*([\d,]+)\*\*", md)
    if m:
        try:
            total = float(m.group(1).replace(",", ""))
        except ValueError:
            total = 0

    in_table = False
    header_7col = False
    for line in md.splitlines():
        line = line.strip()
        # 识别表头 · 判列数
        if line.startswith("|") and ("Category" in line or "Description" in line) and "Total" in line:
            header_7col = "Unit Price" in line or "Unit\xa0Price" in line
            continue
        if line.startswith("|") and "---" in line:
            in_table = True
            continue
        if in_table and line.startswith("|"):
            cells = [c.strip() for c in line.split("|")[1:-1]]
            if header_7col and len(cells) >= 7:
                # 7 列：# | Category | Description | Qty | Unit | Unit Price | Total
                rows.append({
                    "cat": cells[1],
                    "desc": cells[2],
                    "sub": cells[4],  # unit
                    "qty": cells[3],
                    "amt": cells[6],
                })
            elif len(cells) >= 5:
                # 老 5 列格式
                rows.append({
                    "cat": cells[0],
                    "desc": cells[1] if len(cells) > 1 else "",
                    "sub": cells[2] if len(cells) > 2 else "",
                    "qty": cells[3] if len(cells) > 3 else "",
                    "amt": cells[4] if len(cells) > 4 else "",
                })
        elif in_table and not line.startswith("|"):
            in_table = False
            header_7col = False

    # fallback total · 累加 rows（if Grand Total 没抓到）
    if not total:
        for r in rows:
            amt = r.get("amt", "").replace(",", "").replace("HK$", "").replace("¥", "").replace("**", "").strip()
            try:
                total += float(amt)
            except ValueError:
                pass

    return rows, total, currency


def parse_boq_floor_area(md: str) -> float:
    """从 boq-HK.md 头部 "**Floor area**: 42.0 m²" 抽面积"""
    import re as _re
    m = _re.search(r"\*\*Floor area\*\*\s*[:：]\s*([\d.]+)", md)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass
    return 0


def parse_compliance_verdict(md: str) -> str:
    """从 compliance-HK.md 抽 Verdict 行 · 返 'COMPLIANT' / 'NON-COMPLIANT' / 'ADVISORY' / '—'"""
    import re as _re
    m = _re.search(r"\*\*Verdict\*\*:\s*(?:✅|⚠️|❌)?\s*([A-Z\-]+)", md)
    if m:
        return m.group(1).strip()
    return "—"


def parse_compliance_md(md: str) -> list[dict]:
    """从 compliance-HK.md 的表格抽 checks"""
    checks = []
    in_table = False
    for line in md.splitlines():
        line = line.strip()
        if line.startswith("| Check") or (line.startswith("|") and "Check" in line and "Status" in line):
            in_table = True
            continue
        if in_table and line.startswith("|") and "---" in line:
            continue
        if in_table and line.startswith("|"):
            cells = [c.strip() for c in line.split("|")[1:-1]]
            if len(cells) >= 5:
                status = cells[4]
                ok = "✅" in status
                warn = "⚠️" in status
                fail = "❌" in status
                checks.append({
                    "name": re.sub(r"\*\*|\[|\]", "", cells[0]).strip(),
                    "value": cells[1],
                    "limit": cells[2],
                    "unit": cells[3],
                    "status": "advisory" if warn else ("pass" if ok else "fail" if fail else "unknown"),
                    "note": cells[5] if len(cells) > 5 else "",
                })
        elif in_table and not line.startswith("|"):
            in_table = False
    return checks


# ───────── render / variants 扫描 ─────────

def list_renders(mvp_dir: Path, slug: str) -> list[dict]:
    """列所有 render 图 · 路径指向 WebP 部署位置

    源：
      1. mvp_dir/renders/*.png (室内标准)
      2. mvp_dir/*.png (建筑 interior/massing/elev/floor/site)
      3. mvp_dir/variants/v*/renders/*.png (多变体 MVP)
    """
    sources = []
    rdir = mvp_dir / "renders"
    if rdir.is_dir():
        sources.extend(sorted(rdir.glob("*.png")))
    if not sources:
        arch_patterns = ["interior.png", "massing.png", "elev-*.png", "floor-*.png", "site*.png"]
        for pat in arch_patterns:
            sources.extend(sorted(mvp_dir.glob(pat)))

    # 多变体 fallback
    if not sources:
        variants_dir = mvp_dir / "variants"
        if variants_dir.is_dir():
            for v in sorted(variants_dir.iterdir()):
                if not v.is_dir():
                    continue
                if not (len(v.name) >= 3 and v.name[0] == "v" and v.name[1].isdigit()):
                    continue
                v_rdir = v / "renders"
                if v_rdir.is_dir():
                    v_pngs = sorted(v_rdir.glob("*.png"))
                    if v_pngs:
                        out = []
                        for p in v_pngs:
                            name = p.stem
                            out.append({
                                "id": name.split("_", 1)[0] if "_" in name else name,
                                "file": f"/assets/mvps/{slug}/variants/{v.name}/renders/{name}.webp",
                                "title": name.replace("_", " ").replace("-", " ").title(),
                                "tag": name,
                            })
                        return out
                break

    out = []
    for p in sources:
        name = p.stem
        out.append({
            "id": name.split("_", 1)[0] if "_" in name else name,
            "file": f"/assets/mvps/{slug}/renders/{name}.webp",
            "title": name.replace("_", " ").replace("-", " ").title(),
            "tag": name,
        })
    return out


def list_fe_renders(fe_root: Path, slug: str) -> list[dict]:
    """Phase 9.4 · LIGHT pipeline 产的 renders 落在 Arctura-Front-end/assets/mvps/<slug>/renders/
    不在 StartUP-Building 侧 · 补一个扫 FE 侧 renders 的路径
    """
    rdir = fe_root / "assets" / "mvps" / slug / "renders"
    if not rdir.is_dir():
        return []
    out = []
    for p in sorted(rdir.iterdir()):
        if p.suffix.lower() not in (".png", ".webp", ".jpg", ".jpeg"):
            continue
        name = p.stem
        out.append({
            "id": name.split("_", 1)[0] if "_" in name else name,
            "file": f"/assets/mvps/{slug}/renders/{p.name}",
            "title": name.replace("_", " ").replace("-", " ").title(),
            "tag": name,
        })
    return out


def scan_variants(mvp_dir: Path, slug: str) -> list[dict]:
    """扫 variants/v*-*/ 子目录 · 返回 variants.list 条目"""
    variants_dir = mvp_dir / "variants"
    if not variants_dir.is_dir():
        return []
    out = []
    for v in sorted(variants_dir.iterdir()):
        if not v.is_dir():
            continue
        name = v.name
        if name.startswith("_") or name.startswith("."):
            continue
        if not (len(name) >= 3 and name[0] == "v" and name[1].isdigit()):
            continue
        vbrief = safe_read_json(v / "brief.json")
        project_zh = vbrief.get("project", "")
        project_en = vbrief.get("project_en", "")
        style_zh = project_zh.split("·")[-1].strip() if "·" in project_zh else project_zh
        style_en = project_en.split("·")[-1].strip() if "·" in project_en else project_en
        label = style_en or style_zh or name.split("-", 1)[-1].replace("-", " ").title()
        desc = (vbrief.get("space", {}) or {}).get("description", "") or ""
        out.append({
            "id": name,
            "name": label,
            "name_zh": style_zh if "·" in project_zh else "",
            "desc": desc[:120] + ("…" if len(desc) > 120 else ""),
            "thumb": f"/assets/mvps/{slug}/variants/{name}/thumb.webp",
            "hero": f"/assets/mvps/{slug}/variants/{name}/hero.webp",
        })
    return out


# ───────── 分类 ─────────

def categorize_mvp(mvp: dict) -> str:
    """按 brief/scenario/slug 分类到 gallery filter · 顺序: 更特异的先"""
    name = (mvp.get("name_en") or mvp.get("name") or "").lower()
    scenario = (mvp.get("scenario") or "").lower()
    btype = (mvp.get("building_type") or "").lower()
    slug = (mvp.get("slug") or "").lower()
    text = f"{name} {scenario} {btype} {slug}"
    if any(w in text for w in ["clinic", "fitness", "wellness", "pool", "dental", "daycare", "medical", "hospital"]):
        return "wellness"
    if any(w in text for w in ["cafe", "restaurant", "hotel", "bar", "bakery", "tea", "lounge", "coffee", "bistro", "retreat"]):
        return "hospitality"
    if any(w in text for w in ["office", "cowork", "startup", "conference", "study-room", "study-hall", "studio", "recording"]):
        return "workplace"
    if any(w in text for w in ["house", "home", "villa", "penthouse", "living", "bedroom", "elderly", "residential", "family"]):
        return "residential"
    if any(w in text for w in ["library", "gallery", "museum", "community", "book", "retail", "floral", "hair", "salon", "sports", "art-pavilion", "mixed-use", "nt-family", "village"]):
        return "civic"
    if any(w in text for w in ["kids", "daycare", "esports", "game", "industrial-living"]):
        return "residential"
    return "other"


# ───────── 主入口 ─────────

def build_mvp_record(
    mvp_dir: Path,
    mvp_type: str,
    agg: dict,
    fe_root: Path,
    asset_urls: Optional[dict] = None,
) -> tuple[dict, dict]:
    """从单个 MVP 目录抽取数据 · 返回 (index_entry, full_data) tuple

    参数:
      mvp_dir: StartUP-Building/studio-demo/mvp/<slug>/ 真产物目录
      mvp_type: "P1-interior" / "P2-architecture"
      agg: ALL-MVPS-ENERGY-BOQ.json 聚合数据（批量跑时用 · worker 传 {}）
      fe_root: Arctura-Front-end/ 根目录 · 查找 assets/ 和 LIGHT pipeline 产的 renders
      asset_urls: Phase 9.8 · blob_push.upload_mvp_assets 的返值 · URL 指向 Vercel Blob CDN
                  · None 时（老 MVP 批量跑 / 本机 preview）走老逻辑 /assets/mvps/<slug>/...

    返回: (index_entry, full_data) — 给 build_mvp_data.py 用
    """
    slug = mvp_dir.name
    brief = safe_read_json(mvp_dir / "brief.json")
    room = safe_read_json(mvp_dir / "room.json")
    building = safe_read_json(mvp_dir / "building.json")
    metrics = safe_read_json(mvp_dir / "case-study" / "metrics.json")

    boq_md = safe_read_text(mvp_dir / "energy" / "boq-HK.md")
    compliance_md = safe_read_text(mvp_dir / "energy" / "compliance-HK.md")

    # Multi-variant fallback
    variants_dir = mvp_dir / "variants"
    if not brief and variants_dir.is_dir():
        for v in sorted(variants_dir.iterdir()):
            if v.is_dir() and len(v.name) >= 3 and v.name[0] == "v" and v.name[1].isdigit():
                brief = brief or safe_read_json(v / "brief.json")
                room = room or safe_read_json(v / "room.json")
                building = building or safe_read_json(v / "building.json")
                metrics = metrics or safe_read_json(v / "case-study" / "metrics.json")
                boq_md = boq_md or safe_read_text(v / "energy" / "boq-HK.md")
                compliance_md = compliance_md or safe_read_text(v / "energy" / "compliance-HK.md")
                if brief:
                    break

    boq_rows, boq_total, currency = parse_boq_md(boq_md)
    compliance_checks = parse_compliance_md(compliance_md)
    verdict_from_md = parse_compliance_verdict(compliance_md)

    # Phase 9.4 · LIGHT pipeline 产的 renders 在 fe_root/assets/mvps/<slug>/renders/
    # 老 MVP renders 在 mvp_dir/renders/ · 两侧都扫 · fe_root 优先（新 pipeline）
    renders = list_fe_renders(fe_root, slug) or list_renders(mvp_dir, slug)

    # Phase 9.4 · 从 compliance_md 抽真 EUI · 比 metrics.json fallback 强（metrics 常 None）
    eui_from_compliance = 0
    for c in compliance_checks:
        if "EUI" in c.get("name", "") or "Energy Use Intensity" in c.get("name", ""):
            try:
                eui_from_compliance = float(c.get("value", "0").replace(",", ""))
            except ValueError:
                pass
            break

    # 聚合优先 · compliance_md · fallback metrics
    eui = (agg.get("eui_kwh_m2_yr") or
           eui_from_compliance or
           (metrics.get("energy", {}) or {}).get("eui_kwh_m2_yr") or
           metrics.get("eui_kwh_m2_yr") or 0)
    total_energy = (agg.get("total_energy_kwh") or
                    (metrics.get("energy", {}) or {}).get("total_kwh_yr") or
                    metrics.get("annual_energy_kwh") or 0)
    area = (agg.get("floor_area_m2") or
            parse_boq_floor_area(boq_md) or
            metrics.get("area_sqm_scene") or
            metrics.get("area_sqm") or
            (brief.get("space", {}) or {}).get("area_sqm") or 0)
    grand_total = (agg.get("boq_grand_total") or
                   (metrics.get("boq", {}) or {}).get("grand_total") or
                   metrics.get("boq_hkd") or
                   boq_total or 0)
    cost_per_m2 = (agg.get("boq_cost_per_m2") or
                   (metrics.get("boq", {}) or {}).get("unit_cost_per_sqm") or
                   metrics.get("cost_per_m2_hkd") or
                   (grand_total / area if area else 0))

    complete = bool(
        brief and
        (room or building) and
        len(renders) >= 6 and
        ((mvp_dir / "floorplan.png").exists() or (fe_root / "assets" / "mvps" / slug / "floorplan.png").exists()) and
        boq_rows and
        compliance_checks and
        metrics
    )

    index_entry = {
        "slug": slug,
        "name": _first_str(
            metrics.get("project_name_en"),
            brief.get("project_en") if isinstance(brief.get("project_en"), str) else None,
            brief.get("project") if isinstance(brief.get("project"), str) else None,
            slug,
        ),
        "name_zh": _first_str(
            metrics.get("project_name_zh"),
            brief.get("project_zh") if isinstance(brief.get("project_zh"), str) else None,
        ) or "",
        "type": mvp_type,
        "cat": categorize_mvp({
            "name_en": metrics.get("project_name_en"),
            "scenario": metrics.get("scenario"),
            "building_type": agg.get("building_type"),
            "slug": slug,
        }),
        "area_m2": round(float(area)) if area else 0,
        "eui": round(float(eui), 1) if eui else None,
        "cost_per_m2": round(float(cost_per_m2)) if cost_per_m2 else None,
        "currency": currency,
        "compliance": (agg.get("compliance_verdict") or
                       (verdict_from_md if verdict_from_md != "—" else None) or
                       (metrics.get("compliance", {}) or {}).get("status") or
                       metrics.get("compliance_status") or "—"),
        "thumb": f"/assets/mvps/{slug}/thumb.webp",
        "hero": f"/assets/mvps/{slug}/hero.webp",
        "complete": complete,
    }

    # zones
    zones = []
    for z in (brief.get("functional_zones") or []):
        zones.append({
            "id": (z.get("name") or "").lower().replace(" ", "_")[:20],
            "name": z.get("name", ""),
            "zh": z.get("name_zh", ""),
            "area": z.get("area_m2") or z.get("area_sqm") or 0,
            "notes": ", ".join(z.get("key_objects", [])),
            "x": 0, "y": 0, "w": 20, "h": 20,
        })

    # style + palette
    style_raw = brief.get("style")
    style = style_raw if isinstance(style_raw, dict) else {}
    style_keywords = style.get("keywords") if isinstance(style, dict) else None
    if not style_keywords and isinstance(style_raw, str):
        style_keywords = [style_raw]
    if not style_keywords and isinstance(style_raw, list):
        style_keywords = style_raw
    palette_raw = style.get("palette") if isinstance(style, dict) else None
    palette = []
    if isinstance(palette_raw, dict):
        palette = [{"name": k, "hex": v} for k, v in palette_raw.items()]
    elif isinstance(palette_raw, list):
        for p in palette_raw:
            if isinstance(p, dict):
                palette.append(p)
            elif isinstance(p, str) and p.startswith("#"):
                palette.append({"name": "", "hex": p})

    # Phase 9.4 · moodboard 产的 palette 6 色 · 从 moodboard.json 读（如 brief 没）
    if not palette:
        moodboard = safe_read_json(mvp_dir / "moodboard.json") or safe_read_json(
            fe_root / "assets" / "mvps" / slug / "moodboard.json"
        )
        mb_palette = moodboard.get("palette") or moodboard.get("swatches") or []
        if isinstance(mb_palette, list):
            for p in mb_palette:
                if isinstance(p, dict) and p.get("hex"):
                    palette.append({"name": p.get("name", ""), "hex": p["hex"]})
                elif isinstance(p, str) and p.startswith("#"):
                    palette.append({"name": "", "hex": p})

    # 3D model GLB · 多源 fallback
    model_glb = None
    for cand in [
        fe_root / "assets" / "mvps" / slug / "model.glb",
        mvp_dir / "exports" / f"{slug}.glb",
    ]:
        if cand.exists():
            if cand.is_relative_to(fe_root):
                model_glb = "/" + str(cand.relative_to(fe_root))
            else:
                model_glb = f"/assets/mvps/{slug}/{cand.name}"
            break
    if not model_glb:
        variants_assets = fe_root / "assets" / "mvps" / slug / "variants"
        if variants_assets.is_dir():
            for v in sorted(variants_assets.iterdir()):
                if v.is_dir() and (v / "model.glb").exists():
                    model_glb = f"/assets/mvps/{slug}/variants/{v.name}/model.glb"
                    break

    # Phase 9.4 · decks + downloads · 扫真产物
    decks = []
    decks_dir = mvp_dir / "decks"
    if decks_dir.is_dir():
        for name, label in [
            ("deck-client.pptx", "Client deck (PPTX)"),
            ("deck-client.pdf", "Client deck (PDF)"),
            ("deck-client.md", "Client deck (Markdown)"),
        ]:
            f = decks_dir / name
            if f.exists():
                decks.append({
                    "name": name,
                    "label": label,
                    "size_kb": round(f.stat().st_size / 1024, 1),
                    "url": f"/assets/mvps/{slug}/decks/{name}",
                })

    downloads = []
    # bundle
    bundle = fe_root / "assets" / "mvps" / slug / "bundle.zip"
    if bundle.exists():
        downloads.append({
            "name": f"{slug}-bundle.zip",
            "ext": "zip",
            "sub": "All artifacts",
            "size": f"{round(bundle.stat().st_size / 1024)} KB",
            "url": f"/assets/mvps/{slug}/bundle.zip",
        })
    # exports 5 件套
    exports_dir = mvp_dir / "exports"
    if exports_dir.is_dir():
        for ext, label in [("glb", "3D model (GLB)"), ("obj", "3D mesh (OBJ)"),
                           ("fbx", "3D scene (FBX)"), ("ifc", "BIM (IFC4)"),
                           ("dxf", "2D CAD (DXF)")]:
            f = exports_dir / f"{slug}.{ext}"
            if f.exists():
                downloads.append({
                    "name": f"{slug}.{ext}",
                    "ext": ext,
                    "sub": label,
                    "size": f"{round(f.stat().st_size / 1024)} KB",
                    "url": f"/assets/mvps/{slug}/exports/{slug}.{ext}",
                })
    # energy CSV
    boq_csv = mvp_dir / "energy" / "boq-HK.csv"
    if boq_csv.exists():
        downloads.append({
            "name": "boq-HK.csv",
            "ext": "csv",
            "sub": "BOQ spreadsheet",
            "size": f"{round(boq_csv.stat().st_size / 1024, 1)} KB",
            "url": f"/assets/mvps/{slug}/energy/boq-HK.csv",
        })
    # CLIENT-README
    client_readme = mvp_dir / "CLIENT-README.md"
    if client_readme.exists():
        downloads.append({
            "name": "CLIENT-README.md",
            "ext": "md",
            "sub": "Client documentation",
            "size": f"{round(client_readme.stat().st_size / 1024, 1)} KB",
            "url": f"/assets/mvps/{slug}/CLIENT-README.md",
        })

    # floorplan / moodboard · fe_root 优先（LIGHT 产的） · fallback mvp_dir
    def _first_asset(*cands: Path) -> str | None:
        for p in cands:
            if p.exists():
                if p.is_relative_to(fe_root):
                    return "/" + str(p.relative_to(fe_root)).replace("\\", "/")
        return None

    floorplan_url = _first_asset(
        fe_root / "assets" / "mvps" / slug / "floorplan.webp",
        fe_root / "assets" / "mvps" / slug / "floorplan.png",
    )
    if not floorplan_url and (mvp_dir / "floorplan.png").exists():
        floorplan_url = f"/assets/mvps/{slug}/floorplan.webp"  # build-images 后存在

    moodboard_url = _first_asset(
        fe_root / "assets" / "mvps" / slug / "moodboard.webp",
        fe_root / "assets" / "mvps" / slug / "moodboard.png",
    )
    if not moodboard_url and (mvp_dir / "moodboard.png").exists():
        moodboard_url = f"/assets/mvps/{slug}/moodboard.webp"

    # Phase 9.8 · asset_urls 覆盖 · 如果传入了 Blob URLs 就用 Blob · 否则继续老 /assets/ 路径
    if asset_urls:
        # renders · Blob URL 覆盖所有 file 字段（保持 id/title/tag 不变 · 只换 URL）
        if asset_urls.get("renders"):
            for i, r in enumerate(renders):
                if i < len(asset_urls["renders"]):
                    r["file"] = asset_urls["renders"][i]
        # GLB
        if asset_urls.get("glb"):
            model_glb = asset_urls["glb"]
        # misc: floorplan / moodboard
        misc = asset_urls.get("misc") or {}
        if misc.get("floorplan.png"):
            floorplan_url = misc["floorplan.png"]
        if misc.get("moodboard.png"):
            moodboard_url = misc["moodboard.png"]
        # decks · 更新 url 字段
        blob_decks = asset_urls.get("decks") or {}
        for d in decks:
            ext_key = d.get("name", "").split(".")[-1].lower()
            if ext_key in blob_decks:
                d["url"] = blob_decks[ext_key]
        # downloads · 更新 url · 包含 bundle / exports / energy csv / CLIENT-README
        blob_bundle = asset_urls.get("bundle")
        blob_exports = asset_urls.get("exports") or {}
        blob_energy = asset_urls.get("energy") or {}
        blob_glb = asset_urls.get("glb")
        for d in downloads:
            ext = d.get("ext", "").lower()
            name = d.get("name", "")
            if ext == "zip" and blob_bundle:
                d["url"] = blob_bundle
            elif ext == "glb" and blob_glb:
                d["url"] = blob_glb
            elif ext in blob_exports:
                d["url"] = blob_exports[ext]
            elif ext == "csv" and blob_energy.get("boq_csv"):
                d["url"] = blob_energy["boq_csv"]
            elif name == "CLIENT-README.md" and misc.get("CLIENT-README.md"):
                d["url"] = misc["CLIENT-README.md"]

    full_data = {
        "slug": slug,
        "cat": index_entry["cat"],
        "type": mvp_type,
        "complete": complete,
        "model_glb": model_glb,
        "project": {
            "name": index_entry["name"],
            "zh": index_entry["name_zh"],
            "area": index_entry["area_m2"],
            "location": "Hong Kong",
            "budgetHKD": brief.get("budget_hkd") or 0,
            "style": ", ".join(style_keywords) if isinstance(style_keywords, list) else (style_keywords or ""),
            "palette": palette,
        },
        "renders": renders,
        "floorplan": floorplan_url,
        "moodboard": moodboard_url,
        "hero_img": f"/assets/mvps/{slug}/hero.webp",
        "thumb_img": f"/assets/mvps/{slug}/thumb.webp",
        "zones": zones,
        "furniture": [],
        "pricing": {
            "HK": {
                "label": "Hong Kong",
                "currency": currency or "HK$",
                "perM2": index_entry["cost_per_m2"] or 0,
                "rows": boq_rows,
                "total": f"{round(grand_total):,}" if grand_total else "0",
                "totalNumber": round(grand_total) if grand_total else 0,
                "subtotal": f"{round(grand_total / 1.47):,}" if grand_total else "0",
                "mep": f"{round(grand_total / 1.47 * 0.25):,}" if grand_total else "0",
                "prelim": f"{round(grand_total / 1.47 * 0.12):,}" if grand_total else "0",
                "cont": f"{round(grand_total / 1.47 * 0.10):,}" if grand_total else "0",
            },
        },
        "energy": {
            "eui": eui,
            "limit": 150,
            "annual": total_energy,
            "engine": metrics.get("energy", {}).get("engine", "EnergyPlus"),
        },
        "compliance": {
            "HK": {
                "code": agg.get("code", "HK_BEEO_BEC_2021"),
                "label": "HK · BEEO 2021",
                "checks": compliance_checks,
                "items": compliance_checks,
                "verdict": index_entry["compliance"],
                "score": (
                    f"{sum(1 for c in compliance_checks if c.get('status') == 'pass')}/{len(compliance_checks)} passed"
                    if compliance_checks else ""
                ),
            },
        },
        "variants": {"list": scan_variants(mvp_dir, slug)},
        "timeline": [],
        "decks": decks,
        "downloads": downloads or [
            {"name": f"{slug}-bundle.zip", "ext": "zip", "sub": "All artifacts", "size": "TBD"},
        ],
        "editable": default_editable(index_entry["cat"], area),
        "derived": {
            "eui_kwh_m2_yr": round(float(eui), 1) if eui else 0,
            "cost_total": round(float(grand_total)) if grand_total else 0,
            "cost_per_m2": round(float(cost_per_m2)) if cost_per_m2 else 0,
            "co2_t_per_yr": round(float(eui) * float(area) * 0.59 / 1000, 2) if (area and eui) else 0,
        },
    }

    return index_entry, full_data


def build_fe_payload(
    mvp_dir: Path,
    slug: str,
    fe_root: Path,
    mvp_type: str = "P1-interior",
    agg: dict | None = None,
    asset_urls: dict | None = None,
) -> dict:
    """Phase 9.4 主入口 · 返前端 data/mvps/<slug>.json payload · worker + save.js 用

    slug 作为独立参数是因为 worker 跑的时候 mvp_dir.name 已经是 slug，
    但为了防御性（dir 名和 slug 漂移）· 显式传。

    asset_urls (Phase 9.8 · optional):
      blob_push.upload_mvp_assets() 的返值 · 把本地 /assets/mvps/<slug>/* 路径
      替换为 Vercel Blob CDN URL · 让前端不依赖 Vercel deploy 分发资产。
    """
    _index, full_data = build_mvp_record(mvp_dir, mvp_type, agg or {}, fe_root, asset_urls=asset_urls)
    return full_data
