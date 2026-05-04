// 鲁棒 LLM JSON 解析器 · Phase 11.8
//
// 背景：用户切到 Claude Sonnet 报错 `Unexpected token '\`'`，因为 Claude 经常包 ```json fence
// 即使 system_prompt 说"严格 JSON"。GPT-5 走 response_format=json_object 不包 fence。
// 这是同 shape 的"信任输入太宽"反模式：之前 dict.get(x, default) 假设 x 在 enum；
// 这里 JSON.parse(content) 假设 content 是干净 JSON。
//
// 处理策略（按 cost 升序尝试 · 第一个成功即返）：
//   1. 严格 JSON.parse（GPT-5 模式）
//   2. 剥 markdown fence: ```json ... ``` 或 ``` ... ```
//   3. 抽第一个 {...} 平衡块（散文 + 裸 JSON 场景）
//   4. 清理 trailing comma + 智能引号 + 重试
//
// 失败抛 LLMParseError 含原始内容前 500 字符（debug 用）。
//
// Python 对称实现：_build/arctura_mvp/chat/llm_parse_json.py · 同 fixture 测试锁。

export class LLMParseError extends Error {
  constructor(message, raw) {
    super(message);
    this.name = "LLMParseError";
    this.raw = raw;
  }
}

/** 找第一个平衡的 {...} 或 [...] 块 · 返起止 index 或 null
 *  忽略字符串内的 { } · 处理转义 */
function findBalancedJsonBlock(text) {
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (ch !== "{" && ch !== "[") continue;
    const open = ch;
    const close = ch === "{" ? "}" : "]";
    let depth = 0;
    let inStr = false;
    let escape = false;
    for (let j = i; j < text.length; j++) {
      const c = text[j];
      if (escape) { escape = false; continue; }
      if (c === "\\") { escape = true; continue; }
      if (c === '"' && !escape) { inStr = !inStr; continue; }
      if (inStr) continue;
      if (c === open) depth++;
      else if (c === close) {
        depth--;
        if (depth === 0) return { start: i, end: j + 1 };
      }
    }
  }
  return null;
}

/** 剥 markdown 代码块（```json ... ``` 或 ``` ... ```）· 返内容或 null */
function stripMarkdownFence(text) {
  // 多行 fence · 允许 fence tag 是 json/JSON/javascript/js 或空
  const m = text.match(/```(?:json|JSON|javascript|js)?\s*\n?([\s\S]*?)\n?```/);
  return m ? m[1].trim() : null;
}

/** 清理常见 LLM JSON 笔误：trailing comma · 智能引号 */
function cleanupJsonString(s) {
  return s
    // 智能引号 → 直引号
    .replace(/[“”]/g, '"')
    .replace(/[‘’]/g, "'")
    // trailing comma in object: ,}
    .replace(/,(\s*[}\]])/g, "$1");
}

/**
 * 鲁棒 LLM JSON 解析 · 多策略级联
 * @param {string} raw - LLM message.content 原始文本
 * @returns {object|array} 解析后的 JSON
 * @throws LLMParseError 全策略失败
 */
export function parseLLMJson(raw) {
  if (typeof raw !== "string") {
    throw new LLMParseError(`expected string, got ${typeof raw}`, raw);
  }
  const text = raw.trim();
  if (!text) {
    throw new LLMParseError("empty content", raw);
  }

  // 策略 1：严格 parse
  try {
    return JSON.parse(text);
  } catch {}

  // 策略 2：剥 markdown fence
  const stripped = stripMarkdownFence(text);
  if (stripped) {
    try {
      return JSON.parse(stripped);
    } catch {}
    // fence 内还可能有 trailing comma 等 · 清理后再试
    try {
      return JSON.parse(cleanupJsonString(stripped));
    } catch {}
  }

  // 策略 3：抽第一个平衡 JSON 块（散文 + JSON 混合）
  // ⚠ 如果文本本身以 { 或 [ 开头 · 跳过这一步 · 否则会从被截断的 JSON 中挑出内部子对象当合法（Phase 11.9 真实 bug）
  // 例：{"reply":"x","brief_patch":{"zones":[{"name":"a"}]}, ← 被截断
  //     如果跑 balanced block 会返 inner {"name":"a"} 当结果 · 严重错误
  const startsWithBrace = text[0] === "{" || text[0] === "[";
  if (!startsWithBrace) {
    const block = findBalancedJsonBlock(text);
    if (block) {
      const slice = text.slice(block.start, block.end);
      try {
        return JSON.parse(slice);
      } catch {}
      try {
        return JSON.parse(cleanupJsonString(slice));
      } catch {}
    }
  }

  // 策略 4：整体 cleanup 再试
  try {
    return JSON.parse(cleanupJsonString(text));
  } catch {}

  // 全失败
  throw new LLMParseError(
    `parseLLMJson 全策略失败: ${text.slice(0, 200)}...`,
    raw,
  );
}

// 内部 helpers 暴露用于单测
export const _internals = {
  findBalancedJsonBlock,
  stripMarkdownFence,
  cleanupJsonString,
};
