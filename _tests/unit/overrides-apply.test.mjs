// JS overrides-apply / scene-ops-mapping 单测
// Python 端跨语言对应：_build/arctura_mvp/tests/test_derive.py
// 跑：node --test _tests/unit/overrides-apply.test.mjs

import { test } from "node:test";
import assert from "node:assert/strict";
import { applyOverridesToScene, validateOverrides, NAMESPACES, OVERRIDES_SCHEMA_VERSION }
  from "../../api/_shared/overrides-apply.js";
import { opsToOverridesDelta, mergeOverridesDelta, resetOverrides, SCENE_OPS_COUNT, SCENE_OP_NAMES, namespaceFor }
  from "../../api/_shared/scene-ops-mapping.js";

function baseScene() {
  return {
    bounds: { w: 5, d: 4, h: 2.8 },
    walls: [{ id: "wall_Back" }, { id: "wall_S" }],
    objects: [{ id: "obj_desk_1", pos: [0, 0, 0], material_id: "default" }],
    assemblies: [{ id: "asm_desk_1", part_ids: ["obj_desk_1"], pos: [0, 0, 0], material_id_primary: "default" }],
    lights: [{ id: "sun_1", type: "sun", intensity: 3.0, pos: [0, 0, 0] }],
    materials: { default: { base_color: "#fff" } },
    floor: { material_id: "woodfloor" },
    ceiling: { material_id: "wall" },
  };
}

test("16 个 op 全部有 namespace 映射", () => {
  assert.equal(SCENE_OPS_COUNT, 16);
  for (const op of SCENE_OP_NAMES) {
    assert.ok(namespaceFor(op), `${op} 没 namespace 映射`);
  }
});

test("空 overrides · scene 不变（深拷贝）", () => {
  const s = applyOverridesToScene(baseScene(), {});
  assert.deepEqual(s.objects, baseScene().objects);
  // 验证深拷贝
  s.objects[0].pos[0] = 99;
  assert.equal(baseScene().objects[0].pos[0], 0);
});

test("layout 移动 assembly", () => {
  const s = applyOverridesToScene(baseScene(), {
    layout: { o1: { target: "assembly", target_id: "asm_desk_1", pos: [9, 9, 0] } },
  });
  assert.deepEqual(s.assemblies[0].pos, [9, 9, 0]);
});

test("layout 加新 object · target=added", () => {
  const s = applyOverridesToScene(baseScene(), {
    layout: { o1: { target: "added", payload: { id: "new_chair_x", type: "chair_standard", pos: [1, 1, 0] } } },
  });
  assert.equal(s.objects.length, 2);
  assert.equal(s.objects[1].id, "new_chair_x");
});

test("orphan target_id · 静默跳过 · 不抛", () => {
  const s = applyOverridesToScene(baseScene(), {
    layout: { o1: { target: "assembly", target_id: "asm_does_not_exist", pos: [9, 9, 0] } },
  });
  assert.deepEqual(s.assemblies[0].pos, [0, 0, 0]);
});

test("appearance 改 floor + 内联新建 material", () => {
  const s = applyOverridesToScene(baseScene(), {
    appearance: {
      materials_added: { my_blue: { base_color: "#0033FF" } },
      floor: { material_id: "my_blue" },
    },
  });
  assert.equal(s.materials.my_blue.base_color, "#0033FF");
  assert.equal(s.floor.material_id, "my_blue");
});

test("appearance 改 wall material（按 wall_id）", () => {
  const s = applyOverridesToScene(baseScene(), {
    appearance: { walls: { wall_Back: { material_id: "concrete" } } },
  });
  const wall = s.walls.find(w => w.id === "wall_Back");
  assert.equal(wall.material_id, "concrete");
});

test("tombstones 删除 assembly + 自动清 part_ids", () => {
  const s = applyOverridesToScene(baseScene(), {
    tombstones: { assemblies: ["asm_desk_1"] },
  });
  assert.equal(s.assemblies.length, 0);
});

test("tombstones 删除 object · assembly.part_ids 同步清", () => {
  const s = applyOverridesToScene(baseScene(), {
    tombstones: { objects: ["obj_desk_1"] },
  });
  assert.equal(s.objects.length, 0);
  assert.deepEqual(s.assemblies[0].part_ids, []);
});

test("lighting intensity_scale · 批量缩放", () => {
  const s = applyOverridesToScene(baseScene(), {
    lighting: { sun_1: { intensity_scale: 0.5 } },
  });
  assert.equal(s.lights[0].intensity, 1.5);
});

test("lighting _added · 加新灯", () => {
  const s = applyOverridesToScene(baseScene(), {
    lighting: { _added: [{ id: "new_lamp", type: "point", pos: [1, 1, 2] }] },
  });
  assert.equal(s.lights.length, 2);
  assert.equal(s.lights[1].id, "new_lamp");
});

test("validateOverrides · 未知 namespace 报错", () => {
  const errs = validateOverrides({ unknown_ns: {} });
  assert.ok(errs.some(e => e.includes("unknown namespace")));
});

