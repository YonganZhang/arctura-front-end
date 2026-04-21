// scene-ops.js — 把 ops 应用到 scene · 纯函数 · 服务端和客户端可共用
// 13 个 op 见 api/scene/README.md

// ───────── 深拷贝 · 避免 mutate 入参 ─────────

function clone(obj) {
  return JSON.parse(JSON.stringify(obj));
}

// ───────── fuzzy match ─────────
// 对 scene.objects / walls / lights 做 id / label / type 的模糊查找
// 让 LLM 不需要严格给 id · "衣柜" / "closet" / "obj_closet" 都能命中

export function findObject(scene, query) {
  if (!query) return null;
  const q = String(query).trim().toLowerCase();
  const objects = scene.objects || [];
  // 1. 精确 id
  const byId = objects.find(o => o.id?.toLowerCase() === q);
  if (byId) return byId;
  // 2. id 去前缀 obj_
  const byBare = objects.find(o => o.id?.toLowerCase() === `obj_${q}`);
  if (byBare) return byBare;
  // 3. label 完全相等（中英文）
  const byLabel = objects.find(
    o => o.label_zh === query || o.label_en?.toLowerCase() === q || o.label_en === query
  );
  if (byLabel) return byLabel;
  // 4. label 包含 query
  const byLabelContains = objects.find(
    o => (o.label_zh || "").includes(query) ||
         (o.label_en || "").toLowerCase().includes(q)
  );
  if (byLabelContains) return byLabelContains;
  // 5. type 包含 query
  const byType = objects.find(o => (o.type || "").toLowerCase().includes(q));
  if (byType) return byType;
  return null;
}

// Assembly fuzzy match · Phase 3 · default target for chat / card edits
export function findAssembly(scene, query) {
  if (!query) return null;
  const q = String(query).trim().toLowerCase();
  const assemblies = scene.assemblies || [];
  const byId = assemblies.find(a => a.id?.toLowerCase() === q);
  if (byId) return byId;
  const byLabel = assemblies.find(
    a => a.label_zh === query || a.label_en?.toLowerCase() === q
  );
  if (byLabel) return byLabel;
  const byLabelContains = assemblies.find(
    a => (a.label_zh || "").includes(query) || (a.label_en || "").toLowerCase().includes(q)
  );
  if (byLabelContains) return byLabelContains;
  const byType = assemblies.find(a => (a.type || "").toLowerCase().includes(q));
  if (byType) return byType;
  return null;
}

// 给 object 找所属 assembly（back-ref via object.assembly_id · 或者遍历 part_ids）
export function findAssemblyByObjectId(scene, objectId) {
  if (!objectId || !scene.assemblies) return null;
  // 1. object 自带 assembly_id
  const obj = (scene.objects || []).find(o => o.id === objectId);
  if (obj?.assembly_id) {
    return scene.assemblies.find(a => a.id === obj.assembly_id) || null;
  }
  // 2. fallback 遍历 part_ids
  return scene.assemblies.find(a => (a.part_ids || []).includes(objectId)) || null;
}

export function findWall(scene, query) {
  if (!query) return null;
  const q = String(query).trim().toLowerCase();
  const walls = scene.walls || [];
  const byId = walls.find(w => w.id?.toLowerCase() === q);
  if (byId) return byId;
  const byBare = walls.find(w => w.id?.toLowerCase() === `wall_${q}`);
  if (byBare) return byBare;
  const byName = walls.find(w => (w.name || "").toLowerCase() === q);
  if (byName) return byName;
  const byNameContains = walls.find(w => (w.name || "").toLowerCase().includes(q));
  if (byNameContains) return byNameContains;
  return null;
}

export function findLight(scene, query) {
  if (!query) return null;
  const q = String(query).trim().toLowerCase();
  const lights = scene.lights || [];
  if (q === "all") return lights;  // 特殊值 = 所有灯
  const byId = lights.find(l => l.id?.toLowerCase() === q);
  if (byId) return byId;
  const byType = lights.filter(l => l.type?.toLowerCase() === q);
  if (byType.length) return byType.length === 1 ? byType[0] : byType;
  return null;
}

