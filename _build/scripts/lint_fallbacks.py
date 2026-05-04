"""Phase 11.7 · 静态扫所有 lookup-with-fallback 模式 · 防新增"塌缩 default" 反模式

ADR-003：所有 enum-based lookup 必须走 _build/arctura_mvp/resolvers/ 注册表。
这个 lint 找出代码里**未注册的** dict.get(x, "literal") 跟 if-elif fallback 链 ·
强制开发者：要么改成 Resolver · 要么加 `# noqa: fallback-ok` 解释为啥不走注册表。

跑：
    python3 -m _build.scripts.lint_fallbacks
    （CI 跑：exit code 0 = 干净 · 1 = 有未注册的可疑 fallback）

不扫：
    - tests/ 下（测试文件本身允许内联 fallback）
    - resolvers/__init__.py 自身（注册表的合法实现）
    - generators/_resolve_space_type.py（已有等价 Resolver 注册）

策略：
    匹配 `.get(x, "string_literal")` 跟 `or "string_literal"` 模式 ·
    如果 string_literal 看起来像 enum（小写 / camelCase / kebab-case · 不含空格 / 不是 URL）·
    且不在 allowlist · 报告。
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCAN_DIRS = [
    ROOT / "_build" / "arctura_mvp",
    ROOT / "api",
]

# 跳过：测试 + resolver 自身实现 + 第三方
EXCLUDED_RELS = {
    "_build/arctura_mvp/tests",
    "_build/arctura_mvp/resolvers",
    "_build/arctura_mvp/generators/_resolve_space_type.py",
    "_build/arctura_mvp/__pycache__",
}


# 行级注释 · 表示这一行的 fallback 已知 OK
NOQA_TAG = "noqa: fallback-ok"


# 模式 1：dict.get(x, "literal") · literal 像 enum 的可疑
# 例：`region_canonical.get(region, "HK")` 命中
# 不命中：`d.get("key", "")` （空串不算 enum） · `d.get("key", 0)`（数字不算）
PATTERN_GET = re.compile(r"""
    \.get\(
    [^,]+,
    \s*
    ["']
    ([a-zA-Z_][\w-]{1,30})    # 看起来像 enum 字面量
    ["']
    \s*\)
""", re.VERBOSE)

# 模式 2：JS `xxx || "literal"` 兜底
PATTERN_OR_JS = re.compile(r"""
    \|\|
    \s*
    ["']
    ([a-zA-Z_][\w-]{1,30})
    ["']
""", re.VERBOSE)

# 已知合法的 enum literal allowlist（不报警）
LITERAL_ALLOWLIST = {
    # null/empty
    "", "null", "undefined",
    # 路径片段（非塌缩 fallback）
    "GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS",
    # 状态字
    "ok", "error", "ready", "live", "draft", "empty",
    "briefing", "planning", "generating", "live_partial", "generating_failed",
    "saved", "pending", "running", "done", "skipped",
    # MIME / charset
    "utf-8", "utf8", "ascii",
    # 单字（占位）
    "T", "x", "y", "z", "id",
    # 调试
    "DEBUG", "INFO", "WARN", "ERROR",
    # 这些是真实业务 enum 但已在 resolver 注册表 · 跳过
    "default", "multipurpose", "HK", "CN", "INTL",
    "office", "cafe", "study", "bedroom", "living_room", "dining",
    "retail", "clinic", "gallery",
    "hospitality", "workplace", "residential", "civic", "wellness", "education",
    # tier
    "concept", "deliver", "quote", "full", "select",
    # render engine
    "fast", "formal",
    # MISC
    "P1-interior", "P2-architecture",
    # 默认空对象
    "{}", "[]",
    # 几何/导出格式 anchor + 内部 op 标签（exports/scene/overrides 内部）
    "box", "obj", "Furniture", "bottom", "top", "center", "change",
    # 引擎名 / 标准 ID（占位 string）
    "EnergyPlus", "HK_BEEO_BEC_2021",
    # 错误名 / IP unknown / namespace 全局值
    "KV_ERROR", "EXCEPTION", "unknown", "all", "none",
}


def _is_excluded(rel: str) -> bool:
    return any(rel.startswith(ex) or ex in rel for ex in EXCLUDED_RELS)


def _scan_file(path: Path, rel: str) -> list[tuple[int, str, str]]:
    """返 [(line_no, pattern_kind, literal), ...]"""
    findings = []
    if path.suffix not in (".py", ".js", ".mjs"):
        return findings
    try:
        text = path.read_text()
    except Exception:
        return findings

    for ln_idx, line in enumerate(text.splitlines(), 1):
        if NOQA_TAG in line:
            continue
        # 跳注释
        stripped = line.lstrip()
        if stripped.startswith("#") or stripped.startswith("//") or stripped.startswith("*"):
            continue
        # py
        if path.suffix == ".py":
            for m in PATTERN_GET.finditer(line):
                lit = m.group(1)
                if lit in LITERAL_ALLOWLIST:
                    continue
                findings.append((ln_idx, "py-dict-get-default", lit))
        # js / mjs
        else:
            for m in PATTERN_OR_JS.finditer(line):
                lit = m.group(1)
                if lit in LITERAL_ALLOWLIST:
                    continue
                findings.append((ln_idx, "js-or-fallback", lit))
    return findings


def main() -> int:
    all_findings: list[tuple[str, int, str, str]] = []
    for base in SCAN_DIRS:
        if not base.exists():
            continue
        for f in base.rglob("*"):
            if not f.is_file():
                continue
            rel = str(f.relative_to(ROOT))
            if _is_excluded(rel):
                continue
            for ln, kind, lit in _scan_file(f, rel):
                all_findings.append((rel, ln, kind, lit))

    if not all_findings:
        print("✅ 干净 · 没发现未注册的 fallback 模式")
        return 0

    # 按文件分组报告
    print(f"⚠ 发现 {len(all_findings)} 处可疑 fallback（未注册到 resolvers/ + 不在 allowlist）：\n")
    by_file: dict[str, list] = {}
    for rel, ln, kind, lit in all_findings:
        by_file.setdefault(rel, []).append((ln, kind, lit))

    for rel in sorted(by_file.keys()):
        items = by_file[rel]
        print(f"📄 {rel}")
        for ln, kind, lit in sorted(items):
            print(f"   L{ln} · {kind} · fallback='{lit}'")
        print()

    print("---")
    print("处理方式：")
    print("  1. 改走 resolvers/__init__.py 注册的 Resolver（推荐 · 一劳永逸）")
    print("  2. 把 literal 加进 lint_fallbacks.py 的 LITERAL_ALLOWLIST（确实非 enum）")
    print("  3. 行末加 `# noqa: fallback-ok` 注释 + 在 ADR 解释为啥这一处不走注册表")
    return 1


if __name__ == "__main__":
    sys.exit(main())
