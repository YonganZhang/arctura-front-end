// node --test project-space/lib/scene-tools.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import { isSceneTool, toolToOps, sceneSummary, SCENE_TOOL_NAMES } from "./scene-tools.js";
import { applyOps } from "./scene-ops.js";

const baseScene = () => ({
  schema_version: "1.0", unit: "m",
  bounds: { w: 5, d: 4, h: 2.8 },
  walls: [
    { id: "wall_N", start: [-2.5, 2, 0], end: [2.5, 2, 0], height: 2.8, thickness: 0.1, material_id: "wall" },
  ],
  objects: [
    { id: "obj_closet", type: "closet_tall", pos: [2.0, 1.5, 1.0], size: [0.6, 0.35, 2.0],
      material_id: "wood", label_en: "Closet", label_zh: "衣柜" },
  ],
  lights: [
    { id: "pendant_1", type: "pendant", pos: [0, 0, 2.5], cct: 3000, power: 60, intensity: 48 },
  ],
  materials: { wall: { base_color: "#F5F1E8" }, wood: { base_color: "#8B6F47" } },
});

test("SCENE_TOOL_NAMES has 13 entries", () => {
  assert.equal(SCENE_TOOL_NAMES.size, 13);
});

test("isSceneTool recognizes names", () => {
  assert.ok(isSceneTool("move_furniture"));
  assert.ok(isSceneTool("add_window"));
  assert.ok(!isSceneTool("set_editable"));      // Phase 1.8
  assert.ok(!isSceneTool("unknown"));
});

test("move_furniture pos_delta · resolves to move_object", () => {
  const r = toolToOps({ name: "move_furniture", args: { id_or_name: "衣柜", pos_delta: [-0.3, 0, 0] } }, baseScene());
  assert.equal(r.ops.length, 1);
  assert.equal(r.ops[0].op, "move_object");
  assert.equal(r.ops[0].id, "obj_closet");
  assert.deepEqual(r.ops[0].pos, [1.7, 1.5, 1.0]);
});

test("move_furniture with rotation · emits 2 ops", () => {
  const r = toolToOps({
    name: "move_furniture",
    args: { id_or_name: "obj_closet", pos_absolute: [1, 1, 1], rotation_deg: [0, 0, 90] },
  }, baseScene());
  assert.equal(r.ops.length, 2);
  assert.equal(r.ops[0].op, "move_object");
  assert.equal(r.ops[1].op, "rotate_object");
});

test("move_furniture with unknown name · rejected", () => {
  const r = toolToOps({ name: "move_furniture", args: { id_or_name: "幽灵", pos_delta: [0, 0, 0] } }, baseScene());
  assert.equal(r.ops.length, 0);
  assert.ok(r.reason);
});

test("remove_furniture by zh label", () => {
  const r = toolToOps({ name: "remove_furniture", args: { id_or_name: "衣柜" } }, baseScene());
  assert.equal(r.ops.length, 1);
  assert.equal(r.ops[0].op, "remove_object");
  assert.equal(r.ops[0].id, "obj_closet");
});

test("add_furniture direct pass-through", () => {
  const r = toolToOps({
    name: "add_furniture",
    args: { type: "chair_standard", pos: [1, 1, 0], label_zh: "新椅" },
  }, baseScene());
  assert.equal(r.ops.length, 1);
  assert.equal(r.ops[0].op, "add_object");
  assert.equal(r.ops[0].type, "chair_standard");
  assert.equal(r.ops[0].label_zh, "新椅");
});

test("change_material with base_color auto-inline", () => {
  const r = toolToOps({
    name: "change_material",
    args: { target: "wall_N", base_color: "#E8DCC8" },
  }, baseScene());
  assert.equal(r.ops.length, 1);
  assert.equal(r.ops[0].target, "wall_N");
  assert.equal(r.ops[0].base_color, "#E8DCC8");
});

test("add_window → add_opening with type=window", () => {
  const r = toolToOps({
    name: "add_window",
    args: { wall_id: "wall_N", pos_along: 2.5, width: 1.5, height: 1.5, sill: 0.9 },
  }, baseScene());
  assert.equal(r.ops.length, 1);
  assert.equal(r.ops[0].op, "add_opening");
  assert.equal(r.ops[0].type, "window");
  assert.equal(r.ops[0].wall_id, "wall_N");
});

test("add_door → add_opening with type=door", () => {
  const r = toolToOps({
    name: "add_door",
    args: { wall_id: "wall_N", pos_along: 1.0, width: 0.9, height: 2.0 },
  }, baseScene());
  assert.equal(r.ops[0].op, "add_opening");
  assert.equal(r.ops[0].type, "door");
});

test("change_light id_or_name='all' pass through", () => {
  const r = toolToOps({ name: "change_light", args: { id_or_name: "all", cct: 2700 } }, baseScene());
  assert.equal(r.ops[0].id_or_name, "all");
  assert.equal(r.ops[0].cct, 2700);
});

// ───────── 端到端：tool → op → scene ─────────

test("e2e: move_furniture tool → applyOps → scene updated", () => {
  const scene = baseScene();
  const r = toolToOps({ name: "move_furniture", args: { id_or_name: "衣柜", pos_delta: [-0.3, 0, 0] } }, scene);
  const result = applyOps(scene, r.ops);
  assert.equal(result.applied.length, 1);
  assert.deepEqual(result.newScene.objects.find(o => o.id === "obj_closet").pos, [1.7, 1.5, 1.0]);
});

// ───────── scene summary ─────────

test("sceneSummary includes objects + walls + lights", () => {
  const s = sceneSummary(baseScene(), ["chair_standard", "desk_standard"]);
  assert.match(s, /衣柜/);
  assert.match(s, /wall_N/);
  assert.match(s, /pendant_1/);
  assert.match(s, /chair_standard/);
});

test("sceneSummary truncates at 40 objects (token guard)", () => {
  const scene = baseScene();
  scene.objects = Array.from({ length: 60 }, (_, i) => ({
    id: `obj_item_${i}`,
    type: "custom",
    pos: [0, 0, 0],
    size: [0.1, 0.1, 0.1],
    material_id: "wood",
    label_en: `Item${i}`,
    label_zh: `物件${i}`,
  }));
  const s = sceneSummary(scene);
  assert.match(s, /\+20 more/);
});
