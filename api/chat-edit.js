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

// System prompt · Phase 4 · 所有请求都输出 plan（用户确认前不执行）
function buildSystemPrompt(state) {
  const editable = state.editable || {};
  const variants = (state.variants?.list || []).map(v => `${v.id} (${v.name})`).join(", ") || "none";
  return `You are an AI design co-pilot inside the Arctura Labs interior-design platform.
The user is editing a real project. Your job:
1. Understand user's request（can be subjective like "更温馨" or exact like "删衣柜"）
2. Break it into concrete steps (1 step for simple, N steps for compound intent)
3. 每步附带要调用的 tool_call · 服务端 dry-run 每步 · 用户确认后才真 apply

Current project state:
- slug: ${state.slug}
- category: ${state.cat}
- current editable: ${JSON.stringify(editable)}
- available variants: ${variants}

Available tools:
${TOOLS.map(t => `  • ${t.name}: ${t.description}
    params: ${JSON.stringify(t.parameters.properties)}`).join("\n")}

Editable field ranges:
- area_m2: 10-1000 · insulation_mm: 0-300 · glazing_uvalue: 0.6-6.0 (lower=better)
- lighting_cct: 2200-6500K (warmer=lower · 2700 暖 · 3000 中 · 4000 冷)
- lighting_density_w_m2: 1-30 · wwr: 0-0.95 · region: HK/CN/US/JP

**Output format (strict)** · 一律用 plan 结构：

<1-2 sentences explanation · 告诉用户你的思路>

\`\`\`json
{
  "plan": {
    "intent": "一句话概括用户意图",
    "steps": [
      { "id": 1, "desc": "<中文描述这步做啥>", "tool_call": { "name": "...", "args": {...} } }
    ]
  }
}
\`\`\`

**例 1 · 简单指令（1 step）**：

User: "删衣柜"
Assistant: 好，把衣柜从场景里删掉。
\`\`\`json
{"plan":{"intent":"删除衣柜","steps":[
  {"id":1,"desc":"删除衣柜及其所有零件","tool_call":{"name":"remove_furniture","args":{"id_or_name":"衣柜"}}}
]}}
\`\`\`

**例 2 · 模糊意图（多 step）**：

User: "让房间更温馨"
Assistant: 为营造温暖氛围 · 降色温 + 墙刷暖米 + 加一盏阅读角落地灯。
\`\`\`json
{"plan":{"intent":"让房间更温馨","steps":[
  {"id":1,"desc":"主灯色温降到 2700K 暖光","tool_call":{"name":"change_light","args":{"id_or_name":"all","cct":2700}}},
  {"id":2,"desc":"北墙刷暖米色 #E8DCC8","tool_call":{"name":"change_material","args":{"target":"wall_N","base_color":"#E8DCC8"}}},
  {"id":3,"desc":"阅读角加一盏落地灯","tool_call":{"name":"add_furniture","args":{"type":"lamp_floor","pos":[1.8,-1.0,0],"label_zh":"阅读灯"}}}
]}}
\`\`\`

**例 3 · 相对指令**：

User: "把沙发往左移 30cm"
Assistant: 把沙发 x 方向平移 -30cm。
\`\`\`json
{"plan":{"intent":"沙发左移","steps":[
  {"id":1,"desc":"沙发左移 30cm","tool_call":{"name":"move_furniture","args":{"id_or_name":"沙发","pos_delta":[-0.3,0,0]}}}
]}}
\`\`\`

**例 4 · 不可操作**（如场景里没有"宠物"）：

User: "删掉宠物"
Assistant: 场景里没有宠物对象 · 无法删除。可以告诉我具体家具名？
（不 emit plan 代码块）

Rules:
- **CRITICAL**: 可操作的请求必须 emit plan 代码块 · 就算只 1 step 也要用 plan 包装 · 统一格式。
- 多步顺序：由浅入深（先小改再大改）· 便于用户逐项审核
- 每步 desc 用中文 · 具体说数值（2700K · 0.3m · #E8DCC8）· 不要空话
- 每 tool_call 的 name / args 必须精确按上面 tools 列表
- 如果用户请求超 tool 覆盖范围 · 不 emit plan · text 里解释` + buildScenePromptFragment(state.scene, state._availableFurnitureTypes);
}

