// Vercel Edge Function · /api/brief/chat · SSE
// Phase 6.B Brief Chat · 多轮对话 + schema-guided 填充 + state 推进
//
// body: { slug, user_message }
// response: SSE
//   event: start · {}
//   event: reply · {text}
//   event: brief_update · {brief_patch, brief, completeness, ready_for_tier, missing}
//   event: heartbeat · {elapsed_ms}
//   event: complete · {final_state}
//   event: error · {message}
//
// 状态转移：
//   state=empty → state=briefing（首轮）
//   state=briefing → state=briefing（多轮）
//   state=briefing → state=planning（用户显式 confirm + ready_for_tier）
//   其他 state → 409

export const config = { runtime: "edge" };

const KV_URL = process.env.UPSTASH_REDIS_REST_URL;
const KV_TOKEN = process.env.UPSTASH_REDIS_REST_TOKEN;
const LLM_KEY = process.env.ZHIZENGZENG_API_KEY;

// ─────── Upstash helpers ───────

async function kv(cmd, ...args) {
  const path = [cmd, ...args.map(a => encodeURIComponent(String(a)))].join("/");
  const r = await fetch(`${KV_URL}/${path}`, {
    headers: { Authorization: `Bearer ${KV_TOKEN}` },
  });
  if (!r.ok) throw new Error(`KV ${cmd}: HTTP ${r.status}`);
  return (await r.json()).result;
}

async function kvGetJson(key) {
  const v = await kv("get", key);
  return v ? JSON.parse(v) : null;
}

async function kvSetJson(key, obj, ttl) {
  const val = JSON.stringify(obj);
  if (ttl) return kv("set", key, val, "EX", ttl);
  return kv("set", key, val);
}

async function kvPersist(key) {
  return kv("persist", key);
}

// ─────── Brief engine (JS 版 · 跟 Python brief_engine.py 同步) ───────

// Brief rules · 单一真源 · 跟 _build/arctura_mvp/schemas/brief-rules.json 保持一致
// 对称文件: api/_shared/brief-rules.json · 改一边必须改另一边（_tests/brief-rules-cross-lang.spec.mjs 保护）
// ⚠ Edge runtime 不支持 fs · 这里 inline 引（build 时 Vercel bundle · 同步靠测试）
import briefRules from "../_shared/brief-rules.json" with { type: "json" };
import { K } from "../_shared/kv-keys.js";
import { extractDisplayName, isPlaceholderName } from "../_shared/project-name.js";
import { normalizeBriefSpaceType } from "../_shared/normalize-brief.js";
import { parseLLMJson, LLMParseError } from "../_shared/llm-parse-json.js";

const SYSTEM_PROMPT = briefRules.system_prompt;

// path string "space.area_sqm" → array ["space","area_sqm"] · 单节点仍用 string
function parsePath(s) { return s.includes(".") ? s.split(".") : s; }
const MUST_FILL = briefRules.must_fill_for_planning.map(parsePath);
const NICE_FIELDS = briefRules.nice_to_have.map(parsePath);
const WEIGHTS = briefRules.completeness_weights;
const READY_THRESHOLD = briefRules.ready_for_tier_threshold;

function pathGet(obj, path) {
  if (typeof path === "string") return obj?.[path];
  let cur = obj;
  for (const k of path) { if (!cur || typeof cur !== "object") return undefined; cur = cur[k]; }
  return cur;
}

function nonempty(v) {
  if (v == null) return false;
  if (typeof v === "string") return v.length > 0;
  if (Array.isArray(v)) return v.length > 0;
  if (typeof v === "object") return Object.keys(v).length > 0;
  return true;
}

function completeness(brief) {
  if (!brief) return 0;
  const must = MUST_FILL.filter(p => nonempty(pathGet(brief, p))).length / MUST_FILL.length;
  const nice = NICE_FIELDS.filter(p => nonempty(pathGet(brief, p))).length / NICE_FIELDS.length;
  return Math.round((must * WEIGHTS.must_fill + nice * WEIGHTS.nice_to_have) * 100) / 100;
}

function readyForTier(brief) {
  return MUST_FILL.every(p => nonempty(pathGet(brief, p))) && completeness(brief) >= READY_THRESHOLD;
}

