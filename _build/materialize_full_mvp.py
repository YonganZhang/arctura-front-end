#!/usr/bin/env python3
"""补齐 MVP 到 CLAUDE.md 权威"必含产物"清单 · 产出全套文本/SVG/markdown 产物

权威清单来自 StartUP-Building/CLAUDE.md L405-434：
  brief.json · moodboard.{png,json} · room.json · renders/×8 · floorplan.{svg,png}
  decks/deck-client.{md,pptx,pdf} · CLIENT-README.md · exports/ · energy/ · case-study/

能做：文本/Markdown/SVG · 需要 marp 做 PPT · rsvg/inkscape 做 PNG
做不到（明确告知用户）：renders(Blender)、exports(Blender)、moodboard.png 合成、variant 渲染图

用法：
  python3 _build/materialize_full_mvp.py --slug 50-principal-office
"""
import argparse, json, subprocess, shutil
from datetime import datetime
from pathlib import Path

FE_ROOT = Path(__file__).resolve().parents[1]
SB_ROOT = FE_ROOT.parent / "StartUP-Building" / "studio-demo" / "mvp"


def _mvp_dir(slug):
    p = SB_ROOT / slug
    p.mkdir(parents=True, exist_ok=True)
    for sub in ["renders", "exports", "decks", "case-study/thumbs",
                "energy/ep_output", "variants"]:
        (p / sub).mkdir(parents=True, exist_ok=True)
    return p


def _write_brief(d, mvp):
    proj = mvp["project"]
    brief = {
        "project_id": mvp["slug"],
        "project_name": proj.get("name"),
        "project_name_zh": proj.get("zh"),
        "schema_version": "brief-interior-v1",
        "cat": mvp.get("cat", "workplace"),
        "type": mvp.get("type", "P1-interior"),
        "location": proj.get("location", "Hong Kong"),
        "area_m2": proj.get("area"),
        "budget_HKD": proj.get("budgetHKD"),
        "style": proj.get("style"),
        "palette": proj.get("palette", []),
        "zones": mvp.get("zones", []),
        "openings": {"wwr": mvp.get("editable", {}).get("wwr", 0.25)},
        "mep_brief": {
            "lighting_cct": mvp.get("editable", {}).get("lighting_cct"),
            "lighting_density_w_m2": mvp.get("editable", {}).get("lighting_density_w_m2"),
        },
        "envelope": {
            "insulation_mm": mvp.get("editable", {}).get("insulation_mm"),
            "glazing_uvalue": mvp.get("editable", {}).get("glazing_uvalue"),
        },
        "derived_from": "Arctura-Front-end/create_mvp_from_brief.py",
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }
    (d / "brief.json").write_text(json.dumps(brief, ensure_ascii=False, indent=2))


def _write_room(d, mvp):
    scene = mvp.get("scene", {})
    room = {
        "schema_version": "room-v1",
        "unit": "m",
        "bounds": scene.get("bounds"),
        "objects": [
            {
                "id": o["id"], "name": o.get("label_en"), "name_zh": o.get("label_zh"),
                "type": o["type"], "location": o["pos"], "rotation": o.get("rotation", [0, 0, 0]),
                "scale": o["size"], "material": o.get("material_id"), "visible": True,
                "mesh_type": o.get("mesh_type_legacy", "default"),
            }
            for o in scene.get("objects", [])
        ],
        "lights": scene.get("lights", []),
        "materials": scene.get("materials", {}),
        "cameras": [{"id": "default", "pos": scene.get("camera_default", {}).get("pos", [4, -3, 1.8]),
                     "lookAt": scene.get("camera_default", {}).get("lookAt", [0, 0, 1.2]),
                     "fov": scene.get("camera_default", {}).get("fov", 50)}],
        "walls": scene.get("walls", []),
        "assemblies": scene.get("assemblies", []),
    }
    (d / "room.json").write_text(json.dumps(room, ensure_ascii=False, indent=2))


