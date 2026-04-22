#!/usr/bin/env python3
"""Arctura 新 MVP 统一创建入口 · brief → 完整 MVP JSON + bundle.zip + index

用途：
  绕开上游 Pipelines deliverables 路径 · 让前端/chat/外部客户端能直接从 brief 起一个新 MVP。
  与 build_mvp_data.py 互补（那个扫 deliverables · 这个接 brief）· 产出字段完全对齐 schema。

CLI 使用：
  python3 _build/create_mvp_from_brief.py --brief brief.json [--slug 50-principal-office]
  python3 _build/create_mvp_from_brief.py --retrofit 50-principal-office  # 已存在的补齐 variants/bundle/index

Python import 使用：
  from create_mvp_from_brief import create_mvp_from_brief
  create_mvp_from_brief(brief_dict, slug="50-principal-office")

未来接口预留：
  POST /api/mvp/create · body=brief.json · 返回 {slug, url}  (Edge function · 未实装)

产出：
  1. data/mvps/<slug>.json           完整 MVP 文件（过 schema）
  2. assets/mvps/<slug>/bundle.zip   打包全部 MVP 内容（JSON + brief + README）
  3. data/mvps-index.json            append 新条目（画廊可见）
"""

from __future__ import annotations
import argparse
import io
import json
import sys
import zipfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
ASSETS = ROOT / "assets"

FURNITURE_LIB = json.loads((DATA / "furniture-library.json").read_text())["items"]


# ───────── Scene 推导 ─────────

