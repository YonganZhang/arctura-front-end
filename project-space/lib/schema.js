// schema.js — state 和 tool input 的校验 · ESM
// 没有 zod 的超轻量方案：手写 validate 函数，返回 { ok, errors }

// ───────── Editable 字段的合法范围 ─────────

export const EDITABLE_RANGES = {
  area_m2: { min: 10, max: 1000, type: "number" },
  insulation_mm: { min: 0, max: 300, type: "number" },
  glazing_uvalue: { min: 0.6, max: 6.0, type: "number" },
  lighting_cct: { min: 2200, max: 6500, type: "number" },
  lighting_density_w_m2: { min: 1, max: 30, type: "number" },
  wwr: { min: 0, max: 0.95, type: "number" },
  region: { enum: ["HK", "CN", "US", "JP"], type: "string" },
};

export function validateEditableField(path, value) {
  const rule = EDITABLE_RANGES[path];
  if (!rule) return { ok: false, error: `Unknown editable field: ${path}` };
  if (rule.enum) {
    if (!rule.enum.includes(value)) {
      return { ok: false, error: `${path} must be one of ${rule.enum.join("/")}` };
    }
    return { ok: true };
  }
  const v = Number(value);
  if (!Number.isFinite(v)) return { ok: false, error: `${path} must be a number, got ${typeof value}` };
  if (v < rule.min || v > rule.max) {
    return { ok: false, error: `${path}=${v} out of range [${rule.min}, ${rule.max}]` };
  }
  return { ok: true };
}

// ───────── Tool 定义（给 LLM 看的 schema）──────────

export const TOOLS = [
  {
    name: "set_editable",
    description: "Set an editable design field to a specific value. Use for explicit values (e.g. 'change CCT to 2700').",
    parameters: {
      type: "object",
      properties: {
        field: { type: "string", enum: Object.keys(EDITABLE_RANGES), description: "Which editable field to change" },
        value: { description: "New value (number for numeric fields, or enum value for region)" },
      },
      required: ["field", "value"],
    },
  },
  {
    name: "scale_editable",
    description: "Scale a numeric editable field by a multiplicative factor (e.g. '+25% area').",
    parameters: {
      type: "object",
      properties: {
        field: { type: "string", enum: ["area_m2", "insulation_mm", "lighting_density_w_m2", "glazing_uvalue"],
                 description: "Which numeric field to scale" },
        factor: { type: "number", description: "Multiplicative factor (1.25 = +25%)" },
      },
      required: ["field", "factor"],
    },
  },
  {
    name: "switch_variant",
    description: "Switch to a pre-rendered variant. Only works for MVPs with variants.list non-empty.",
    parameters: {
      type: "object",
      properties: {
        variant_id: { type: "string", description: "The variant ID (e.g. 'v2-wabi-sabi')" },
      },
      required: ["variant_id"],
    },
  },
  {
    name: "switch_region",
    description: "Change the compliance region (affects which code book is checked and cost multiplier).",
    parameters: {
      type: "object",
      properties: {
        region: { type: "string", enum: ["HK", "CN", "US", "JP"], description: "Target region" },
      },
      required: ["region"],
    },
  },
  {
    name: "append_timeline",
    description: "Add a human-readable entry to the project timeline describing what just changed.",
    parameters: {
      type: "object",
      properties: {
        title: { type: "string", description: "Short title (e.g. 'Warmer lighting')" },
        diff: { type: "string", description: "Diff summary (e.g. 'CCT 3000K→2700K · EUI +4 · cost unchanged')" },
      },
      required: ["title", "diff"],
    },
  },
];

// ───────── Tool call 校验 ─────────

export function validateToolCall(call, state) {
  if (!call || typeof call !== "object") return { ok: false, error: "tool_call must be an object" };
  const { name, args } = call;
  if (!name || typeof name !== "string") return { ok: false, error: "tool_call.name missing" };
  const tool = TOOLS.find(t => t.name === name);
  if (!tool) return { ok: false, error: `Unknown tool: ${name}` };
  if (!args || typeof args !== "object") return { ok: false, error: `${name}.args missing` };

  // 必填字段
  for (const req of tool.parameters.required || []) {
    if (args[req] === undefined || args[req] === null) {
      return { ok: false, error: `${name}.args.${req} missing` };
    }
  }

  // 针对性检查
  if (name === "set_editable") {
    return validateEditableField(args.field, args.value);
  }
  if (name === "scale_editable") {
    if (!EDITABLE_RANGES[args.field]) return { ok: false, error: `Unknown field: ${args.field}` };
    if (!Number.isFinite(Number(args.factor)) || args.factor <= 0) {
      return { ok: false, error: `factor must be a positive number` };
    }
    // 放大后值不能越界
    const current = state?.editable?.[args.field] ?? 0;
    const next = current * Number(args.factor);
    return validateEditableField(args.field, next);
  }
  if (name === "switch_variant") {
    const list = state?.variants?.list || [];
    if (list.length === 0) {
      return { ok: false, error: `This MVP has no variants available. Available editable fields can still be modified.` };
    }
    const found = list.find(v => v.id === args.variant_id);
    if (!found) {
      return { ok: false, error: `variant_id '${args.variant_id}' not found. Available: ${list.map(v => v.id).join(", ")}` };
    }
    return { ok: true };
  }
  if (name === "switch_region") {
    if (!["HK", "CN", "US", "JP"].includes(args.region)) {
      return { ok: false, error: `region must be HK/CN/US/JP` };
    }
    return { ok: true };
  }
  if (name === "append_timeline") {
    if (!args.title || !args.diff) return { ok: false, error: "title and diff required" };
    return { ok: true };
  }
  return { ok: true };
}

// ───────── 导出简化的 LLM function-calling schema ─────────
// 智增增 gateway 的 LLM 可能不原生支持 tool-use；fallback 用 JSON prompt 模式
// 这个 schema 给 system prompt 用，教 LLM 怎么生成 tool_calls

export function toolsForPrompt() {
  return TOOLS.map(t => ({
    name: t.name,
    description: t.description,
    parameters: t.parameters,
  }));
}
