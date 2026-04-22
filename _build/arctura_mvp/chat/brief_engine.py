"""Brief 对话引擎 · schema-guided 多轮填充

核心函数 step() 纯函数：
  (user_message, history, current_brief) → {reply, brief_patch, completeness, ready_for_tier, next_question}

对齐上游 schema: _build/arctura_mvp/schemas/brief-interior.schema.json
LLM: 默认 gpt-5.4（Phase 6 定案 · 可 override）· 走 ZHIZENGZENG gateway
"""
from __future__ import annotations
import json
import os
import re
from pathlib import Path
from typing import Optional, Callable

SCHEMA_PATH = Path(__file__).parent.parent / "schemas" / "brief-interior.schema.json"
_RULES_PATH = Path(__file__).parent.parent / "schemas" / "brief-rules.json"


def _load_rules() -> dict:
    return json.loads(_RULES_PATH.read_text())


_RULES = _load_rules()

def _parse_path(s: str):
    """将 'space.area_sqm' 转成 tuple ('space', 'area_sqm'); 无点号则返回字符串"""
    if "." in s:
        return tuple(s.split("."))
    return s

# must-fill / nice-to-have / system prompt · 全来自 JSON · 单一真源
MUST_FILL_FOR_PLANNING = [_parse_path(p) for p in _RULES["must_fill_for_planning"]]
NICE_TO_HAVE = [_parse_path(p) for p in _RULES["nice_to_have"]]
_WEIGHTS = _RULES["completeness_weights"]
_READY_THRESHOLD = _RULES["ready_for_tier_threshold"]


def load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text())


def _path_get(obj: dict, path) -> object:
    if isinstance(path, str):
        return obj.get(path)
    cur = obj
    for k in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(k)
    return cur


def _path_set(obj: dict, path, value):
    if isinstance(path, str):
        obj[path] = value
        return
    cur = obj
    for k in path[:-1]:
        cur = cur.setdefault(k, {})
    cur[path[-1]] = value


def _nonempty(v) -> bool:
    if v is None:
        return False
    if isinstance(v, (list, dict, str)) and len(v) == 0:
        return False
    return True


def completeness(brief: dict) -> float:
    """0.0-1.0 · must-fill 占 60% · nice-to-have 占 40%（权重来自 brief-rules.json）"""
    if not brief:
        return 0.0
    must_score = sum(1 for p in MUST_FILL_FOR_PLANNING if _nonempty(_path_get(brief, p))) / len(MUST_FILL_FOR_PLANNING)
    nice_score = sum(1 for p in NICE_TO_HAVE if _nonempty(_path_get(brief, p))) / len(NICE_TO_HAVE)
    return round(must_score * _WEIGHTS["must_fill"] + nice_score * _WEIGHTS["nice_to_have"], 2)


def ready_for_tier(brief: dict) -> bool:
    """所有 must-fill 都填 + completeness ≥ 阈值（阈值来自 brief-rules.json）"""
    for p in MUST_FILL_FOR_PLANNING:
        if not _nonempty(_path_get(brief, p)):
            return False
    return completeness(brief) >= _READY_THRESHOLD


def missing_must_fields(brief: dict) -> list[str]:
    out = []
    for p in MUST_FILL_FOR_PLANNING:
        if not _nonempty(_path_get(brief, p)):
            out.append(".".join(p) if isinstance(p, tuple) else p)
    return out


# ───── LLM prompt ─────

SYSTEM_PROMPT = _RULES["system_prompt"]


def make_user_prompt(user_message: str, current_brief: dict, schema: dict) -> str:
    """给 LLM 的本轮用户 prompt · 含当前 brief + schema 摘要 + 用户话"""
    missing = missing_must_fields(current_brief)
    comp = completeness(current_brief)
    return f"""## 当前 brief（已填部分）
```json
{json.dumps(current_brief, ensure_ascii=False, indent=2)}
```

## 状态
- completeness: {comp}
- 还缺必填: {missing or "无 · 可以进入选档"}

## 用户本轮说
{user_message}

按系统指令输出 JSON（reply + brief_patch + next_question + pii_fields）。"""


# ───── LLM 调用（injectable · 测试用 mock）─────

