// node --test project-space/lib/scene-ops.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import { applyOps, findObject, findWall, findAssembly, findAssemblyByObjectId, computeDerived, listOps } from "./scene-ops.js";

const baseScene = () => ({
  schema_version: "1.0",
  unit: "m",
  bounds: { w: 5, d: 4, h: 2.8 },
  walls: [
    { id: "wall_N", name: "BackWall",
      start: [-2.5, 2.0, 0], end: [2.5, 2.0, 0],
      height: 2.8, thickness: 0.1, material_id: "wall" },
    { id: "wall_W", name: "LeftWall",
      start: [-2.5, -2.0, 0], end: [-2.5, 2.0, 0],
      height: 2.8, thickness: 0.1, material_id: "wall" },
  ],
  floor: { material_id: "floor", thickness: 0.02 },
  objects: [
    { id: "obj_desk", type: "desk_standard",
      pos: [-1.4, -0.5, 0.75], size: [1.4, 0.7, 0.02],
      material_id: "wood", label_en: "Desk", label_zh: "书桌" },
    { id: "obj_chair", type: "chair_standard",
      pos: [-1.4, -1.0, 0.45], size: [0.5, 0.5, 0.05],
      material_id: "charcoal", label_en: "Chair", label_zh: "办公椅" },
    { id: "obj_closet", type: "closet_tall",
      pos: [2.0, 1.5, 1.0], size: [0.6, 0.35, 2.0],
      material_id: "wood", label_en: "Closet", label_zh: "衣柜" },
  ],
  lights: [
    { id: "pendant_1", type: "pendant", pos: [0, 0, 2.5],
      cct: 3000, power: 60, intensity: 48 },
  ],
  materials: {
    wall: { base_color: "#F5F1E8", roughness: 0.9, metallic: 0 },
    floor: { base_color: "#8B6F47", roughness: 0.6, metallic: 0 },
    wood: { base_color: "#8B6F47", roughness: 0.6, metallic: 0 },
    charcoal: { base_color: "#2C3539", roughness: 0.6, metallic: 0 },
  },
});

// ───────── fuzzy match ─────────

test("findObject: exact id / bare name / zh label / en label / type", () => {
  const s = baseScene();
  assert.equal(findObject(s, "obj_closet")?.id, "obj_closet");
  assert.equal(findObject(s, "closet")?.id, "obj_closet");          // bare
  assert.equal(findObject(s, "衣柜")?.id, "obj_closet");            // zh label
  assert.equal(findObject(s, "Closet")?.id, "obj_closet");          // en label
  assert.equal(findObject(s, "closet_tall")?.id, "obj_closet");     // type
  assert.equal(findObject(s, "nonexistent"), null);
});

test("findWall: id / bare / name fuzzy", () => {
  const s = baseScene();
  assert.equal(findWall(s, "wall_N")?.id, "wall_N");
  assert.equal(findWall(s, "N")?.id, "wall_N");
  assert.equal(findWall(s, "BackWall")?.id, "wall_N");
  assert.equal(findWall(s, "back")?.id, "wall_N");  // contains
});

// ───────── OP tests ─────────

test("move_object: closet 往左移 30cm (absolute pos)", () => {
  const r = applyOps(baseScene(), [
    { op: "move_object", id: "obj_closet", pos: [1.7, 1.5, 1.0] },
  ]);
  assert.equal(r.applied.length, 1);
  assert.equal(r.rejected.length, 0);
  assert.deepEqual(r.newScene.objects.find(o => o.id === "obj_closet").pos, [1.7, 1.5, 1.0]);
});

test("move_object: fuzzy id by zh label", () => {
  const r = applyOps(baseScene(), [
    { op: "move_object", id: "衣柜", pos: [1.0, 1.0, 1.0] },
  ]);
  assert.equal(r.applied.length, 1);
  assert.deepEqual(r.newScene.objects.find(o => o.id === "obj_closet").pos, [1.0, 1.0, 1.0]);
});

test("move_object: missing target → rejected", () => {
  const r = applyOps(baseScene(), [
    { op: "move_object", id: "obj_ghost", pos: [0, 0, 0] },
  ]);
  assert.equal(r.applied.length, 0);
  assert.equal(r.rejected.length, 1);
  assert.match(r.rejected[0].reason, /not found/);
});

test("remove_object: desk removed", () => {
  const r = applyOps(baseScene(), [{ op: "remove_object", id: "obj_desk" }]);
  assert.equal(r.applied.length, 1);
  assert.equal(r.newScene.objects.length, 2);
  assert.equal(r.newScene.objects.find(o => o.id === "obj_desk"), undefined);
});