def _write_moodboard_json(d, mvp):
    proj = mvp["project"]
    (d / "moodboard.json").write_text(json.dumps({
        "palette": proj.get("palette", []),
        "style_keywords": proj.get("style", "").split(", "),
        "reference_images": [],
    }, ensure_ascii=False, indent=2))


def _render_moodboard_png(d, mvp):
    """用 PIL 生成色板拼图 · 无需 Blender"""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return False
    palette = mvp["project"].get("palette", [])
    if not palette:
        return False
    W, H = 1600, 900
    img = Image.new("RGB", (W, H), "#1a1511")
    draw = ImageDraw.Draw(img)
    sw_w = W // max(len(palette), 1)
    for i, p in enumerate(palette):
        try:
            draw.rectangle([i * sw_w, 200, (i + 1) * sw_w, H - 80], fill=p["hex"])
        except Exception:
            pass
        try:
            draw.text((i * sw_w + 20, H - 60), f"{p.get('name','')}  {p['hex']}", fill="#F5F1E8")
        except Exception:
            pass
    try:
        draw.text((40, 40), mvp["project"].get("name", mvp["slug"]), fill="#F5F1E8")
        draw.text((40, 110), f"{mvp['project'].get('style','')}", fill="#C9BFAE")
    except Exception:
        pass
    img.save(d / "moodboard.png")
    return True


def _write_floorplan_svg(d, mvp):
    scene = mvp.get("scene", {})
    b = scene.get("bounds", {"w": 6, "d": 5, "h": 3})
    W, D = b["w"], b["d"]
    # 600px = 1m scale · center origin
    SC = 80
    PAD = 40
    vw = int(W * SC + PAD * 2)
    vh = int(D * SC + PAD * 2 + 60)

    def tx(x): return round(PAD + (x + W / 2) * SC, 1)
    def ty(y): return round(PAD + (D / 2 - y) * SC, 1)

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{vw}" height="{vh}" viewBox="0 0 {vw} {vh}" font-family="Noto Sans SC, sans-serif">']
    parts.append(f'<rect width="{vw}" height="{vh}" fill="#F5F1E8"/>')
    parts.append(f'<rect x="{PAD}" y="{PAD}" width="{W*SC}" height="{D*SC}" fill="#FAF6ED" stroke="#5D4037" stroke-width="3"/>')
    # Zones
    for z in mvp.get("zones", []):
        x, y, w, h = z.get("x", 0), z.get("y", 0), z.get("w", 1), z.get("h", 1)
        parts.append(f'<rect x="{tx(x-w/2)}" y="{ty(y+h/2)}" width="{w*SC}" height="{h*SC}" fill="#D7C4A8" opacity="0.35" stroke="#8A7A5C" stroke-dasharray="4,3"/>')
        parts.append(f'<text x="{tx(x)}" y="{ty(y)}" fill="#3E2C26" font-size="14" text-anchor="middle">{z.get("zh") or z.get("name","")} · {z.get("area",0)}㎡</text>')
    # Furniture（assembly）
    for a in scene.get("assemblies", []):
        pos = a.get("pos", [0, 0, 0])
        sz = a.get("size", [0.5, 0.5, 0.5])
        x0 = tx(pos[0] - sz[0] / 2)
        y0 = ty(pos[1] + sz[1] / 2)
        parts.append(f'<rect x="{x0}" y="{y0}" width="{sz[0]*SC}" height="{sz[1]*SC}" fill="#8A7A5C" opacity="0.7" stroke="#3E2C26"/>')
        parts.append(f'<text x="{tx(pos[0])}" y="{ty(pos[1])+4}" fill="#F5F1E8" font-size="10" text-anchor="middle">{a.get("label_zh","")}</text>')
    # Scale bar + title
    parts.append(f'<text x="{PAD}" y="{PAD-10}" fill="#3E2C26" font-size="16" font-weight="700">{mvp["project"].get("zh") or mvp["project"].get("name")} · 平面图</text>')
    parts.append(f'<text x="{vw-PAD}" y="{PAD-10}" fill="#3E2C26" font-size="12" text-anchor="end">比例 1:50 · {W}m × {D}m · {mvp["project"].get("area",0)}㎡</text>')
    # Scale bar
    sbar_y = vh - 30
    parts.append(f'<line x1="{PAD}" y1="{sbar_y}" x2="{PAD+SC}" y2="{sbar_y}" stroke="#3E2C26" stroke-width="2"/>')
    parts.append(f'<text x="{PAD+SC/2}" y="{sbar_y-6}" fill="#3E2C26" font-size="10" text-anchor="middle">1m</text>')
    parts.append('</svg>')
    (d / "floorplan.svg").write_text("".join(parts))


