// Phase 11.4 后审 · 跨语言一致性 · JS 侧测试
// 对应 Python: _build/arctura_mvp/tests/test_cross_lang_overrides.py
//
// 同一份 fixture · 两端跑应用 · 校验同样不变式 · 双绿 = 行为对称
//
// 子智能体审查 #4 / Gemini ADR 审查 #6 都 flag 了这个测试缺。

import { test } from "node:test";
import assert from "node:assert/strict";
import { applyOverridesToScene } from "../../api/_shared/overrides-apply.js";
import fixture from "../../_build/arctura_mvp/tests/fixtures/cross_lang_apply_overrides.json"
  with { type: "json" };

for (const c of fixture.cases) {
  test(`cross-lang JS · ${c.name}`, () => {
    const final = applyOverridesToScene(c.base_scene, c.overrides);
    const inv = c.expected_invariants;

    if ("objects_count" in inv) {
      assert.equal(final.objects.length, inv.objects_count,
        `${c.name}: objects 数不对`);
    }
    if ("objects_contains_id" in inv) {
      const ids = final.objects.map(o => o.id);
      assert.ok(ids.includes(inv.objects_contains_id),
        `${c.name}: objects 缺 ${inv.objects_contains_id}`);
    }
    if ("floor_material" in inv) {
      assert.equal(final.floor?.material_id, inv.floor_material);
    }
    if ("asm_desk_1_pos" in inv) {
      const asm = final.assemblies.find(a => a.id === "asm_desk_1");
      assert.deepEqual(asm?.pos, inv.asm_desk_1_pos);
    }
    if ("asm_real_pos" in inv) {
      const asm = final.assemblies.find(a => a.id === "asm_real");
      assert.deepEqual(asm?.pos, inv.asm_real_pos,
        `${c.name}: orphan 该静默跳过 · pos 被改了`);
    }
    if ("lights_count" in inv) {
      assert.equal(final.lights.length, inv.lights_count);
    }
    if ("sun_1_intensity" in inv) {
      const sun = final.lights.find(l => l.id === "sun_1");
      assert.ok(Math.abs(sun.intensity - inv.sun_1_intensity) < 1e-3);
    }
  });
}

test("JS apply 顺序内部强制 · 倒序 input 跟正序 input 等结果", () => {
  const base = {
    bounds: { w: 5, d: 4, h: 2.8 }, walls: [],
    objects: [{ id: "obj_x", pos: [0, 0, 0] }],
    assemblies: [], lights: [], materials: {}, floor: {}, ceiling: {},
  };
  const reversed = {
    lighting: { _added: [{ id: "new_l", type: "point" }] },
    layout: { o1: { target: "object", target_id: "obj_x", pos: [1, 1, 0] } },
    tombstones: { objects: [] },
  };
  const normal = {
    tombstones: { objects: [] },
    layout: { o1: { target: "object", target_id: "obj_x", pos: [1, 1, 0] } },
    lighting: { _added: [{ id: "new_l", type: "point" }] },
  };
  const s1 = applyOverridesToScene(base, reversed);
  const s2 = applyOverridesToScene(base, normal);
  assert.deepEqual(s1.objects[0].pos, [1, 1, 0]);
  assert.deepEqual(s2.objects[0].pos, [1, 1, 0]);
  assert.equal(s1.lights.length, 1);
  assert.equal(s2.lights.length, 1);
  assert.equal(s1.lights[0].id, "new_l");
  assert.equal(s2.lights[0].id, "new_l");
});
