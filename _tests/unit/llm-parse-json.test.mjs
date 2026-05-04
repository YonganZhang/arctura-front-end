// Phase 11.8 · JS LLM JSON 解析器测试 · 跟 Python 共享 fixture
// 跑：node --test _tests/unit/llm-parse-json.test.mjs

import { test } from "node:test";
import assert from "node:assert/strict";
import { parseLLMJson, LLMParseError, _internals }
  from "../../api/_shared/llm-parse-json.js";
import fixture from "../../_build/arctura_mvp/tests/fixtures/llm_responses.json"
  with { type: "json" };

function partialMatch(expect, actual, path = "") {
  if (expect && typeof expect === "object" && !Array.isArray(expect)
      && actual && typeof actual === "object" && !Array.isArray(actual)) {
    for (const [k, v] of Object.entries(expect)) {
      assert.ok(k in actual, `${path}: 缺字段 ${k}`);
      partialMatch(v, actual[k], `${path}.${k}`);
    }
  } else {
    assert.deepEqual(actual, expect, `${path}: 期望 ${JSON.stringify(expect)} 实际 ${JSON.stringify(actual)}`);
  }
}

for (const c of fixture.cases) {
  test(`real-world · ${c.name}`, () => {
    const result = parseLLMJson(c.raw);
    if (c.expect_type === "array") {
      assert.ok(Array.isArray(result));
      return;
    }
    if (c.expect) partialMatch(c.expect, result, c.name);
  });
}

for (const c of fixture.expected_to_fail) {
  test(`expected-fail · ${c.name}`, () => {
    let err = null;
    try { parseLLMJson(c.raw); } catch (e) { err = e; }
    assert.ok(err instanceof LLMParseError, `${c.name} 应抛 LLMParseError`);
    if (c.expected_error) {
      assert.ok(err.message.includes(c.expected_error),
        `${c.name}: 消息不含 '${c.expected_error}'`);
    }
  });
}

test("非 string · 抛 LLMParseError", () => {
  assert.throws(() => parseLLMJson(123), LLMParseError);
  assert.throws(() => parseLLMJson(null), LLMParseError);
  assert.throws(() => parseLLMJson(undefined), LLMParseError);
});

test("纯空白 · 抛 empty content", () => {
  let err = null;
  try { parseLLMJson("  \n\n   "); } catch (e) { err = e; }
  assert.ok(err.message.includes("empty content"));
});

test("fence 内大量空白 · 仍能 parse", () => {
  const raw = "```json\n\n\n  {\"x\":1}  \n\n\n```";
  assert.deepEqual(parseLLMJson(raw), { x: 1 });
});

test("多个 JSON 块 · 返第一个", () => {
  const raw = "First: {\"a\":1} Second: {\"b\":2}";
  assert.deepEqual(parseLLMJson(raw), { a: 1 });
});

test("fence 内坏 JSON 但外面有平衡块 · 救回", () => {
  const raw = "```json\n{not valid\n```\n\nActual: {\"good\":true}";
  const result = parseLLMJson(raw);
  assert.equal(result.good, true);
});

test("平衡块处理字符串内的 {} · 不误识别", () => {
  const text = '{"x":"text with } in string","y":1}';
  const block = _internals.findBalancedJsonBlock(text);
  assert.ok(block);
  assert.equal(text.slice(block.start, block.end), text);
});

test("智能引号 + trailing comma · cleanup 救回", () => {
  const src = '{“x”:1, “y”:2,}';
  const out = _internals.cleanupJsonString(src);
  assert.deepEqual(JSON.parse(out), { x: 1, y: 2 });
});

test("LLMParseError 保 raw 字段（debug 友好）", () => {
  let err = null;
  try { parseLLMJson("not json at all"); } catch (e) { err = e; }
  assert.ok(err instanceof LLMParseError);
  assert.equal(err.raw, "not json at all");
});