function missingMust(brief) {
  return MUST_FILL.filter(p => !nonempty(pathGet(brief, p)))
    .map(p => Array.isArray(p) ? p.join(".") : p);
}

function deepMerge(base, patch) {
  const out = { ...base };
  for (const [k, v] of Object.entries(patch || {})) {
    if (out[k] && typeof out[k] === "object" && !Array.isArray(out[k])
        && v && typeof v === "object" && !Array.isArray(v)) {
      out[k] = deepMerge(out[k], v);
    } else {
      out[k] = v;
    }
  }
  return out;
}

// extractDisplayName / isPlaceholderName 已抽到 api/_shared/project-name.js（Step 1 重构）
// normalizeBriefSpaceType 抽到 api/_shared/normalize-brief.js（Step 1 修 Codex 反馈 #5）

// ─────── LLM call · ZHIZENGZENG gateway · gpt-5.4 ───────

// Phase 9.6 · 允许的 LLM 模型列表 · 跟 ZHIZENGZENG gateway 支持的对齐
// 前端 dropdown 选 · 后端 allowlist 拒非法
const ALLOWED_MODELS = ["gpt-5.4", "gpt-5", "gpt-4.1", "claude-sonnet-4-6", "deepseek-v3.2"];
const DEFAULT_MODEL = "gpt-5.4";