export function findOpening(scene, query) {
  if (!query) return null;
  const q = String(query).trim().toLowerCase();
  for (const w of scene.walls || []) {
    for (const op of w.openings || []) {
      if (op.id?.toLowerCase() === q) return { opening: op, wall: w };
    }
  }
  return null;
}

// ───────── id generator ─────────

function nextObjectId(scene, type) {
  const prefix = `obj_${type}`;
  const existing = (scene.objects || [])
    .map(o => o.id || "")
    .filter(id => id.startsWith(prefix));
  let n = existing.length + 1;
  // 确保不撞
  while (existing.some(id => id === `${prefix}_${n}`)) n++;
  return `${prefix}_${n}`;
}

function nextLightId(scene, type) {
  const prefix = type; // e.g. "pendant"
  const existing = (scene.lights || [])
    .map(l => l.id || "")
    .filter(id => id.startsWith(prefix + "_"));
  let n = existing.length + 1;
  while (existing.some(id => id === `${prefix}_${n}`)) n++;
  return `${prefix}_${n}`;
}

function nextOpeningId(wall, type) {
  const prefix = type === "window" ? "win" : "door";
  const existing = (wall.openings || []).map(o => o.id || "");
  let n = existing.length + 1;
  while (existing.some(id => id === `${prefix}_${wall.id.replace(/^wall_/, "")}_${n}`)) n++;
  return `${prefix}_${wall.id.replace(/^wall_/, "")}_${n}`;
}

function nextInlineMaterialId(scene) {
  const mats = scene.materials || {};
  let n = 1;
  while (mats[`mat_inline_${n}`]) n++;
  return `mat_inline_${n}`;
}

// ───────── ops 实现 ─────────
// 每个 op 返回 { ok: bool, before: {...}, after: {...}, reason?: string }
// before / after 是 op 影响的 entity 局部快照（非整 scene）

function opMoveObject(scene, op) {
  const obj = findObject(scene, op.id || op.id_or_name);
  if (!obj) return { ok: false, reason: `object not found: ${op.id || op.id_or_name}` };
  if (!Array.isArray(op.pos) || op.pos.length !== 3) {
    return { ok: false, reason: "pos must be [x, y, z]" };
  }
  const before = { pos: [...obj.pos] };
  obj.pos = op.pos.map(v => Math.round(v * 1000) / 1000);
  return { ok: true, before, after: { pos: obj.pos } };
}

function opRotateObject(scene, op) {
  const obj = findObject(scene, op.id || op.id_or_name);
  if (!obj) return { ok: false, reason: `object not found: ${op.id || op.id_or_name}` };
  if (!Array.isArray(op.rotation) || op.rotation.length !== 3) {
    return { ok: false, reason: "rotation must be [rx, ry, rz] in degrees" };
  }
  const before = { rotation: obj.rotation ? [...obj.rotation] : [0, 0, 0] };
  obj.rotation = op.rotation.map(v => Math.round(v * 1000) / 1000);
  return { ok: true, before, after: { rotation: obj.rotation } };
}

function opResizeObject(scene, op) {
  const obj = findObject(scene, op.id || op.id_or_name);
  if (!obj) return { ok: false, reason: `object not found: ${op.id || op.id_or_name}` };
  if (!Array.isArray(op.size) || op.size.length !== 3 || op.size.some(v => v <= 0)) {
    return { ok: false, reason: "size must be [w, d, h] with all values > 0" };
  }
  const before = { size: [...obj.size] };
  obj.size = op.size.map(v => Math.round(v * 1000) / 1000);
  return { ok: true, before, after: { size: obj.size } };
}

function opRemoveObject(scene, op) {
  const obj = findObject(scene, op.id || op.id_or_name);
  if (!obj) return { ok: false, reason: `object not found: ${op.id || op.id_or_name}` };
  const before = clone(obj);
  scene.objects = (scene.objects || []).filter(o => o.id !== obj.id);
  return { ok: true, before, after: null };
}

