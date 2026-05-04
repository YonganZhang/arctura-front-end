// brief.space.type → 标准类型解析 · 关键词包含匹配 · 取并集
//
// JS 实现 · 跟 Python `_build/arctura_mvp/generators/_resolve_space_type.py` 双端共享。
// 关键词表唯一真源：`api/_shared/space-type-keywords.json`（Edge bundle import）
// 跨语言一致性：`_build/arctura_mvp/tests/test_resolve_space_type.py` + `_tests/resolve-space-type.spec.mjs` 双向锁。

import KEYWORDS_TABLE from "./space-type-keywords.json" with { type: "json" };

const KEYWORDS = KEYWORDS_TABLE.keywords;
const ENUM = KEYWORDS_TABLE.enum;

/**
 * @param {string|null|undefined} raw - brief.space.type 原始值
 * @returns {string[]} 命中的标准类型 · 保序去重 · 空 / 无匹配 → ["default"]
 */
export function resolveSpaceType(raw) {
  if (raw === null || raw === undefined) return ["default"];
  let text = String(raw).trim().toLowerCase();
  if (!text) return ["default"];
  // 'living_room' / 'home_study' 这类下划线命名 · 替换为空格让词边界能命中
  text = text.replace(/_/g, " ");

  // 英文关键词用词边界匹配（防 'bar' in 'barber' / 'studio' in 'studio apartment' 误命中）
  // 中文关键词用 substring（中文无空格分隔 · 词边界 \b 不适用）
  const ASCII_RE = /^[\x00-\x7F]+$/;
  const escapeRegex = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

  const hits = [];
  for (const [stdType, kws] of Object.entries(KEYWORDS)) {
    for (const kw of kws) {
      const kwLower = String(kw).toLowerCase();
      let idx = -1;
      if (ASCII_RE.test(kwLower)) {
        const re = new RegExp("\\b" + escapeRegex(kwLower) + "\\b");
        const m = text.match(re);
        if (m) idx = m.index;
      } else {
        idx = text.indexOf(kwLower);
      }
      if (idx >= 0) {
        hits.push([idx, stdType]);
        break;
      }
    }
  }
  if (hits.length === 0) return ["default"];

  hits.sort((a, b) => a[0] - b[0]);
  const seen = new Set();
  const out = [];
  for (const [, std] of hits) {
    if (!seen.has(std)) {
      seen.add(std);
      out.push(std);
    }
  }
  return out;
}

export function listSpaceTypeEnum() {
  return [...ENUM];
}