function parseLLMReply(raw) {
  // 提取文本 + JSON 代码块 · 支持 {plan:...} 或 {tool_calls:...}（兼容旧）
  if (!raw) return { text: "(no response)", tool_calls: [], plan: null };
  const jsonMatch = raw.match(/```(?:json)?\s*(\{[\s\S]*?\})\s*```/);
  let tool_calls = [];
  let plan = null;
  let text = raw;
  if (jsonMatch) {
    text = raw.replace(jsonMatch[0], "").trim();
    try {
      const parsed = JSON.parse(jsonMatch[1]);
      if (parsed.plan && Array.isArray(parsed.plan.steps)) {
        plan = parsed.plan;
        // 同时为 legacy 代码路径填 tool_calls（所有步骤的 tool_call 铺平）
        tool_calls = parsed.plan.steps.map(s => s.tool_call).filter(Boolean);
      } else {
        tool_calls = parsed.tool_calls || [];
      }
    } catch (e) {
      // JSON 解析失败
    }
  }
  return { text: text.trim(), tool_calls, plan };
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

  let body;
  try {
    body = await req.json();
  } catch {
    return jsonResponse({ error: "Invalid JSON body" }, 400);
  }

  // Phase 4 · action=apply · 用户确认 plan 后执行选中的 tool_calls · 不走 LLM
  if (body?.action === "apply") {
    const { slug, currentState, tool_calls } = body;
    if (!slug || !currentState || !Array.isArray(tool_calls)) {
      return jsonResponse({ error: "Required: slug, currentState, tool_calls (array)" }, 400);
    }
    const url = new URL(req.url);
    const origin = `${url.protocol}//${url.host}`;
    const variantLoader = await makeVariantLoader(origin);
    const r = await applyToolCalls(currentState, tool_calls, variantLoader);
    return jsonResponse({
      text: "已应用确认的改动",
      newState: r.newState,
      applied: r.applied,
      rejected: r.rejected,
    });
  }

  const apiKey = process.env.ZHIZENGZENG_API_KEY;
  if (!apiKey) return jsonResponse({ error: "Server misconfigured: ZHIZENGZENG_API_KEY missing" }, 500);

  const requestStart = Date.now();
  const { slug, userMessage, model, chatHistory = [] } = body;
  let currentState = body.currentState;
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

  // LLM 调用 · Phase 4 · 初次 14s + 自修 6s = 20s · 留 5s 给 dry-run 和 Edge overhead
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
  // Phase 4 优化：timeout 后 retry 几乎必失败（LLM 慢期 6s 不够）· 只在 5xx 时 retry
  const maxAttempts = 2;
  let lastErr;
  while (attempt < maxAttempts) {
    attempt++;
    const budget = attempt === 1 ? 20000 : 4000;   // 初次 20s（Edge 25s 硬限 · 留 5s overhead+dry-run）· 5xx retry 才 4s
    try {
      llmResp = await callLLM(budget);
      break;
    } catch (err) {
      lastErr = err;
      const isTimeout = err.name === "AbortError" || err.message?.includes("abort");
      const is5xx = err.status === 502 || err.status === 503 || err.status === 429;
      // timeout 不 retry（浪费时间）· 只有 5xx/429 retry
      const isRetryable = is5xx;
      if (attempt >= maxAttempts || !isRetryable) {
        const status = err.status && err.status >= 400 ? err.status : 504;
        const msg = isTimeout ? "LLM 响应超时（>20s） · 试试短一点的句子，或换个模型（点上方 Model 下拉 · 换 deepseek-v3-chat 更快）"
                  : err.status ? `Upstream error ${err.status}` : "LLM call failed";
        return jsonResponse({
          error: msg,
          detail: (err.detail || String(err.message || err)).slice(0, 300),
          retryable: isTimeout || is5xx,
        }, status);
      }
    }
  }

  const choice = llmResp.choices?.[0];
  const rawText = choice?.message?.content || "";
  const usedModel = llmResp.model || model;
  const usage = llmResp.usage || null;

  // 解析出 tool_calls
  let parsed = parseLLMReply(rawText);

  // 若 LLM 没 emit plan 但用户消息像是操作请求 · retry 1 次要求输出 plan 格式
  const ACTION_VERBS = /(删|移|换|加|放|改|升|降|旋转|缩放|remove|delete|move|change|add|place|set|shift|rotate|resize|scale|color|paint|hide|show|温馨|冷|暖|亮|暗|现代|简约|北欧)/i;
  if (!parsed.plan && parsed.tool_calls.length === 0 && ACTION_VERBS.test(userMessage) && attempt === 1) {
    const retryMessages = [
      { role: "system", content: systemPrompt },
      ...userTurns,
      { role: "user", content: userMessage },
      { role: "assistant", content: rawText },
      { role: "user", content: '你上面忘了 emit plan 代码块 · 请**立即**重新回复 · 必须包含 ```json{"plan":{"intent":"...","steps":[...]}}``` 代码块 · 每步带 tool_call。否则改动无效。' },
    ];
    payload.messages = retryMessages;
    try {
      const retryResp = await callLLM(8000);
      const retryText = retryResp.choices?.[0]?.message?.content || "";
      const retryParsed = parseLLMReply(retryText);
      if (retryParsed.plan || retryParsed.tool_calls.length > 0) {
        parsed = { text: parsed.text + " (自动重试)", tool_calls: retryParsed.tool_calls, plan: retryParsed.plan };
      }
    } catch {}
  }

  // Variant loader 通过 request origin 拿 variant JSON
  const url = new URL(req.url);
  const origin = `${url.protocol}//${url.host}`;
  const variantLoader = await makeVariantLoader(origin);

  // Phase 4 · plan 模式 · 不直接 apply · dry-run 每步 · 返回给前端等用户确认
  if (parsed.plan && Array.isArray(parsed.plan.steps)) {
    let steps = parsed.plan.steps;
    let dry = await dryRunPlan(currentState, steps, variantLoader);
    // Self-correction · 若有任何 step 失败 · 给 LLM 反馈 1 轮重 emit
    const failures = dry.stepResults.filter(r => !r.dry_run.ok);
    const elapsedMs = Date.now() - requestStart;
    const remainingBudget = 22000 - elapsedMs;   // Edge 25s 上限 · 留 3s margin
    // 初次 LLM 18s budget · elapsedMs 可能接近 18s · remainingBudget 留 6s 可自修 · 否则直接返回
    if (failures.length > 0 && remainingBudget > 6000) {
      const feedback = failures.map(f => `step ${f.id}: ${f.dry_run.reason}`).join("\n");
      const correctionMessages = [
        { role: "system", content: systemPrompt },
        ...userTurns,
        { role: "user", content: userMessage },
        { role: "assistant", content: rawText },
        { role: "user", content: `你的 plan dry-run 发现问题：\n${feedback}\n请基于当前 scene 状态 · 修正这些 step（或删除 · 或换参数 · 或换位置）· 重新 emit 完整 plan。` },
      ];
      payload.messages = correctionMessages;
      try {
        const correctBudget = Math.min(8000, remainingBudget - 1500);
        const retryResp = await callLLM(correctBudget);
        const retryText = retryResp.choices?.[0]?.message?.content || "";
        const retryParsed = parseLLMReply(retryText);
        if (retryParsed.plan && retryParsed.plan.steps?.length > 0) {
          steps = retryParsed.plan.steps;
          dry = await dryRunPlan(currentState, steps, variantLoader);
          parsed = { ...parsed, text: retryParsed.text || parsed.text, plan: retryParsed.plan };
        }
      } catch {}
    }
    // 每步附 dry_run 结果返回前端
    const stepsWithDry = steps.map(s => {
      const r = dry.stepResults.find(r => r.id === s.id);
      return { ...s, dry_run: r?.dry_run || null };
    });
    return jsonResponse({
      text: parsed.text || "(planning)",
      plan: { ...parsed.plan, steps: stepsWithDry },
      previewState: dry.finalState,     // 全部执行后会变成这样 · 客户端仅用于预览
      newState: currentState,            // 当前状态（未改动）
      applied: [],
      rejected: [],
      model: usedModel,
      usage,
    });
  }

  // 降级 1：LLM 只 emit tool_calls 没 plan · 包成合成 plan 让前端也能审核
  if (parsed.tool_calls && parsed.tool_calls.length > 0) {
    const syntheticSteps = parsed.tool_calls.map((tc, i) => ({
      id: i + 1,
      desc: tc.name || "操作",
      tool_call: tc,
    }));
    const dry = await dryRunPlan(currentState, syntheticSteps, variantLoader);
    const stepsWithDry = syntheticSteps.map(s => {
      const r = dry.stepResults.find(r => r.id === s.id);
      return { ...s, dry_run: r?.dry_run || null };
    });
    return jsonResponse({
      text: parsed.text || "(auto-wrapped plan)",
      plan: { intent: userMessage.slice(0, 40), steps: stepsWithDry, _synthetic: true },
      previewState: dry.finalState,
      newState: currentState,
      applied: [],
      rejected: [],
      model: usedModel,
      usage,
    });
  }

  // 降级 2：LLM 没 emit plan 也没 tool_calls（纯信息性回复）· 返回文字
  return jsonResponse({
    text: parsed.text || "(processed)",
    newState: currentState,
    applied: [],
    rejected: [],
    model: usedModel,
    usage,
  });
}