test("add_object: new chair gets unique id + auto assembly (Phase 3.L invariant)", () => {
  const r = applyOps(baseScene(), [
    { op: "add_object", type: "chair_standard", pos: [1.5, -1.0, 0.45] },
  ]);
  assert.equal(r.applied.length, 1);
  const added = r.newScene.objects.find(o => o.id?.startsWith("obj_chair_standard"));
  assert.ok(added);
  assert.deepEqual(added.pos, [1.5, -1.0, 0.45]);
  // 关键不变式：每个 object 有 assembly_id + scene.assemblies 有对应 entry
  assert.ok(added.assembly_id, "new object should have assembly_id");
  const asm = (r.newScene.assemblies || []).find(a => a.id === added.assembly_id);
  assert.ok(asm, "corresponding assembly should exist");
  assert.deepEqual(asm.part_ids, [added.id], "assembly.part_ids should reference object");
  assert.equal(asm.primary_part_id, added.id);
  assert.equal(asm._generated_by, "manual");
});

test("add_object: AABB collision with existing assembly → rejected (防两家具穿模)", () => {
  const scene = sceneWithAssembly();   // has asm_chair_1 at [-1.4, -1.0, 0] size [0.5, 0.55, 0.85]
  const r = applyOps(scene, [
    { op: "add_object", type: "chair_standard", pos: [-1.4, -1.0, 0.4], size: [0.5, 0.5, 0.9] },
  ]);
  assert.equal(r.applied.length, 0);
  assert.equal(r.rejected.length, 1);
  assert.match(r.rejected[0].reason, /位置冲突|重叠/);
});

test("add_object: far enough → accepted (边界贴但没显著重叠)", () => {
  const scene = sceneWithAssembly();
  const r = applyOps(scene, [
    { op: "add_object", type: "chair_standard", pos: [2.0, -1.5, 0], size: [0.5, 0.5, 0.9] },
  ]);
  assert.equal(r.applied.length, 1);
});

test("move_assembly: collision check handles self-exclusion", () => {
  const scene = sceneWithAssembly();
  // 自己不跟自己冲突 · 移到稍微偏移的位置应该 OK
  const r = applyOps(scene, [
    { op: "move_assembly", id: "asm_chair_1", pos: [0, 0, 0] },
  ]);
  assert.equal(r.applied.length, 1, "moving assembly to free position should succeed");
});

test("add_object then remove_assembly: cascade removes auto-created assembly + object", () => {
  const scene = baseScene();
  // 先 add
  const r1 = applyOps(scene, [{ op: "add_object", type: "chair_standard", pos: [0, 0, 0] }]);
  const newAsmId = r1.newScene.assemblies[r1.newScene.assemblies.length - 1].id;
  const newObjId = r1.newScene.objects[r1.newScene.objects.length - 1].id;
  // 再 remove assembly
  const r2 = applyOps(r1.newScene, [{ op: "remove_assembly", id: newAsmId }]);
  assert.equal(r2.applied.length, 1);
  assert.equal(r2.newScene.objects.find(o => o.id === newObjId), undefined, "object removed too");
  assert.equal(r2.newScene.assemblies.find(a => a.id === newAsmId), undefined, "assembly removed");
});

test("add_object: missing type → rejected", () => {
  const r = applyOps(baseScene(), [{ op: "add_object", pos: [0, 0, 0] }]);
  assert.equal(r.rejected.length, 1);
});

test("resize_object: size must be positive", () => {
  const r = applyOps(baseScene(), [
    { op: "resize_object", id: "obj_desk", size: [1.6, 0, 0.02] },
  ]);
  assert.equal(r.rejected.length, 1);
});

test("rotate_object: 90 degrees", () => {
  const r = applyOps(baseScene(), [
    { op: "rotate_object", id: "obj_desk", rotation: [0, 0, 90] },
  ]);
  assert.equal(r.applied.length, 1);
  assert.deepEqual(r.newScene.objects.find(o => o.id === "obj_desk").rotation, [0, 0, 90]);
});

test("move_wall: offset [dx, dy, 0]", () => {
  const r = applyOps(baseScene(), [
    { op: "move_wall", id: "wall_N", offset: [0, -0.5, 0] },
  ]);
  assert.equal(r.applied.length, 1);
  const w = r.newScene.walls.find(w => w.id === "wall_N");
  assert.equal(w.start[1], 1.5);
  assert.equal(w.end[1], 1.5);
});