def _build_scene_from_brief(brief: dict) -> dict:
    """从 brief 推导一个合法 scene。brief 可带 `scene_override` 直接注入。

    默认按 brief.area 决定 bounds · brief.key_furniture 清单决定 assemblies。
    """
    if brief.get("scene_override"):
        return brief["scene_override"]

    area = brief.get("area", 20)
    # 近似按 1.3:1 比例算房间（6:5 for 30㎡, 5:4 for 20㎡）
    w = round((area * 1.25) ** 0.5, 1)
    d = round(area / w, 1)
    h = brief.get("ceiling_h", 3.0 if area >= 25 else 2.8)
    bounds = {"w": w, "d": d, "h": h}

    # 4 墙自动
    walls = [
        {"id": "wall_Back", "name": "BackWall", "start": [-w/2, d/2, 0], "end": [w/2, d/2, 0], "height": h, "thickness": 0.1, "material_id": "wall"},
        {"id": "wall_auto_S", "name": "AutoWall_S", "start": [-w/2, -d/2, 0], "end": [w/2, -d/2, 0], "height": h, "thickness": 0.1, "material_id": "wall", "_auto": True},
        {"id": "wall_auto_E", "name": "AutoWall_E", "start": [w/2, -d/2, 0], "end": [w/2, d/2, 0], "height": h, "thickness": 0.1, "material_id": "wall", "_auto": True},
        {"id": "wall_auto_W", "name": "AutoWall_W", "start": [-w/2, -d/2, 0], "end": [-w/2, d/2, 0], "height": h, "thickness": 0.1, "material_id": "wall", "_auto": True},
    ]

    # key_furniture: 明确的家具清单（有则用 · 无则 fallback 到 type-based default）
    key_furniture = brief.get("key_furniture") or _default_furniture_for_type(brief.get("type", "office"))

    objects, assemblies = [], []
    for i, item in enumerate(key_furniture, 1):
        ftype = item["type"]
        fdef = FURNITURE_LIB.get(ftype, {})
        dsz = item.get("size") or fdef.get("default_size") or [0.5, 0.5, 0.5]
        pos = item["pos"]
        rot = item.get("rotation", [0, 0, 0])
        mat = item.get("material_id") or fdef.get("default_color", "#CCCCCC")
        label_en = item.get("label_en", fdef.get("label_en", ftype))
        label_zh = item.get("label_zh", fdef.get("label_zh", ftype))
        obj_id = f"obj_{ftype}_{i}"
        asm_id = f"asm_{ftype}_{i}"
        objects.append({
            "id": obj_id, "type": ftype, "pos": pos, "size": dsz, "rotation": rot,
            "material_id": mat, "label_en": label_en, "label_zh": label_zh,
            "assembly_id": asm_id,
        })
        assemblies.append({
            "id": asm_id, "type": ftype, "pos": pos, "rotation": rot, "size": dsz,
            "part_ids": [obj_id], "primary_part_id": obj_id,
            "material_id_primary": mat,
            "label_en": label_en, "label_zh": label_zh,
            "_generated_by": "manual",
        })

    # 3 基础灯光（sun + 主区 area + 氛围 point）
    lights = [
        {"id": "sun_1", "type": "sun", "dir": [0.3, 0.55, -0.78], "power": 3.0, "intensity": 3.0, "color": [1.0, 0.95, 0.85]},
        {"id": "area_2", "type": "area", "pos": [0, 0.5, h - 0.2], "power": 80.0, "intensity": 5.5, "color": [1.0, 0.95, 0.85], "size": 1.0, "size_y": 0.8, "shape": "RECTANGLE"},
        {"id": "point_3", "type": "point", "pos": [w/2 - 0.5, -d/2 + 0.5, h - 1.4], "power": 45.0, "intensity": 24.0, "color": [1.0, 0.88, 0.7]},
    ]

    # 材质表（可被 brief.materials 覆盖 · 默认带一套完整）
    materials = brief.get("materials") or {
        "woodfloor": {"base_color": "#C9B38C", "roughness": 0.55, "metallic": 0.0, "label": "Floor"},
        "wall": {"base_color": "#F5F1E8", "roughness": 0.92, "metallic": 0.0, "label": "Wall"},
        "oak_light": {"base_color": "#D7C4A8", "roughness": 0.55, "metallic": 0.0, "label": "LightOak"},
        "charcoal": {"base_color": "#6B6F73", "roughness": 0.7, "metallic": 0.02, "label": "Charcoal"},
        "linen_cream": {"base_color": "#D9CFB8", "roughness": 0.97, "metallic": 0.0, "label": "CreamLinen"},
        "screen": {"base_color": "#111318", "roughness": 0.25, "metallic": 0.05, "label": "Screen"},
    }

    return {
        "schema_version": "1.0",
        "unit": "m",
        "bounds": bounds,
        "walls": walls,
        "objects": objects,
        "assemblies": assemblies,
        "lights": lights,
        "materials": materials,
        "env": {"hdri": "/assets/hdri/interior_neutral_2k.hdr", "hdri_intensity": 1.0, "background_color": "#E8E2D5"},
        "floor": {"material_id": "woodfloor", "thickness": 0.02},
        "ceiling": {"material_id": "wall", "thickness": 0.05, "height": h, "_auto": True},
        "camera_default": {"pos": [w * 0.7, -d * 0.7, h * 0.6], "lookAt": [0, 0, 1.2], "fov": 50},
    }


def _default_furniture_for_type(t: str) -> list[dict]:
    """没 key_furniture 时按 type 给个默认布局"""
    if t == "office":
        return [
            {"type": "desk_standard", "pos": [0, 1.0, 0], "label_zh": "办公桌"},
            {"type": "chair_standard", "pos": [0, 1.6, 0], "rotation": [0, 0, 180], "label_zh": "办公椅"},
            {"type": "shelf_open", "pos": [-2, 0, 1.0], "label_zh": "书架"},
        ]
    return []


# ───────── Variants 骨架（3 方案默认）─────────