def default_llm_call(system_prompt: str, user_prompt: str, *, history: list = None,
                     model: str = "gpt-5.4", timeout: int = 20) -> str:
    """默认走 ZHIZENGZENG gateway · OpenAI-compatible"""
    import urllib.request

    api_key = os.environ.get("ZHIZENGZENG_API_KEY")
    if not api_key:
        raise RuntimeError("ZHIZENGZENG_API_KEY 未设")

    messages = [{"role": "system", "content": system_prompt}]
    for turn in (history or []):
        messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({"role": "user", "content": user_prompt})

    body = json.dumps({
        "model": model,
        "messages": messages,
        "temperature": 0.3,
        "response_format": {"type": "json_object"},
    }).encode()
    req = urllib.request.Request(
        "https://api.zhizengzeng.com/v1/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read())
    return d["choices"][0]["message"]["content"]


# ───── 主 step（纯函数 · 多轮对话）─────

def step(user_message: str, *,
         history: Optional[list] = None,
         current_brief: Optional[dict] = None,
         llm_call: Callable = default_llm_call,
         model: str = "gpt-5.4") -> dict:
    """推进一轮 brief 对话

    Returns: {
      reply: str,                # 给用户看的人话
      brief: dict,                # 合并 patch 后的新 brief
      brief_patch: dict,          # 本轮更新的字段
      completeness: float,
      ready_for_tier: bool,
      missing: list[str],
      next_question: str,
      pii_fields: list[str],
    }
    """
    current_brief = current_brief or {}
    schema = load_schema()
    user_prompt = make_user_prompt(user_message, current_brief, schema)

    raw = llm_call(SYSTEM_PROMPT, user_prompt, history=history, model=model)
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        # 兜底：从文本里抽 JSON
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if not m:
            raise ValueError(f"LLM 没返 JSON: {raw[:300]}")
        parsed = json.loads(m.group())

    reply = parsed.get("reply", "")
    patch = parsed.get("brief_patch", {}) or {}
    next_q = parsed.get("next_question", "")
    pii = parsed.get("pii_fields", []) or []

    # Deep merge patch 到 brief
    new_brief = _deep_merge(dict(current_brief), patch)
    # PII 合并
    existing_pii = set(new_brief.get("_pii_fields", []))
    new_brief["_pii_fields"] = sorted(existing_pii | set(pii))

    return {
        "reply": reply,
        "brief": new_brief,
        "brief_patch": patch,
        "completeness": completeness(new_brief),
        "ready_for_tier": ready_for_tier(new_brief),
        "missing": missing_must_fields(new_brief),
        "next_question": next_q,
        "pii_fields": pii,
    }


def _deep_merge(base: dict, patch: dict) -> dict:
    """递归 merge · patch 覆盖 base · dict 合并 · list 替换"""
    out = dict(base)
    for k, v in patch.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


# ───── Self-test（mock LLM · 不需真 API）─────

if __name__ == "__main__":
    # mock 基于最近的 user message（取 up 里"用户本轮说"后到第一个 ## 前的内容）
    def _extract_user(up):
        m = re.search(r"## 用户本轮说\s*\n(.+?)(?=\n##|$)", up, re.DOTALL)
        return m.group(1).strip() if m else up

    def mock_llm(sp, up, history=None, model=None):
        user_msg = _extract_user(up)
        if "校长办公室" in user_msg:
            return json.dumps({
                "reply": "好 · 校长办公室 · 请问面积大概多少 ㎡ ?",
                "brief_patch": {
                    "project": "校长办公室 · Principal Office",
                    "client": "学校校长",
                    "space": {"type": "办公室改造"},
                },
                "next_question": "面积 ㎡",
                "pii_fields": ["client"],
            })
        elif "平米" in user_msg or "㎡" in user_msg or "30" in user_msg:
            return json.dumps({
                "reply": "30 ㎡ · 合适单人办公+小接待 · 风格偏好？",
                "brief_patch": {"space": {"area_sqm": 30, "n_floors": 1}},
                "next_question": "风格关键词",
                "pii_fields": [],
            })
        else:
            return json.dumps({"reply": "ok", "brief_patch": {}, "next_question": "", "pii_fields": []})

    print("=== Turn 1 ===")
    r = step("帮我做一个校长办公室的设计", llm_call=mock_llm)
    print(f"  reply: {r['reply']}")
    print(f"  completeness: {r['completeness']}")
    print(f"  ready: {r['ready_for_tier']}")
    print(f"  missing: {r['missing']}")
    print(f"  pii: {r['pii_fields']}")

    print("\n=== Turn 2 ===")
    r2 = step("30 平米", current_brief=r["brief"], llm_call=mock_llm)
    print(f"  reply: {r2['reply']}")
    print(f"  completeness: {r2['completeness']}")
    print(f"  missing: {r2['missing']}")
    print(f"  brief 合并后: {json.dumps(r2['brief'], ensure_ascii=False)[:150]}")

    assert "project" in r["brief"]
    assert r2["brief"]["space"]["area_sqm"] == 30
    assert r2["brief"]["space"]["type"] == "办公室改造"  # 第一轮的没被覆盖
    print("\n✓ brief_engine smoke passed")
