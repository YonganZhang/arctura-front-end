// Phase 11.4 · ADR-001 §"差量 SSOT" · scene-ops 16 op → overrides 4 namespace 映射
//
// 这是文档化 + 校验层，不是改写 scene-ops.js dispatcher 的入口。
// dispatcher 仍直接 mutate scene 给前端立即反馈；用户点 Save 时调
// `opsToOverrides(opsList, baseSceneSnapshot)` 转成 overrides 落 KV。
//
// 16 op 来自 project-space/lib/scene-ops.js dispatcher（Codex v2 #4 反馈：实际 16 个不是 13）
//
// 映射表（每个 op 落进哪个 namespace · 必要时多个 namespace）：
//
// | # | op                 | namespace            | 说明 |
// |---|--------------------|----------------------|------|
// | 1 | move_object        | layout (target=object)        | 目标 obj_id |
// | 2 | rotate_object      | layout (target=object)        | 同上 · rotation |
// | 3 | resize_object      | layout (target=object)        | 同上 · size |
// | 4 | remove_object      | tombstones.objects + 自动清 part_ids | |
// | 5 | add_object         | layout._added (含完整 payload + override_id) | 不依赖 nextObjectId |
// | 6 | move_assembly      | layout (target=assembly)      | |
// | 7 | rotate_assembly    | layout (target=assembly)      | |
// | 8 | remove_assembly    | tombstones.assemblies         | |
// | 9 | move_wall          | structural.walls (_op=move)   | |
// |10 | resize_wall        | structural.walls (_op=resize) | |
// |11 | add_opening        | structural.openings (_op=add) | |
// |12 | remove_opening     | structural.openings (_op=remove) | |
// |13 | add_light          | lighting._added                | |
// |14 | change_light       | lighting[id]                   | 含 intensity_scale 批量 |
// |15 | remove_light       | lighting[id]._op=remove        | |
// |16 | change_material    | appearance.{floor,ceiling,walls,assemblies,objects}  | |

import { validateOverrides } from "./overrides-apply.js";

const OP_TO_NAMESPACE = {
  move_object:    "layout",
  rotate_object:  "layout",
  resize_object:  "layout",
  remove_object:  "tombstones",
  add_object:     "layout",
  move_assembly:  "layout",
  rotate_assembly:"layout",
  remove_assembly:"tombstones",
  move_wall:      "structural",
  resize_wall:    "structural",
  add_opening:    "structural",
  remove_opening: "structural",
  add_light:      "lighting",
  change_light:   "lighting",
  remove_light:   "lighting",
  change_material:"appearance",
};

export const SCENE_OP_NAMES = Object.keys(OP_TO_NAMESPACE);
export const SCENE_OPS_COUNT = SCENE_OP_NAMES.length;  // 16

export function namespaceFor(opType) {
  return OP_TO_NAMESPACE[opType] || null;
}

let __genCounter = 0;
function _stableOverrideId(opType) {
  __genCounter++;
  return `ov_${opType}_${Date.now().toString(36)}_${__genCounter}`;
}

/**
 * 把一组 ops 转换成 overrides delta（merge 进 K.projectOverrides(slug) 现有值）
 * 不应用到 scene · 那是 derive() 的职责。
 *
 * @param {Array<Op>} ops - scene-ops.js 应用过的 ops list
 * @returns {Object} overrides delta（含 4 namespace + tombstones）
 */
