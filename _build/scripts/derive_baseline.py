"""Phase 11.2 · Migration baseline extractor (read-only)

ADR-001 §"5 步落地路线" Step 3：在 derive 提纯之前，先扫描所有现有 MVP，
记录"当前 scene/editable/derived 各字段的真实值"作为 baseline。
后续 Step 11.3 引入 derive() 之后，跑同样脚本对比 baseline，得到 canonical-subset diff。

⚠ 本脚本 read-only · 不写 KV / 不改文件 / 不删数据 · 只输出报告 JSON

用法：
    python3 -m _build.scripts.derive_baseline > /tmp/baseline.json
    python3 -m _build.scripts.derive_baseline --diff /tmp/baseline.json  # 二次跑做对比

Codex 二审 #4 反馈：byte-equal 太硬 · 我们用 canonical subset：
  - scene: bounds + 主家具 type 集合 + 灯数（忽略坐标精度 / decor / camera 等抖动）
  - editable: insulation_mm / lighting_cct / wwr / region 等 scalar 字段
  - derived: eui_kwh_m2_yr / cost_total （epsilon 1e-3）
  - 忽略 _generated_by / timestamps / urls / hero / thumb / renders[] / downloads
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from typing import Any

# 项目根
ROOT = Path(__file__).resolve().parents[2]
DATA_MVPS = ROOT / "data" / "mvps"

# Canonical subset 抽取规则
SCENE_KEYS_TRACKED = {
    "bounds": "object_subset",         # {w, d, h}
    "objects": "count_only",           # 不记位置 · 只数量
    "assemblies": "type_set",          # 集合（去 decor）
    "lights": "count_and_types",       # 数量 + types
    "materials": "key_set",            # 用了哪些 material key
    "walls": "count_only",
    "_generated_by": "ignore",
    "_generated_for_slug": "ignore",
    "camera_default": "ignore",
    "env": "ignore",
    "ceiling": "ignore",
    "floor": "ignore",
}

EDITABLE_FIELDS_TRACKED = ["area_m2", "insulation_mm", "glazing_uvalue",
                             "lighting_cct", "lighting_density_w_m2", "wwr", "region"]
DERIVED_FIELDS_TRACKED = ["eui_kwh_m2_yr", "cost_total", "cost_per_m2", "co2_t_per_yr"]

DECOR_TYPES = {"book", "vase", "cup", "plant_small", "picture_frame"}

EPSILON = 1e-3


def _extract_scene_subset(scene: dict) -> dict:
    """从 scene 抽 canonical subset · 忽略坐标抖动 · 只保结构语义"""
    if not isinstance(scene, dict):
        return {"_present": False}
    out: dict[str, Any] = {"_present": True}

    bounds = scene.get("bounds") or {}
    if isinstance(bounds, dict):
        out["bounds"] = {k: round(bounds.get(k, 0), 2) for k in ("w", "d", "h")}

    objects = scene.get("objects") or []
    out["objects_count"] = len(objects)

    assemblies = scene.get("assemblies") or []
    main_types = sorted({a.get("type") for a in assemblies
                         if a.get("type") and a.get("type") not in DECOR_TYPES})
    out["main_furniture_types"] = main_types
    out["assemblies_count"] = len(assemblies)
    out["decor_count"] = sum(1 for a in assemblies if a.get("type") in DECOR_TYPES)

    lights = scene.get("lights") or []
    out["lights_count"] = len(lights)
    out["lights_types"] = sorted({l.get("type") for l in lights if l.get("type")})

    materials = scene.get("materials") or {}
    out["material_keys"] = sorted(materials.keys()) if isinstance(materials, dict) else []

    walls = scene.get("walls") or []
    out["walls_count"] = len(walls)

    return out


def _extract_editable_derived(payload: dict) -> dict:
    """fe_payload 顶层的 editable / derived 抽出来"""
    out = {"editable": {}, "derived": {}}
    edit = payload.get("editable") or {}
    if isinstance(edit, dict):
        for f in EDITABLE_FIELDS_TRACKED:
            if f in edit:
                out["editable"][f] = edit[f]
    der = payload.get("derived") or {}
    if isinstance(der, dict):
        for f in DERIVED_FIELDS_TRACKED:
            if f in der:
                out["derived"][f] = der[f]
    return out


def _extract_brief_subset(payload: dict) -> dict:
    """从 fe_payload.project / brief 抽语义关键字段"""
    out: dict[str, Any] = {}
    proj = payload.get("project") or {}
    if isinstance(proj, dict):
        out["area"] = proj.get("area")
        out["style"] = proj.get("style")
    # brief 在 KV 里 · fe_payload 里通常没有完整 brief
    out["_brief_in_payload"] = bool(payload.get("brief"))
    return out


def extract_baseline_from_disk() -> dict:
    """扫 data/mvps/<slug>.json 的 46 静态快照 · 出 baseline

    （不读 KV · 也不依赖 worker · 完全离线 · CI 友好）
    """
    if not DATA_MVPS.exists():
        return {"error": f"DATA_MVPS missing: {DATA_MVPS}"}
    out = {"version": "v1", "schema": "Phase 11.2 baseline", "items": {}}
    for f in sorted(DATA_MVPS.glob("*.json")):
        slug = f.stem
        try:
            payload = json.loads(f.read_text())
        except Exception as e:
            out["items"][slug] = {"_error": f"parse: {e}"}
            continue
        scene_subset = _extract_scene_subset(payload.get("scene") or {})
        ed = _extract_editable_derived(payload)
        bs = _extract_brief_subset(payload)
        out["items"][slug] = {
            "scene": scene_subset,
            **ed,
            "brief_meta": bs,
            "complete": payload.get("complete"),
            "cat": payload.get("cat"),
            "type": payload.get("type"),
        }
    out["count"] = len(out["items"])
    return out


def diff_canonical(old: dict, new: dict, path: str = "") -> list[dict]:
    """递归 diff · 浮点数容忍 EPSILON · 数组保序对比 · 返扁平 diff list"""
    diffs: list[dict] = []
    if isinstance(old, dict) and isinstance(new, dict):
        keys = set(old.keys()) | set(new.keys())
        for k in sorted(keys):
            sub_path = f"{path}.{k}" if path else k
            if k not in old:
                diffs.append({"path": sub_path, "kind": "added", "new": new[k]})
            elif k not in new:
                diffs.append({"path": sub_path, "kind": "removed", "old": old[k]})
            else:
                diffs.extend(diff_canonical(old[k], new[k], sub_path))
    elif isinstance(old, list) and isinstance(new, list):
        if old != new:
            diffs.append({"path": path, "kind": "list_diff",
                          "old": old, "new": new,
                          "old_len": len(old), "new_len": len(new)})
    elif isinstance(old, (int, float)) and isinstance(new, (int, float)):
        if abs(old - new) > EPSILON:
            diffs.append({"path": path, "kind": "scalar_diff", "old": old, "new": new})
    else:
        if old != new:
            diffs.append({"path": path, "kind": "value_diff", "old": old, "new": new})
    return diffs


def diff_baselines(baseline_a: dict, baseline_b: dict) -> dict:
    """两次 baseline 对比 · 输出每个 slug 的 canonical diff"""
    items_a = baseline_a.get("items", {})
    items_b = baseline_b.get("items", {})
    slugs = sorted(set(items_a.keys()) | set(items_b.keys()))
    report = {
        "summary": {
            "total_slugs": len(slugs),
            "only_in_a": [],
            "only_in_b": [],
            "identical": 0,
            "diff_count": 0,
            "high_risk_slugs": [],   # diff > 5 字段
        },
        "diffs": {},
    }
    for slug in slugs:
        if slug not in items_b:
            report["summary"]["only_in_a"].append(slug)
            continue
        if slug not in items_a:
            report["summary"]["only_in_b"].append(slug)
            continue
        d = diff_canonical(items_a[slug], items_b[slug])
        if not d:
            report["summary"]["identical"] += 1
        else:
            report["summary"]["diff_count"] += 1
            report["diffs"][slug] = d
            if len(d) > 5:
                report["summary"]["high_risk_slugs"].append(slug)
    return report


def main():
    ap = argparse.ArgumentParser(description="Migration baseline extractor (read-only)")
    ap.add_argument("--diff", help="对比给定 baseline 文件 · 当前快照作 'new'")
    ap.add_argument("--pretty", action="store_true", help="缩进 JSON 输出")
    ap.add_argument("--summary", action="store_true", help="只输出 summary 不输出 items")
    args = ap.parse_args()

    current = extract_baseline_from_disk()

    if args.diff:
        old = json.loads(Path(args.diff).read_text())
        report = diff_baselines(old, current)
        out = report["summary"] if args.summary else report
    else:
        if args.summary:
            out = {
                "count": current.get("count", 0),
                "slugs_sample": list(current.get("items", {}).keys())[:5],
            }
        else:
            out = current

    print(json.dumps(out, ensure_ascii=False, indent=2 if args.pretty else None))


if __name__ == "__main__":
    main()