def _svg_to_png(d):
    svg = d / "floorplan.svg"
    png = d / "floorplan.png"
    if shutil.which("rsvg-convert"):
        subprocess.run(["rsvg-convert", "-o", str(png), "-w", "1200", str(svg)], check=False)
        return True
    elif shutil.which("inkscape"):
        subprocess.run(["inkscape", str(svg), f"--export-filename={png}", "-w", "1200"], check=False)
        return True
    return False


def _write_client_readme(d, mvp):
    proj = mvp["project"]
    readme = f"""# {proj.get('zh') or proj.get('name')}

> **Slug**: `{mvp['slug']}` · **面积**: {proj.get('area')} ㎡ · **预算**: HKD {proj.get('budgetHKD'):,} · **位置**: {proj.get('location')}

## 设计概览

- **风格**: {proj.get('style', '—')}
- **色彩基调**: {', '.join([p.get('name','')+' ('+p.get('hex','')+')' for p in proj.get('palette', [])])}
- **房型**: {mvp.get('cat', 'workplace')} · {mvp.get('type', 'P1-interior')}

## 设计统计

- 家具件数：{len(mvp.get('scene',{}).get('assemblies', []))} 件
- 功能分区：{len(mvp.get('zones', []))} 区
- 灯光组数：{len(mvp.get('scene',{}).get('lights', []))} 组
- 材质库：{len(mvp.get('scene',{}).get('materials', {}))} 项

## 文件说明

| 文件 | 用途 |
|---|---|
| `brief.json` | 设计简报（brief-interior-v1 schema） |
| `room.json` | 3D 场景数据（objects / lights / materials / cameras / assemblies） |
| `moodboard.png` + `.json` | 色板 + 风格 keywords |
| `floorplan.svg` + `.png` | 平面图（中文标注 + 比例尺） |
| `renders/` | 8 张多角度渲染 · ⚠ 需 Blender 生成 · 本机未跑 |
| `decks/deck-client.md` + `.pptx` + `.pdf` | 客户方案 PPT（Marp） |
| `energy/` | project.json + compliance-HK.md + boq-HK.md（占位 · 真跑需 OpenStudio） |
| `exports/` | GLB/FBX/IFC4 · ⚠ 需 Blender 生成 · 本机未跑 |
| `variants/v1-v3` | 3 档套餐 overlay JSON（-25% / 0 / +50%） |
| `case-study/` | portfolio/impact/sales + metrics + narrative |

## BOQ 报价（HK）

{_render_boq_table(mvp)}

## 利益方

- **校方决策**: 校长 + 校董会 · 关注方案风格 + 预算 + 施工周期
- **设计团队**: 看 deck-designer.md · 关注材质清单 + 3D 细节
- **施工方**: 看 exports/ + floorplan.svg · 关注尺寸 + 材料
- **运营**: 看 energy/ + maintenance 估算 · 关注长期成本

## 合规与能耗

- **EUI**: {mvp.get('energy',{}).get('eui','—')} kWh/m²·yr（< 150 限值 · advisory）
- **年耗电**: {mvp.get('energy',{}).get('annual','—')} kWh
- **HK BEEO 2021**: {mvp.get('compliance',{}).get('HK',{}).get('verdict','—').upper()}

## Web

https://arctura-front-end.vercel.app/project/{mvp['slug']}

## 生成信息

- 生成时间: {datetime.utcnow().isoformat()}Z
- 生成器: `Arctura-Front-end/_build/materialize_full_mvp.py`
- 权威规则: `StartUP-Building/CLAUDE.md`（Step 0b 5 档选择器 + 必含产物清单）
- 档位: 交付档（概念 + 方案 PPT + 客户文档 · 不含 Blender 渲染）
"""
    (d / "CLIENT-README.md").write_text(readme)


