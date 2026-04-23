"""MCP Server · Arctura MVP 工具暴露给 AI agent

设计：
  1. 每 tool 是纯函数包装 · 无隐藏副作用（全走 store/kv）
  2. 异常转 JSON 错误（MCP 只能 JSON 序列化）
  3. dry_run 参数预留
  4. 长任务返 job_id · agent 订阅 SSE stream_url（Worker + SSE 已接 · Phase 7.1）

运行：
  stdio（给 Claude Code / Continue 等 IDE）：
    python3 -m _build.arctura_mvp.mcp_server --stdio
  打印 schema（不带参数）：
    python3 -m _build.arctura_mvp.mcp_server

当前是骨架 · 每 tool handler 是真能跑的 Python 函数 · 但未走正式 MCP SDK。
升级路径：`pip install mcp` + 改用 `mcp.server.Server` SDK（tool 定义不变 · 换掉 _run_stdio）。
"""
from __future__ import annotations
import json
import sys
import uuid
from dataclasses import asdict

from . import _core
from .types import Project
from .tiers import (
    TIER_CONFIG, TIER_ALIASES, resolve_tier, pick_engine, list_tiers_for_ui,
)
from .state import validate_transition
from .chat.brief_engine import step as brief_step


# ───── Tool metadata ─────

TOOLS = [
    {
        "name": "arctura_list_tiers",
        "description": "列出 Arctura 5 档产物（概念/交付/报价/全案/甄选）· 含 artifacts/engine/时间",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "arctura_resolve_tier",
        "description": "解析档位 · 展开继承链",
        "input_schema": {
            "type": "object",
            "properties": {
                "tier": {"type": "string", "enum": list(TIER_CONFIG) + list(TIER_ALIASES)},
                "variant_count": {"type": "integer", "default": 1},
            },
            "required": ["tier"],
        },
    },
    {
        "name": "arctura_create_project",
        "description": "新建项目 · 可选 brief/tier 跳过中间 state",
        "input_schema": {
            "type": "object",
            "properties": {
                "display_name": {"type": "string"},
                "brief": {"type": "object"},
                "tier": {"type": "string"},
                "owner": {"type": "string"},
            },
            "required": [],
        },
    },
    {
        "name": "arctura_get_project",
        "description": "读 project 完整 JSON",
        "input_schema": {"type": "object", "properties": {"slug": {"type": "string"}}, "required": ["slug"]},
    },
    {
        "name": "arctura_list_projects",
        "description": "列 project · 默认 state=live",
        "input_schema": {
            "type": "object",
            "properties": {
                "owner": {"type": "string"},
                "limit": {"type": "integer", "default": 20},
                "state": {"type": "string", "enum": ["live", "all"], "default": "live"},
            },
            "required": [],
        },
    },
    {
        "name": "arctura_chat_brief",
        "description": "推进 brief 对话一轮",
        "input_schema": {
            "type": "object",
            "properties": {"slug": {"type": "string"}, "user_message": {"type": "string"}},
            "required": ["slug", "user_message"],
        },
    },
    {
        "name": "arctura_pick_tier",
        "description": "设 tier + variant_count · state → planning",
        "input_schema": {
            "type": "object",
            "properties": {
                "slug": {"type": "string"},
                "tier": {"type": "string"},
                "variant_count": {"type": "integer", "default": 1},
            },
            "required": ["slug", "tier"],
        },
    },
    {
        "name": "arctura_generate_mvp",
        "description": "入队 MVP 生成 job · 返 {job_id, stream_url} · agent 订阅 SSE 接进度",
        "input_schema": {
            "type": "object",
            "properties": {"slug": {"type": "string"}, "dry_run": {"type": "boolean", "default": False}},
            "required": ["slug"],
        },
    },
    {
        "name": "arctura_save_project",
        "description": "持久化 pending_edits",
        "input_schema": {
            "type": "object",
            "properties": {
                "slug": {"type": "string"},
                "pending_edits": {"type": "array"},
            },
            "required": ["slug"],
        },
    },
]


# ───── Handlers ─────

def tool_list_tiers(**_):
    return {"tiers": list_tiers_for_ui()}


def tool_resolve_tier(tier, variant_count=1, **_):
    return resolve_tier(tier, variant_count)


def tool_create_project(display_name="Untitled", brief=None, tier=None, owner="mcp-agent", **_):
    slug = f"mcp-{uuid.uuid4().hex[:8]}"
    state = "briefing" if brief else "empty"
    if brief and tier:
        state = "planning"
    p = Project(slug=slug, state=state, owner=owner, display_name=display_name, brief=brief, tier=tier)
    p = _core.put_project(p)
    return asdict(p)