// Phase 3.M · 两 assembly AABB 碰撞检测 · 返回第一个显著重叠的对象
function _findCollision(scene, newPos, newSize) {
  const nBox = {
    min: [newPos[0] - newSize[0]/2, newPos[1] - newSize[1]/2, newPos[2] - newSize[2]/2],
    max: [newPos[0] + newSize[0]/2, newPos[1] + newSize[1]/2, newPos[2] + newSize[2]/2],
  };
  const newVol = Math.max(0.001, newSize[0] * newSize[1] * newSize[2]);
  for (const asm of scene.assemblies || []) {
    if (!asm.pos || !asm.size) continue;
    const oBox = {
      min: [asm.pos[0] - asm.size[0]/2, asm.pos[1] - asm.size[1]/2, asm.pos[2] - asm.size[2]/2],
      max: [asm.pos[0] + asm.size[0]/2, asm.pos[1] + asm.size[1]/2, asm.pos[2] + asm.size[2]/2],
    };
    const ox = Math.max(0, Math.min(nBox.max[0], oBox.max[0]) - Math.max(nBox.min[0], oBox.min[0]));
    const oy = Math.max(0, Math.min(nBox.max[1], oBox.max[1]) - Math.max(nBox.min[1], oBox.min[1]));
    const oz = Math.max(0, Math.min(nBox.max[2], oBox.max[2]) - Math.max(nBox.min[2], oBox.min[2]));
    const overlap = ox * oy * oz;
    // 阈值：重叠 > 新物件体积 30% + 至少 0.01m³（否则 rug 贴地板不算冲突）
    if (overlap > newVol * 0.3 && overlap > 0.01) {
      return { asm, overlap_m3: overlap };
    }
  }
  return null;
}

function opAddObject(scene, op) {
  if (!op.type) return { ok: false, reason: "add_object requires type" };
  if (!Array.isArray(op.pos) || op.pos.length !== 3) {
    return { ok: false, reason: "add_object requires pos [x,y,z]" };
  }
  // 防两家具穿模
  const newSize = op.size || [0.5, 0.5, 0.5];
  const collision = _findCollision(scene, op.pos, newSize);
  if (collision) {
    return {
      ok: false,
      reason: `位置冲突：与 ${collision.asm.label_zh || collision.asm.id} 重叠 ${collision.overlap_m3.toFixed(2)}m³ · 换个位置`,
    };
  }
  scene.objects = scene.objects || [];
  scene.assemblies = scene.assemblies || [];
  const id = nextObjectId(scene, op.type);
  const asmId = nextAssemblyId(scene, op.type);
  const entry = {
    id,
    type: op.type,
    pos: op.pos.map(v => Math.round(v * 1000) / 1000),
    size: op.size || [0.5, 0.5, 0.5],
    material_id: op.material_id || "default",
    label_en: op.label_en || op.type,
    label_zh: op.label_zh || op.type,
    assembly_id: asmId,      // 反向 ref · 架构不变式："每个 object 归属一个 assembly"
  };
  if (op.rotation) entry.rotation = op.rotation;
  if (op.zone) entry.zone = op.zone;
  scene.objects.push(entry);
  // Phase 3.L · 自动建 single_object assembly · 保证 procedural renderer 看得见
  const asmEntry = {
    id: asmId,
    type: op.type,
    pos: [...entry.pos],
    rotation: entry.rotation || [0, 0, 0],
    size: [...entry.size],
    part_ids: [id],
    primary_part_id: id,
    material_id_primary: entry.material_id,
    label_en: entry.label_en,
    label_zh: entry.label_zh,
    _generated_by: "manual",
  };
  if (op.zone) asmEntry.zone = op.zone;
  scene.assemblies.push(asmEntry);
  return { ok: true, before: null, after: clone(entry) };
}

function nextAssemblyId(scene, type) {
  const prefix = `asm_${type}`;
  const existing = (scene.assemblies || [])
    .map(a => a.id || "")
    .filter(id => id.startsWith(prefix + "_"));
  let n = existing.length + 1;
  while (existing.some(id => id === `${prefix}_${n}`)) n++;
  return `${prefix}_${n}`;
}