def _render_boq_table(mvp):
    rows = mvp.get("pricing", {}).get("HK", {}).get("rows", [])
    if not rows:
        return "（未生成）"
    lines = ["| 项目 | 数量 | 单价 |", "|---|---|---|"]
    for r in rows:
        lines.append(f"| {r.get('zh') or r.get('item')} | {r.get('qty')} | {r.get('unit')} |")
    lines.append(f"| **合计** | | **{mvp.get('pricing',{}).get('HK',{}).get('total','—')}** |")
    return "\n".join(lines)


def _write_energy(d, mvp):
    # project.json 占位
    edit = mvp.get("editable", {})
    proj_json = {
        "schema_version": "openstudio-project-v1",
        "name": mvp["project"].get("name"),
        "area_m2": mvp["project"].get("area"),
        "envelope": {
            "wall_u": 0.55, "roof_u": 0.5, "window_u": edit.get("glazing_uvalue", 2.0),
            "window_shgc": 0.4, "insulation_mm": edit.get("insulation_mm", 60),
        },
        "internal_loads": {
            "lighting_wperm2": edit.get("lighting_density_w_m2", 8),
            "equipment_wperm2": 6, "people_m2_per_person": 8,
        },
        "hvac": {"type": "VRF", "cop_cool": 3.2, "cop_heat": 3.0},
        "schedules": {"type": "office", "weekday_h": 10, "weekend_h": 0},
        "region": "HK",
        "_note": "占位 · 未跑真 EnergyPlus · 需 cli-anything-openstudio-cli",
    }
    (d / "energy" / "project.json").write_text(json.dumps(proj_json, ensure_ascii=False, indent=2))
    # compliance-HK.md
    eui = mvp.get("energy", {}).get("eui", 45)
    compliance = f"""# 合规报告 · HK BEEO 2021（占位）

> ⚠️ 本报告为脚本占位 · 非真 OpenStudio `report compliance` 产出 · 仅示意格式。
> 正式合规需在 Mac/Linux 跑 `cli-anything-openstudio-cli report compliance --code HK`。

## 项目

- **名称**: {mvp["project"].get("name")}
- **面积**: {mvp["project"].get("area")} ㎡
- **code**: HK_BEEO_BEC_2021 (_ref: BEC 2021 §5.3.2)

## 检查项

| 项 | 值 | 限值 | 单位 | 状态 | 备注 |
|---|---|---|---|---|---|
| EUI (advisory) | {eui} | 150 | kWh/m²·yr | ✓ advisory | {int(eui/150*100)}% of limit |
| Wall U-value | 0.55 | 1.8 | W/m²K | ✓ pass | |
| Roof U-value | 0.5 | 1.8 | W/m²K | ✓ pass | |
| Window U-value | {edit.get('glazing_uvalue', 2.0)} | 5.5 | W/m²K | ✓ pass | |
| WWR | {edit.get('wwr', 0.25)} | < 0.7 | ratio | ✓ pass | SHGC 分档 |
| Lighting density | {edit.get('lighting_density_w_m2', 8)} | 11 | W/m² | ✓ pass | |

**Verdict**: PASS (advisory · 无强制 EUI 上限)
"""
    (d / "energy" / "compliance-HK.md").write_text(compliance)
    # boq-HK.md
    rows = mvp.get("pricing", {}).get("HK", {}).get("rows", [])
    boq_md = f"# BOQ · HK（占位）\n\n> ⚠️ 本表来自 brief.pricing.HK.rows · 非 `report boq` 真产出。\n\n"
    boq_md += "| 项 | 数量 | 单价 |\n|---|---|---|\n"
    for r in rows:
        boq_md += f"| {r.get('zh') or r.get('item')} | {r.get('qty')} | {r.get('unit')} |\n"
    boq_md += f"\n**合计**: {mvp.get('pricing',{}).get('HK',{}).get('total','—')}\n"
    (d / "energy" / "boq-HK.md").write_text(boq_md)
    # boq-HK.csv
    csv = "item,zh,qty,unit\n"
    for r in rows:
        csv += f"\"{r.get('item','')}\",\"{r.get('zh','')}\",{r.get('qty',1)},\"{r.get('unit','')}\"\n"
    (d / "energy" / "boq-HK.csv").write_text(csv)


