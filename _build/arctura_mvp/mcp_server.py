"""MCP Server · Arctura Phase 8 · Namespace-based tool layout

设计（一劳永逸 · 扩展友好）：
  1. Tools grouped by resource namespace · `arctura_<resource>_<verb>`
  2. TOOL_NAMESPACES dict · 加新 tool = 加一行 dict entry · 无副作用
  3. 旧 tool 名保留 alias · 下版本 deprecate

运行：
  stdio（给 Claude Code / Continue 等 IDE）：
    python3 -m _build.arctura_mvp.mcp_server --stdio
  打印 schema（不带参数）：
    python3 -m _build.arctura_mvp.mcp_server

JSON-RPC 2.0 兼容 · tools/list + tools/call。
"""
from __future__ import annotations
import json
import os
import secrets
import sys
import uuid
from dataclasses import asdict

from . import _core
from .types import Project
from .product_registry import (
    PRODUCTS, TIER_META, list_tiers_for_ui,
    resolve_tier_products, get_spec_for_artifact, all_tier_ids,
)
from .tiers import resolve_tier, pick_engine
from .state import validate_transition
from .chat.brief_engine import step as brief_step


# ───────────────────────────────────────────────────────────
# Namespace: project (CRUD + revision)
# ───────────────────────────────────────────────────────────

def tool_project_create(display_name="Untitled", brief=None, tier=None, owner="mcp-agent", **_):
    slug = f"mcp-{uuid.uuid4().hex[:8]}"
    state = "briefing" if brief else "empty"
    if brief and tier:
        state = "planning"
    p = Project(slug=slug, state=state, owner=owner, display_name=display_name,
                brief=brief, tier=tier)
    p = _core.put_project(p)
    return asdict(p)


def tool_project_get(slug, **_):
    p = _core.get_project(slug)
    return asdict(p) if p else None


def tool_project_list(owner=None, limit=20, state="live", **_):
    r = _core.list_projects(owner=owner, limit=limit)
    if state == "live":
        r["projects"] = [p for p in r["projects"] if p["state"] == "live"]
    return r


def tool_project_delete(slug, **_):
    ok = _core.delete_project(slug)
    return {"deleted": ok}


def tool_project_history(slug, **_):
    """返 data/mvps/<slug>.json 的 GitHub commit 历史（通过本地 gh CLI）"""
    import subprocess
    try:
        proc = subprocess.run(
            ["gh", "api",
             f"repos/YonganZhang/arctura-front-end/commits?path=data/mvps/{slug}.json&per_page=20"],
            capture_output=True, text=True, timeout=15,
        )
        if proc.returncode != 0:
            return {"error": f"gh api fail: {proc.stderr[:200]}", "commits": []}
        data = json.loads(proc.stdout)
        return {"commits": [
            {"sha": c["sha"], "short_sha": c["sha"][:7],
             "date": c["commit"]["committer"]["date"],
             "message": c["commit"]["message"]}
            for c in data
        ]}
    except Exception as e:
        return {"error": str(e), "commits": []}


# ───────────────────────────────────────────────────────────
# Namespace: brief
# ───────────────────────────────────────────────────────────

def tool_brief_chat(slug, user_message, **_):
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
        "brief": r["brief"],
        "completeness": r["completeness"],
        "ready_for_tier": r["ready_for_tier"],
        "missing": r["missing"],
        "next_question": r["next_question"],
    }


def tool_brief_validate(brief, **_):
    """用 vendor/schemas/brief-interior.schema.json 验证 brief · + completeness"""
    from .chat.brief_engine import completeness, ready_for_tier, missing_must_fields
    return {
        "valid": brief is not None and isinstance(brief, dict),
        "completeness": completeness(brief),
        "ready_for_tier": ready_for_tier(brief),
        "missing_must": missing_must_fields(brief),
    }


# ───────────────────────────────────────────────────────────
# Namespace: tier
# ───────────────────────────────────────────────────────────

def tool_tier_list(**_):
    return {"tiers": list_tiers_for_ui()}


def tool_tier_resolve(tier, variant_count=1, **_):
    return resolve_tier(tier, variant_count)


def tool_tier_pick(slug, tier, variant_count=1, **_):
    """设 project.tier + state→planning · 为后续 job_enqueue 铺路"""
    p = _core.get_project(slug)
    if not p:
        return {"error": "project not found"}
    if tier not in all_tier_ids():
        return {"error": f"unknown tier: {tier} · valid={all_tier_ids()}"}
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


# ───────────────────────────────────────────────────────────
# Namespace: pipeline (严老师 pipeline catalog read-only)
# ───────────────────────────────────────────────────────────