// ───────── Assembly ops · Phase 3 ─────────
// 作用于"逻辑家具"级别：一把椅子 = assembly；内部 parts 跟随
// move / rotate 需要同步更新 parts 的 pos / rotation（delta 传递给每个 part）

function _assemblyFind(scene, idOrQuery) {
  return findAssembly(scene, idOrQuery);
}

function opMoveAssembly(scene, op) {
  const asm = _assemblyFind(scene, op.id || op.id_or_name);
  if (!asm) return { ok: false, reason: `assembly not found: ${op.id || op.id_or_name}` };
  let newPos;
  let delta;
  if (Array.isArray(op.pos) && op.pos.length === 3) {
    newPos = op.pos.map(v => Math.round(v * 1000) / 1000);
    delta = newPos.map((v, i) => v - asm.pos[i]);
  } else if (Array.isArray(op.delta) && op.delta.length === 3) {
    delta = op.delta;
    newPos = asm.pos.map((v, i) => Math.round((v + delta[i]) * 1000) / 1000);
  } else {
    return { ok: false, reason: "need pos or delta [x,y,z]" };
  }
  // Phase 3.M · 碰撞检测（排除自身）
  const otherAssemblies = { ...scene, assemblies: (scene.assemblies || []).filter(a => a.id !== asm.id) };
  const collision = _findCollision(otherAssemblies, newPos, asm.size || [0.5, 0.5, 0.5]);
  if (collision) {
    return {
      ok: false,
      reason: `移动目标位置冲突：与 ${collision.asm.label_zh || collision.asm.id} 重叠 · 换个位置`,
    };
  }
  const before = { pos: [...asm.pos], parts: (asm.part_ids || []).map(pid => {
    const p = (scene.objects || []).find(o => o.id === pid);
    return p ? { id: pid, pos: [...p.pos] } : null;
  }).filter(Boolean) };

  asm.pos = newPos;
  // 同步所有 parts 的 pos（加 delta）
  for (const pid of asm.part_ids || []) {
    const p = (scene.objects || []).find(o => o.id === pid);
    if (p) p.pos = p.pos.map((v, i) => Math.round((v + delta[i]) * 1000) / 1000);
  }
  return { ok: true, before, after: { pos: asm.pos, delta, parts_moved: (asm.part_ids || []).length } };
}

function opRotateAssembly(scene, op) {
  const asm = _assemblyFind(scene, op.id || op.id_or_name);
  if (!asm) return { ok: false, reason: `assembly not found: ${op.id || op.id_or_name}` };
  if (!Array.isArray(op.rotation) || op.rotation.length !== 3) {
    return { ok: false, reason: "rotation must be [rx, ry, rz] degrees" };
  }
  const newRot = op.rotation.map(v => Math.round(v * 1000) / 1000);
  const before = { rotation: asm.rotation ? [...asm.rotation] : [0, 0, 0] };
  asm.rotation = newRot;
  // 注：parts 的 rotation 不联动（procedural 模式下 parts 已 hidden · 不影响；raw 模式以 parts 自己 rotation 为准）
  return { ok: true, before, after: { rotation: newRot } };
}

function opRemoveAssembly(scene, op) {
  const asm = _assemblyFind(scene, op.id || op.id_or_name);
  if (!asm) return { ok: false, reason: `assembly not found: ${op.id || op.id_or_name}` };
  const before = { assembly: clone(asm), parts: (asm.part_ids || []).map(pid => {
    const p = (scene.objects || []).find(o => o.id === pid);
    return p ? clone(p) : null;
  }).filter(Boolean) };
  const partIdSet = new Set(asm.part_ids || []);
  scene.objects = (scene.objects || []).filter(o => !partIdSet.has(o.id));
  scene.assemblies = (scene.assemblies || []).filter(a => a.id !== asm.id);
  return { ok: true, before, after: null };
}