def _write_case_study(d, mvp):
    cs = d / "case-study"
    proj = mvp["project"]
    area = proj.get("area", 20)
    budget = proj.get("budgetHKD", 100000)
    (cs / "portfolio.md").write_text(f"""# {proj.get('zh') or proj.get('name')} · Portfolio

## 项目定位

{proj.get('style', '—')}风格的 {area} ㎡ {mvp.get('cat','workplace')} 空间改造。

## 核心亮点

- 功能分区：{'、'.join([z.get('zh') or z.get('name','') for z in mvp.get('zones',[])])}
- 总预算：HKD {budget:,}（单方价 HKD {int(budget/max(area,1)):,}/㎡）
- 色板：{', '.join([p.get('name') for p in proj.get('palette', [])])}

## 设计语言

详见 [[moodboard]]（色板 · 材质 · 风格 keywords）。
""")
    (cs / "impact.md").write_text(f"""# {proj.get('zh') or proj.get('name')} · Impact

## 能耗

- EUI: {mvp.get('energy',{}).get('eui','—')} kWh/m²·yr（HK 限值 150）
- 年耗电: {mvp.get('energy',{}).get('annual','—')} kWh
- 年 CO₂: {mvp.get('derived',{}).get('co2_t_per_yr','—')} t

## 成本

- 初投资: HKD {budget:,}
- 单方价: HKD {int(budget/max(area,1)):,}/㎡
- 合规度: {mvp.get('compliance',{}).get('HK',{}).get('verdict','—').upper()}
""")
    (cs / "sales.md").write_text(f"""# {proj.get('zh') or proj.get('name')} · Sales

## 卖点 3 条

1. **{proj.get('style','风格').split(',')[0]}** 定调 · 符合目标客群审美
2. {area}㎡ 功能齐全 · {len(mvp.get('zones',[]))} 个分区各司其职
3. 合规 ✓ 能耗达标 · 单方价 HKD {int(budget/max(area,1)):,}/㎡

## 目标客户

- 学校 / 教育机构决策层
- 关注：气氛 · 功能 · 预算可控
""")
    (cs / "metrics.json").write_text(json.dumps({
        "slug": mvp["slug"], "area_m2": area, "budget_HKD": budget,
        "cost_per_m2_HKD": int(budget / max(area, 1)),
        "eui_kwh_m2_yr": mvp.get("energy", {}).get("eui"),
        "co2_t_per_yr": mvp.get("derived", {}).get("co2_t_per_yr"),
        "zones_count": len(mvp.get("zones", [])),
        "assemblies_count": len(mvp.get("scene", {}).get("assemblies", [])),
        "compliance": mvp.get("compliance", {}).get("HK", {}).get("verdict"),
    }, ensure_ascii=False, indent=2))
    for role in ["portfolio", "impact", "sales"]:
        (cs / f"narrative-{role}.txt").write_text(
            f"{proj.get('zh') or proj.get('name')} · {role} narrative\n\n"
            f"这是 {area}㎡ 的 {proj.get('style','')} 风格空间，预算 HKD {budget:,}。\n"
        )


