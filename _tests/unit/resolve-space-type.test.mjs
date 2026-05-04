// JS resolve-space-type 单元测试 · 用 Node 内置 node:test runner（不引入 Vitest 依赖）
// 跑：node --test _tests/unit/resolve-space-type.test.mjs
//
// 跨语言一致性：跟 _build/arctura_mvp/tests/test_resolve_space_type.py 共享 fixture
// (api/_shared/space-type-keywords.json)，关键 case 双端必须返同样结果。

import { test } from "node:test";
import assert from "node:assert/strict";
import { resolveSpaceType, listSpaceTypeEnum } from "../../api/_shared/resolve-space-type.js";

test("enum 全部不会 fallback 到 default", () => {
  for (const stdType of listSpaceTypeEnum()) {
    assert.deepEqual(resolveSpaceType(stdType), [stdType], `${stdType} 应解析到自己`);
  }
});

test("大小写 / 空白鲁棒 · 下划线变空格", () => {
  assert.deepEqual(resolveSpaceType("Office"), ["office"]);
  assert.deepEqual(resolveSpaceType("OFFICE"), ["office"]);
  assert.deepEqual(resolveSpaceType("  cafe  "), ["cafe"]);
  assert.deepEqual(resolveSpaceType("Living_Room"), ["living_room"]);
  assert.deepEqual(resolveSpaceType("living room"), ["living_room"]);
});

test("中文别名命中", () => {
  assert.ok(resolveSpaceType("校长办公室").includes("office"));
  assert.ok(resolveSpaceType("咖啡厅").includes("cafe"));
  assert.ok(resolveSpaceType("书房").includes("study"));
  assert.ok(resolveSpaceType("零售店铺").includes("retail"));
  assert.ok(resolveSpaceType("画廊").includes("gallery"));
  assert.ok(resolveSpaceType("多功能空间").includes("multipurpose"));
});

test("英文别名命中", () => {
  assert.ok(resolveSpaceType("principal office").includes("office"));
  assert.ok(resolveSpaceType("workspace").includes("office"));
  assert.ok(resolveSpaceType("coffee shop").includes("cafe"));
  assert.ok(resolveSpaceType("dental clinic").includes("clinic"));
  assert.ok(resolveSpaceType("co-working").includes("multipurpose"));
});

test("hybrid cafe-office 同时命中两类（今天 bug 的精确 reproduce）", () => {
  const out = resolveSpaceType("hybrid cafe-office");
  assert.ok(out.includes("cafe"));
  assert.ok(out.includes("office"));
  assert.ok(out.indexOf("cafe") < out.indexOf("office"), "cafe 应在 office 前（在文本中位置）");
});

test("showroom cafe → gallery + cafe", () => {
  const out = resolveSpaceType("showroom cafe");
  assert.ok(out.includes("gallery"));
  assert.ok(out.includes("cafe"));
});

test("'校长办公室' 多关键词命中同一标准类型 · 去重", () => {
  // '校长' 命中 office · '办公' 又命中 office · 应去重为 [office]
  assert.deepEqual(resolveSpaceType("校长办公室"), ["office"]);
});

test("兜底情况", () => {
  assert.deepEqual(resolveSpaceType(null), ["default"]);
  assert.deepEqual(resolveSpaceType(undefined), ["default"]);
  assert.deepEqual(resolveSpaceType(""), ["default"]);
  assert.deepEqual(resolveSpaceType("   "), ["default"]);
  assert.deepEqual(resolveSpaceType("completely random gibberish xyz"), ["default"]);
});

test("listSpaceTypeEnum 返 10 个标准类型", () => {
  const e = listSpaceTypeEnum();
  assert.equal(e.length, 10);
  assert.ok(e.includes("multipurpose"));
});

test("词边界 · 防 substring 误命中（Codex 三审 #6）", () => {
  // 'barber' 不该命中 'bar'（dining）
  assert.ok(!resolveSpaceType("barber").includes("dining"),
    "barber 误命中 bar/dining · 词边界失效");
  // 'studio apartment' 不该命中 office（studio 已从 office 关键词移除）
  assert.ok(!resolveSpaceType("studio apartment").includes("office"),
    "studio apartment 误判 office");
  // 'librarian' 不该命中 study（library）
  assert.ok(!resolveSpaceType("librarian").includes("study"));
  // 但 'cocktail bar' 仍应命中 dining（bar 是独立词）
  assert.ok(resolveSpaceType("cocktail bar").includes("dining"));
});