test("resize_wall: height 3.2", () => {
  const r = applyOps(baseScene(), [
    { op: "resize_wall", id: "wall_N", height: 3.2 },
  ]);
  assert.equal(r.applied.length, 1);
  assert.equal(r.newScene.walls.find(w => w.id === "wall_N").height, 3.2);
});

test("add_opening: window on wall_N", () => {
  const r = applyOps(baseScene(), [
    { op: "add_opening", wall_id: "wall_N", type: "window",
      pos_along: 2.5, width: 1.5, height: 1.5, sill: 0.9 },
  ]);
  assert.equal(r.applied.length, 1);
  const w = r.newScene.walls.find(w => w.id === "wall_N");
  assert.equal(w.openings.length, 1);
  assert.equal(w.openings[0].type, "window");
});

test("add_opening: exceeds wall bounds → rejected", () => {
  const r = applyOps(baseScene(), [
    { op: "add_opening", wall_id: "wall_N", type: "window",
      pos_along: 4.9, width: 1.5, height: 1.5 },
  ]);
  assert.equal(r.rejected.length, 1);
  assert.match(r.rejected[0].reason, /exceeds wall/);
});

test("remove_opening: removes by id", () => {
  const r = applyOps(baseScene(), [
    { op: "add_opening", wall_id: "wall_N", type: "window",
      pos_along: 2.5, width: 1.5, height: 1.5 },
    { op: "remove_opening", id: "win_N_1" },
  ]);
  assert.equal(r.applied.length, 2);
  const w = r.newScene.walls.find(w => w.id === "wall_N");
  assert.equal(w.openings.length, 0);
});

test("add_light: pendant with cct + power", () => {
  const r = applyOps(baseScene(), [
    { op: "add_light", type: "pendant", pos: [0, 0, 2.5], cct: 2700, power: 80 },
  ]);
  assert.equal(r.applied.length, 1);
  // baseline has pendant_1 · new one should be pendant_2
  const added = r.newScene.lights.find(l => l.id === "pendant_2");
  assert.ok(added, "new light should be pendant_2");
  assert.equal(added.cct, 2700);
  assert.equal(added.power, 80);
  assert.ok(added.intensity > 0);
  assert.equal(r.newScene.lights.length, 2);
});

test("change_light: warm all lights", () => {
  const r = applyOps(baseScene(), [
    { op: "change_light", id_or_name: "all", cct: 2700 },
  ]);
  assert.equal(r.applied.length, 1);
  assert.equal(r.newScene.lights[0].cct, 2700);
});

test("change_material: inline base_color generates new material_id", () => {
  const r = applyOps(baseScene(), [
    { op: "change_material", target: "wall_N", base_color: "#E8DCC8" },
  ]);
  assert.equal(r.applied.length, 1);
  const w = r.newScene.walls.find(w => w.id === "wall_N");
  assert.ok(w.material_id.startsWith("mat_inline_"));
  assert.equal(r.newScene.materials[w.material_id].base_color, "#E8DCC8");
});

test("change_material: target=floor", () => {
  const r = applyOps(baseScene(), [
    { op: "change_material", target: "floor", material_id: "wood" },
  ]);
  assert.equal(r.applied.length, 1);
  assert.equal(r.newScene.floor.material_id, "wood");
});

test("change_material: unknown material_id → rejected", () => {
  const r = applyOps(baseScene(), [
    { op: "change_material", target: "obj_desk", material_id: "missing" },
  ]);
  assert.equal(r.rejected.length, 1);
});

// ───────── batch · 部分成功 ─────────

test("batch: mix ok + rejected doesn't stop later ops", () => {
  const r = applyOps(baseScene(), [
    { op: "move_object", id: "obj_desk", pos: [1, 1, 0.75] },
    { op: "move_object", id: "obj_ghost", pos: [0, 0, 0] },  // rejected
    { op: "remove_object", id: "obj_chair" },
  ]);
  assert.equal(r.applied.length, 2);
  assert.equal(r.rejected.length, 1);
  assert.deepEqual(r.newScene.objects.find(o => o.id === "obj_desk").pos, [1, 1, 0.75]);
  assert.equal(r.newScene.objects.find(o => o.id === "obj_chair"), undefined);
});

test("batch: unknown op rejected but others pass", () => {
  const r = applyOps(baseScene(), [
    { op: "move_object", id: "obj_desk", pos: [0, 0, 0.75] },
    { op: "bogus_op", foo: 1 },
  ]);
  assert.equal(r.applied.length, 1);
  assert.equal(r.rejected.length, 1);
  assert.match(r.rejected[0].reason, /unknown op/);
});

