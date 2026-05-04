// 跨语言一致性 · Python resolver 跟 JS resolver 关键 case 必须返同样结果
// 不直接跑 Python · 用 fixture 文件做契约（任何 case Python 也得过 · 同 case 在
// _build/arctura_mvp/tests/test_resolve_space_type.py 单测里也存在）。

import { test } from "node:test";
import assert from "node:assert/strict";
import { resolveSpaceType, listSpaceTypeEnum } from "../../api/_shared/resolve-space-type.js";
import KEYWORDS_TABLE from "../../api/_shared/space-type-keywords.json" with { type: "json" };

// fixture 自身完整性
test("fixture · enum 跟 keywords keys 一致", () => {
  const enumSet = new Set(KEYWORDS_TABLE.enum);
  const kwKeys = new Set(Object.keys(KEYWORDS_TABLE.keywords));
  assert.deepEqual([...enumSet].sort(), [...kwKeys].sort(),
    "fixture enum 跟 keywords keys drift · scene generator 会有 enum 没默认家具");
});

test("fixture · 每个标准类型至少 2 个关键词", () => {
  for (const [stdType, kws] of Object.entries(KEYWORDS_TABLE.keywords)) {
    assert.ok(Array.isArray(kws) && kws.length >= 2,
      `${stdType} 关键词太少（${kws.length}）· 命中率会很差`);
  }
});

test("fixture · 关键词无空字符串 / 无重复", () => {
  for (const [stdType, kws] of Object.entries(KEYWORDS_TABLE.keywords)) {
    const set = new Set();
    for (const kw of kws) {
      assert.equal(typeof kw, "string", `${stdType} 关键词非 string: ${kw}`);
      assert.ok(kw.trim().length > 0, `${stdType} 含空关键词`);
      assert.ok(!set.has(kw), `${stdType} 关键词 '${kw}' 重复`);
      set.add(kw);
    }
  }
});

// 跨语言 case · 这些 case 在 Python test_resolve_space_type.py 里也覆盖
const CROSS_LANG_CASES = [
  ["office", ["office"]],
  ["cafe", ["cafe"]],
  ["multipurpose", ["multipurpose"]],
  ["校长办公室", ["office"]],
  ["principal office", ["office"]],
  ["咖啡厅", ["cafe"]],
  ["dental clinic", ["clinic"]],
  ["画廊", ["gallery"]],
  ["co-working", ["multipurpose"]],
  ["", ["default"]],
  [null, ["default"]],
];

for (const [input, expected] of CROSS_LANG_CASES) {
  test(`cross-lang · resolveSpaceType(${JSON.stringify(input)}) → ${JSON.stringify(expected)}`, () => {
    assert.deepEqual(resolveSpaceType(input), expected);
  });
}

test("cross-lang · hybrid cafe-office 同时含 cafe 跟 office", () => {
  const out = resolveSpaceType("hybrid cafe-office");
  assert.ok(out.includes("cafe"));
  assert.ok(out.includes("office"));
});
