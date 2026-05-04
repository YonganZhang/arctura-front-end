// brief.project → display_name 抽取 · 兼容历史多种形状（见 ADR-002）
//
// 抽出原因：原本写在 api/brief/chat.js（Edge route），单测要 import route 模块容易把
// route 副作用一起导进来。抽到 _shared 后纯函数 · 双侧（chat.js / projects.js / save.js）
// 共享 · 单测干净。

/**
 * 历史形状（按出现先后 · 见 ADR-002）：
 *   - string                       "T"
 *   - {name}                       Phase < 6
 *   - {zh, en}                     某些早期 case
 *   - {title}                      偶发
 *   - {display_name}               偶发
 *   - {name_cn, name_en, slug}     当前 canonical（Phase 11.1+）
 *   - {name: {cn, en}}             少数 nested
 *
 * 优先级（中文 > 英文 > legacy 单字段）：
 *   1. name_cn / zh / name.cn  — 中文 canonical
 *   2. name_en / en / name.en  — 英文 canonical
 *   3. name / display_name / title  — legacy（语种不明 · 不优先）
 */
export function extractDisplayName(briefProject) {
  if (briefProject == null) return null;

  // legacy: 字符串
  if (typeof briefProject === "string") {
    const t = briefProject.trim();
    return t || null;
  }

  if (typeof briefProject !== "object" || Array.isArray(briefProject)) return null;

  const pick = (v) => (typeof v === "string" && v.trim() ? v.trim() : null);
  const nestedName = (briefProject.name && typeof briefProject.name === "object" && !Array.isArray(briefProject.name))
    ? briefProject.name : null;

  // 中文 canonical
  const cn = pick(briefProject.name_cn)
        || pick(briefProject.zh)
        || (nestedName ? pick(nestedName.cn) : null);
  if (cn) return cn;

  // 英文 canonical
  const en = pick(briefProject.name_en)
        || pick(briefProject.en)
        || (nestedName ? pick(nestedName.en) : null);
  if (en) return en;

  // legacy 单字段（语种不明）
  return pick(briefProject.name)
      || pick(briefProject.display_name)
      || pick(briefProject.title)
      || null;
}

/**
 * 占位名集合 · 大小写/前后空白都视为占位
 * 这些是各 API 端创建 project 时的默认值，display_name 是它们才能被 chat 同步覆盖
 */
const PLACEHOLDERS_NORMALIZED = new Set([
  "",
  "未命名项目",
  "未命名",
  "untitled",
  "untitled project",
  "no name",
  "draft",
  "草稿",
]);

export function isPlaceholderName(name) {
  if (name == null) return true;
  const s = String(name).trim().toLowerCase();
  return PLACEHOLDERS_NORMALIZED.has(s);
}

// ───── Anon cookie helper · 跨 endpoint 单一真源 ─────
// （之前 api/projects.js 设 `arctura_anon=...` 但 overrides.js 读 `anon_id=...` ·
//  Phase 11.4 cookie 名不匹配 → owner 校验沦为装饰 · 子智能体 + Codex 双 flag 后修）
export const ANON_COOKIE_NAME = "arctura_anon";

export function readAnonCookie(req) {
  const c = req.headers.get("cookie") || "";
  const re = new RegExp("(?:^|;\\s*)" + ANON_COOKIE_NAME + "=([^;]+)");
  const m = c.match(re);
  return m ? decodeURIComponent(m[1]) : null;
}
