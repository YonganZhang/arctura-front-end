"""鲁棒 LLM JSON 解析器 · Python 端 · Phase 11.8

跟 api/_shared/llm-parse-json.js 对称实现 · 共享 fixture 锁跨语言一致。
背景：Claude 包 ```json fence · GPT-5 走 strict JSON · LLM 偶尔 trailing comma /
智能引号。直接 json.loads(content) 是脆弱假设。

策略（按 cost 升序）：
  1. 严格 json.loads
  2. 剥 markdown fence
  3. 抽第一个 {...} 平衡块
  4. 清理 trailing comma + 智能引号 + 重试
"""
from __future__ import annotations
import json
import re


class LLMParseError(Exception):
    def __init__(self, message: str, raw: str = ""):
        super().__init__(message)
        self.raw = raw


_FENCE_RE = re.compile(r"```(?:json|JSON|javascript|js)?\s*\n?(.*?)\n?```", re.DOTALL)


def _find_balanced_json_block(text: str) -> tuple[int, int] | None:
    """找第一个平衡的 {...} 或 [...] 块 · 返 (start, end) · 忽略字符串内括号"""
    for i, ch in enumerate(text):
        if ch not in "{[":
            continue
        open_ch = ch
        close_ch = "}" if ch == "{" else "]"
        depth = 0
        in_str = False
        escape = False
        for j in range(i, len(text)):
            c = text[j]
            if escape:
                escape = False
                continue
            if c == "\\":
                escape = True
                continue
            if c == '"' and not escape:
                in_str = not in_str
                continue
            if in_str:
                continue
            if c == open_ch:
                depth += 1
            elif c == close_ch:
                depth -= 1
                if depth == 0:
                    return (i, j + 1)
    return None


def _strip_markdown_fence(text: str) -> str | None:
    m = _FENCE_RE.search(text)
    return m.group(1).strip() if m else None


def _cleanup_json_string(s: str) -> str:
    """智能引号 → 直引号 · 移除 trailing comma"""
    s = s.replace("“", '"').replace("”", '"')
    s = s.replace("‘", "'").replace("’", "'")
    # trailing comma in object/array
    s = re.sub(r",(\s*[}\]])", r"\1", s)
    return s


def parse_llm_json(raw: str):
    """鲁棒 LLM JSON 解析 · 多策略级联

    Args:
        raw: LLM message.content 原始文本
    Returns:
        dict 或 list（解析结果）
    Raises:
        LLMParseError: 全策略失败
    """
    if not isinstance(raw, str):
        raise LLMParseError(f"expected string · got {type(raw).__name__}", str(raw))
    text = raw.strip()
    if not text:
        raise LLMParseError("empty content", raw)

    # 1. 严格
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 2. 剥 fence
    stripped = _strip_markdown_fence(text)
    if stripped is not None:
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            pass
        try:
            return json.loads(_cleanup_json_string(stripped))
        except json.JSONDecodeError:
            pass

    # 3. 平衡 JSON 块
    block = _find_balanced_json_block(text)
    if block:
        s, e = block
        sl = text[s:e]
        try:
            return json.loads(sl)
        except json.JSONDecodeError:
            pass
        try:
            return json.loads(_cleanup_json_string(sl))
        except json.JSONDecodeError:
            pass

    # 4. 整体 cleanup
    try:
        return json.loads(_cleanup_json_string(text))
    except json.JSONDecodeError:
        pass

    raise LLMParseError(f"parse_llm_json 全策略失败: {text[:200]}...", raw)


__all__ = ["parse_llm_json", "LLMParseError"]
