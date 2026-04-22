// scene-tools.js — 把 LLM tool calls 转换成 scene-ops 的 ops
// 还提供 scene 摘要（注入 LLM prompt 用）和 可用家具 type 注入

import { findObject, findWall, findLight, findOpening, findAssembly, findAssemblyByObjectId } from "./scene-ops.js";

// 解析"家具名"为正确的 assembly / object · assembly 优先（procedural 模式下它是可见的主体）
// 返回 { kind: "assembly"|"object", entity } 或 null
function resolveFurniture(scene, query) {
  const asm = findAssembly(scene, query);
  if (asm) return { kind: "assembly", entity: asm };
  const obj = findObject(scene, query);
  if (obj) {
    // 如果 object 属于某 assembly · 作用于 assembly（整件家具）
    const owner = findAssemblyByObjectId(scene, obj.id);
    if (owner) return { kind: "assembly", entity: owner };
    return { kind: "object", entity: obj };
  }
  return null;
}

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
      // FIX · 优先作用于 assembly（procedural 模式渲染的主体）· 否则作用于 object
      const res = resolveFurniture(scene, a.id_or_name);
      if (!res) return { ops: [], reason: `家具不存在: ${a.id_or_name}` };
      const ops = [];
      const moveOp = res.kind === "assembly" ? "move_assembly" : "move_object";
      const rotOp = res.kind === "assembly" ? "rotate_assembly" : "rotate_object";
      if (a.pos_absolute) {
        ops.push({ op: moveOp, id: res.entity.id, pos: a.pos_absolute });
      } else if (a.pos_delta) {
        if (res.kind === "assembly") {
          ops.push({ op: "move_assembly", id: res.entity.id, delta: a.pos_delta });
        } else {
          const pos = res.entity.pos.map((v, i) => v + (a.pos_delta[i] || 0));
          ops.push({ op: "move_object", id: res.entity.id, pos });
        }
      }
      if (a.rotation_deg) {
        ops.push({ op: rotOp, id: res.entity.id, rotation: a.rotation_deg });
      }
      if (ops.length === 0) return { ops: [], reason: "需要 pos_absolute / pos_delta / rotation_deg 至少一项" };
      return { ops };
    }

    case "resize_furniture": {
      // resize 只能作用于 object（assembly.size 是 parts 聚合 · 不能直接改）
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
      // FIX · 优先 remove_assembly（级联删所有 parts）· 否则 remove_object
      const res = resolveFurniture(scene, a.id_or_name);
      if (!res) return { ops: [], reason: `家具不存在: ${a.id_or_name}` };
      const op = res.kind === "assembly" ? "remove_assembly" : "remove_object";
      return { ops: [{ op, id: res.entity.id }] };
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
      // FIX · target 如果是模糊家具名 · 解析成 assembly id（让 change_material op 看得懂）
      let target = a.target;
      if (target && target !== "floor" && target !== "ceiling") {
        const wall = findWall(scene, target);
        if (wall) {
          target = wall.id;
        } else {
          const res = resolveFurniture(scene, target);
          if (res) target = res.entity.id;  // assembly.id 或 object.id
        }
      }
      const op = { op: "change_material", target };
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

**Few-shot 中文例子**（必须用 scene tool · 不要用 set_editable / scale_editable）:

User: "删掉衣柜"
Assistant: 好，把衣柜删掉。
\`\`\`json
{"tool_calls":[{"name":"remove_furniture","args":{"id_or_name":"衣柜"}}]}
\`\`\`

User: "把沙发往左移 50 厘米"
Assistant: 把沙发向 x 负方向平移 50cm。
\`\`\`json
{"tool_calls":[{"name":"move_furniture","args":{"id_or_name":"沙发","pos_delta":[-0.5,0,0]}}]}
\`\`\`

User: "把书架换成白色"
Assistant: 把书架换成纯白（#FFFFFF）。
\`\`\`json
{"tool_calls":[{"name":"change_material","args":{"target":"书架","base_color":"#FFFFFF"}}]}
\`\`\`

User: "把墙刷米色"
Assistant: 4 面墙都改成米色（#E8DCC8）。
\`\`\`json
{"tool_calls":[
  {"name":"change_material","args":{"target":"wall_N","base_color":"#E8DCC8"}},
  {"name":"change_material","args":{"target":"wall_S","base_color":"#E8DCC8"}},
  {"name":"change_material","args":{"target":"wall_E","base_color":"#E8DCC8"}},
  {"name":"change_material","args":{"target":"wall_W","base_color":"#E8DCC8"}}
]}
\`\`\`

User: "加一把椅子到窗边"
Assistant: 在窗边加一把标准椅子。
\`\`\`json
{"tool_calls":[{"name":"add_furniture","args":{"type":"chair_standard","pos":[1.5,-1.0,0],"label_zh":"窗边椅"}}]}
\`\`\`

User: "把吊灯调暖一点"
Assistant: 吊灯色温调到 2700K 暖光。
\`\`\`json
{"tool_calls":[{"name":"change_light","args":{"id_or_name":"all","cct":2700}}]}
\`\`\`

User: "北墙加个窗"
Assistant: 在北墙中间加一扇 1.5m 宽 × 1.5m 高的窗。
\`\`\`json
{"tool_calls":[{"name":"add_window","args":{"wall_id":"wall_N","pos_along":2.5,"width":1.5,"height":1.5,"sill":0.9}}]}
\`\`\`
`;

// ───────── Full system prompt builder · 供 chat-edit.js 用 ─────────

export function buildScenePromptFragment(scene, availableFurnitureTypes) {
  if (!scene) return "";
  return `\n\n${sceneSummary(scene, availableFurnitureTypes)}\n\n${SCENE_TOOLS_PROMPT}`;
}