# Pipeline catalog · 只读 · Phase 8 从严老师 spec 提炼
_PIPELINE_CATALOG = [
    {"id": "P0", "name": "Asset Intake", "script": "playbooks/scripts/asset-intake/",
     "light_compat": "partial", "purpose": "客户文件 → brief + IFC"},
    {"id": "P1", "name": "Interior Design", "script": "CLI-Anything/blender (full)",
     "light_compat": "no", "purpose": "单房间 3D + 渲染 + 平面图"},
    {"id": "P2", "name": "Architecture Design", "script": "CLI-Anything/blender (full)",
     "light_compat": "no", "purpose": "多层建筑 3D + 制图"},
    {"id": "P3", "name": "Brief Intake", "script": "playbooks/scripts/brief-intake/run_intake.py",
     "light_compat": "polyfilled", "purpose": "自由文本 → brief.json（LIGHT 用 /api/brief/chat）"},
    {"id": "P4", "name": "AI Render Enhancement", "script": "playbooks/scripts/ai_render/",
     "light_compat": "no", "purpose": "ControlNet + SDXL 写实化"},
    {"id": "P6", "name": "BOQ", "script": "CLI-Anything/openstudio report boq",
     "light_compat": "no", "purpose": "工料报价"},
    {"id": "P7", "name": "Energy-Sim", "script": "CLI-Anything/openstudio run simulate",
     "light_compat": "no", "purpose": "EnergyPlus 能耗模拟"},
    {"id": "P8", "name": "Compliance", "script": "CLI-Anything/openstudio report compliance",
     "light_compat": "no", "purpose": "codes.json v2 合规检查"},
    {"id": "P9", "name": "What-If", "script": "CLI-Anything/openstudio report whatif",
     "light_compat": "no", "purpose": "参数敏感性扫描"},
    {"id": "P10", "name": "A/B Variants", "script": "playbooks/scripts/ab-comparison/",
     "light_compat": "partial", "purpose": "3 方案对比 · LIGHT 可产 diff-matrix"},
    {"id": "P11", "name": "Case Study", "script": "playbooks/scripts/case-study/",
     "light_compat": "polyfilled", "purpose": "portfolio/impact/sales · LIGHT 可产"},
]


def tool_pipeline_list(**_):
    return {"pipelines": _PIPELINE_CATALOG}


def tool_pipeline_describe(pipeline_id, **_):
    for p in _PIPELINE_CATALOG:
        if p["id"] == pipeline_id:
            return p
    return {"error": f"unknown pipeline: {pipeline_id}"}


# ───────────────────────────────────────────────────────────
# Namespace: artifact (registry read API)
# ───────────────────────────────────────────────────────────

def tool_artifact_list(tier=None, **_):
    """列所有产物 · 可按 tier 过滤"""
    if tier:
        products = resolve_tier_products(tier)
    else:
        products = list(PRODUCTS.values())
    return {
        "artifacts": [
            {
                "key": p.key,
                "id": p.id,
                "name": p.name,
                "lang_hint_en": p.lang_hint_en,
                "tiers": p.tiers,
                "light_compatible": p.light_producer is not None,
                "full_pipeline": p.full_pipeline,
                "spec_ref": p.spec_ref,
                "addon": p.addon,
            }
            for p in products
        ]
    }


def tool_artifact_describe(name, **_):
    spec = get_spec_for_artifact(name)
    if not spec:
        return {"error": f"unknown artifact: {name}"}
    return {
        **{k: v for k, v in asdict(spec).items()},
        "light_compatible": spec.light_producer is not None,
    }


# ───────────────────────────────────────────────────────────
# Namespace: job (enqueue + status)
# ───────────────────────────────────────────────────────────

def tool_job_enqueue(slug, **_):
    """入队 MVP 生成 job · 返 {job_id, stream_url}"""
    try:
        return _core.enqueue_job(slug)
    except ValueError as e:
        return {"error": str(e)}


def tool_job_status(job_id, **_):
    """查 job 状态 · 从 KV 读"""
    from .store import kv, keys as K
    try:
        meta_raw = kv.get(K.job(job_id))
        if not meta_raw:
            return {"error": "job not found", "job_id": job_id}
        return json.loads(meta_raw)
    except Exception as e:
        return {"error": str(e)}


# ───────────────────────────────────────────────────────────
# Namespace: save
# ───────────────────────────────────────────────────────────

def tool_save_project(slug, pending_edits=None, **_):
    """持久化 pending_edits · 真 git commit 走 /api/projects/<slug>/save Edge function
    · MCP 侧这里只 KV update（因 Python 无 GITHUB_TOKEN 本地）
    """
    p = _core.get_project(slug)
    if not p:
        return {"error": "project not found"}
    cleared = len(pending_edits or [])
    p.pending_count = 0
    _core.put_project(p, expected_version=p.version)
    return {"ok": True, "pending_cleared": cleared, "commit_sha": None,
            "version": p.version,
            "_note": "真 git commit 走 Edge /api/projects/<slug>/save · MCP 只 KV"}


