"""Phase 11.4 · overrides 应用层 · ADR-001 §"差量 SSOT"

overrides 4 namespace 设计（修 Codex v2 反馈：layout/structural/appearance/lighting）：
{
  "layout": {
    "<override_id>": {
      "target": "object" | "assembly",
      "target_id": "asm_desk_1" | "obj_desk_1",
      "pos": [x, y, z],     # 可选 · 不写表示不改 pos
      "rotation": [rx,ry,rz],
      "size": [w, d, h]
    }
  },
  "structural": {
    "walls": [{"id":"wall_Back", "start":[...], "end":[...], "_op":"resize"|"move"}],
    "openings": [{"_op":"add", "wall_id":"...", "kind":"door|window", "x":..., "w":...}]
  },
  "appearance": {
    "floor": {"material_id": "..."},
    "ceiling": {"material_id": "..."},
    "walls": {"<wall_id>": {"material_id": "..."}},
    "assemblies": {"<asm_id>": {"material_id": "..."}},
    "objects": {"<obj_id>": {"material_id": "..."}},
    "materials_added": {"<new_mat_id>": {"base_color": "...", ...}}
  },
  "lighting": {
    "<light_id>": {
      "_op": "change" | "remove",
      "pos": [...], "dir": [...], "color": [...], "power": 80, "intensity": 5.5,
      "size": ..., "size_y": ..., "shape": "RECTANGLE", "cct": 3000
    },
    "_added": [{"id":"light_new_xxx", "type":"point", ...}]
  },
  "tombstones": {
    "objects": ["obj_id_1"],     # 删除标记 · derive 时跳过
    "assemblies": ["asm_id_1"],
    "lights": ["light_id_1"]
  }
}

校验规则：
  - 每个 override 必须有 stable id（override_id 用户拖动产生 · 不依赖 base scene 的 nextObjectId）
  - 找不到 target_id（譬如 brief 重生成后家具变了）→ 标 orphaned · 不抛 · 让 UI 提醒用户 reset
  - tombstones 不可与 layout 同 id 共存（删除胜过修改）
"""
from __future__ import annotations
import copy
from typing import Any

OVERRIDES_SCHEMA_VERSION = "v1"
NAMESPACES = ("layout", "structural", "appearance", "lighting", "tombstones")


def _is_dict(x):
    return isinstance(x, dict)


def _is_list(x):
    return isinstance(x, list)


def apply_overrides_to_scene(base_scene: dict, overrides: dict) -> dict:
    """读 overrides 4 namespace · 应用到 base scene · 返新 dict（不 mutate base）

    顺序（重要 · 后操作覆盖前操作）：
      1. tombstones 删除（最先 · 后续操作不会碰已删的）
      2. appearance 改 material（最廉价 · 不动几何）
      3. layout 改 pos/rotation/size
      4. structural 改 walls/openings
      5. lighting 改灯
    """
    if not _is_dict(overrides) or not overrides:
        return copy.deepcopy(base_scene)

    scene = copy.deepcopy(base_scene)

    # 1. tombstones · 删除
    tombstones = overrides.get("tombstones") or {}
    if _is_dict(tombstones):
        _apply_tombstones(scene, tombstones)

    # 2. appearance · material
    appearance = overrides.get("appearance") or {}
    if _is_dict(appearance):
        _apply_appearance(scene, appearance)

    # 3. layout · pos / rotation / size
    layout = overrides.get("layout") or {}
    if _is_dict(layout):
        _apply_layout(scene, layout)

    # 4. structural · walls / openings
    structural = overrides.get("structural") or {}
    if _is_dict(structural):
        _apply_structural(scene, structural)

    # 5. lighting
    lighting = overrides.get("lighting") or {}
    if _is_dict(lighting):
        _apply_lighting(scene, lighting)

    return scene


def _apply_tombstones(scene: dict, tomb: dict):
    """删除 objects / assemblies / lights · 删除前先记 · 防 orphan"""
    obj_ids = set(tomb.get("objects") or [])
    asm_ids = set(tomb.get("assemblies") or [])
    light_ids = set(tomb.get("lights") or [])

    if obj_ids:
        scene["objects"] = [o for o in scene.get("objects", [])
                            if o.get("id") not in obj_ids]
        # 同时把 assembly.part_ids 里的引用清掉
        for a in scene.get("assemblies", []):
            a["part_ids"] = [pid for pid in (a.get("part_ids") or []) if pid not in obj_ids]
    if asm_ids:
        scene["assemblies"] = [a for a in scene.get("assemblies", [])
                                if a.get("id") not in asm_ids]
    if light_ids:
        scene["lights"] = [l for l in scene.get("lights", [])
                           if l.get("id") not in light_ids]


def _apply_layout(scene: dict, layout: dict):
    """layout 用 override_id 索引 · 每条 override 含 target/target_id

    target=="added" · payload 是新 object 完整定义（用户 add_object 产生）·
    Codex 三审 #2：Python 端原本只支持 target=object/assembly · 缺 added 分支 ·
    导致 derive 后 frontend 加的 object 全丢
    """
    objects_by_id = {o.get("id"): o for o in scene.get("objects", [])}
    asms_by_id = {a.get("id"): a for a in scene.get("assemblies", [])}

    for override_id, change in layout.items():
        if not _is_dict(change):
            continue
        target = change.get("target")

        # target=added · 加新 object 到 scene.objects
        if target == "added":
            payload = change.get("payload")
            if _is_dict(payload):
                scene.setdefault("objects", []).append(dict(payload))
            continue

        tid = change.get("target_id")
        if not tid:
            continue
        bag = objects_by_id if target == "object" else asms_by_id
        item = bag.get(tid)
        if item is None:
            # orphan · brief 重生后 target 不存在 · 静默跳过 · UI 应提醒
            continue
        if "pos" in change and _is_list(change["pos"]):
            item["pos"] = list(change["pos"])
        if "rotation" in change and _is_list(change["rotation"]):
            item["rotation"] = list(change["rotation"])
        if "size" in change and _is_list(change["size"]):
            item["size"] = list(change["size"])


