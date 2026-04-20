// apply-tools.js — 把 LLM 返回的 tool_calls 应用到 state
// ESM · 纯函数 · 调用 compute.recomputeAll 自动刷新派生字段

import { recomputeAll } from "./compute.js";
import { validateToolCall } from "./schema.js";

// 深拷贝 · 避免修改入参
function clone(obj) {
  return JSON.parse(JSON.stringify(obj));
}

function human(call) {
  const a = call.args || {};
  switch (call.name) {
    case "set_editable":
      return `${a.field} → ${a.value}`;
    case "scale_editable":
      return `${a.field} × ${a.factor}`;
    case "switch_variant":
      return `switched to variant ${a.variant_id}`;
    case "switch_region":
      return `compliance region → ${a.region}`;
    case "append_timeline":
      return `timeline: ${a.title}`;
    default:
      return `${call.name}(${JSON.stringify(a)})`;
  }
}

// 应用单个 tool 到 state · 返回 next state（不 mutate 入参）
// 不做 recompute，批量应用完再统一算一次
// variantLoader 可以是 sync 或 async（返回 Promise），本函数自己 await
async function applyOne(state, call, variantLoader) {
  const { name, args } = call;
  const s = clone(state);

  if (name === "set_editable") {
    s.editable = s.editable || {};
    s.editable[args.field] = args.value;
    return s;
  }
  if (name === "scale_editable") {
    s.editable = s.editable || {};
    const current = Number(s.editable[args.field]) || 0;
    s.editable[args.field] = current * Number(args.factor);
    return s;
  }
  if (name === "switch_region") {
    s.editable = s.editable || {};
    s.editable.region = args.region;
    return s;
  }
  if (name === "switch_variant") {
    // variantLoader 是可选回调：(slug, variantId) => variantJson | null | Promise<variantJson | null>
    if (variantLoader) {
      const v = await variantLoader(s.slug, args.variant_id);
      if (!v) {
        // 加载失败 → 抛错 · 走 rejected 路径 · 不静默 no-op
        throw new Error(`variant data not found on server for "${args.variant_id}"`);
      }
      // 把 variant 的核心字段 overlay 到 state
      s.active_variant_id = args.variant_id;
      s.project = { ...(s.project || {}), ...(v.project || {}) };
      s.renders = v.renders || s.renders;
      s.hero_img = v.hero_img || s.hero_img;
      s.thumb_img = v.thumb_img || s.thumb_img;
      s.floorplan = v.floorplan || s.floorplan;
      s.moodboard = v.moodboard || s.moodboard;
      s.zones = v.zones || s.zones;
      s.pricing = { ...(s.pricing || {}), ...(v.pricing || {}) };
      s.energy = { ...(s.energy || {}), ...(v.energy || {}) };
      s.compliance = { ...(s.compliance || {}), ...(v.compliance || {}) };
      s.editable = { ...(s.editable || {}), ...(v.editable || {}) };
      // 更新 model_glb · 如果 variant 有
      if (v.model_glb) s.model_glb = v.model_glb;
    } else {
      // 无 loader · 只标记（前端后续自己加载）
      s.active_variant_id = args.variant_id;
    }
    return s;
  }
  if (name === "append_timeline") {
    s.timeline = [...(s.timeline || [])];
    s.timeline.push({
      time: new Date().toISOString(),
      title: args.title,
      diff: args.diff,
      source: "chat",
    });
    return s;
  }
  // 未知 tool：原样返回（validateToolCall 在前面应该已拒绝）
  return s;
}

// 批量 apply · 返回 { state, applied, rejected, timelineEntries }
// async 因为 variantLoader 可能是网络请求
export async function applyTools(baseState, calls, options = {}) {
  const { variantLoader = null, autoTimeline = true } = options;
  let state = clone(baseState);
  const applied = [];
  const rejected = [];

  for (const call of calls || []) {
    const valid = validateToolCall(call, state);
    if (!valid.ok) {
      rejected.push({ call, reason: valid.error });
      continue;
    }
    try {
      state = await applyOne(state, call, variantLoader);
      applied.push({ call, summary: human(call) });
    } catch (err) {
      rejected.push({ call, reason: `apply failed: ${err.message}` });
    }
  }

  // Recompute 派生字段（一次，批量之后）
  if (applied.length > 0) {
    state = recomputeAll(state);
  }

  // 自动加一条 timeline（如果 LLM 没主动 append）
  const hadTimeline = applied.some(a => a.call.name === "append_timeline");
  if (autoTimeline && applied.length > 0 && !hadTimeline) {
    state.timeline = [...(state.timeline || [])];
    state.timeline.push({
      time: new Date().toISOString(),
      title: `${applied.length} change${applied.length > 1 ? "s" : ""}`,
      diff: applied.map(a => a.summary).join(" · "),
      source: "chat",
    });
  }

  return { state, applied, rejected };
}
