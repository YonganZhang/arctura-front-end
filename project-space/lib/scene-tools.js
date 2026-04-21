// scene-tools.js — 把 LLM tool calls 转换成 scene-ops 的 ops
// 还提供 scene 摘要（注入 LLM prompt 用）和 可用家具 type 注入

import { findObject, findWall, findLight, findOpening } from "./scene-ops.js";

// ───────── Scene tool names（对应 api/scene/TOOLS.md）─────────

export const SCENE_TOOL_NAMES = new Set([
  "move_furniture", "resize_furniture", "remove_furniture", "add_furniture",
  "change_material",
  "add_light", "change_light", "remove_light",
  "move_wall", "resize_wall",
  "add_window", "add_door", "remove_opening",
]);

export function isSceneTool(name) {
  return SCENE_TOOL_NAMES.has(name);
}

// ───────── Tool call → ops 转换器 ─────────
// 返回 { ops: [...] } 或 { ops: [], reason: "..." } 失败

export function toolToOps(call, scene) {
  const a = call.args || {};
  switch (call.name) {
    case "move_furniture": {
      const obj = findObject(scene, a.id_or_name);
      if (!obj) return { ops: [], reason: `家具不存在: ${a.id_or_name}` };
      const ops = [];
      if (a.pos_absolute) {
        ops.push({ op: "move_object", id: obj.id, pos: a.pos_absolute });
      } else if (a.pos_delta) {
        const pos = obj.pos.map((v, i) => v + (a.pos_delta[i] || 0));
        ops.push({ op: "move_object", id: obj.id, pos });
      }
      if (a.rotation_deg) {
        ops.push({ op: "rotate_object", id: obj.id, rotation: a.rotation_deg });
      }
      if (ops.length === 0) return { ops: [], reason: "需要 pos_absolute / pos_delta / rotation_deg 至少一项" };
      return { ops };
    }

    case "resize_furniture": {
      const obj = findObject(scene, a.id_or_name);
      if (!obj) return { ops: [], reason: `家具不存在: ${a.id_or_name}` };
      let size = a.size;
      if (!size && a.scale) {
        size = obj.size.map((v, i) => v * (a.scale[i] || 1));
      }
      if (!size) return { ops: [], reason: "需要 size 或 scale" };
      return { ops: [{ op: "resize_object", id: obj.id, size }] };
    }

    case "remove_furniture": {
      const obj = findObject(scene, a.id_or_name);
      if (!obj) return { ops: [], reason: `家具不存在: ${a.id_or_name}` };
      return { ops: [{ op: "remove_object", id: obj.id }] };
    }

    case "add_furniture": {
      if (!a.type) return { ops: [], reason: "add_furniture 需要 type" };
      if (!Array.isArray(a.pos)) return { ops: [], reason: "add_furniture 需要 pos [x,y,z]" };
      const op = {
        op: "add_object",
        type: a.type,
        pos: a.pos,
      };
      if (a.rotation_deg) op.rotation = a.rotation_deg;
      if (a.zone) op.zone = a.zone;
      if (a.label_zh) op.label_zh = a.label_zh;
      return { ops: [op] };
    }

    case "change_material": {
      const op = { op: "change_material", target: a.target };
      if (a.material_id) op.material_id = a.material_id;
      if (a.base_color) op.base_color = a.base_color;
      if (a.material) op.material = a.material;
      return { ops: [op] };
    }

    case "add_light": {
      if (!a.type) return { ops: [], reason: "add_light 需要 type" };
      return { ops: [{
        op: "add_light",
        type: a.type,
        pos: a.pos,
        cct: a.cct,
        power: a.power,
      }] };
    }

    case "change_light":
      return { ops: [{
        op: "change_light",
        id_or_name: a.id_or_name,
        cct: a.cct, power: a.power, intensity_scale: a.intensity_scale,
      }] };

    case "remove_light":
      return { ops: [{ op: "remove_light", id_or_name: a.id_or_name }] };

    case "move_wall": {
      const op = { op: "move_wall", id: a.id };
      if (a.offset) op.offset = a.offset;
      if (a.start) op.start = a.start;
      if (a.end) op.end = a.end;
      return { ops: [op] };
    }

    case "resize_wall":
      return { ops: [{ op: "resize_wall", id: a.id, height: a.height, thickness: a.thickness }] };

    case "add_window":
    case "add_door":
      return { ops: [{
        op: "add_opening",
        wall_id: a.wall_id,
        type: call.name === "add_window" ? "window" : "door",
        pos_along: a.pos_along,
        width: a.width,
        height: a.height,
        sill: a.sill,
      }] };

    case "remove_opening":
      return { ops: [{ op: "remove_opening", id: a.id }] };

    default:
      return { ops: [], reason: `unknown scene tool: ${call.name}` };
  }
}

// ───────── Scene summary for prompt injection ─────────

