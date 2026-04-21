// node --test project-space/lib/scene-ops.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import { applyOps, findObject, findWall, computeDerived, listOps } from "./scene-ops.js";

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

test("add_object: new chair gets unique id", () => {
  const r = applyOps(baseScene(), [
    { op: "add_object", type: "chair_standard", pos: [1.5, -1.0, 0.45] },
  ]);
  assert.equal(r.applied.length, 1);
  const added = r.newScene.objects.find(o => o.id?.startsWith("obj_chair_standard"));
  assert.ok(added);
  assert.deepEqual(added.pos, [1.5, -1.0, 0.45]);
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

test("listOps: 13 ops exposed", () => {
  assert.equal(listOps().length, 13);
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