test("validateOverrides · layout 缺 target_id 报错", () => {
  const errs = validateOverrides({ layout: { o1: { target: "assembly" } } });
  assert.ok(errs.some(e => e.includes("target_id")));
});

test("validateOverrides · target=added 不需要 target_id", () => {
  const errs = validateOverrides({ layout: { o1: { target: "added", payload: { id: "x" } } } });
  assert.deepEqual(errs, []);
});

test("opsToOverridesDelta · 16 op 全 dispatch 不抛", () => {
  // 喂一组 ops · 必须不抛
  const delta = opsToOverridesDelta([
    { type: "move_object", id: "obj_desk_1", pos: [1, 2, 0] },
    { type: "rotate_assembly", id: "asm_desk_1", rotation: [0, 0, 90] },
    { type: "remove_object", id: "obj_x" },
    { type: "remove_assembly", id: "asm_x" },
    { type: "add_object", payload: "minimal" },
    { type: "change_material", target: "floor", material_id: "concrete" },
    { type: "change_light", id: "sun_1", intensity_scale: 0.5 },
    { type: "remove_light", id: "sun_1" },
    { type: "move_wall", id: "wall_Back", start: [0, 0, 0], end: [5, 0, 0] },
    { type: "add_opening", id: "win_1", wall_id: "wall_Back", kind: "window", x: 1, w: 1.5 },
  ]);
  // layout / structural / appearance / lighting / tombstones 都该有
  assert.ok(delta.layout);
  assert.ok(delta.structural);
  assert.ok(delta.appearance);
  assert.ok(delta.lighting);
  assert.ok(delta.tombstones);
  assert.ok(delta.tombstones.objects.includes("obj_x"));
  assert.ok(delta.tombstones.assemblies.includes("asm_x"));
});

test("mergeOverridesDelta · layout 累加 · structural 数组追加 · tombstones 去重", () => {
  const a = {
    layout: { o1: { target: "object", target_id: "x" } },
    tombstones: { objects: ["x", "y"] },
  };
  const b = {
    layout: { o2: { target: "object", target_id: "z" } },
    tombstones: { objects: ["y", "w"] },
  };
  const out = mergeOverridesDelta(a, b);
  assert.equal(Object.keys(out.layout).length, 2);
  assert.deepEqual(out.tombstones.objects.sort(), ["w", "x", "y"]);
});

test("resetOverrides · 按 namespace 清", () => {
  const ov = { layout: { o1: {} }, appearance: { floor: { material_id: "c" } } };
  const r1 = resetOverrides(ov, "layout");
  assert.ok(!r1.layout);
  assert.ok(r1.appearance);
  const r2 = resetOverrides(ov, "all");
  assert.deepEqual(r2, {});
});

test("opsToOverridesDelta · add_object payload unwrap 正确", () => {
  // Codex 三审 #4：原本 `payload:{...op}` 把 type:"add_object" 元数据混进 payload
  // 修后必须 unwrap op.payload 或 op.object · 或剥掉 type
  const d1 = opsToOverridesDelta([
    { type: "add_object", payload: { id: "lamp_x", type: "lamp_floor", pos: [1, 1, 0] } },
  ]);
  const layoutEntry = Object.values(d1.layout)[0];
  assert.equal(layoutEntry.target, "added");
  assert.equal(layoutEntry.payload.id, "lamp_x");
  assert.equal(layoutEntry.payload.type, "lamp_floor");
  assert.ok(!("type" in layoutEntry.payload && layoutEntry.payload.type === "add_object"),
    "payload 含了 op.type='add_object' 元数据 · unwrap 失效");

  // legacy: op 自身就是 object（无 payload 嵌套）
  const d2 = opsToOverridesDelta([
    { type: "add_object", id: "lamp_y", object_type: "lamp_floor", pos: [2, 2, 0] },
  ]);
  const e2 = Object.values(d2.layout)[0];
  assert.equal(e2.target, "added");
  assert.equal(e2.payload.id, "lamp_y");
  assert.ok(!("type" in e2.payload), "legacy 形状下 op.type 应被剥掉");
});

test("end-to-end · 4 ops → delta → apply → scene 反映改动", () => {
  const ops = [
    { type: "move_assembly", id: "asm_desk_1", pos: [3, 3, 0] },
    { type: "change_material", target: "floor", material_id: "concrete" },
    { type: "remove_light", id: "sun_1" },
  ];
  const delta = opsToOverridesDelta(ops);
  const errs = validateOverrides(delta);
  assert.deepEqual(errs, []);
  const final = applyOverridesToScene(baseScene(), delta);
  assert.deepEqual(final.assemblies[0].pos, [3, 3, 0]);
  assert.equal(final.floor.material_id, "concrete");
  assert.equal(final.lights.length, 0);
});

test("OVERRIDES_SCHEMA_VERSION 跟 NAMESPACES 导出", () => {
  assert.equal(OVERRIDES_SCHEMA_VERSION, "v1");
  assert.equal(NAMESPACES.length, 5);
});