// ───────── Shared · 把 tool_calls 应用到 state（真 apply · 用 in dry-run 和 apply 动作）─────────
async function applyToolCalls(currentState, tool_calls, variantLoader) {
  const editableCalls = tool_calls.filter(c => !isSceneTool(c?.name));
  const sceneCalls = tool_calls.filter(c => isSceneTool(c?.name));
  let { state: newState, applied, rejected } = await applyTools(currentState, editableCalls, {
    variantLoader,
    autoTimeline: true,
  });
  if (sceneCalls.length > 0 && newState.scene) {
    const opPairs = [];
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
        applied.push({ call: pair?.call || { name: `scene_${a.op.op}` }, summary: `scene: ${a.op.op}` });
      }
      for (const r of sceneResult.rejected) {
        const pair = opPairs.find(p => p.op === r.op);
        rejected.push({ call: pair?.call || { name: `scene_${r.op?.op || "?"}` }, reason: r.reason });
      }
    }
  } else if (sceneCalls.length > 0 && !newState.scene) {
    for (const call of sceneCalls) {
      rejected.push({ call, reason: "此 MVP 暂无 scene 数据" });
    }
  }
  return { newState, applied, rejected };
}

// ───────── Dry-run · 在 state 克隆上 sequential apply 每步 · 不 mutate 入参 ─────────
async function dryRunPlan(state, steps, variantLoader) {
  const stepResults = [];
  let workState = JSON.parse(JSON.stringify(state));
  for (const step of steps || []) {
    const call = step?.tool_call;
    if (!call?.name) {
      stepResults.push({ id: step.id, dry_run: { ok: false, reason: "step 缺 tool_call" } });
      continue;
    }
    try {
      const r = await applyToolCalls(workState, [call], variantLoader);
      const stepOk = r.applied.length > 0 && r.rejected.length === 0;
      workState = r.newState;
      stepResults.push({
        id: step.id,
        dry_run: {
          ok: stepOk,
          reason: stepOk ? null : (r.rejected[0]?.reason || "step rejected"),
          applied_count: r.applied.length,
        },
      });
    } catch (e) {
      stepResults.push({ id: step.id, dry_run: { ok: false, reason: String(e.message || e).slice(0, 140) } });
    }
  }
  return { stepResults, finalState: workState };
}
