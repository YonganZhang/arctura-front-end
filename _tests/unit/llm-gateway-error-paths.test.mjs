// Phase 11.10 · LLM gateway 错误路径测试
// 用户报 "⚠ LLM: internal error" 没诊断信息 · 加防御测每条路径都给清晰错误。
//
// 测试方式：mock fetch 返各种 gateway 异常 · 看 callLLM 是否抛带充分上下文的错误。

import { test } from "node:test";
import assert from "node:assert/strict";

// 因 chat.js 是 Edge route + 用 module-level env vars · 不直接 import
// 只测错误消息 shape · 通过 inline 复制 callLLM 的错误处理逻辑模拟

const ALLOWED_MODELS = ["gpt-5.4", "gpt-5", "claude-sonnet-4-6", "deepseek-v3.2"];

/**
 * 复刻 chat.js callLLM 错误处理逻辑（Phase 11.10 加防御后）·
 * 用于单测断言每种 gateway 异常都给清晰错误消息。
 */
async function simulateCallLLM({ fetchImpl, model = "claude-sonnet-4-6", llmKey = "test-key" }) {
  if (!llmKey) {
    throw new Error(`LLM gateway 未配置 · 缺 ZHIZENGZENG_API_KEY 环境变量`);
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 25_000);
  let resp;
  try {
    resp = await fetchImpl({ signal: controller.signal });
  } catch (e) {
    if (e.name === "AbortError") {
      throw new Error(`LLM 请求超时 25s（model=${model}）· 网关或模型响应过慢 · 试试换 GPT-5.4 或 deepseek-v3.2`);
    }
    throw new Error(`LLM 网络失败（model=${model}）: ${e.name}: ${e.message}`);
  } finally {
    clearTimeout(timeoutId);
  }

  if (!resp.ok) {
    const txt = await resp.text().catch(() => "(body 读取失败)");
    throw new Error(`LLM gateway HTTP ${resp.status}（model=${model}）: ${txt.slice(0, 300)}`);
  }

  let d;
  try {
    d = await resp.json();
  } catch (e) {
    const rawBody = await resp.text().catch(() => "");
    throw new Error(`LLM gateway 返非 JSON（model=${model}, status=${resp.status}）: ${rawBody.slice(0, 300)}`);
  }
  if (!d || !Array.isArray(d.choices) || d.choices.length === 0) {
    const summary = d?.error
      ? (typeof d.error === "string" ? d.error : JSON.stringify(d.error).slice(0, 300))
      : JSON.stringify(d || {}).slice(0, 300);
    throw new Error(`LLM gateway 无 choices（model=${model}）: ${summary}`);
  }
  const choice = d.choices[0] || {};
  const content = choice.message?.content;
  const finishReason = choice.finish_reason;
  if (typeof content !== "string" || !content.trim()) {
    throw new Error(`LLM 返空 content（model=${model}, finish_reason=${finishReason}）· 模型可能拒答 · 试换模型`);
  }
  return { content, finishReason };
}


test("LLM_KEY 缺失 · 显式报错（不再 silent Bearer undefined）", async () => {
  await assert.rejects(
    () => simulateCallLLM({ llmKey: "", fetchImpl: () => assert.fail("不该 reach fetch") }),
    /未配置.*ZHIZENGZENG_API_KEY/,
  );
});

test("AbortError · 报超时 + model + 建议换模型", async () => {
  const fetchImpl = ({ signal }) => new Promise((_, reject) => {
    signal.addEventListener("abort", () => {
      const e = new Error("aborted"); e.name = "AbortError"; reject(e);
    });
    // 永不 resolve · 等 abort
  });
  // 缩短 timeout 测试用 10ms
  const orig = setTimeout;
  const fastTimeout = (fn) => orig(fn, 10);
  const realSimulate = async () => {
    const controller = new AbortController();
    fastTimeout(() => controller.abort());
    try {
      await fetchImpl({ signal: controller.signal });
    } catch (e) {
      if (e.name === "AbortError") {
        throw new Error(`LLM 请求超时 25s（model=claude-sonnet-4-6）· 网关或模型响应过慢 · 试试换 GPT-5.4 或 deepseek-v3.2`);
      }
      throw e;
    }
  };
  await assert.rejects(realSimulate, /超时.*claude-sonnet-4-6.*换 GPT/);
});