def _build_variants_skeleton(brief: dict, slug: str) -> dict:
    preset = brief.get("variants_preset")
    if preset:
        return {"list": preset}

    # 默认 3 方案：基础 / 标准 / 高端
    base_name = brief.get("name", slug)
    area = brief.get("area", 20)
    base_price = brief.get("budgetHKD", 100000)
    return {
        "list": [
            {
                "id": "v1-essential",
                "name": "v1",
                "name_zh": "基础方案",
                "desc": f"{base_name} · 基础配置 · 核心家具齐全 · 成本优先",
                "priceHKD": int(base_price * 0.75),
                "priceDeltaPct": -25,
                "thumb": None,
                "hero": None,
            },
            {
                "id": "v2-standard",
                "name": "v2",
                "name_zh": "标准方案",
                "desc": f"{base_name} · 标准配置 · 含接待/陈列区 · 品质均衡",
                "priceHKD": int(base_price),
                "priceDeltaPct": 0,
                "thumb": None,
                "hero": None,
            },
            {
                "id": "v3-premium",
                "name": "v3",
                "name_zh": "高端方案",
                "desc": f"{base_name} · 高端定制 · 整面陈列墙 + 软包升级 + 定制灯具",
                "priceHKD": int(base_price * 1.5),
                "priceDeltaPct": 50,
                "thumb": None,
                "hero": None,
            },
        ]
    }


# ───────── 其他字段推导 ─────────

def _build_pricing(brief: dict) -> dict:
    rows = brief.get("pricing_rows") or []
    total = brief.get("budgetHKD", 100000)
    return {
        "HK": {
            "label": "Hong Kong",
            "currency": "HKD",
            "perM2": int(total / max(brief.get("area", 20), 1)),
            "rows": rows,
            "total": f"HKD ~{total:,}",
        }
    }


def _build_energy(brief: dict) -> dict:
    area = brief.get("area", 20)
    eui = brief.get("energy_eui", 45.0)
    return {"eui": eui, "limit": 150, "annual": round(eui * area, 1), "engine": "EnergyPlus"}


def _build_compliance(brief: dict) -> dict:
    eui = brief.get("energy_eui", 45.0)
    return {
        "HK": {
            "code": "HK_BEEO_BEC_2021",
            "label": "HK · BEEO 2021",
            "checks": [{
                "name": "EUI", "value": str(eui), "limit": "150", "unit": "kWh/m2*yr",
                "status": "pass" if eui < 150 else "fail",
                "note": f"{int(eui/150*100)}% of limit",
            }],
            "verdict": "pass" if eui < 150 else "fail",
        }
    }


def _build_editable(brief: dict) -> dict:
    return {
        "area_m2": brief.get("area", 20),
        "insulation_mm": brief.get("insulation_mm", 60),
        "glazing_uvalue": brief.get("glazing_uvalue", 2.0),
        "lighting_cct": brief.get("lighting_cct", 3000),
        "lighting_density_w_m2": brief.get("lighting_density_w_m2", 8),
        "wwr": brief.get("wwr", 0.25),
        "region": "HK",
    }


def _build_derived(brief: dict) -> dict:
    area = brief.get("area", 20)
    total = brief.get("budgetHKD", 100000)
    eui = brief.get("energy_eui", 45.0)
    return {
        "eui_kwh_m2_yr": eui,
        "cost_total": total,
        "cost_per_m2": int(total / max(area, 1)),
        "co2_t_per_yr": round(eui * area * 0.5 / 1000, 2),
    }


def _build_zones(brief: dict) -> list[dict]:
    zones = brief.get("zones") or []
    for z in zones:
        z.setdefault("notes", "")
    return zones


def _build_downloads(slug: str) -> list[dict]:
    return [
        {"name": f"{slug}-bundle.zip", "ext": "zip", "sub": "All artifacts",
         "size": "TBD", "href": f"/assets/mvps/{slug}/bundle.zip"},
    ]


# ───────── Bundle 打包 ─────────