// ───────── derived ─────────

test("computeDerived: baseline counts", () => {
  const d = computeDerived(baseScene());
  assert.equal(d.object_count, 3);
  assert.equal(d.wall_count, 2);
  assert.equal(d.light_count, 1);
  assert.ok(d.area_m2 > 0);
  assert.ok(d.perimeter_m > 0);
});

test("derived: remove_object decrements object_count", () => {
  const r = applyOps(baseScene(), [{ op: "remove_object", id: "obj_desk" }]);
  assert.equal(r.derived.object_count, 2);
});

test("listOps: 16 ops exposed (13 base + 3 assembly · Phase 3)", () => {
  const ops = listOps();
  assert.equal(ops.length, 16);
  assert.ok(ops.includes("move_assembly"));
  assert.ok(ops.includes("remove_assembly"));
  assert.ok(ops.includes("rotate_assembly"));
});

// ───────── Assembly ops (Phase 3) ─────────

const sceneWithAssembly = () => ({
  schema_version: "1.0",
  unit: "m",
  bounds: { w: 5, d: 4, h: 2.8 },
  walls: [],
  objects: [
    { id: "obj_chair",     type: "chair_standard", pos: [-1.4, -1.0, 0.45], size: [0.5, 0.5, 0.05],
      material_id: "charcoal", label_zh: "办公椅", assembly_id: "asm_chair_1" },
    { id: "obj_chairback", type: "custom",         pos: [-1.4, -1.25, 0.75], size: [0.5, 0.06, 0.6],
      material_id: "charcoal", label_zh: "椅背",   assembly_id: "asm_chair_1" },
    { id: "obj_laptop",    type: "custom",         pos: [-1.4, -0.5, 0.78], size: [0.3, 0.2, 0.02],
      material_id: "screen", label_zh: "笔记本",  assembly_id: "asm_single_2" },
  ],
  assemblies: [
    { id: "asm_chair_1", type: "chair_standard", pos: [-1.4, -1.0, 0],
      part_ids: ["obj_chair", "obj_chairback"], primary_part_id: "obj_chair",
      size: [0.5, 0.55, 0.85], material_id_primary: "charcoal",
      label_zh: "办公椅", _generated_by: "naming_regex" },
    { id: "asm_single_2", type: "custom", pos: [-1.4, -0.5, 0.78],
      part_ids: ["obj_laptop"], primary_part_id: "obj_laptop",
      size: [0.3, 0.2, 0.02], material_id_primary: "screen",
      label_zh: "笔记本", _generated_by: "single_object" },
  ],
  lights: [],
  materials: { charcoal: { base_color: "#2C3539" }, screen: { base_color: "#0D1017" } },
});

test("findAssembly: by id / zh label / type", () => {
  const s = sceneWithAssembly();
  assert.equal(findAssembly(s, "asm_chair_1")?.id, "asm_chair_1");
  assert.equal(findAssembly(s, "办公椅")?.id, "asm_chair_1");
  assert.equal(findAssembly(s, "chair_standard")?.id, "asm_chair_1");
  assert.equal(findAssembly(s, "ghost"), null);
});

test("findAssembly: 中文同义词 · 衣柜 → closet_tall · 椅子 → chair_standard", () => {
  const s = {
    schema_version: "1.0", unit: "m", bounds: { w: 5, d: 4, h: 2.8 },
    walls: [], lights: [], materials: {default:{base_color:"#CCC"}},
    objects: [
      { id: "obj_cabinet", type: "closet_tall", pos: [2, 1.5, 1], size: [0.6, 0.35, 2], material_id: "default", label_zh: "收纳柜" },
      { id: "obj_chair", type: "chair_standard", pos: [0, 0, 0.4], size: [0.5, 0.5, 0.05], material_id: "default", label_zh: "办公椅" },
    ],
    assemblies: [
      { id: "asm_closet", type: "closet_tall", pos: [2, 1.5, 0], size: [0.6, 0.35, 2],
        part_ids: ["obj_cabinet"], primary_part_id: "obj_cabinet", label_zh: "收纳柜" },
      { id: "asm_chair", type: "chair_standard", pos: [0, 0, 0], size: [0.5, 0.5, 0.85],
        part_ids: ["obj_chair"], primary_part_id: "obj_chair", label_zh: "办公椅" },
    ],
  };
  // 用户说"衣柜" · label_zh 是"收纳柜" · 但同义词映射到 closet_tall → 命中 asm_closet
  assert.equal(findAssembly(s, "衣柜")?.id, "asm_closet");
  assert.equal(findAssembly(s, "橱柜")?.id, "asm_closet");
  assert.equal(findAssembly(s, "椅子")?.id, "asm_chair");
});

