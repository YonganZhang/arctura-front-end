// Vercel Edge Function — Chat → 真改 state
// POST /api/chat-edit
// body: {
//   slug: string,
//   userMessage: string,
//   currentState: <full MVP state>,
//   model: string,
//   chatHistory?: [{role, content}, ...],
// }
// response: {
//   text: string,         // LLM 给用户的自然语言回复
//   newState: <state>,    // 应用 tool calls 后的 state（含 derived 重算）
//   applied: [{call, summary}, ...],
//   rejected: [{call, reason}, ...],
//   model: string,
//   usage?: {...},
// }

export const config = { runtime: "edge" };

import { applyTools } from "../project-space/lib/apply-tools.js";
import { toolsForPrompt, TOOLS } from "../project-space/lib/schema.js";
import { applyOps } from "../project-space/lib/scene-ops.js";
import { isSceneTool, toolToOps, buildScenePromptFragment } from "../project-space/lib/scene-tools.js";

const GATEWAY = "https://api.zhizengzeng.com/v1/chat/completions";

function jsonResponse(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function usesCompletionTokens(model) {
  return /^(gpt-5|o[1-9])/i.test(model);
}

// System prompt · 教 LLM 怎么用 tools
function buildSystemPrompt(state) {
  const editable = state.editable || {};
  const variants = (state.variants?.list || []).map(v => `${v.id} (${v.name})`).join(", ") || "none";
  return `You are an AI design co-pilot inside the Arctura Labs interior-design platform.
The user is editing a real project. Your job:
1. Understand their natural-language request
2. Reply briefly (1-2 sentences) explaining what you're changing and why
3. Emit one or more tool_calls as a JSON code block to actually apply changes

Current project state:
- slug: ${state.slug}
- category: ${state.cat}
- current editable: ${JSON.stringify(editable)}
- available variants: ${variants}

Available tools (emit as JSON):
${TOOLS.map(t => `  • ${t.name}: ${t.description}
    params: ${JSON.stringify(t.parameters.properties)}`).join("\n")}

Editable field ranges:
- area_m2: 10-1000
- insulation_mm: 0-300 (XPS thickness)
- glazing_uvalue: 0.6-6.0 W/m²K (lower = better)
- lighting_cct: 2200-6500 K (warmer = lower, e.g. 2700 warm / 3000 neutral / 4000 cool)
- lighting_density_w_m2: 1-30
- wwr: 0-0.95 (window-to-wall ratio)
- region: HK/CN/US/JP (affects compliance + cost)

**Reply format (strict)**:
<plain text explanation for the user, 1-2 sentences>

\`\`\`json
{"tool_calls": [
  {"name": "set_editable", "args": {"field": "lighting_cct", "value": 2700}}
]}
\`\`\`

Examples:

User: "make it warmer"
Assistant: Dropped the color temperature from 3000K to 2700K for a warmer, cozier feel. EUI will go up a couple points.
\`\`\`json
{"tool_calls": [{"name": "set_editable", "args": {"field": "lighting_cct", "value": 2700}}]}
\`\`\`

User: "show me the wabi-sabi variant"
Assistant: Switching to the Japanese Wabi-Sabi variant — raw wood, white walls, pottery accents.
\`\`\`json
{"tool_calls": [{"name": "switch_variant", "args": {"variant_id": "v2-wabi-sabi"}}]}
\`\`\`

User: "scale up 25%"
Assistant: Scaling the floor area by 1.25× (40→50 m²). Budget and energy use will grow proportionally.
\`\`\`json
{"tool_calls": [{"name": "scale_editable", "args": {"field": "area_m2", "factor": 1.25}}]}
\`\`\`

User: "check Tokyo code"
Assistant: Switching compliance region to Japan (省エネ法 2025). This is a stricter envelope code; some items may fail.
\`\`\`json
{"tool_calls": [{"name": "switch_region", "args": {"region": "JP"}}]}
\`\`\`

Rules:
- Always emit at least one tool_call in the JSON block UNLESS the request is purely informational (then no JSON block)
- If the user asks for something impossible (e.g. a variant that doesn't exist), explain why and don't emit tool_calls
- Keep the natural-language reply short (1-2 sentences). The JSON block is separate.
- Never invent new tool names or fields. Use only what's listed above.` + buildScenePromptFragment(state.scene, state._availableFurnitureTypes);
}

function parseLLMReply(raw) {
  // 提取文本 + JSON 代码块
  if (!raw) return { text: "(no response)", tool_calls: [] };
  // 找 ```json ... ``` 块
  const jsonMatch = raw.match(/```(?:json)?\s*(\{[\s\S]*?\})\s*```/);
  let tool_calls = [];
  let text = raw;
  if (jsonMatch) {
    text = raw.replace(jsonMatch[0], "").trim();
    try {
      const parsed = JSON.parse(jsonMatch[1]);
      tool_calls = parsed.tool_calls || [];
    } catch (e) {
      // JSON 解析失败 → 无 tool_calls，text 保留原样
    }
  }
  return { text: text.trim(), tool_calls };
}

// 服务端 variant loader · 通过自身 domain fetch
async function makeVariantLoader(origin) {
  return async (slug, variantId) => {
    try {
      const url = `${origin}/data/mvps/${slug}/variants/${variantId}.json`;
      const r = await fetch(url);
      if (!r.ok) return null;
      return await r.json();
    } catch {
      return null;
    }
  };
}

export default async function handler(req) {
  if (req.method !== "POST") return jsonResponse({ error: "POST only" }, 405);

  const apiKey = process.env.ZHIZENGZENG_API_KEY;
  if (!apiKey) return jsonResponse({ error: "Server misconfigured: ZHIZENGZENG_API_KEY missing" }, 500);

  let body;
  try {
    body = await req.json();
  } catch {
    return jsonResponse({ error: "Invalid JSON body" }, 400);
  }

  const { slug, userMessage, currentState, model, chatHistory = [] } = body;
  if (!slug || !userMessage || !currentState || !model) {
    return jsonResponse({ error: "Required: slug, userMessage, currentState, model" }, 400);
  }

  // 若 state 有 scene · 拿可用家具 type 注入 prompt（让 LLM 只用库内 type）
  let availableFurnitureTypes = [];
  if (currentState.scene) {
    try {
      const reqUrl = new URL(req.url);
      const origin0 = `${reqUrl.protocol}//${reqUrl.host}`;
      const libResp = await fetch(`${origin0}/data/furniture-library.json`);
      if (libResp.ok) {
        const lib = await libResp.json();
        availableFurnitureTypes = Object.keys(lib.items || {});
      }
    } catch {}
    // 不 mutate 入参 · 挂到 currentState 的浅 copy
    currentState = { ...currentState, _availableFurnitureTypes: availableFurnitureTypes };
  }

  // 构造 LLM messages
  const systemPrompt = buildSystemPrompt(currentState);
  const userTurns = Array.isArray(chatHistory)
    ? chatHistory.filter(m => m && (m.role === "user" || m.role === "assistant"))
    : [];
  const messages = [
    { role: "system", content: systemPrompt },
    ...userTurns,
    { role: "user", content: userMessage },
  ];

  // 调 LLM
  const maxTok = 800;
  const payload = { model, messages, temperature: 0.3 };
  if (usesCompletionTokens(model)) payload.max_completion_tokens = maxTok;
  else payload.max_tokens = maxTok;

  // LLM 调用 · 最多 2 次尝试（第一次 18s · 慢了就重试 8s）· 覆盖 25s Edge 上限
  async function callLLM(timeoutMs) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const upstream = await fetch(GATEWAY, {
        method: "POST",
        headers: { Authorization: `Bearer ${apiKey}`, "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        signal: controller.signal,
      });
      clearTimeout(timer);
      if (!upstream.ok) {
        const errText = await upstream.text().catch(() => "");
        const err = new Error(`upstream_${upstream.status}`);
        err.detail = errText.slice(0, 300);
        err.status = upstream.status;
        throw err;
      }
      return await upstream.json();
    } catch (e) {
      clearTimeout(timer);
      throw e;
    }
  }

  let llmResp;
  let attempt = 0;
  const maxAttempts = 2;
  let lastErr;
  while (attempt < maxAttempts) {
    attempt++;
    const budget = attempt === 1 ? 18000 : 8000;
    try {
      llmResp = await callLLM(budget);
      break;
    } catch (err) {
      lastErr = err;
      const isTimeout = err.name === "AbortError" || err.message?.includes("abort");
      const isRetryable = isTimeout || err.status === 502 || err.status === 503 || err.status === 504 || err.status === 429;
      if (attempt >= maxAttempts || !isRetryable) {
        // 最终失败 · 返回友好错误
        const status = err.status && err.status >= 400 ? err.status : 504;
        const msg = isTimeout ? "LLM 响应超时（>20s） · 试试短一点的句子，或换个模型（点上方 Model 下拉）"
                  : err.status ? `Upstream error ${err.status}` : "LLM call failed";
        return jsonResponse({
          error: msg,
          detail: (err.detail || String(err.message || err)).slice(0, 300),
          retryable: isRetryable,
        }, status);
      }
      // 重试前不等 · 直接再 fetch（新 timeout budget）
    }
  }

  const choice = llmResp.choices?.[0];
  const rawText = choice?.message?.content || "";
  const usedModel = llmResp.model || model;
  const usage = llmResp.usage || null;

  // 解析出 tool_calls
  const parsed = parseLLMReply(rawText);

  // Variant loader 通过 request origin 拿 variant JSON
  const url = new URL(req.url);
  const origin = `${url.protocol}//${url.host}`;
  const variantLoader = await makeVariantLoader(origin);

  // 分离 scene tool calls（13 个新 tool）与 editable tool calls（5 个老 tool）
  const editableCalls = [];
  const sceneCalls = [];
  for (const call of parsed.tool_calls) {
    if (isSceneTool(call?.name)) sceneCalls.push(call);
    else editableCalls.push(call);
  }

  // 先应用 editable tools · applyTools 会替换 currentState
  let { state: newState, applied, rejected } = await applyTools(currentState, editableCalls, {
    variantLoader,
    autoTimeline: true,
  });

  // 再应用 scene tools
  if (sceneCalls.length > 0 && newState.scene) {
    const opPairs = []; // 每 entry: { call, op } · 用对象引用匹配回调
    for (const call of sceneCalls) {
      const r = toolToOps(call, newState.scene);
      if (r.ops.length === 0) {
        rejected.push({ call, reason: r.reason || "no ops produced" });
        continue;
      }
      for (const op of r.ops) opPairs.push({ call, op });
    }
    if (opPairs.length > 0) {
      const opsOnly = opPairs.map(p => p.op);
      const sceneResult = applyOps(newState.scene, opsOnly);
      newState = { ...newState, scene: sceneResult.newScene };
      for (const a of sceneResult.applied) {
        const pair = opPairs.find(p => p.op === a.op);
        applied.push({
          call: pair?.call || { name: `scene_${a.op.op}` },
          summary: `scene: ${a.op.op}`,
        });
      }
      for (const r of sceneResult.rejected) {
        const pair = opPairs.find(p => p.op === r.op);
        rejected.push({
          call: pair?.call || { name: `scene_${r.op?.op || "unknown"}` },
          reason: r.reason,
        });
      }
    }
  } else if (sceneCalls.length > 0 && !newState.scene) {
    for (const call of sceneCalls) {
      rejected.push({ call, reason: "此 MVP 暂无 scene 数据（Phase 2.0 pilot 只在 01-study-room 启用）" });
    }
  }

  return jsonResponse({
    text: parsed.text || "(processed)",
    newState,
    applied,
    rejected,
    model: usedModel,
    usage,
  });
}
