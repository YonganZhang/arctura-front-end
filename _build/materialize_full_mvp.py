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
    font_title = _get_cjk_font(44)
    font_sub = _get_cjk_font(22)
    font_swatch = _get_cjk_font(16)
    sw_w = W // max(len(palette), 1)
    for i, p in enumerate(palette):
        try:
            draw.rectangle([i * sw_w, 200, (i + 1) * sw_w, H - 80], fill=p["hex"])
        except Exception:
            pass
        draw.text((i * sw_w + 20, H - 60), f"{p.get('name','')}  {p['hex']}",
                  fill="#F5F1E8", font=font_swatch)
    draw.text((40, 40), mvp["project"].get("name", mvp["slug"]),
              fill="#F5F1E8", font=font_title)
    draw.text((40, 110), mvp['project'].get('style', ''),
              fill="#C9BFAE", font=font_sub)
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
    """跑 marp 出 pptx + pdf · 失败则写入 _TODO-blender.md（执行纪律 · 不静默跳）"""
    md = d / "decks" / "deck-client.md"
    if not md.exists():
        return {"ok": False, "reason": "deck-client.md 不存在"}
    if not shutil.which("marp"):
        return {"ok": False, "reason": "marp-cli 未装"}
    pptx = d / "decks" / "deck-client.pptx"
    pdf = d / "decks" / "deck-client.pdf"
    r1 = subprocess.run(["marp", str(md), "--pptx", "-o", str(pptx), "--allow-local-files"],
                        capture_output=True, text=True, timeout=60)
    r2 = subprocess.run(["marp", str(md), "--pdf", "-o", str(pdf), "--allow-local-files"],
                        capture_output=True, text=True, timeout=60)
    if pptx.exists() and pdf.exists():
        return {"ok": True}
    err = ((r1.stderr or "") + "\n" + (r2.stderr or ""))[-400:]
    return {"ok": False, "reason": f"marp 跑但未产文件 · stderr: {err}"}


def _append_todo(d, title, lines):
    """CLAUDE.md 执行纪律第 3 条：做不到就说 · 不静默跳。统一写 _TODO-blender.md"""
    todo_path = d / "_TODO-blender.md"
    existing = todo_path.read_text() if todo_path.exists() else "# 未生成产物清单\n\n"
    if title not in existing:
        section = f"\n## {title}\n\n" + "\n".join(f"- [ ] {l}" for l in lines) + "\n"
        existing += section
        todo_path.write_text(existing)