def _build_bundle(slug: str, mvp_doc: dict, brief: dict) -> Path:
    """打包所有产物 zip · 放在 assets/mvps/<slug>/bundle.zip"""
    out_dir = ASSETS / "mvps" / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    zpath = out_dir / "bundle.zip"

    readme = _render_readme(slug, mvp_doc)

    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"{slug}/README.md", readme)
        zf.writestr(f"{slug}/brief.json", json.dumps(brief, ensure_ascii=False, indent=2))
        zf.writestr(f"{slug}/mvp.json", json.dumps(mvp_doc, ensure_ascii=False, indent=2))
        zf.writestr(f"{slug}/scene.json", json.dumps(mvp_doc.get("scene", {}), ensure_ascii=False, indent=2))
        # 若现有真 renders/hero/floorplan/moodboard 本地有文件 · 拉进去
        for p in out_dir.glob("**/*"):
            if p.is_file() and p.name != "bundle.zip":
                rel = p.relative_to(out_dir)
                zf.write(p, arcname=f"{slug}/assets/{rel}")
    return zpath


def _render_readme(slug: str, mvp: dict) -> str:
    proj = mvp.get("project", {})
    return f"""# {proj.get('name', slug)}

- **Slug**: `{slug}`
- **面积**: {proj.get('area', '—')} m²
- **位置**: {proj.get('location', '—')}
- **预算**: HKD {proj.get('budgetHKD', '—'):,}
- **风格**: {proj.get('style', '—')}

## 内容

- `brief.json` — 原始 brief（用户 + AI 推导的参数）
- `mvp.json` — 完整 MVP 文件（scene + variants + pricing + energy + compliance）
- `scene.json` — 3D 场景数据独立版
- `assets/` — renders / hero / thumb / moodboard 等（如果有）

## 生成

由 `_build/create_mvp_from_brief.py` 产出 · 生成时间 {datetime.utcnow().isoformat()}Z

## Web

在线访问：https://arctura-front-end.vercel.app/project/{slug}
"""


# ───────── mvps-index 更新 ─────────

def _update_index(mvp: dict):
    ip = DATA / "mvps-index.json"
    index = json.loads(ip.read_text())
    slug = mvp["slug"]
    entry = {
        "slug": slug,
        "name": mvp["project"].get("name_en") or mvp["project"].get("name"),
        "name_zh": mvp["project"].get("zh") or mvp["project"].get("name"),
        "type": mvp.get("type", "P1-interior"),
        "cat": mvp.get("cat", "workplace"),
        "area_m2": mvp["project"].get("area", 20),
        "eui": mvp.get("derived", {}).get("eui_kwh_m2_yr", 45),
        "cost_per_m2": mvp.get("derived", {}).get("cost_per_m2", 0),
        "currency": "HKD",
        "compliance": mvp.get("compliance", {}).get("HK", {}).get("verdict", "pass"),
        "thumb": mvp.get("thumb_img"),
        "hero": mvp.get("hero_img"),
        "complete": bool(mvp.get("complete")),
    }
    # 去重 · upsert
    index = [e for e in index if e.get("slug") != slug]
    index.append(entry)
    index.sort(key=lambda x: x.get("slug", ""))
    ip.write_text(json.dumps(index, ensure_ascii=False, indent=2))


# ───────── 主入口 ─────────

