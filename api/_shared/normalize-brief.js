// brief 写入 KV 前的归一化（API 边界 normalize · 解决 strict-enum 消费方问题）
//
// 三段语义（修 Codex 三审 #1 + #2）：
//   space.type           — strict enum（前端 dropdown / 报告生成读这个 · 永远是 10 个 enum 之一）
//   space.type_raw       — 用户/LLM 的原始字符串（溯源 · 仅 normalize 改写时存）
//   space.resolved_types — 多命中时的并集（scene generator 读这个保家具并集信号）
//
// 决策：
//   - 已是 enum (大小写归一)        → space.type = enum · 不动其他
//   - 单一命中 (e.g. '校长办公室')   → space.type = 'office' · type_raw = '校长办公室'
//   - 多命中  (e.g. 'hybrid cafe-office') → space.type = 'multipurpose' · type_raw 原值 · resolved_types = ['cafe','office']
//   - 全 miss (e.g. 'alien xyz')    → space.type = 'multipurpose' (safe enum default · strict dropdown 不炸) · type_raw 原值 · resolved_types = []

import { resolveSpaceType, listSpaceTypeEnum } from "./resolve-space-type.js";

export function normalizeBriefSpaceType(brief) {
  if (!brief || typeof brief !== "object") return brief;
  const space = brief.space;
  if (!space || typeof space !== "object") return brief;

  const raw = space.type;
  if (raw == null || raw === "") return brief;
  if (typeof raw !== "string") return brief;

  const ENUM = new Set(listSpaceTypeEnum());
  const trimmed = raw.trim().toLowerCase();

  // 已是 enum · trim+lower 写回 · 清理 resolved_types/type_raw 避免老脏数据残留
  if (ENUM.has(trimmed)) {
    space.type = trimmed;
    delete space.resolved_types;
    // 不删 type_raw（如果之前已写过 · 是历史溯源）
    return brief;
  }

  const resolved = resolveSpaceType(raw);

  // 全 miss：写 multipurpose（safe enum default）· raw 保留溯源
  if (resolved.length === 0 || (resolved.length === 1 && resolved[0] === "default")) {
    if (!space.type_raw) space.type_raw = raw;
    space.type = "multipurpose";
    space.resolved_types = [];
    return brief;
  }

  // 单一命中
  if (resolved.length === 1) {
    if (!space.type_raw && raw.trim().toLowerCase() !== resolved[0]) {
      space.type_raw = raw;
    }
    space.type = resolved[0];
    delete space.resolved_types;  // 单命中不需要并集
    return brief;
  }

  // 多命中 · canonical type 写 multipurpose · resolved_types 留并集 · scene 读它
  if (!space.type_raw) space.type_raw = raw;
  space.type = "multipurpose";
  space.resolved_types = resolved;
  return brief;
}