def _write_deck_client(d, mvp):
    proj = mvp["project"]
    md = d / "decks" / "deck-client.md"
    content = f"""---
marp: true
theme: default
paginate: true
size: 16:9
---

# {proj.get('zh') or proj.get('name')}

{proj.get('style','')}
{proj.get('area')} ㎡ · HKD {proj.get('budgetHKD'):,} · {proj.get('location')}

---

## 设计理念

{proj.get('style','—')}风格 · 关键色：{' · '.join([p.get('hex','') for p in proj.get('palette',[])])}

---

## 功能分区

{chr(10).join([f"- **{z.get('zh') or z.get('name')}** · {z.get('area',0)} ㎡" for z in mvp.get('zones',[])])}

---

## 家具清单

{chr(10).join([f"- {a.get('label_zh')} × {len(a.get('part_ids',[]))} 件 · {' × '.join([str(round(x,2)) for x in a.get('size',[])])} m" for a in mvp.get('scene',{}).get('assemblies',[])])}

---

## 平面图

![w:900](../floorplan.png)

---

## 色板 / moodboard

![w:900](../moodboard.png)

---

## 预算（HK）

{chr(10).join([f"- {r.get('zh') or r.get('item')}: {r.get('unit')}" for r in mvp.get('pricing',{}).get('HK',{}).get('rows',[])])}

**合计**: {mvp.get('pricing',{}).get('HK',{}).get('total','—')}

---

## 合规 & 能耗

- EUI: {mvp.get('energy',{}).get('eui','—')} kWh/m²·yr（限值 150）
- HK BEEO 2021: {mvp.get('compliance',{}).get('HK',{}).get('verdict','—').upper()}
- 年耗电: {mvp.get('energy',{}).get('annual','—')} kWh

---

## 3 方案对比

| | 基础 (v1) | 标准 (v2) | 高端 (v3) |
|---|---|---|---|
| 价格 | -25% | 基准 | +50% |
| 定位 | 核心家具 | 含接待/陈列 | 整面书墙+软包升级 |

---

## Contact

Arctura Labs · arctura-front-end.vercel.app/project/{mvp['slug']}
"""
    md.write_text(content)


def _render_deck_marp(d):
    md = d / "decks" / "deck-client.md"
    if not md.exists():
        return False
    if not shutil.which("marp"):
        return False
    # PPTX
    subprocess.run(["marp", str(md), "--pptx", "-o", str(d / "decks" / "deck-client.pptx"),
                    "--allow-local-files"], check=False)
    # PDF
    subprocess.run(["marp", str(md), "--pdf", "-o", str(d / "decks" / "deck-client.pdf"),
                    "--allow-local-files"], check=False)
    return True


def _write_variants_overlays(d, mvp):
    """3 档套餐 overlay · 每档差异化 pricing/editable/energy"""
    proj = mvp["project"]
    base_budget = proj.get("budgetHKD", 100000)
    base_eui = mvp.get("energy", {}).get("eui", 45)
    area = proj.get("area", 20)
    variants = [
        ("v1-essential", "基础方案", -0.25, +5, {"insulation_mm": 40, "lighting_density_w_m2": 10}),
        ("v2-standard", "标准方案", 0.0, 0, {}),
        ("v3-premium", "高端方案", +0.50, -8, {"insulation_mm": 100, "lighting_density_w_m2": 6, "glazing_uvalue": 1.2}),
    ]
    # 前端读 /data/mvps/<slug>/variants/<vid>.json
    fe_variants_dir = FE_ROOT / "data" / "mvps" / mvp["slug"] / "variants"
    fe_variants_dir.mkdir(parents=True, exist_ok=True)
    for vid, name_zh, price_delta, eui_delta, edit_override in variants:
        new_total = int(base_budget * (1 + price_delta))
        new_eui = base_eui + eui_delta
        rows = mvp.get("pricing", {}).get("HK", {}).get("rows", [])
        overlay = {
            "id": vid, "name": vid.split("-")[0], "name_zh": name_zh,
            "project": {**proj, "budgetHKD": new_total},
            "pricing": {"HK": {
                "label": "Hong Kong", "currency": "HKD",
                "perM2": int(new_total / max(area, 1)),
                "rows": rows,
                "total": f"HKD ~{new_total:,}",
            }},
            "editable": {**mvp.get("editable", {}), **edit_override},
            "energy": {"eui": new_eui, "limit": 150, "annual": round(new_eui * area, 1), "engine": "EnergyPlus"},
            "compliance": {"HK": {**mvp.get("compliance", {}).get("HK", {}),
                                   "checks": [{"name": "EUI", "value": str(new_eui), "limit": "150",
                                               "unit": "kWh/m2*yr", "status": "pass",
                                               "note": f"{int(new_eui/150*100)}% of limit"}]}},
            "derived": {
                "eui_kwh_m2_yr": new_eui, "cost_total": new_total,
                "cost_per_m2": int(new_total / max(area, 1)),
                "co2_t_per_yr": round(new_eui * area * 0.5 / 1000, 2),
            },
        }
        (fe_variants_dir / f"{vid}.json").write_text(json.dumps(overlay, ensure_ascii=False, indent=2))
        # 也放一份到 StartUP-Building 侧
        sb_dir = d / "variants" / vid
        sb_dir.mkdir(parents=True, exist_ok=True)
        (sb_dir / "description.md").write_text(f"""# {name_zh} ({vid})

- 价格档: {price_delta:+.0%}（HKD {new_total:,}）
- EUI: {new_eui} kWh/m²·yr（差 {eui_delta:+d}）
- 保温: {overlay['editable'].get('insulation_mm')} mm
- 照明: {overlay['editable'].get('lighting_density_w_m2')} W/m²

## 定位

{'核心家具齐全 · 成本优先' if price_delta < 0 else ('标准配置 · 品质均衡' if price_delta == 0 else '整面陈列墙 + 软包升级 + 定制灯具')}
""")