# ───────────────────────────────────────────────────────────
# Namespace table · 加 tool = 在这里加一行
# ───────────────────────────────────────────────────────────

TOOL_NAMESPACES: dict[str, dict] = {
    "project": {
        "create":  tool_project_create,
        "get":     tool_project_get,
        "list":    tool_project_list,
        "delete":  tool_project_delete,
        "history": tool_project_history,
    },
    "brief": {
        "chat":     tool_brief_chat,
        "validate": tool_brief_validate,
    },
    "tier": {
        "list":    tool_tier_list,
        "resolve": tool_tier_resolve,
        "pick":    tool_tier_pick,
    },
    "pipeline": {
        "list":     tool_pipeline_list,
        "describe": tool_pipeline_describe,
    },
    "artifact": {
        "list":     tool_artifact_list,
        "describe": tool_artifact_describe,
    },
    "job": {
        "enqueue": tool_job_enqueue,
        "status":  tool_job_status,
    },
    "save": {
        "project": tool_save_project,
    },
}


def _build_handlers() -> dict[str, callable]:
    out = {}
    for ns, verbs in TOOL_NAMESPACES.items():
        for verb, fn in verbs.items():
            out[f"arctura_{ns}_{verb}"] = fn
    return out


# ───────────────────────────────────────────────────────────
# Backward-compat aliases · 旧工具名继续 work · Phase 9 deprecate
# ───────────────────────────────────────────────────────────

TOOL_ALIASES: dict[str, str] = {
    "arctura_list_tiers":     "arctura_tier_list",
    "arctura_resolve_tier":   "arctura_tier_resolve",
    "arctura_create_project": "arctura_project_create",
    "arctura_get_project":    "arctura_project_get",
    "arctura_list_projects":  "arctura_project_list",
    "arctura_chat_brief":     "arctura_brief_chat",
    "arctura_pick_tier":      "arctura_tier_pick",
    "arctura_generate_mvp":   "arctura_job_enqueue",
    "arctura_save_project":   "arctura_save_project",
}


TOOL_HANDLERS = _build_handlers()
# 旧名映射到新 handler
for old, new in TOOL_ALIASES.items():
    if new in TOOL_HANDLERS:
        TOOL_HANDLERS[old] = TOOL_HANDLERS[new]


# ───────────────────────────────────────────────────────────
# Schema · tools/list 响应
# ───────────────────────────────────────────────────────────

def _build_tools_schema() -> list[dict]:
    """简化的 input_schema 生成 · 用 inspect.signature 推参数
    · Phase 8 · 基本参数只声明类型 · required 按 non-default 推
    """
    import inspect
    tools = []
    for ns, verbs in TOOL_NAMESPACES.items():
        for verb, fn in verbs.items():
            name = f"arctura_{ns}_{verb}"
            sig = inspect.signature(fn)
            props = {}
            required = []
            for pname, param in sig.parameters.items():
                if pname == "_" or param.kind == inspect.Parameter.VAR_KEYWORD:
                    continue
                if param.kind == inspect.Parameter.VAR_POSITIONAL:
                    continue
                t = "string"
                if param.annotation is int or (isinstance(param.default, int) and param.default is not None):
                    t = "integer"
                elif param.annotation is bool or isinstance(param.default, bool):
                    t = "boolean"
                elif isinstance(param.default, list):
                    t = "array"
                elif isinstance(param.default, dict):
                    t = "object"
                props[pname] = {"type": t}
                if param.default is inspect.Parameter.empty:
                    required.append(pname)
            doc = (fn.__doc__ or "").strip().split("\n")[0][:80]
            tools.append({
                "name": name,
                "description": doc,
                "input_schema": {"type": "object", "properties": props, "required": required},
            })
    return tools


TOOLS = _build_tools_schema()


# ───────────────────────────────────────────────────────────
# stdio JSON-RPC 2.0 compatible server
# ───────────────────────────────────────────────────────────

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
                    args = params.get("arguments", {})
                    result = handler(**args)
            else:
                result = {"error": f"unknown method: {method}"}
            resp = {"jsonrpc": "2.0", "id": rid, "result": result}
        except Exception as e:
            resp = {"jsonrpc": "2.0", "id": rid,
                    "error": {"code": -32603, "message": str(e)}}
        sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
        sys.stdout.flush()


# ───────────────────────────────────────────────────────────
# CLI entry
# ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    if "--stdio" in sys.argv:
        _run_stdio()
    else:
        # 不带参 · 打印 schema + namespace summary
        print(f"Arctura MCP · Phase 8 · {len(TOOL_HANDLERS)} tools (含 {len(TOOL_ALIASES)} alias)")
        print(f"\nNamespaces:")
        for ns, verbs in TOOL_NAMESPACES.items():
            print(f"  {ns}: {', '.join(verbs.keys())}")
        print(f"\nTool schemas:")
        print(json.dumps(TOOLS, ensure_ascii=False, indent=2))