function opMoveWall(scene, op) {
  const wall = findWall(scene, op.id);
  if (!wall) return { ok: false, reason: `wall not found: ${op.id}` };
  if (op.offset) {
    if (!Array.isArray(op.offset) || op.offset.length !== 3)
      return { ok: false, reason: "offset must be [dx, dy, dz]" };
    const before = { start: [...wall.start], end: [...wall.end] };
    wall.start = wall.start.map((v, i) => Math.round((v + op.offset[i]) * 1000) / 1000);
    wall.end = wall.end.map((v, i) => Math.round((v + op.offset[i]) * 1000) / 1000);
    return { ok: true, before, after: { start: wall.start, end: wall.end } };
  }
  if (!Array.isArray(op.start) || !Array.isArray(op.end))
    return { ok: false, reason: "need start+end or offset" };
  const before = { start: [...wall.start], end: [...wall.end] };
  wall.start = op.start.map(v => Math.round(v * 1000) / 1000);
  wall.end = op.end.map(v => Math.round(v * 1000) / 1000);
  return { ok: true, before, after: { start: wall.start, end: wall.end } };
}

function opResizeWall(scene, op) {
  const wall = findWall(scene, op.id);
  if (!wall) return { ok: false, reason: `wall not found: ${op.id}` };
  const before = { height: wall.height, thickness: wall.thickness };
  if (typeof op.height === "number" && op.height > 0) wall.height = op.height;
  if (typeof op.thickness === "number" && op.thickness > 0) wall.thickness = op.thickness;
  return { ok: true, before, after: { height: wall.height, thickness: wall.thickness } };
}

function opAddOpening(scene, op) {
  const wall = findWall(scene, op.wall_id);
  if (!wall) return { ok: false, reason: `wall not found: ${op.wall_id}` };
  if (!op.type || !["window", "door"].includes(op.type))
    return { ok: false, reason: "type must be 'window' or 'door'" };
  if (typeof op.pos_along !== "number" || typeof op.width !== "number" || typeof op.height !== "number")
    return { ok: false, reason: "add_opening requires pos_along, width, height" };
  // 验证 opening 在墙范围内
  const wallLen = Math.hypot(wall.end[0] - wall.start[0], wall.end[1] - wall.start[1]);
  if (op.pos_along - op.width / 2 < 0 || op.pos_along + op.width / 2 > wallLen) {
    return { ok: false, reason: `opening exceeds wall (wall length=${wallLen.toFixed(2)}m)` };
  }
  wall.openings = wall.openings || [];
  const id = nextOpeningId(wall, op.type);
  const entry = {
    id,
    type: op.type,
    pos_along: op.pos_along,
    width: op.width,
    height: op.height,
    sill: typeof op.sill === "number" ? op.sill : (op.type === "door" ? 0 : 0.9),
  };
  wall.openings.push(entry);
  return { ok: true, before: null, after: clone(entry) };
}

function opRemoveOpening(scene, op) {
  const found = findOpening(scene, op.id);
  if (!found) return { ok: false, reason: `opening not found: ${op.id}` };
  const before = clone(found.opening);
  found.wall.openings = (found.wall.openings || []).filter(o => o.id !== found.opening.id);
  return { ok: true, before, after: null };
}

function opAddLight(scene, op) {
  if (!op.type) return { ok: false, reason: "add_light requires type" };
  scene.lights = scene.lights || [];
  const id = nextLightId(scene, op.type);
  const entry = { id, type: op.type };
  if (op.type === "sun" || op.type === "directional") {
    entry.dir = op.dir || [0, 0, -1];
  } else {
    if (!Array.isArray(op.pos) || op.pos.length !== 3)
      return { ok: false, reason: "add_light requires pos for non-directional lights" };
    entry.pos = op.pos;
  }
  if (typeof op.cct === "number") entry.cct = op.cct;
  if (typeof op.power === "number") {
    entry.power = op.power;
    const factor = { sun: 1.0, area: 0.05, point: 0.5, pendant: 0.8, spot: 0.5, directional: 1.0 }[op.type] || 1.0;
    entry.intensity = Math.round(op.power * factor * 1000) / 1000;
  } else if (typeof op.intensity === "number") {
    entry.intensity = op.intensity;
  }
  if (op.color) entry.color = op.color;
  scene.lights.push(entry);
  return { ok: true, before: null, after: clone(entry) };
}