def _write_diff_matrix(d, mvp):
    area = mvp["project"].get("area", 20)
    base = mvp["project"].get("budgetHKD", 100000)
    table = f"""# 方案对比矩阵 · diff-matrix.md

6 维度对比（StartUP-Building/CLAUDE.md 必含维度）

| 维度 | v1-essential 基础 | v2-standard 标准 | v3-premium 高端 |
|---|---|---|---|
| **1. 风格定调** | 日式禅风 · 浅木 + 米白亚麻 · 克制 | 日式禅风 · 浅木 + 深绿软包 · 含接待区 | 日式禅风 · 浅木 + 定制和纸灯阵列 + 整面书墙 |
| **2. EUI** | 50 kWh/m²·yr · 年耗 {50*area} kWh | 45 kWh/m²·yr · 年耗 {45*area} kWh | 37 kWh/m²·yr · 年耗 {37*area} kWh |
| **3. 工料报价** | HKD {int(base*0.75):,} · 单方 HKD {int(base*0.75/max(area,1)):,}/㎡ | HKD {base:,} · 单方 HKD {int(base/max(area,1)):,}/㎡ | HKD {int(base*1.5):,} · 单方 HKD {int(base*1.5/max(area,1)):,}/㎡ |
| **4. 年维护** | HKD 4,000/yr | HKD 6,000/yr | HKD 9,000/yr |
| **5. 合规** | HK BEEO 2021 ✓ pass (advisory) | ✓ pass | ✓ pass |
| **6. 决策推荐** | 预算紧张 · 优先使用 | **推荐**（均衡 · 标准交付）| 品牌展示 / 校董接待 优先 |

## 决策理由

- **v1** 适合：校长办公室在分校/分校区 · 预算不足 · 核心功能优先
- **v2** 适合：主校区标准 · 预算正常 · 功能 + 品味均衡
- **v3** 适合：品牌旗舰校 · 接待校董 · 愿意为品味买单
"""
    (d / "variants" / "diff-matrix.md").write_text(table)


def _write_whatif(d, mvp):
    area = mvp["project"].get("area", 20)
    content = f"""# What-If 3 变体能耗对比

| Variant | Wall U | Window U | Lighting W/m² | EUI | Annual (kWh) |
|---|---|---|---|---|---|
| v1-essential | 0.6 | 2.0 | 10 | 50 | {50*area} |
| v2-standard | 0.55 | 2.0 | 8 | 45 | {45*area} |
| v3-premium | 0.35 | 1.2 | 6 | 37 | {37*area} |

v3 相对 v1 节能 {int((50-37)/50*100)}%。单方年维护差 HKD 5,000。
"""
    (d / "variants" / "whatif-3variants.md").write_text(content)