test("findAssemblyByObjectId: back-ref resolution", () => {
  const s = sceneWithAssembly();
  assert.equal(findAssemblyByObjectId(s, "obj_chairback")?.id, "asm_chair_1");
  assert.equal(findAssemblyByObjectId(s, "obj_laptop")?.id, "asm_single_2");
  assert.equal(findAssemblyByObjectId(s, "obj_ghost"), null);
});

test("move_assembly: pos → parts follow with delta", () => {
  const r = applyOps(sceneWithAssembly(), [
    { op: "move_assembly", id: "asm_chair_1", pos: [0, 0, 0] },
  ]);
  assert.equal(r.applied.length, 1);
  const ns = r.newScene;
  const asm = ns.assemblies.find(a => a.id === "asm_chair_1");
  assert.deepEqual(asm.pos, [0, 0, 0]);
  // parts should have moved by delta [+1.4, +1.0, -0]
  const chair = ns.objects.find(o => o.id === "obj_chair");
  const back  = ns.objects.find(o => o.id === "obj_chairback");
  assert.deepEqual(chair.pos, [0, 0, 0.45]);
  assert.deepEqual(back.pos, [0, -0.25, 0.75]);
  // Other assembly's parts untouched
  const lap = ns.objects.find(o => o.id === "obj_laptop");
  assert.deepEqual(lap.pos, [-1.4, -0.5, 0.78]);
});

test("move_assembly: delta variant", () => {
  const r = applyOps(sceneWithAssembly(), [
    { op: "move_assembly", id: "asm_chair_1", delta: [0.5, 0, 0] },
  ]);
  assert.equal(r.applied.length, 1);
  const asm = r.newScene.assemblies.find(a => a.id === "asm_chair_1");
  assert.equal(asm.pos[0], -0.9);
  const chair = r.newScene.objects.find(o => o.id === "obj_chair");
  assert.equal(chair.pos[0], -0.9);
});

test("move_assembly: fuzzy id by zh label", () => {
  const r = applyOps(sceneWithAssembly(), [
    { op: "move_assembly", id: "办公椅", pos: [1, 1, 0] },
  ]);
  assert.equal(r.applied.length, 1);
});

test("move_assembly: missing → rejected, no mutation", () => {
  const s = sceneWithAssembly();
  const before = JSON.stringify(s);
  const r = applyOps(s, [{ op: "move_assembly", id: "ghost", pos: [0, 0, 0] }]);
  assert.equal(r.rejected.length, 1);
  assert.equal(JSON.stringify(s), before, "original scene untouched");
});

test("remove_assembly: cascades delete to all parts", () => {
  const r = applyOps(sceneWithAssembly(), [
    { op: "remove_assembly", id: "asm_chair_1" },
  ]);
  assert.equal(r.applied.length, 1);
  const ns = r.newScene;
  assert.equal(ns.assemblies.length, 1);
  assert.equal(ns.assemblies[0].id, "asm_single_2");
  // Both parts gone
  assert.equal(ns.objects.find(o => o.id === "obj_chair"), undefined);
  assert.equal(ns.objects.find(o => o.id === "obj_chairback"), undefined);
  assert.equal(ns.objects.length, 1);  // only laptop remains
});

test("rotate_assembly: updates rotation (parts unchanged · procedural handles render)", () => {
  const r = applyOps(sceneWithAssembly(), [
    { op: "rotate_assembly", id: "asm_chair_1", rotation: [0, 0, 90] },
  ]);
  assert.equal(r.applied.length, 1);
  const asm = r.newScene.assemblies.find(a => a.id === "asm_chair_1");
  assert.deepEqual(asm.rotation, [0, 0, 90]);
});

test("assembly ops: derived counts untouched (assemblies not in derived)", () => {
  const r = applyOps(sceneWithAssembly(), [
    { op: "remove_assembly", id: "asm_single_2" },
  ]);
  // laptop got removed as part of assembly · object_count drops
  assert.equal(r.derived.object_count, 2);
});

// ───────── invariant: original scene not mutated ─────────

test("immutability: input scene not mutated", () => {
  const s = baseScene();
  const before = JSON.stringify(s);
  applyOps(s, [
    { op: "move_object", id: "obj_desk", pos: [9, 9, 9] },
    { op: "remove_object", id: "obj_chair" },
  ]);
  assert.equal(JSON.stringify(s), before);
});