def create_mvp_from_brief(brief: dict, slug: str | None = None) -> dict:
    """核心函数 · 可被 CLI / Python / 未来的 HTTP API 共用。

    Returns: 完整 MVP 文件 dict。同时写入 data/mvps/<slug>.json · bundle.zip · 更新 index。
    """
    slug = slug or brief.get("slug") or _auto_slug(brief)

    scene = _build_scene_from_brief(brief)
    mvp = {
        "slug": slug,
        "cat": brief.get("cat", "workplace"),
        "type": brief.get("schema_type", "P1-interior"),
        "complete": brief.get("complete", True),
        "project": {
            "name": brief.get("name", slug),
            "zh": brief.get("name_zh", brief.get("name", slug)),
            "area": brief.get("area", 20),
            "location": brief.get("location", "Hong Kong"),
            "budgetHKD": brief.get("budgetHKD", 100000),
            "style": brief.get("style", ""),
            "palette": brief.get("palette", []),
        },
        "renders": brief.get("renders", []),
        "floorplan": brief.get("floorplan"),
        "moodboard": brief.get("moodboard"),
        "hero_img": brief.get("hero_img"),
        "thumb_img": brief.get("thumb_img"),
        "zones": _build_zones(brief),
        "furniture": [],
        "pricing": _build_pricing(brief),
        "energy": _build_energy(brief),
        "compliance": _build_compliance(brief),
        "variants": _build_variants_skeleton(brief, slug),
        "timeline": [],
        "decks": [],
        "downloads": _build_downloads(slug),
        "editable": _build_editable(brief),
        "derived": _build_derived(brief),
        "scene": scene,
    }

    # 写 MVP JSON
    out = DATA / "mvps" / f"{slug}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(mvp, ensure_ascii=False, indent=2))

    # 写 bundle
    _build_bundle(slug, mvp, brief)

    # upsert index
    _update_index(mvp)

    return mvp


def _auto_slug(brief: dict) -> str:
    name = brief.get("name", "new-mvp").lower().replace(" ", "-").replace("·", "")
    return f"99-{name[:40]}"


def retrofit_existing(slug: str) -> dict:
    """把已有的 MVP 补齐：variants(如果为空) + downloads + bundle + index"""
    p = DATA / "mvps" / f"{slug}.json"
    if not p.exists():
        raise FileNotFoundError(f"MVP {slug} 不存在")
    mvp = json.loads(p.read_text())

    # variants 空 → 按现有 project 填 3 方案
    vlist = mvp.get("variants", {}).get("list") or []
    if not vlist:
        fake_brief = {
            "name": mvp["project"].get("name", slug),
            "area": mvp["project"].get("area", 20),
            "budgetHKD": mvp["project"].get("budgetHKD", 100000),
        }
        mvp["variants"] = _build_variants_skeleton(fake_brief, slug)

    # downloads 空 → 补
    if not mvp.get("downloads"):
        mvp["downloads"] = _build_downloads(slug)

    # 写回
    p.write_text(json.dumps(mvp, ensure_ascii=False, indent=2))

    # bundle · reuse brief-like subset
    mini_brief = {
        "name": mvp["project"].get("name"),
        "area": mvp["project"].get("area"),
        "location": mvp["project"].get("location"),
        "budgetHKD": mvp["project"].get("budgetHKD"),
        "style": mvp["project"].get("style"),
        "palette": mvp["project"].get("palette", []),
        "_retrofit": True,
    }
    _build_bundle(slug, mvp, mini_brief)

    # index
    _update_index(mvp)

    return mvp


def _cli():
    ap = argparse.ArgumentParser()
    ap.add_argument("--brief", help="brief.json 路径")
    ap.add_argument("--slug", help="输出 slug（可选 · 不给自动推）")
    ap.add_argument("--retrofit", help="已存在 MVP 补齐模式（传 slug）")
    args = ap.parse_args()

    if args.retrofit:
        mvp = retrofit_existing(args.retrofit)
        print(f"✓ 补齐 {args.retrofit}")
        print(f"  variants: {len(mvp['variants']['list'])} 方案")
        print(f"  downloads: {len(mvp['downloads'])} 条")
        print(f"  bundle: assets/mvps/{args.retrofit}/bundle.zip")
        print(f"  index: data/mvps-index.json upserted")
    elif args.brief:
        brief = json.loads(Path(args.brief).read_text())
        mvp = create_mvp_from_brief(brief, slug=args.slug)
        print(f"✓ 新 MVP {mvp['slug']} 已生成")
        print(f"  JSON: data/mvps/{mvp['slug']}.json")
        print(f"  bundle: assets/mvps/{mvp['slug']}/bundle.zip")
        print(f"  URL: https://arctura-front-end.vercel.app/project/{mvp['slug']}")
    else:
        ap.error("需要 --brief 或 --retrofit")


if __name__ == "__main__":
    _cli()