export function sceneSummary(scene, availableTypes = []) {
  if (!scene) return "";
  const lines = [];
  const { bounds, walls = [], objects = [], lights = [], materials = {} } = scene;

  lines.push("## Current Scene Summary");
  lines.push("");
  if (bounds) {
    lines.push(`Room bounds: ${bounds.w}m × ${bounds.d}m × ${bounds.h}m`);
  }

  if (objects.length > 0) {
    lines.push(`Objects (${objects.length} total):`);
    for (const o of objects.slice(0, 40)) {  // 40 件封顶，防 token 爆
      const label = o.label_zh || o.label_en || o.id;
      lines.push(`  - ${o.id} (${o.type}) @ [${o.pos.join(", ")}] · ${label}`);
    }
    if (objects.length > 40) lines.push(`  ... +${objects.length - 40} more`);
  }

  if (walls.length > 0) {
    lines.push(`Walls (${walls.length}): ${walls.map(w => w.id).join(", ")}`);
    const openings = walls.flatMap(w => (w.openings || []).map(o => ({ id: o.id, wall: w.id, type: o.type })));
    if (openings.length > 0) {
      lines.push(`Openings: ${openings.map(o => `${o.id} (${o.type} @ ${o.wall})`).join(", ")}`);
    }
  }
  if (scene.floor) lines.push(`Floor: material ${scene.floor.material_id}`);
  if (scene.ceiling) lines.push(`Ceiling: material ${scene.ceiling.material_id} @ h=${scene.ceiling.height}m`);

  if (lights.length > 0) {
    lines.push(`Lights (${lights.length}):`);
    for (const l of lights) {
      const parts = [l.id, l.type];
      if (l.cct) parts.push(`${l.cct}K`);
      if (l.power) parts.push(`${l.power}W`);
      lines.push(`  - ${parts.join(" · ")}`);
    }
  }

  if (Object.keys(materials).length > 0) {
    lines.push(`Materials: ${Object.keys(materials).slice(0, 20).join(", ")}${Object.keys(materials).length > 20 ? ", ..." : ""}`);
  }

  if (availableTypes.length > 0) {
    lines.push("");
    lines.push("## Available Furniture Types (for add_furniture)");
    lines.push(availableTypes.join(", "));
  }

  return lines.join("\n");
}

// ───────── scene tools prompt fragment ─────────

export const SCENE_TOOLS_PROMPT = `
## Scene-level tools (use ONLY if current state has "scene" field)

move_furniture(id_or_name, pos_absolute? OR pos_delta?, rotation_deg?)
  — 移动 / 旋转家具。id_or_name 可以是 id / 中英文 label / type 中任一。
  — pos_delta = 相对移动 [dx,dy,dz] 米；pos_absolute = 绝对坐标。
  — 例：用户说 "把衣柜往左移 30cm" → move_furniture(id_or_name="衣柜", pos_delta=[-0.3, 0, 0])

resize_furniture(id_or_name, size? OR scale?)
  — size = 绝对 [w,d,h] 米；scale = 倍数 [sw,sd,sh]

remove_furniture(id_or_name)
  — 删除物体

add_furniture(type, pos, rotation_deg?, zone?, label_zh?)
  — type 必须是下方 "Available Furniture Types" 之一
  — pos = [x,y,z] 米

change_material(target, material_id? OR base_color? OR material?)
  — target = object_id | wall_id | "floor" | "ceiling" | 中英文名
  — base_color = "#RRGGBB"（最方便 · 自动创建新 material）

add_light(type, pos, cct?, power?)
  — type: pendant | point | area | spot
  — cct: 1500-6500K · power: W

change_light(id_or_name, cct?, power?, intensity_scale?)
  — id_or_name 可用 "all" 改所有灯

remove_light(id_or_name)

move_wall(id, offset? OR start + end?)
  — offset = [dx,dy,dz] 相对平移全墙

resize_wall(id, height?, thickness?)

add_window(wall_id, pos_along, width, height, sill?)
add_door(wall_id, pos_along, width, height)
  — pos_along = 沿墙起→终点的距离（米）

remove_opening(id)
  — id 例如 "win_N_1" / "door_E_1"

**Rules**:
- 使用 scene 摘要里已存在的 id / label / type；不要凭空编 id
- 若用户请求超出当前能力（比如 "让它更浪漫" 这种主观），用 change_material 调颜色或 change_light 调 CCT 去近似
- 对需要多个 op 的请求，一次性 emit 多个 tool_calls
`;

// ───────── Full system prompt builder · 供 chat-edit.js 用 ─────────

export function buildScenePromptFragment(scene, availableFurnitureTypes) {
  if (!scene) return "";
  return `\n\n${sceneSummary(scene, availableFurnitureTypes)}\n\n${SCENE_TOOLS_PROMPT}`;
}
