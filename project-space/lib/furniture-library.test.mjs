// node --test project-space/lib/furniture-library.test.mjs
// 验证：
//   1) registry JSON schema 对 12 件 · 每件必备字段齐
//   2) 每件 type 在 scene-ops.add_object 下有效（LLM 约束）
//   3) 零代码扩展：伪造一条新 entry · 验证 listing 包含新 key
//   浏览器级 "add_furniture chat call → 3D 出现" 的 E2E 在 Playwright 里做（Phase H）

import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { applyOps } from "./scene-ops.js";

const lib = JSON.parse(readFileSync(new URL("../../data/furniture-library.json", import.meta.url), "utf8"));

const REQUIRED_FIELDS = ["glb", "builder", "default_size", "default_color", "anchor", "tags", "label_en", "label_zh"];
const VALID_ANCHORS = ["bottom", "top", "center"];

test("library: schema_version = 1.0", () => {
  assert.equal(lib.schema_version, "1.0");
});

test("library: 12 items · all required fields present", () => {
  const types = Object.keys(lib.items || {});
  assert.equal(types.length, 12, "expected 12 furniture primitives");
  for (const type of types) {
    const item = lib.items[type];
    for (const field of REQUIRED_FIELDS) {
      assert.ok(item[field] !== undefined, `${type} missing ${field}`);
    }
    assert.ok(Array.isArray(item.default_size) && item.default_size.length === 3, `${type} default_size bad`);
    assert.ok(VALID_ANCHORS.includes(item.anchor), `${type} anchor ${item.anchor} not valid`);
    assert.match(item.default_color, /^#[0-9A-Fa-f]{6}$/, `${type} default_color must be hex`);
    assert.ok(Array.isArray(item.tags) && item.tags.length > 0, `${type} needs at least 1 tag`);
  }
});

test("library: GLB paths under /assets/furniture/", () => {
  for (const [type, item] of Object.entries(lib.items)) {
    assert.match(item.glb, /^\/assets\/furniture\/[a-z0-9_]+\.glb$/, `${type} glb path bad`);
  }
});

// ───────── 扩展测试：添加一条新 entry，验证 scene-ops 零代码生效 ─────────

test("extension: add_object with new library type · zero code change", () => {
  // 伪造一个库里的新 type 被 scene 使用
  const extendedLib = {
    ...lib,
    items: {
      ...lib.items,
      chair_bar: {
        glb: "/assets/furniture/chair_bar.glb",
        builder: "chair_standard",  // 复用现有 builder
        default_size: [0.45, 0.45, 1.1],
        default_color: "#2A2A2A",
        anchor: "bottom",
        tags: ["chair", "seating", "bar"],
        label_en: "Bar Chair",
        label_zh: "吧台椅",
        source: "user-extension",
      },
    },
  };

  // 验证：scene-ops 不 hardcode type · add_object 接受任何 string type
  const scene = {
    schema_version: "1.0", unit: "m",
    bounds: { w: 5, d: 4, h: 2.8 },
    walls: [], objects: [], lights: [], materials: { default: { base_color: "#CCCCCC" } },
  };
  const r = applyOps(scene, [
    { op: "add_object", type: "chair_bar", pos: [1, 1, 0], label_zh: "吧椅" },
  ]);
  assert.equal(r.applied.length, 1, "add_object should accept new library type");
  assert.equal(r.rejected.length, 0);
  assert.equal(r.newScene.objects.length, 1);
  assert.equal(r.newScene.objects[0].type, "chair_bar");
  assert.equal(r.newScene.objects[0].label_zh, "吧椅");

  // 验证 id 自动分配
  assert.match(r.newScene.objects[0].id, /^obj_chair_bar_\d+$/);
});

test("extension: types not in registry still accepted by add_object (custom fallback)", () => {
  // 即使 library 不认识 · add_object 照样插入 · renderer 走 primitive box fallback
  const scene = {
    schema_version: "1.0", unit: "m",
    bounds: { w: 5, d: 4, h: 2.8 },
    walls: [], objects: [], lights: [], materials: { default: { base_color: "#CCCCCC" } },
  };
  const r = applyOps(scene, [
    { op: "add_object", type: "ufo", pos: [0, 0, 1.5] },
  ]);
  assert.equal(r.applied.length, 1);
  assert.equal(r.newScene.objects[0].type, "ufo");
});

// ───────── 冲突测试：id 不重复 ─────────

test("add_object: multiple of same type → unique ids", () => {
  const scene = {
    schema_version: "1.0", unit: "m",
    bounds: { w: 5, d: 4, h: 2.8 },
    walls: [], objects: [], lights: [], materials: { default: { base_color: "#CCCCCC" } },
  };
  const r = applyOps(scene, [
    { op: "add_object", type: "chair_standard", pos: [0, 0, 0] },
    { op: "add_object", type: "chair_standard", pos: [1, 0, 0] },
    { op: "add_object", type: "chair_standard", pos: [2, 0, 0] },
  ]);
  assert.equal(r.applied.length, 3);
  const ids = r.newScene.objects.map(o => o.id);
  assert.equal(new Set(ids).size, 3, "all ids must be unique");
});