function opChangeLight(scene, op) {
  const target = findLight(scene, op.id || op.id_or_name);
  if (!target) return { ok: false, reason: `light not found: ${op.id || op.id_or_name}` };
  const targets = Array.isArray(target) ? target : [target];
  const before = targets.map(t => ({
    id: t.id,
    cct: t.cct, power: t.power, intensity: t.intensity,
  }));
  const after = [];
  for (const l of targets) {
    if (typeof op.cct === "number") l.cct = op.cct;
    if (typeof op.power === "number") {
      l.power = op.power;
      const factor = { sun: 1.0, area: 0.05, point: 0.5, pendant: 0.8, spot: 0.5, directional: 1.0 }[l.type] || 1.0;
      l.intensity = Math.round(op.power * factor * 1000) / 1000;
    }
    if (typeof op.intensity_scale === "number") {
      l.intensity = Math.round((l.intensity || 1.0) * op.intensity_scale * 1000) / 1000;
    }
    after.push({ id: l.id, cct: l.cct, power: l.power, intensity: l.intensity });
  }
  return { ok: true, before, after };
}

function opRemoveLight(scene, op) {
  const target = findLight(scene, op.id || op.id_or_name);
  if (!target) return { ok: false, reason: `light not found: ${op.id || op.id_or_name}` };
  const targets = Array.isArray(target) ? target : [target];
  const before = targets.map(t => clone(t));
  const ids = new Set(targets.map(t => t.id));
  scene.lights = (scene.lights || []).filter(l => !ids.has(l.id));
  return { ok: true, before, after: null };
}

function opChangeMaterial(scene, op) {
  // inline material
  let mat_id = op.material_id;
  if (!mat_id && op.material) {
    mat_id = nextInlineMaterialId(scene);
    scene.materials = scene.materials || {};
    scene.materials[mat_id] = { roughness: 0.8, metallic: 0.0, ...op.material };
  }
  if (!mat_id && op.base_color) {
    mat_id = nextInlineMaterialId(scene);
    scene.materials = scene.materials || {};
    scene.materials[mat_id] = {
      base_color: op.base_color,
      roughness: op.roughness ?? 0.8,
      metallic: op.metallic ?? 0.0,
      label: `inline ${op.base_color}`,
    };
  }
  if (!mat_id) return { ok: false, reason: "need material_id or base_color or material" };
  if (!scene.materials?.[mat_id]) return { ok: false, reason: `unknown material_id: ${mat_id}` };

  const target = op.target;
  if (!target) return { ok: false, reason: "change_material requires target" };

  // 4 种 target
  if (target === "floor") {
    if (!scene.floor) scene.floor = { thickness: 0.02, material_id: "default" };
    const before = { material_id: scene.floor.material_id };
    scene.floor.material_id = mat_id;
    return { ok: true, before, after: { material_id: mat_id } };
  }
  if (target === "ceiling") {
    if (!scene.ceiling) scene.ceiling = { material_id: "default", height: scene.bounds?.h || 2.8 };
    const before = { material_id: scene.ceiling.material_id };
    scene.ceiling.material_id = mat_id;
    return { ok: true, before, after: { material_id: mat_id } };
  }
  // wall
  const wall = findWall(scene, target);
  if (wall) {
    const before = { material_id: wall.material_id };
    wall.material_id = mat_id;
    return { ok: true, before, after: { material_id: mat_id } };
  }
  // object
  const obj = findObject(scene, target);
  if (obj) {
    const before = { material_id: obj.material_id };
    obj.material_id = mat_id;
    return { ok: true, before, after: { material_id: mat_id } };
  }
  return { ok: false, reason: `target not found: ${target}` };
}

// ───────── dispatcher ─────────

const OPS = {
  move_object: opMoveObject,
  rotate_object: opRotateObject,
  resize_object: opResizeObject,
  remove_object: opRemoveObject,
  add_object: opAddObject,
  // Phase 3 · assembly 级 ops（作用于"逻辑家具" · parts 跟随）
  move_assembly: opMoveAssembly,
  rotate_assembly: opRotateAssembly,
  remove_assembly: opRemoveAssembly,
  // wall / opening / light / material
  move_wall: opMoveWall,
  resize_wall: opResizeWall,
  add_opening: opAddOpening,
  remove_opening: opRemoveOpening,
  add_light: opAddLight,
  change_light: opChangeLight,
  remove_light: opRemoveLight,
  change_material: opChangeMaterial,
};