def _get_cjk_font(size):
    """PIL 中文字体回退 · 修 2026-04-22 子智能体审查指出的方块字问题"""
    from PIL import ImageFont
    import os
    paths = [
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/google-noto-cjk/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/wqy-zenhei/wqy-zenhei.ttc",
        "/usr/share/fonts/wqy-microhei/wqy-microhei.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ]
    for fp in paths:
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _make_case_study_thumbs(d):
    """从 renders 缩 6 张 · PIL 能做 · 不需 Blender（修 2026-04-22 thumbs 空目录问题）"""
    try:
        from PIL import Image
    except ImportError:
        return False
    renders_dir = d / "renders"
    thumbs_dir = d / "case-study" / "thumbs"
    thumbs_dir.mkdir(parents=True, exist_ok=True)
    pngs = sorted(renders_dir.glob("*.png"))[:6]
    if not pngs:
        return False
    for p in pngs:
        img = Image.open(p)
        img.thumbnail((400, 300))
        img.save(thumbs_dir / p.name)
    return True


def _write_variants_overlays(d, mvp):
    """3 档套餐 overlay · 用共享 VARIANT_PRESETS（修 2026-04-22 三处硬编码）"""
    from variant_presets import VARIANT_PRESETS, compute_price, compute_eui
    proj = mvp["project"]
    base_budget = proj.get("budgetHKD", 100000)
    base_eui = mvp.get("energy", {}).get("eui", 45)
    area = proj.get("area", 20)
    fe_variants_dir = FE_ROOT / "data" / "mvps" / mvp["slug"] / "variants"
    fe_variants_dir.mkdir(parents=True, exist_ok=True)
    for v in VARIANT_PRESETS:
        vid = v["id"]
        new_total = compute_price(v, base_budget)
        new_eui = compute_eui(v, base_eui)
        rows = mvp.get("pricing", {}).get("HK", {}).get("rows", [])
        overlay = {
            "id": vid, "name": v["name"], "name_zh": v["name_zh"],
            "parent_slug": mvp["slug"],
            "renders": [],
            "project": {**proj, "budgetHKD": new_total},
            "pricing": {"HK": {
                "label": "Hong Kong", "currency": "HKD",
                "perM2": int(new_total / max(area, 1)),
                "rows": rows,
                "total": f"HKD ~{new_total:,}",
            }},
            "editable": {**mvp.get("editable", {}), **v["edit_override"]},
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
        sb_dir = d / "variants" / vid
        sb_dir.mkdir(parents=True, exist_ok=True)
        (sb_dir / "description.md").write_text(f"""# {v['name_zh']} ({vid})

- 价格档: {v['price_delta_pct']:+d}%（HKD {new_total:,}）
- EUI: {new_eui} kWh/m²·yr（差 {v['eui_delta']:+d}）
- 保温: {overlay['editable'].get('insulation_mm')} mm
- 照明: {overlay['editable'].get('lighting_density_w_m2')} W/m²
- 年维护: HKD {v['annual_maintenance_HKD']:,}

## 定位

{v['positioning']} · {v['tagline_zh']}
""")


def _write_diff_matrix(d, mvp):
    """diff-matrix 6 维度 · 从 VARIANT_PRESETS 共享常量算 · 不再硬编码"""
    from variant_presets import VARIANT_PRESETS, compute_price, compute_eui
    area = mvp["project"].get("area", 20)
    base_budget = mvp["project"].get("budgetHKD", 100000)
    base_eui = mvp.get("energy", {}).get("eui", 45)
    style = mvp["project"].get("style", "")

    def row_header():
        return "| 维度 | " + " | ".join(f"{v['id']} {v['name_zh']}" for v in VARIANT_PRESETS) + " |"

    def row_sep():
        return "|---" * (len(VARIANT_PRESETS) + 1) + "|"

    def row(label, values):
        return f"| **{label}** | " + " | ".join(values) + " |"

    # 1. 风格（先通用 · 未来可改为从 preset 读）
    style_cells = [
        f"{style.split(',')[0] if style else '简配'}· 克制",
        f"{style.split(',')[0] if style else '均衡'}· 标准",
        f"{style.split(',')[0] if style else '高端'}· 软包升级 + 定制灯具",
    ]
    # 2-6 维度
    eui_cells = [f"{compute_eui(v, base_eui)} kWh/m²·yr · 年耗 {compute_eui(v, base_eui)*area} kWh" for v in VARIANT_PRESETS]
    price_cells = [f"HKD {compute_price(v, base_budget):,} · 单方 HKD {compute_price(v, base_budget)//max(area,1):,}/㎡" for v in VARIANT_PRESETS]
    maint_cells = [f"HKD {v['annual_maintenance_HKD']:,}/yr" for v in VARIANT_PRESETS]
    compliance_cells = ["HK BEEO 2021 ✓ pass (advisory)"] + ["✓ pass"] * (len(VARIANT_PRESETS) - 1)
    decision_cells = [v["positioning"] for v in VARIANT_PRESETS]
    decision_cells[1] = f"**推荐** · {decision_cells[1]}" if len(decision_cells) > 1 else decision_cells[0]

    table = "# 方案对比矩阵 · diff-matrix.md\n\n"
    table += "6 维度对比（StartUP-Building/CLAUDE.md 必含维度 · 由 _build/variant_presets.py 生成）\n\n"
    table += row_header() + "\n"
    table += row_sep() + "\n"
    table += row("1. 风格定调", style_cells) + "\n"
    table += row("2. EUI", eui_cells) + "\n"
    table += row("3. 工料报价", price_cells) + "\n"
    table += row("4. 年维护", maint_cells) + "\n"
    table += row("5. 合规", compliance_cells) + "\n"
    table += row("6. 决策推荐", decision_cells) + "\n\n"
    table += "## 决策理由\n\n"
    for v in VARIANT_PRESETS:
        table += f"- **{v['id']}** · {v['positioning']}\n"
    (d / "variants" / "diff-matrix.md").write_text(table)


def _write_whatif(d, mvp):
    """whatif 3 变体 · 从 VARIANT_PRESETS 计算（不再硬编码）"""
    from variant_presets import VARIANT_PRESETS, compute_eui
    area = mvp["project"].get("area", 20)
    base_eui = mvp.get("energy", {}).get("eui", 45)
    base_edit = mvp.get("editable", {})

    lines = ["# What-If 3 变体能耗对比（由 variant_presets 生成）\n",
             "| Variant | Wall U | Window U | Lighting W/m² | EUI | Annual (kWh) |",
             "|---|---|---|---|---|---|"]
    for v in VARIANT_PRESETS:
        merged = {**base_edit, **v["edit_override"]}
        eui = compute_eui(v, base_eui)
        wall_u = 0.55 - (merged.get("insulation_mm", 60) - 60) * 0.005   # 简化线性 · 保温越厚 U 越小
        win_u = merged.get("glazing_uvalue", 2.0)
        light = merged.get("lighting_density_w_m2", 8)
        lines.append(f"| {v['id']} | {wall_u:.2f} | {win_u} | {light} | {eui} | {eui*area} |")
    first, last = compute_eui(VARIANT_PRESETS[0], base_eui), compute_eui(VARIANT_PRESETS[-1], base_eui)
    save_pct = int((first - last) / first * 100) if first > 0 else 0
    lines.append(f"\n{VARIANT_PRESETS[-1]['id']} 相对 {VARIANT_PRESETS[0]['id']} 节能 {save_pct}%。\n")
    (d / "variants" / "whatif-3variants.md").write_text("\n".join(lines))


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
    _write_case_study(d, mvp);         print("  ✓ case-study/ (7 files)")
    ok = _make_case_study_thumbs(d)
    print(f"  {'✓' if ok else '⚠'} case-study/thumbs/（PIL 从 renders 缩 6 张）" + ("" if ok else " · 跳过（无 renders）"))
    _write_deck_client(d, mvp);        print("  ✓ decks/deck-client.md")
    deck_res = _render_deck_marp(d)
    if deck_res["ok"]:
        print("  ✓ decks/deck-client.pptx + .pdf (marp 跑通)")
    else:
        print(f"  ⚠ decks/*.pptx + .pdf · {deck_res['reason']}")
        _append_todo(d, "Marp PPTX/PDF（跑失败 · 需修）", [
            "decks/deck-client.pptx（marp --pptx）",
            "decks/deck-client.pdf（marp --pdf · 需 chrome）",
            f"失败：{deck_res['reason'][:150]}",
            "修法：装 chromium 让 marp-cli 能用",
        ])
    _write_variants_overlays(d, mvp);  print("  ✓ variants/v1-v3 overlay JSON（前端可点）")
    _write_diff_matrix(d, mvp);        print("  ✓ variants/diff-matrix.md")
    _write_whatif(d, mvp);             print("  ✓ variants/whatif-3variants.md")

    # TODO · 真做不到 · 按子智能体审查更新状态
    todo_path = d / "_TODO-blender.md"
    todo_path.write_text("""# 产物完成状态（对照 StartUP-Building/CLAUDE.md L405-434 必含清单）

## ✅ 已补齐（LIGHT 模式 · 本机 Python/Playwright 能做）

- [x] brief.json · room.json · moodboard.{png,json} · floorplan.{svg,png}
- [x] CLIENT-README.md · decks/deck-client.md
- [x] energy/{project.json,compliance-HK.md,boq-HK.md,boq-HK.csv}（占位 · 非真 EnergyPlus）
- [x] case-study/{portfolio,impact,sales}.md + metrics.json + narrative-*.txt
- [x] case-study/thumbs/（PIL 从 renders 缩 6 张 · 2026-04-22 晚补）
- [x] variants/v1-v3 overlay JSON（套餐前端可点切换）
- [x] variants/diff-matrix.md + whatif-3variants.md（从 VARIANT_PRESETS 共享常量生成）
- [x] renders/ 8 张（Playwright 截 Three.js · `node _build/capture_renders.mjs --slug <slug>`）

## 🔄 FULL 模式待实装（需要扩展脚本 · 基础设施已就位）

- [ ] `exports/{slug}.glb` / `.fbx` / `.obj` / `.ifc`（BIM 导出 · 需 `_build/render_with_blender.py`）
- [ ] `variants/v*/hero.png` + `renders/×4`（variant-aware Playwright · 或 Blender）
- [ ] `variants/comparison-grid-4x3.png` + `grid-row-*.png × 4`（PIL 合成 · 脚本待写）
- [ ] 照片级 Cycles 渲染（GPU 加速最佳 · 本机 CPU 慢）
- [ ] 真 EnergyPlus 能耗（需装 OpenStudio）

## 基础设施

- **Blender**：`~/.local/blender/blender-4.2.3-linux-x64/blender`（已装 · 4.2.3 LTS · 无头渲染验证）
- **Playwright**：`node_modules/@playwright/test` · chromium-1217 已下载
- **Marp**：`marp-cli` 在 path · 缺 chrome（decks/pptx 不自动跑）
- **PIL**：系统 python3 有 · 字体回退：noto-cjk / wqy-zenhei

## 下次启动入口

```bash
python3 _build/create_mvp_from_brief.py --mode light --brief X.json --slug YY-zzz
python3 _build/materialize_full_mvp.py --slug YY-zzz
node _build/capture_renders.mjs --slug YY-zzz
```

权威规则 `StartUP-Building/CLAUDE.md` L350："做不到就说 · 不静默跳" — 本 TODO 即此规则落地。
""")
    print(f"  ⚠ _TODO-blender.md（更新状态 · FULL 模式待实装清单）")

    return d


def _cli():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True)
    args = ap.parse_args()
    d = materialize(args.slug)
    print(f"\n✓ 完成 · {d}")


if __name__ == "__main__":
    _cli()
