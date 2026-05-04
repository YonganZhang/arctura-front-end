"""brief.space.type → 标准类型解析 · 关键词包含匹配 · 取并集

修今天 bug：scene generator 严格 dict lookup 对 LLM 创造性 type
（"hybrid cafe-office" / "校长办公室" / "principal office"）全 miss
→ 全部走 default → 永远生成同一个 scene。

设计：
  - 空输入 → ["default"]
  - 关键词包含匹配（substring · 大小写不敏感 · 中英文都 hit）
  - 命中多个标准类型 → 都返（保序去重）· 由 generator 取家具并集
  - 没命中 → ["default"]

关键词表跟 JS 实现共享 · 见 `api/_shared/space-type-keywords.json`
跨语言一致性由 `tests/test_resolve_space_type.py::test_keyword_table_matches_shared_json` 锁。
"""
from __future__ import annotations
import json
import re
from pathlib import Path
from typing import Iterable

# 跟 JS 共享同一份 fixture · 改一处生效双端
_FIXTURE = Path(__file__).resolve().parents[3] / "api" / "_shared" / "space-type-keywords.json"

# 英文关键词正则：ASCII 范围内用 word boundary · 防 'barber' 误命中 'bar'、'studio apartment' 误命中 'studio'
# 中文关键词不含 ASCII 字母 · 用裸 substring（中文无单词边界 · 直接 in 即可）
_ASCII_RE = re.compile(r"^[\x00-\x7F]+$")


def _load_keywords() -> dict[str, list[str]]:
    """读 fixture · 返 {standard_type: [keyword, ...]} · 失败抛"""
    data = json.loads(_FIXTURE.read_text())
    return {k: list(v) for k, v in data["keywords"].items()}


def _load_enum() -> list[str]:
    return list(json.loads(_FIXTURE.read_text())["enum"])


_KEYWORDS = _load_keywords()
_ENUM = _load_enum()


def resolve_space_type(raw: str | None) -> list[str]:
    """raw 是 brief.space.type 的原始值（LLM 写的可能很脏）

    返：命中的标准类型列表（保序去重）· 空 / 无匹配 → ["default"]

    例：
      "office" → ["office"]
      "校长办公室" → ["office"]（"校长" 命中 office · "办公" 又命中 office · 去重）
      "hybrid cafe-office" → ["cafe", "office"]（按关键词在文本里出现的顺序）
      "showroom cafe" → ["gallery", "cafe"]（showroom 在 gallery 关键词内）
      None / "" → ["default"]
      "随便" → ["default"]
    """
    if raw is None:
        return ["default"]
    text = str(raw).strip().lower()
    if not text:
        return ["default"]
    # 'living_room' / 'home_study' 这类下划线命名 · 替换为空格让词边界能命中
    # （`_` 是 \w · \bliving\b 在 'living_room' 里不触发 → 失败 fallback）
    text = text.replace("_", " ")

    # 收集 (位置, 标准类型) · 按位置排序 · 同位置取首个匹配
    hits: list[tuple[int, str]] = []
    for std_type, kws in _KEYWORDS.items():
        for kw in kws:
            kw_lower = kw.lower()
            if _ASCII_RE.match(kw_lower):
                # 英文关键词 · 词边界匹配 · 防 'bar' in 'barber' / 'studio' in 'studio apartment' 误命中
                m = re.search(rf"\b{re.escape(kw_lower)}\b", text)
                if m:
                    hits.append((m.start(), std_type))
                    break
            else:
                # 中文关键词 · substring（中文无空格分隔）
                idx = text.find(kw_lower)
                if idx >= 0:
                    hits.append((idx, std_type))
                    break

    if not hits:
        return ["default"]

    hits.sort(key=lambda x: x[0])
    seen: set[str] = set()
    out: list[str] = []
    for _, std in hits:
        if std not in seen:
            seen.add(std)
            out.append(std)
    return out


def list_enum() -> list[str]:
    """合法 space.type enum · brief schema / system_prompt 引用"""
    return list(_ENUM)


def merge_furniture_lists(types: Iterable[str], defaults_by_type: dict[str, list[str]]) -> list[str]:
    """给定多个标准类型 · 取家具清单并集（保序 · 去重）"""
    out: list[str] = []
    seen: set[str] = set()
    for t in types:
        for f in defaults_by_type.get(t, defaults_by_type.get("default", [])):
            if f not in seen:
                seen.add(f)
                out.append(f)
    return out
