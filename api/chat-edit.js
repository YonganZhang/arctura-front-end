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
- Never invent new tool names or fields. Use only what's listed above.`;
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

  let llmResp;
  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 25000);
    const upstream = await fetch(GATEWAY, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });
    clearTimeout(timer);
    if (!upstream.ok) {
      const errText = await upstream.text().catch(() => "");
      return jsonResponse({ error: `Upstream ${upstream.status}`, detail: errText.slice(0, 500) }, 502);
    }
    llmResp = await upstream.json();
  } catch (err) {
    return jsonResponse({ error: "LLM request failed", detail: String(err.message || err) }, 504);
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

  // 应用 tool calls
  const { state: newState, applied, rejected } = applyTools(currentState, parsed.tool_calls, {
    variantLoader,
    autoTimeline: true,
  });

  return jsonResponse({
    text: parsed.text || "(processed)",
    newState,
    applied,
    rejected,
    model: usedModel,
    usage,
  });
}
