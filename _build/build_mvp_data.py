#!/usr/bin/env python3
"""
build_mvp_data.py — 扫 StartUP-Building 的 41 个 MVP 产数据 JSON 给前端用

Input:
  - $SB_ROOT/studio-demo/mvp/*/  (室内 25 个)
  - $SB_ROOT/studio-demo/arch-mvp/*/  (建筑 17 个)
  - $SB_ROOT/studio-demo/ALL-MVPS-ENERGY-BOQ.json (聚合能耗/合规)

Output:
  - Arctura-Front-end/data/mvps-index.json  (gallery 摘要)
  - Arctura-Front-end/data/mvps/<slug>.json  (每 MVP 完整数据 · Project Space 用)

Usage:
  source env-linux.sh  # 设 $SB_ROOT
  $PY _build/build_mvp_data.py
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

SB_ROOT = Path(os.environ.get("SB_ROOT", "/root/projects/公司项目/Building-CLI-Anything/StartUP-Building"))
FE_ROOT = Path(__file__).resolve().parents[1]  # Arctura-Front-end/
OUT_DATA = FE_ROOT / "data"
OUT_MVPS = OUT_DATA / "mvps"


# 默认的可编辑字段（chat 能改这些，驱动 derived 重算）
# 工程合理值，不是每个 MVP 的真实 pipeline 输出
def default_editable(mvp_cat: str, area_m2: float) -> dict:
    # lighting density 按场景粗略设定（W/m²）
    light_by_cat = {
        "hospitality": 11,
        "workplace": 9,
        "residential": 6,
        "civic": 8,
        "wellness": 10,
    }
    return {
        "area_m2": round(float(area_m2)) if area_m2 else 40,
        "insulation_mm": 60,        # XPS 墙体保温
        "glazing_uvalue": 2.0,      # W/m²K · 双玻默认
        "lighting_cct": 3000,       # K · 2700=warm / 3000=neutral / 4000=cool
        "lighting_density_w_m2": light_by_cat.get(mvp_cat, 8),
        "wwr": 0.25,                # window-to-wall ratio
        "region": "HK",             # 合规地区：HK / CN / US / JP
    }


def scan_variants(mvp_dir: Path, slug: str) -> list[dict]:
    """扫 variants/v*-*/ 子目录，返回 variants.list 条目（所有 v1/v2/v3 全列，v1 默认选）"""
    variants_dir = mvp_dir / "variants"
    if not variants_dir.is_dir():
        return []
    out = []
    for v in sorted(variants_dir.iterdir()):
        if not v.is_dir():
            continue
        name = v.name
        # 跳过非方案目录（_build_comparison_grid.py 等工具）
        if name.startswith("_") or name.startswith("."):
            continue
        # 必须是 v<digit>-<slug> 的形式（过滤掉 __pycache__ / 其他子目录）
        if not (len(name) >= 3 and name[0] == "v" and name[1].isdigit()):
            continue
        # 读 variant 的 brief 描述
        vbrief = safe_read_json(v / "brief.json")
        # project 字段通常是"禅意茶室 · 日式侘寂"这种 · 取 " · " 后面的风格部分
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


def parse_boq_md(md: str) -> tuple[list[dict], float, str]:
    """从 boq-HK.md 解析表格行 + 总价 + 币种"""
    rows = []
    total = 0
    currency = "HK$"
    if "¥" in md or "RMB" in md:
        currency = "¥"
    elif "US$" in md:
        currency = "US$"

    in_table = False
    header_seen = False
    for line in md.splitlines():
        line = line.strip()
        if line.startswith("|") and "---" in line:
            header_seen = True
            in_table = True
            continue
        if in_table and line.startswith("|"):
            cells = [c.strip() for c in line.split("|")[1:-1]]
            if len(cells) >= 5:
                rows.append({
                    "cat": cells[0],
                    "desc": cells[1] if len(cells) > 1 else "",
                    "sub": cells[2] if len(cells) > 2 else "",
                    "qty": cells[3] if len(cells) > 3 else "",
                    "amt": cells[4] if len(cells) > 4 else "",
                })
        elif in_table and not line.startswith("|"):
            in_table = False

    # 总价从 amt 累加（cells 4 可能含 "88,920"）
    for r in rows:
        amt = r.get("amt", "").replace(",", "").replace("HK$", "").replace("¥", "").strip()
        try:
            total += float(amt)
        except ValueError:
            pass

    return rows, total, currency


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


def list_renders(mvp_dir: Path, slug: str) -> list[dict]:
    """列所有 render 图 · 室内从 renders/ · 建筑从顶层 · 路径指向 WebP 部署位置"""
    sources = []
    rdir = mvp_dir / "renders"
    if rdir.is_dir():
        sources.extend(sorted(rdir.glob("*.png")))
    # 建筑 MVP fallback
    if not sources:
        arch_patterns = ["interior.png", "massing.png", "elev-*.png", "floor-*.png", "site*.png"]
        for pat in arch_patterns:
            sources.extend(sorted(mvp_dir.glob(pat)))

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


def categorize_mvp(mvp: dict) -> str:
    """按 brief/scenario/slug 分类到 gallery filter"""
    name = (mvp.get("name_en") or mvp.get("name") or "").lower()
    scenario = (mvp.get("scenario") or "").lower()
    btype = (mvp.get("building_type") or "").lower()
    slug = (mvp.get("slug") or "").lower()
    text = f"{name} {scenario} {btype} {slug}"
    # 顺序：更特异的先（wellness 比 civic 更特异）
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


def build_mvp_record(mvp_dir: Path, mvp_type: str, agg: dict) -> dict:
    """从单个 MVP 目录抽取数据"""
    slug = mvp_dir.name
    brief = safe_read_json(mvp_dir / "brief.json")
    room = safe_read_json(mvp_dir / "room.json")
    building = safe_read_json(mvp_dir / "building.json")
    metrics = safe_read_json(mvp_dir / "case-study" / "metrics.json")

    boq_md = safe_read_text(mvp_dir / "energy" / "boq-HK.md")
    compliance_md = safe_read_text(mvp_dir / "energy" / "compliance-HK.md")

    # Multi-variant MVP 在顶层可能没 brief/room/metrics/boq · fallback 到第一个 variant
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
    renders = list_renders(mvp_dir, slug)

    # 聚合优先，fallback 到 metrics（metrics.json schema 有两个版本：nested energy.X vs flat X，都 fallback）
    eui = (agg.get("eui_kwh_m2_yr") or
           (metrics.get("energy", {}) or {}).get("eui_kwh_m2_yr") or
           metrics.get("eui_kwh_m2_yr") or 0)
    total_energy = (agg.get("total_energy_kwh") or
                    (metrics.get("energy", {}) or {}).get("total_kwh_yr") or
                    metrics.get("annual_energy_kwh") or 0)
    area = (agg.get("floor_area_m2") or
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

    # 完整度判定
    complete = bool(
        brief and
        (room or building) and
        len(renders) >= 6 and
        (mvp_dir / "floorplan.png").exists() and
        boq_rows and
        compliance_checks and
        metrics
    )

    # Gallery 卡片数据
    index_entry = {
        "slug": slug,
        "name": metrics.get("project_name_en") or brief.get("project") or slug,
        "name_zh": metrics.get("project_name_zh") or brief.get("project_zh") or "",
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
                       (metrics.get("compliance", {}) or {}).get("status") or
                       metrics.get("compliance_status") or "—"),
        "thumb": f"/assets/mvps/{slug}/thumb.webp",
        "hero": f"/assets/mvps/{slug}/hero.webp",
        "complete": complete,
    }

    # Project Space 完整数据（ZEN_DATA 兼容）
    zones = []
    functional = brief.get("functional_zones") or []
    for z in functional:
        zones.append({
            "id": (z.get("name") or "").lower().replace(" ", "_")[:20],
            "name": z.get("name", ""),
            "zh": z.get("name_zh", ""),
            "area": z.get("area_m2") or 0,
            "notes": ", ".join(z.get("key_objects", [])),
            # 坐标没有 — 让 Project Space 用 grid 布局兜底
            "x": 0, "y": 0, "w": 20, "h": 20,
        })

    style_raw = brief.get("style")
    style = style_raw if isinstance(style_raw, dict) else {}
    style_keywords = style.get("keywords") if isinstance(style, dict) else None
    if not style_keywords and isinstance(style_raw, str):
        style_keywords = [style_raw]  # string fallback
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
    # else palette = []

    full_data = {
        "slug": slug,
        "cat": index_entry["cat"],
        "type": mvp_type,
        "complete": complete,
        "project": {
            "name": index_entry["name"],
            "zh": index_entry["name_zh"],
            "area": index_entry["area_m2"],
            "location": "Hong Kong",  # 默认 HK，从 brief 覆盖
            "budgetHKD": brief.get("budget_hkd") or 0,
            "style": ", ".join(style_keywords) if isinstance(style_keywords, list) else (style_keywords or ""),
            "palette": palette,
        },
        "renders": renders,
        "floorplan": f"/assets/mvps/{slug}/floorplan.webp" if (mvp_dir / "floorplan.png").exists() else None,
        "moodboard": f"/assets/mvps/{slug}/moodboard.webp" if (mvp_dir / "moodboard.png").exists() else None,
        "hero_img": f"/assets/mvps/{slug}/hero.webp",
        "thumb_img": f"/assets/mvps/{slug}/thumb.webp",
        "zones": zones,
        "furniture": [],  # 暂不抽（需要 scene 几何算坐标）
        "pricing": {
            "HK": {
                "label": "Hong Kong",
                "currency": currency or "HK$",
                "perM2": index_entry["cost_per_m2"] or 0,
                "rows": boq_rows,
                "total": f"{round(grand_total):,}" if grand_total else "0",
                "totalNumber": round(grand_total) if grand_total else 0,
                # BOQ 分档（合计系数 1.47 = 1 + 0.25 MEP + 0.12 prelim + 0.10 cont）
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
                "items": compliance_checks,   # alias
                "verdict": index_entry["compliance"],
                "score": (
                    f"{sum(1 for c in compliance_checks if c.get('status') == 'pass')}/{len(compliance_checks)} passed"
                    if compliance_checks else ""
                ),
            },
        },
        "variants": {"list": scan_variants(mvp_dir, slug)},
        "timeline": [],
        "decks": [],
        "downloads": [
            {"name": f"{slug}-bundle.zip", "ext": "zip", "sub": "All artifacts", "size": "TBD"},
        ],
        # chat 可以编辑这些字段，前端派生字段（eui/cost/compliance）相应重算
        "editable": default_editable(index_entry["cat"], area),
        # 派生字段 · chat 改 editable 后会 recompute 覆盖这些
        "derived": {
            "eui_kwh_m2_yr": round(float(eui), 1) if eui else 0,
            "cost_total": round(float(grand_total)) if grand_total else 0,
            "cost_per_m2": round(float(cost_per_m2)) if cost_per_m2 else 0,
            "co2_t_per_yr": round(float(eui) * float(area) * 0.59 / 1000, 2) if (area and eui) else 0,
        },
    }

    return index_entry, full_data


def main():
    if not SB_ROOT.exists():
        print(f"❌ SB_ROOT 不存在: {SB_ROOT}")
        sys.exit(1)

    # 读聚合数据
    agg_path = SB_ROOT / "studio-demo" / "ALL-MVPS-ENERGY-BOQ.json"
    agg_data = safe_read_json(agg_path)
    agg_results = agg_data.get("results", []) or []
    agg_by_slug = {r.get("slug"): r for r in agg_results if r.get("slug")}
    print(f"📊 聚合数据: {len(agg_by_slug)} 个 MVP")

    # 扫 mvp + arch-mvp
    OUT_MVPS.mkdir(parents=True, exist_ok=True)
    OUT_DATA.mkdir(parents=True, exist_ok=True)

    index = []
    complete_count = 0

    for base, mvp_type in [("mvp", "P1-interior"), ("arch-mvp", "P2-architecture")]:
        base_dir = SB_ROOT / "studio-demo" / base
        if not base_dir.is_dir():
            continue
        for mvp_dir in sorted(base_dir.iterdir()):
            if not mvp_dir.is_dir() or mvp_dir.name.startswith("_"):
                continue
            slug = mvp_dir.name
            agg = agg_by_slug.get(slug, {})
            try:
                index_entry, full_data = build_mvp_record(mvp_dir, mvp_type, agg)
                index.append(index_entry)
                if index_entry["complete"]:
                    complete_count += 1
                (OUT_MVPS / f"{slug}.json").write_text(
                    json.dumps(full_data, ensure_ascii=False, indent=2), encoding="utf-8"
                )
                print(f"  {'✅' if index_entry['complete'] else '⚠️'} {slug:<40} {index_entry['cat']:<12} EUI={index_entry['eui']} cost={index_entry['cost_per_m2']}")
            except Exception as e:
                print(f"  ❌ {slug}: {e}")
                import traceback
                traceback.print_exc()

    # 按 complete 降序 + slug 升序
    index.sort(key=lambda x: (not x["complete"], x["slug"]))
    (OUT_DATA / "mvps-index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"\n📈 总计: {len(index)} MVP · 完整 {complete_count} · 写入 data/mvps-index.json + data/mvps/*.json")


if __name__ == "__main__":
    main()