async function callLLM(userMessage, brief, history, model = DEFAULT_MODEL) {
  const userPrompt = `## 当前 brief
\`\`\`json
${JSON.stringify(brief, null, 2)}
\`\`\`

## 状态
completeness: ${completeness(brief)}
还缺必填: ${missingMust(brief).join(", ") || "无"}

## 用户本轮说
${userMessage}

按系统指令严格输出 JSON。`;

  const messages = [{ role: "system", content: SYSTEM_PROMPT }];
  for (const t of history || []) messages.push({ role: t.role, content: t.content });
  messages.push({ role: "user", content: userPrompt });

  // gpt-5 系列参数名不同（max_completion_tokens · 不接 temperature / max_tokens）
  const isGpt5 = /^gpt-5/.test(model);
  const body = {
    model,
    messages,
    response_format: { type: "json_object" },
  };
  if (isGpt5) {
    body.max_completion_tokens = 2000;
  } else {
    body.temperature = 0.3;
    body.max_tokens = 2000;
  }

  const resp = await fetch("https://api.zhizengzeng.com/v1/chat/completions", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${LLM_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
  if (!resp.ok) {
    const txt = await resp.text();
    throw new Error(`LLM ${resp.status}: ${txt.slice(0, 200)}`);
  }
  const d = await resp.json();
  const content = d.choices[0].message.content;
  // Phase 11.8 · 鲁棒 LLM JSON 解析（修 Claude Sonnet 包 ```json fence 的塌缩）
  // 之前直接 JSON.parse → 切到 Sonnet 立即炸 "Unexpected token '`'"
  try {
    return parseLLMJson(content);
  } catch (e) {
    if (e instanceof LLMParseError) {
      throw new Error(`LLM 输出非 JSON (${model}): ${String(content).slice(0, 200)}`);
    }
    throw e;
  }
}

// ─────── SSE helpers ───────

function encoder() { return new TextEncoder(); }
function sseMessage(event, data) {
  return `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`;
}

// ─────── Main handler ───────

export default async function handler(req) {
  if (req.method !== "POST") {
    return new Response(JSON.stringify({ error: "method not allowed" }), { status: 405 });
  }

  let body;
  try { body = await req.json(); } catch { body = {}; }
  const { slug, user_message, model: reqModel } = body;

  if (!slug || !user_message) {
    return new Response(JSON.stringify({ error: "missing slug or user_message" }), { status: 400 });
  }
  // Phase 9.6 · 模型 allowlist · 防任意注入
  const model = (reqModel && ALLOWED_MODELS.includes(reqModel)) ? reqModel : DEFAULT_MODEL;

  const enc = encoder();
  const { readable, writable } = new TransformStream();
  const writer = writable.getWriter();
  const heartbeatStart = Date.now();

  // 后台异步处理（不阻塞响应 stream）
  (async () => {
    let closed = false;
    const safeWrite = async (s) => {
      if (closed) return;
      try { await writer.write(enc.encode(s)); }
      catch { closed = true; }
    };
    const heartbeatInterval = setInterval(() => {
      safeWrite(sseMessage("heartbeat", { elapsed_ms: Date.now() - heartbeatStart }));
    }, 12000);

    try {
      await safeWrite(sseMessage("start", { slug }));

      // 读 project + history
      const project = await kvGetJson(K.project(slug));
      if (!project) {
        await safeWrite(sseMessage("error", { message: "project not found", code: 404 }));
        return;
      }
      const allowedStates = ["empty", "briefing", "planning"];
      if (!allowedStates.includes(project.state)) {
        await safeWrite(sseMessage("error", {
          message: `state=${project.state} 不允许 brief chat`,
          code: 409,
        }));
        return;
      }
      const history = (await kvGetJson(K.briefHistory(slug))) || [];
      const currentBrief = project.brief || {};

      // LLM
      let parsed;
      try {
        parsed = await callLLM(user_message, currentBrief, history, model);
      } catch (e) {
        await safeWrite(sseMessage("error", { message: `LLM: ${e.message}` }));
        return;
      }

      const reply = parsed.reply || "";
      const patch = parsed.brief_patch || {};
      const piiNew = parsed.pii_fields || [];
      // Phase 9.6 · suggestions 最多 5 条 · 去重 + 截断
      const suggestions = Array.isArray(parsed.suggestions)
        ? [...new Set(parsed.suggestions.filter(s => typeof s === "string" && s.trim().length > 0))].slice(0, 5)
        : [];

      await safeWrite(sseMessage("reply", {
        text: reply,
        next_question: parsed.next_question || "",
        suggestions,
        model,
      }));

      // Merge brief
      const newBrief = deepMerge(currentBrief, patch);
      const piiSet = new Set([...(newBrief._pii_fields || []), ...piiNew]);
      newBrief._pii_fields = [...piiSet].sort();

      const comp = completeness(newBrief);
      const ready = readyForTier(newBrief);
      const missing = missingMust(newBrief);

      await safeWrite(sseMessage("brief_update", {
        brief_patch: patch,
        brief: newBrief,
        completeness: comp,
        ready_for_tier: ready,
        missing,
      }));

      // API 边界归一化 space.type 到 enum（Codex Step 1 #5 · LLM 自创字符串问题）
      // 这里 mutate newBrief · 写入 KV 时已是 canonical
      normalizeBriefSpaceType(newBrief);

      // 持久化 brief + history · state 推进
      project.brief = newBrief;
      project.version = (project.version || 0) + 1;
      project.updated_at = new Date().toISOString();
      if (project.state === "empty") project.state = "briefing";

      // 同步 display_name from brief.project（修 "未命名项目" bug · 见 ADR-002）
      // 仅当当前 display_name 是占位时才覆盖（不冲用户 PATCH 自设的名字）
      const extracted = extractDisplayName(newBrief.project);
      if (extracted && isPlaceholderName(project.display_name)) {
        project.display_name = extracted.slice(0, 80);
      }
      // ready 且用户显式说"进入选档"类字样 · 推 planning（保守：让前端按钮触发 PATCH · 这里不自动推）

      await kvSetJson(K.project(slug), project, 7 * 86400);

      const newHistory = [...history,
        { role: "user", content: user_message },
        { role: "assistant", content: JSON.stringify({ reply, brief_patch: patch }) },
      ].slice(-20);  // 最多留 20 条（10 轮）
      await kvSetJson(K.briefHistory(slug), newHistory, 7 * 86400);

      await safeWrite(sseMessage("complete", {
        state: project.state,
        version: project.version,
        completeness: comp,
        ready_for_tier: ready,
      }));
    } catch (e) {
      await safeWrite(sseMessage("error", { message: String(e.message || e) }));
    } finally {
      clearInterval(heartbeatInterval);
      closed = true;
      try { await writer.close(); } catch {}
    }
  })();

  return new Response(readable, {
    status: 200,
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache, no-transform",
      "Connection": "keep-alive",
      "X-Accel-Buffering": "no",
    },
  });
}