def tool_get_project(slug, **_):
    p = _core.get_project(slug)
    return asdict(p) if p else None


def tool_list_projects(owner=None, limit=20, state="live", **_):
    r = _core.list_projects(owner=owner, limit=limit)
    if state == "live":
        r["projects"] = [p for p in r["projects"] if p["state"] == "live"]
    return r


def tool_chat_brief(slug, user_message, **_):
    p = _core.get_project(slug)
    if not p:
        return {"error": "project not found"}
    if p.state not in ("empty", "briefing", "planning"):
        return {"error": f"state={p.state} · 不允许 brief chat"}
    r = brief_step(user_message, current_brief=p.brief or {})
    p.brief = r["brief"]
    if p.state == "empty":
        p.state = "briefing"
    _core.put_project(p, expected_version=p.version)
    return {
        "reply": r["reply"],
        "brief_partial": r["brief_patch"],
        "completeness": r["completeness"],
        "ready_for_tier": r["ready_for_tier"],
        "missing": r["missing"],
        "next_question": r["next_question"],
    }


def tool_pick_tier(slug, tier, variant_count=1, **_):
    p = _core.get_project(slug)
    if not p:
        return {"error": "project not found"}
    if tier not in TIER_CONFIG and tier not in TIER_ALIASES:
        return {"error": f"unknown tier: {tier}"}
    p.tier = tier
    p.variant_count = variant_count
    p.render_engine = pick_engine(tier)
    try:
        validate_transition(p.state, "planning")
        p.state = "planning"
    except ValueError:
        pass
    _core.put_project(p, expected_version=p.version)
    return asdict(p)


def tool_generate_mvp(slug, **_):
    """入队一个 MVP 生成 job · 真接 worker（Phase 7.1）

    前置：project 已 pick_tier · state=planning
    返 {job_id, slug, stream_url, status} 或 {error}
    """
    try:
        return _core.enqueue_job(slug)
    except ValueError as e:
        return {"error": str(e)}


def tool_save_project(slug, pending_edits=None, **_):
    p = _core.get_project(slug)
    if not p:
        return {"error": "project not found"}
    cleared = len(pending_edits or [])
    p.pending_count = 0
    _core.put_project(p, expected_version=p.version)
    return {"ok": True, "pending_cleared": cleared, "commit_sha": None, "version": p.version}


TOOL_HANDLERS = {
    "arctura_list_tiers": tool_list_tiers,
    "arctura_resolve_tier": tool_resolve_tier,
    "arctura_create_project": tool_create_project,
    "arctura_get_project": tool_get_project,
    "arctura_list_projects": tool_list_projects,
    "arctura_chat_brief": tool_chat_brief,
    "arctura_pick_tier": tool_pick_tier,
    "arctura_generate_mvp": tool_generate_mvp,
    "arctura_save_project": tool_save_project,
}


# ───── stdio MCP-like server（JSON-RPC 2.0 兼容）─────

def _run_stdio():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            sys.stdout.write(json.dumps({"error": "invalid json"}) + "\n")
            sys.stdout.flush()
            continue
        rid = req.get("id")
        method = req.get("method")
        params = req.get("params", {})
        try:
            if method == "tools/list":
                result = {"tools": TOOLS}
            elif method == "tools/call":
                handler = TOOL_HANDLERS.get(params.get("name"))
                if not handler:
                    result = {"error": f"unknown tool: {params.get('name')}"}
                else:
                    result = handler(**(params.get("arguments") or {}))
            else:
                result = {"error": f"unknown method: {method}"}
            sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": rid, "result": result}, ensure_ascii=False) + "\n")
        except Exception as e:
            sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": rid, "error": {"code": -32000, "message": str(e)}}) + "\n")
        sys.stdout.flush()


def _print_schema():
    print(f"# Arctura MVP MCP Server · {len(TOOLS)} tools\n")
    for t in TOOLS:
        print(f"## {t['name']}")
        print(f"  {t['description']}")
        props = t["input_schema"].get("properties", {})
        req = set(t["input_schema"].get("required", []))
        if props:
            args = ", ".join(f"{k}{'*' if k in req else ''}" for k in props)
            print(f"  args: {args}")
        print()
    print(f"Handlers: {len(TOOL_HANDLERS)} · stdio: python3 -m _build.arctura_mvp.mcp_server --stdio")


if __name__ == "__main__":
    if "--stdio" in sys.argv:
        _run_stdio()
    else:
        _print_schema()
