// extractDisplayName 单测 · 兼容 brief.project 的 3 种历史形状（见 ADR-002）
// 跑：node --test _tests/unit/extract-display-name.test.mjs

import { test } from "node:test";
import assert from "node:assert/strict";
import { extractDisplayName, isPlaceholderName,
         readAnonCookie, ANON_COOKIE_NAME } from "../../api/_shared/project-name.js";

test("canonical {name_cn, name_en} · 优先中文", () => {
  assert.equal(extractDisplayName({ name_cn: "木间咖啡办公", name_en: "Mujiro" }), "木间咖啡办公");
});

test("只有 name_en · 用英文", () => {
  assert.equal(extractDisplayName({ name_en: "Mujiro Cafe" }), "Mujiro Cafe");
});

test("legacy {name} · 兼容老数据", () => {
  assert.equal(extractDisplayName({ name: "老格式" }), "老格式");
});

test("legacy 字符串 · 兼容更老的数据", () => {
  assert.equal(extractDisplayName("T"), "T");
  assert.equal(extractDisplayName("木间咖啡"), "木间咖啡");
});

test("空 / null / 缺字段 · 返 null", () => {
  assert.equal(extractDisplayName(null), null);
  assert.equal(extractDisplayName(undefined), null);
  assert.equal(extractDisplayName(""), null);
  assert.equal(extractDisplayName("  "), null);
  assert.equal(extractDisplayName({}), null);
  assert.equal(extractDisplayName({ name_cn: "" }), null);
  assert.equal(extractDisplayName({ name_cn: "   " }), null);
});

test("name_cn 优先于 name_en 优先于 name", () => {
  assert.equal(
    extractDisplayName({ name_cn: "中", name_en: "EN", name: "legacy" }),
    "中",
  );
  assert.equal(
    extractDisplayName({ name_en: "EN", name: "legacy" }),
    "EN",
  );
});

test("非 string / object / array · 返 null（不抛）", () => {
  assert.equal(extractDisplayName(123), null);
  assert.equal(extractDisplayName([1, 2, 3]), null);
  assert.equal(extractDisplayName(true), null);
});

test("扩展形状 · {zh, en} / {title} / {display_name} / {name: {cn, en}}", () => {
  assert.equal(extractDisplayName({ zh: "中", en: "EN" }), "中");
  assert.equal(extractDisplayName({ en: "EN" }), "EN");
  assert.equal(extractDisplayName({ title: "标题" }), "标题");
  assert.equal(extractDisplayName({ display_name: "DN" }), "DN");
  assert.equal(extractDisplayName({ name: { cn: "嵌套中", en: "Nested" } }), "嵌套中");
  assert.equal(extractDisplayName({ name: { en: "OnlyEN" } }), "OnlyEN");
});

test("ANON_COOKIE_NAME 跟 api/projects.js 设的 cookie 名一致（防 drift · 子智能体 + Codex 双 flag bug）", () => {
  // 这是导致 11.4 owner 校验沦为装饰的 bug 锁
  // api/projects.js:80 设的是 `arctura_anon=...` · 这里必须保证一致
  assert.equal(ANON_COOKIE_NAME, "arctura_anon");
});

test("readAnonCookie · 解析 arctura_anon cookie", () => {
  const fakeReq = (cookieStr) => ({ headers: { get: (k) => k === "cookie" ? cookieStr : null } });
  assert.equal(readAnonCookie(fakeReq("arctura_anon=abc123def456")), "abc123def456");
  assert.equal(readAnonCookie(fakeReq("foo=bar; arctura_anon=xyz789; baz=qux")), "xyz789");
  assert.equal(readAnonCookie(fakeReq("")), null);
  assert.equal(readAnonCookie(fakeReq("anon_id=oldname")), null,
    "旧 cookie 名 anon_id 不该被读到（这正是 bug 来源）");
  assert.equal(readAnonCookie({ headers: { get: () => null } }), null);
});

test("isPlaceholderName · 大小写 / 空白鲁棒", () => {
  assert.equal(isPlaceholderName(null), true);
  assert.equal(isPlaceholderName(undefined), true);
  assert.equal(isPlaceholderName(""), true);
  assert.equal(isPlaceholderName("  "), true);
  assert.equal(isPlaceholderName("未命名项目"), true);
  assert.equal(isPlaceholderName("未命名"), true);
  assert.equal(isPlaceholderName("Untitled"), true);
  assert.equal(isPlaceholderName("UNTITLED"), true);
  assert.equal(isPlaceholderName("untitled project"), true);
  assert.equal(isPlaceholderName("Untitled Project"), true);
  assert.equal(isPlaceholderName("  Draft  "), true);
  assert.equal(isPlaceholderName("草稿"), true);
  // 真名 · 不是占位
  assert.equal(isPlaceholderName("木间咖啡办公"), false);
  assert.equal(isPlaceholderName("Mujiro Cafe"), false);
});