def _apply_appearance(scene: dict, appearance: dict):
    """改材质 · floor / ceiling / wall / assembly / object · 也支持 inline material 创建"""
    # 新增 material（内联创建）
    added = appearance.get("materials_added") or {}
    if _is_dict(added):
        scene.setdefault("materials", {})
        for mat_id, mat_def in added.items():
            if _is_dict(mat_def):
                scene["materials"][mat_id] = dict(mat_def)

    # floor / ceiling
    for k in ("floor", "ceiling"):
        change = appearance.get(k)
        if _is_dict(change) and "material_id" in change:
            scene.setdefault(k, {})["material_id"] = change["material_id"]

    # walls
    walls_change = appearance.get("walls") or {}
    if _is_dict(walls_change):
        walls_by_id = {w.get("id"): w for w in scene.get("walls", [])}
        for wid, change in walls_change.items():
            w = walls_by_id.get(wid)
            if w and _is_dict(change) and "material_id" in change:
                w["material_id"] = change["material_id"]

    # assemblies
    asms_change = appearance.get("assemblies") or {}
    if _is_dict(asms_change):
        asms_by_id = {a.get("id"): a for a in scene.get("assemblies", [])}
        for aid, change in asms_change.items():
            a = asms_by_id.get(aid)
            if a and _is_dict(change) and "material_id" in change:
                a["material_id_primary"] = change["material_id"]

    # objects
    objs_change = appearance.get("objects") or {}
    if _is_dict(objs_change):
        objs_by_id = {o.get("id"): o for o in scene.get("objects", [])}
        for oid, change in objs_change.items():
            o = objs_by_id.get(oid)
            if o and _is_dict(change) and "material_id" in change:
                o["material_id"] = change["material_id"]


def _apply_structural(scene: dict, structural: dict):
    """walls 几何修改（resize/move）· openings 增删（_op=add/remove）"""
    # walls
    walls_changes = structural.get("walls") or []
    if _is_list(walls_changes):
        walls_by_id = {w.get("id"): w for w in scene.get("walls", [])}
        for change in walls_changes:
            if not _is_dict(change):
                continue
            wid = change.get("id")
            w = walls_by_id.get(wid)
            if w is None:
                continue
            for k in ("start", "end", "height", "thickness"):
                if k in change:
                    w[k] = change[k]

    # openings · TODO Step 11.4.5 · 现 schema 已锁但 base scene 没 openings 列表 · 留接口
    openings_changes = structural.get("openings") or []
    if openings_changes:
        scene.setdefault("openings", [])
        for change in openings_changes:
            if not _is_dict(change):
                continue
            op = change.get("_op")
            if op == "add":
                payload = {k: v for k, v in change.items() if k != "_op"}
                if "id" in payload:
                    scene["openings"].append(payload)
            elif op == "remove":
                oid = change.get("id")
                scene["openings"] = [o for o in scene["openings"] if o.get("id") != oid]


def _apply_lighting(scene: dict, lighting: dict):
    """改灯 / 加灯 · `_added` 是数组 · 其他 key 是 light_id → change"""
    added = lighting.get("_added") or []
    if _is_list(added):
        scene.setdefault("lights", [])
        for entry in added:
            if _is_dict(entry) and entry.get("id"):
                scene["lights"].append(dict(entry))

    lights_by_id = {l.get("id"): l for l in scene.get("lights", [])}
    for light_id, change in lighting.items():
        if light_id == "_added":
            continue
        if not _is_dict(change):
            continue
        target = lights_by_id.get(light_id)
        if target is None:
            continue
        op = change.get("_op", "change")
        if op == "remove":
            scene["lights"] = [l for l in scene.get("lights", []) if l.get("id") != light_id]
            continue
        # change · 拷贝指定字段
        for k in ("pos", "dir", "color", "power", "intensity", "size", "size_y", "shape", "cct"):
            if k in change:
                target[k] = change[k]
        # 批量 intensity_scale（Codex v2 反馈 #7：change_light 支持 batch）
        if "intensity_scale" in change:
            scale = float(change["intensity_scale"])
            cur = target.get("intensity", 1.0)
            target["intensity"] = round(cur * scale, 3)


def validate_overrides(overrides: dict) -> list[str]:
    """轻量校验 · 返 error 字符串 list · 空 = 合规"""
    errors: list[str] = []
    if not _is_dict(overrides):
        return ["overrides must be dict"]
    for ns in overrides.keys():
        if ns not in NAMESPACES:
            errors.append(f"unknown namespace: {ns} · allowed: {NAMESPACES}")
    layout = overrides.get("layout") or {}
    if _is_dict(layout):
        for oid, ch in layout.items():
            if not _is_dict(ch):
                errors.append(f"layout.{oid} not dict")
                continue
            # target=="added" 不要求 target_id（payload 自含 · Codex 终审 #2）
            if ch.get("target") == "added":
                if not _is_dict(ch.get("payload")):
                    errors.append(f"layout.{oid} target=added requires payload dict")
                continue
            if not ch.get("target_id"):
                errors.append(f"layout.{oid} missing target_id")
    return errors


__all__ = ["apply_overrides_to_scene", "validate_overrides",
           "OVERRIDES_SCHEMA_VERSION", "NAMESPACES"]
