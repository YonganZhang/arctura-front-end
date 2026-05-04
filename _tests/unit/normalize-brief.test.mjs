// API 边界归一化测试 · brief 写入 KV 前 space.type 必须 enum
// 跑：node --test _tests/unit/normalize-brief.test.mjs

import { test } from "node:test";
import assert from "node:assert/strict";
import { normalizeBriefSpaceType } from "../../api/_shared/normalize-brief.js";

test("已经是 enum · 大小写归一", () => {
  const b = { space: { type: "OFFICE" } };
  normalizeBriefSpaceType(b);
  assert.equal(b.space.type, "office");
  assert.equal(b.space.type_raw, undefined, "已 enum 不该写 type_raw");
});

test("LLM 写 'hybrid cafe-office' · 归一化为 multipurpose + raw + resolved_types 并集", () => {
  const b = { space: { type: "hybrid cafe-office", area_sqm: 30 } };
  normalizeBriefSpaceType(b);
  assert.equal(b.space.type, "multipurpose");
  assert.equal(b.space.type_raw, "hybrid cafe-office");
  // resolved_types 含 cafe+office（也可能含 multipurpose 因 'hybrid' 在 multipurpose 关键词）
  assert.ok(b.space.resolved_types.includes("cafe"), "多命中必须含 cafe");
  assert.ok(b.space.resolved_types.includes("office"), "多命中必须含 office");
  assert.equal(b.space.area_sqm, 30, "其他字段不动");
});

test("LLM 写 '校长办公室' · 归一化为 office + raw", () => {
  const b = { space: { type: "校长办公室" } };
  normalizeBriefSpaceType(b);
  assert.equal(b.space.type, "office");
  assert.equal(b.space.type_raw, "校长办公室");
});

test("LLM 写 'showroom cafe' · 归一化 multipurpose + resolved_types 含 gallery+cafe", () => {
  const b = { space: { type: "showroom cafe" } };
  normalizeBriefSpaceType(b);
  assert.equal(b.space.type, "multipurpose");
  assert.equal(b.space.type_raw, "showroom cafe");
  assert.ok(b.space.resolved_types.includes("gallery"));
  assert.ok(b.space.resolved_types.includes("cafe"));
});

test("完全无法识别的字符串 · type 写 multipurpose（safe enum） · raw 保留", () => {
  const b = { space: { type: "alien xyz totally unknown" } };
  normalizeBriefSpaceType(b);
  // 全 miss 写 multipurpose 让 strict-enum 消费方不炸 · raw 保 LLM 原话
  assert.equal(b.space.type, "multipurpose");
  assert.deepEqual(b.space.resolved_types, []);
  assert.equal(b.space.type_raw, "alien xyz totally unknown");
});

test("缺 space / 缺 type · 不抛 · 不修改", () => {
  const b1 = {};
  normalizeBriefSpaceType(b1);
  assert.deepEqual(b1, {});

  const b2 = { space: {} };
  normalizeBriefSpaceType(b2);
  assert.deepEqual(b2, { space: {} });

  const b3 = { space: { type: "" } };
  normalizeBriefSpaceType(b3);
  assert.equal(b3.space.type, "");

  const b4 = { space: { type: null, area_sqm: 30 } };
  normalizeBriefSpaceType(b4);
  assert.equal(b4.space.type, null);
  assert.equal(b4.space.area_sqm, 30);
});

test("非字符串 type · 不动", () => {
  const b = { space: { type: 123 } };
  normalizeBriefSpaceType(b);
  assert.equal(b.space.type, 123);
});

test("空格 / 大小写已是 enum · trim+lower 写回", () => {
  const b = { space: { type: "  Cafe  " } };
  normalizeBriefSpaceType(b);
  assert.equal(b.space.type, "cafe");
});