export function opsToOverridesDelta(ops) {
  const delta = { layout: {}, structural: { walls: [], openings: [] }, appearance: {}, lighting: {}, tombstones: { objects: [], assemblies: [], lights: [] } };

  for (const op of ops || []) {
    const t = op?.type;
    switch (t) {
      case "move_object":
      case "rotate_object":
      case "resize_object": {
        const oid = _stableOverrideId(t);
        const change = { target: "object", target_id: op.id || op.id_or_name };
        if (op.pos) change.pos = op.pos;
        if (op.rotation) change.rotation = op.rotation;
        if (op.size) change.size = op.size;
        delta.layout[oid] = change;
        break;
      }
      case "move_assembly":
      case "rotate_assembly": {
        const oid = _stableOverrideId(t);
        const change = { target: "assembly", target_id: op.id || op.id_or_name };
        if (op.pos) change.pos = op.pos;
        if (op.rotation) change.rotation = op.rotation;
        delta.layout[oid] = change;
        break;
      }
      case "remove_object":
        if (op.id) delta.tombstones.objects.push(op.id);
        break;
      case "remove_assembly":
        if (op.id) delta.tombstones.assemblies.push(op.id);
        break;
      case "add_object": {
        const oid = _stableOverrideId(t);
        // payload 必须自含完整数据（不依赖 base scene nextObjectId · Codex v2 #5 反馈）
        // Codex 三审 #4：原本 `{...op}` 把整个 op（含 type:"add_object" 元数据）当 payload，
        // 应该 unwrap op.payload 或 op.object，让 payload 是真 object 数据。
        const objPayload = op.payload || op.object || (() => {
          // legacy: op 自身就是 object（含 id/type/pos 等）· 剥掉 op-level 的 type:"add_object"
          const { type: _opType, ...rest } = op;
          return rest;
        })();
        delta.layout[oid] = {
          target: "added",
          override_id: oid,
          payload: objPayload,
        };
        break;
      }
      case "move_wall":
      case "resize_wall": {
        const change = { id: op.id, _op: t === "move_wall" ? "move" : "resize" };
        if (op.start) change.start = op.start;
        if (op.end) change.end = op.end;
        if (op.height) change.height = op.height;
        if (op.thickness) change.thickness = op.thickness;
        delta.structural.walls.push(change);
        break;
      }
      case "add_opening":
        delta.structural.openings.push({ ...op, _op: "add" });
        break;
      case "remove_opening":
        delta.structural.openings.push({ id: op.id, _op: "remove" });
        break;
      case "add_light": {
        const id = op.id || _stableOverrideId(t);
        delta.lighting._added = delta.lighting._added || [];
        delta.lighting._added.push({ ...op, id });
        break;
      }
      case "change_light": {
        const lid = op.id || op.id_or_name;
        if (!lid) break;
        const change = {};
        for (const k of ["pos", "dir", "color", "power", "intensity", "intensity_scale", "size", "size_y", "shape", "cct"]) {
          if (op[k] !== undefined) change[k] = op[k];
        }
        delta.lighting[lid] = { ...(delta.lighting[lid] || {}), ...change };
        break;
      }
      case "remove_light": {
        const lid = op.id || op.id_or_name;
        if (lid) delta.lighting[lid] = { _op: "remove" };
        break;
      }
      case "change_material": {
        const target = op.target;
        const matId = op.material_id;
        if (!target || !matId) break;
        if (target === "floor" || target === "ceiling") {
          delta.appearance[target] = { material_id: matId };
        } else if (target === "wall" && op.id) {
          delta.appearance.walls = delta.appearance.walls || {};
          delta.appearance.walls[op.id] = { material_id: matId };
        } else if (target === "assembly" && op.id) {
          delta.appearance.assemblies = delta.appearance.assemblies || {};
          delta.appearance.assemblies[op.id] = { material_id: matId };
        } else if (target === "object" && op.id) {
          delta.appearance.objects = delta.appearance.objects || {};
          delta.appearance.objects[op.id] = { material_id: matId };
        }
        // inline material 创建
        if (op.inline_material && op.inline_id) {
          delta.appearance.materials_added = delta.appearance.materials_added || {};
          delta.appearance.materials_added[op.inline_id] = op.inline_material;
        }
        break;
      }
      default:
        // 未知 op · 跳过 · 不抛
        break;
    }
  }

  // 清空空 namespace（让 KV 写入更紧凑）
  if (delta.structural.walls.length === 0 && delta.structural.openings.length === 0) {
    delete delta.structural;
  }
  for (const k of ["objects", "assemblies", "lights"]) {
    if (delta.tombstones[k].length === 0) delete delta.tombstones[k];
  }
  if (Object.keys(delta.tombstones).length === 0) delete delta.tombstones;
  if (Object.keys(delta.layout).length === 0) delete delta.layout;
  if (Object.keys(delta.appearance).length === 0) delete delta.appearance;
  if (Object.keys(delta.lighting).length === 0) delete delta.lighting;

  return delta;
}

/**
 * 合并新 delta 进现有 overrides · layout 是 dict 累加 · structural 是数组追加 · tombstones 数组合并去重
 */
export function mergeOverridesDelta(existing, delta) {
  const out = JSON.parse(JSON.stringify(existing || {}));

  if (delta.layout) {
    out.layout = { ...(out.layout || {}), ...delta.layout };
  }
  if (delta.appearance) {
    out.appearance = out.appearance || {};
    for (const k of ["floor", "ceiling"]) {
      if (delta.appearance[k]) out.appearance[k] = delta.appearance[k];
    }
    for (const dictKey of ["walls", "assemblies", "objects", "materials_added"]) {
      if (delta.appearance[dictKey]) {
        out.appearance[dictKey] = { ...(out.appearance[dictKey] || {}), ...delta.appearance[dictKey] };
      }
    }
  }
  if (delta.structural) {
    out.structural = out.structural || {};
    for (const arrKey of ["walls", "openings"]) {
      if (Array.isArray(delta.structural[arrKey])) {
        out.structural[arrKey] = [...(out.structural[arrKey] || []), ...delta.structural[arrKey]];
      }
    }
  }
  if (delta.lighting) {
    out.lighting = out.lighting || {};
    if (Array.isArray(delta.lighting._added)) {
      out.lighting._added = [...(out.lighting._added || []), ...delta.lighting._added];
    }
    for (const [k, v] of Object.entries(delta.lighting)) {
      if (k === "_added") continue;
      out.lighting[k] = { ...(out.lighting[k] || {}), ...v };
    }
  }
  if (delta.tombstones) {
    out.tombstones = out.tombstones || {};
    for (const arrKey of ["objects", "assemblies", "lights"]) {
      if (Array.isArray(delta.tombstones[arrKey])) {
        const set = new Set([...(out.tombstones[arrKey] || []), ...delta.tombstones[arrKey]]);
        out.tombstones[arrKey] = [...set];
      }
    }
  }

  return out;
}

/**
 * 按 namespace reset overrides · ns="all" 清全部
 */
export function resetOverrides(existing, ns = "all") {
  if (!existing) return {};
  if (ns === "all") return {};
  const out = JSON.parse(JSON.stringify(existing));
  delete out[ns];
  return out;
}