export function listOps() {
  return Object.keys(OPS);
}

// ───────── derived 重算 ─────────

function polygonArea(points) {
  // 2D shoelace formula · points: [[x,y], ...]
  let a = 0;
  for (let i = 0; i < points.length; i++) {
    const [x1, y1] = points[i];
    const [x2, y2] = points[(i + 1) % points.length];
    a += x1 * y2 - x2 * y1;
  }
  return Math.abs(a) / 2;
}

export function computeDerived(scene) {
  const walls = scene.walls || [];
  const objects = scene.objects || [];
  const lights = scene.lights || [];

  // perimeter · wall 长度总和
  let perimeter = 0;
  const xs = [], ys = [];
  for (const w of walls) {
    const dx = w.end[0] - w.start[0], dy = w.end[1] - w.start[1];
    perimeter += Math.hypot(dx, dy);
    xs.push(w.start[0], w.end[0]);
    ys.push(w.start[1], w.end[1]);
  }

  // area · 尝试多边形面积（如果墙首尾相连）· 否则 bounds 长 × 宽
  let area = 0;
  if (walls.length >= 3) {
    // 简化：取 walls 端点的凸/AABB 面积兜底
    const minX = Math.min(...xs), maxX = Math.max(...xs);
    const minY = Math.min(...ys), maxY = Math.max(...ys);
    area = (maxX - minX) * (maxY - minY);
  } else if (scene.bounds) {
    area = scene.bounds.w * scene.bounds.d;
  }

  return {
    area_m2: Math.round(area * 100) / 100,
    perimeter_m: Math.round(perimeter * 100) / 100,
    object_count: objects.length,
    wall_count: walls.length,
    light_count: lights.length,
  };
}

// ───────── 主入口 ─────────
// 返回 { newScene, applied, rejected, derived }

export function applyOps(scene, ops) {
  if (!scene) throw new Error("scene is required");
  if (!Array.isArray(ops)) throw new Error("ops must be an array");
  const newScene = clone(scene);
  const applied = [];
  const rejected = [];
  for (const op of ops) {
    if (!op || !op.op) {
      rejected.push({ op, reason: "missing op field" });
      continue;
    }
    const fn = OPS[op.op];
    if (!fn) {
      rejected.push({ op, reason: `unknown op: ${op.op}` });
      continue;
    }
    try {
      const r = fn(newScene, op);
      if (r.ok) {
        applied.push({ op, before: r.before, after: r.after });
      } else {
        rejected.push({ op, reason: r.reason });
      }
    } catch (e) {
      rejected.push({ op, reason: `exception: ${e.message}` });
    }
  }
  const derived = computeDerived(newScene);
  return { newScene, applied, rejected, derived };
}

// ───────── human-readable summary for UI ─────────

export function summarizeOp(applied) {
  const { op } = applied;
  switch (op.op) {
    case "move_object":    return `移动 ${op.id || op.id_or_name}`;
    case "rotate_object":  return `旋转 ${op.id || op.id_or_name}`;
    case "resize_object":  return `调整尺寸 ${op.id || op.id_or_name}`;
    case "remove_object":  return `删除 ${op.id || op.id_or_name}`;
    case "add_object":     return `添加 ${op.type}`;
    case "move_wall":      return `移动墙 ${op.id}`;
    case "resize_wall":    return `调整墙 ${op.id}`;
    case "add_opening":    return `加 ${op.type} 到 ${op.wall_id}`;
    case "remove_opening": return `删 opening ${op.id}`;
    case "add_light":      return `加 ${op.type} 灯`;
    case "change_light":   return `改灯光 ${op.id || op.id_or_name}`;
    case "remove_light":   return `删灯 ${op.id || op.id_or_name}`;
    case "change_material":return `改材质 ${op.target}`;
    default:               return op.op;
  }
}
