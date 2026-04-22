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

# 必填项（ready_for_tier 触发条件）· 不是 schema required · 是 UX 判断
MUST_FILL_FOR_PLANNING = [
    "project",               # 项目名
    ("space", "area_sqm"),   # 面积
    ("style", "keywords"),   # 风格关键词
    "functional_zones",      # 功能分区（非空）
]

# 重要但可 LLM 默认补全（影响 completeness 计算）· 全填 = 1.0
NICE_TO_HAVE = [
    "slug", "client", "business_model",
    ("space", "type"), ("space", "n_floors"),
    ("style", "palette"), ("style", "reference_brands"),
    "lighting", "budget_hkd", "timeline_weeks", "must_have",
    ("envelope", "insulation_mm"), ("openings", "wwr"),
]


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
    """0.0-1.0 · must-fill 占 60% · nice-to-have 占 40%"""
    if not brief:
        return 0.0
    must_score = sum(1 for p in MUST_FILL_FOR_PLANNING if _nonempty(_path_get(brief, p))) / len(MUST_FILL_FOR_PLANNING)
    nice_score = sum(1 for p in NICE_TO_HAVE if _nonempty(_path_get(brief, p))) / len(NICE_TO_HAVE)
    return round(must_score * 0.6 + nice_score * 0.4, 2)


def ready_for_tier(brief: dict) -> bool:
    """所有 must-fill 都填 + completeness ≥ 0.5"""
    for p in MUST_FILL_FOR_PLANNING:
        if not _nonempty(_path_get(brief, p)):
            return False
    return completeness(brief) >= 0.5


def missing_must_fields(brief: dict) -> list[str]:
    out = []
    for p in MUST_FILL_FOR_PLANNING:
        if not _nonempty(_path_get(brief, p)):
            out.append(".".join(p) if isinstance(p, tuple) else p)
    return out


# ───── LLM prompt ─────

SYSTEM_PROMPT = """你是 Arctura 室内设计 brief 对话助手 · 帮用户通过多轮对话生成设计 brief。

**你的目标**：通过 3-7 轮对话把用户的想法填到 brief JSON 里。必须字段（阻塞进入"选档位"阶段）：
- project · 项目名（含中英文）
- space.area_sqm · 面积（数字 · 单位㎡）
- style.keywords · 风格关键词（数组 · 3-6 个）
- functional_zones · 功能分区（数组 · 每区有 name/area_sqm）

**重要但可选**（影响 completeness · 不阻塞）：
slug / client / business_model / space.type / space.n_floors / style.palette / style.reference_brands / lighting / budget_hkd / timeline_weeks / must_have / envelope.insulation_mm / openings.wwr

**对话规则**：
1. 每次**先回复人话**（中文 · 1-2 句 · 确认+引导）· 然后给 JSON 更新
2. 一次只问 1-2 个问题 · 不要连珠炮
3. 用户回答不清楚时 · 给 2-3 个示例引导（比如"日式禅 / 现代极简 / 新中式"）
4. 如果用户已经在一段话里说了很多 · 一次性提取所有字段 · 不要装不懂
5. 用户的 PII（客户名 / 地址 / 预算）标入 `_pii_fields` 字段
6. LLM 自己推导合理默认时 · 标注字段 · 用户可改

**输出格式**（严格）：

```json
{
  "reply": "给用户看的中文回复 · 1-2 句 · 含下一步引导或问题",
  "brief_patch": {
    /* 本轮要更新/追加的字段 · JSON Patch 风格 · merge 到当前 brief */
  },
  "next_question": "下一轮你会问什么 · 简短 · 用于 UI 提示",
  "pii_fields": [ /* 本轮用户输入中的 PII 字段路径 · 如 ["client", "space.address"] */ ]
}
```

严格只输出这个 JSON · 不加其他说明文字（UI 渲染需要）。"""


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