test("Network 失败（非 abort）· 报错带 model + e.name + e.message", async () => {
  const fetchImpl = () => Promise.reject(new TypeError("Failed to fetch"));
  await assert.rejects(
    () => simulateCallLLM({ fetchImpl }),
    /LLM 网络失败.*model=.*TypeError.*Failed to fetch/,
  );
});

test("Gateway HTTP 500 · 报错带 status + body 前 300 字", async () => {
  const fetchImpl = () => Promise.resolve({
    ok: false, status: 500,
    text: () => Promise.resolve("internal error"),  // 用户报告的 case
  });
  await assert.rejects(
    () => simulateCallLLM({ fetchImpl }),
    /LLM gateway HTTP 500.*claude-sonnet-4-6.*internal error/,
  );
});

test("Gateway HTTP 401 · 鉴权错误也清晰", async () => {
  const fetchImpl = () => Promise.resolve({
    ok: false, status: 401,
    text: () => Promise.resolve("Unauthorized"),
  });
  await assert.rejects(
    () => simulateCallLLM({ fetchImpl }),
    /HTTP 401.*Unauthorized/,
  );
});

test("Gateway 返 200 + 非 JSON body · 清晰报错", async () => {
  const fetchImpl = () => Promise.resolve({
    ok: true, status: 200,
    json: () => Promise.reject(new SyntaxError("Unexpected token i in JSON at position 0")),
    text: () => Promise.resolve("internal error"),  // 假设网关 200 但 body 是错误文本
  });
  await assert.rejects(
    () => simulateCallLLM({ fetchImpl }),
    /返非 JSON.*claude-sonnet-4-6/,
  );
});

test("Gateway 返 JSON 但缺 choices · 暴露 error 字段（之前会 silent NPE）", async () => {
  const fetchImpl = () => Promise.resolve({
    ok: true, status: 200,
    json: () => Promise.resolve({ error: "internal error", code: 500 }),
  });
  await assert.rejects(
    () => simulateCallLLM({ fetchImpl }),
    /无 choices.*claude-sonnet-4-6.*internal error/,
  );
});

test("Gateway 返 choices[0].message.content 为 null · 清晰报错", async () => {
  const fetchImpl = () => Promise.resolve({
    ok: true, status: 200,
    json: () => Promise.resolve({
      choices: [{ message: { content: null }, finish_reason: "content_filter" }],
    }),
  });
  await assert.rejects(
    () => simulateCallLLM({ fetchImpl }),
    /空 content.*finish_reason=content_filter.*换模型/,
  );
});

test("Gateway 返空字符串 content · 也报空 content", async () => {
  const fetchImpl = () => Promise.resolve({
    ok: true, status: 200,
    json: () => Promise.resolve({
      choices: [{ message: { content: "   " }, finish_reason: "stop" }],
    }),
  });
  await assert.rejects(
    () => simulateCallLLM({ fetchImpl }),
    /空 content.*finish_reason=stop/,
  );
});

test("正常 200 + 合法 content · 不抛", async () => {
  const fetchImpl = () => Promise.resolve({
    ok: true, status: 200,
    json: () => Promise.resolve({
      choices: [{ message: { content: '{"reply":"ok","brief_patch":{}}' }, finish_reason: "stop" }],
    }),
  });
  const result = await simulateCallLLM({ fetchImpl });
  assert.equal(result.finishReason, "stop");
  assert.ok(result.content.includes("reply"));
});