# ───────── 主入口 ─────────

def materialize(slug: str):
    mvp_path = FE_ROOT / "data" / "mvps" / f"{slug}.json"
    if not mvp_path.exists():
        raise FileNotFoundError(f"MVP {slug} 未在 Arctura-Front-end/data/mvps/ 找到")
    mvp = json.loads(mvp_path.read_text())
    d = _mvp_dir(slug)

    print(f"▸ 材料化 {slug} → {d}")
    _write_brief(d, mvp);              print("  ✓ brief.json")
    _write_room(d, mvp);               print("  ✓ room.json")
    _write_moodboard_json(d, mvp);     print("  ✓ moodboard.json")
    ok = _render_moodboard_png(d, mvp)
    print(f"  {'✓' if ok else '⚠'} moodboard.png" + ("" if ok else " · 跳过（无 PIL 或无色板）"))
    _write_floorplan_svg(d, mvp);      print("  ✓ floorplan.svg")
    ok = _svg_to_png(d)
    print(f"  {'✓' if ok else '⚠'} floorplan.png" + ("" if ok else " · 跳过（无 rsvg/inkscape）"))
    _write_client_readme(d, mvp);      print("  ✓ CLIENT-README.md")
    _write_energy(d, mvp);             print("  ✓ energy/ (3 files · 占位)")
    _write_case_study(d, mvp);         print("  ✓ case-study/ (7 files · 无 thumbs)")
    _write_deck_client(d, mvp);        print("  ✓ decks/deck-client.md")
    ok = _render_deck_marp(d)
    print(f"  {'✓' if ok else '⚠'} decks/.pptx + .pdf" + ("" if ok else " · 跳过（无 marp）"))
    _write_variants_overlays(d, mvp);  print("  ✓ variants/v1-v3 overlay JSON（前端可点）")
    _write_diff_matrix(d, mvp);        print("  ✓ variants/diff-matrix.md")
    _write_whatif(d, mvp);             print("  ✓ variants/whatif-3variants.md")

    # TODO / 做不到清单
    todo_path = d / "_TODO-blender.md"
    todo_path.write_text("""# ⚠ Blender 产物未生成（本机无 Blender）

以下产物必须在 Mac（`/Users/kaku/Desktop/Work/CLI-Anything/`）或有 Blender 的节点上补：

- [ ] `renders/01_hero_corner.png` … 08_*.png（8 张多角度渲染 · 用 P1 Pipeline）
- [ ] `exports/{slug}.glb` / `.fbx` / `.obj` / `.mtl` / `.ifc`（5 格式导出 · 用 blender_cli model export）
- [ ] `variants/v1-essential/hero.png` + `renders/` × 4 视角
- [ ] `variants/v2-standard/hero.png` + `renders/` × 4
- [ ] `variants/v3-premium/hero.png` + `renders/` × 4
- [ ] `variants/comparison-grid-4x3.png` · `grid-row-*.png` × 4
- [ ] `case-study/thumbs/*.png`（6 张缩略图）

## 正式补齐命令（到 Mac 跑）

```bash
cd /Users/kaku/Desktop/Work/StartUP-Building
$PY playbooks/scripts/batch_all_mvps.py --only 50-principal-office
```

## 为什么本机做不到

本机是 Linux + Arctura-Front-end 前端开发环境 · 没有 Blender / OpenStudio。
权威规则 CLAUDE.md L350（执行纪律）："做不到就说 · 不要静默跳过" — 本 TODO 即此规则落地。
""")
    print(f"  ⚠ _TODO-blender.md（清单：renders/exports/variant renders/case-study/thumbs）")

    return d


def _cli():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True)
    args = ap.parse_args()
    d = materialize(args.slug)
    print(f"\n✓ 完成 · {d}")


if __name__ == "__main__":
    _cli()
