// Vercel Edge Function · /api/projects/<slug>
// GET   → 读 KV project:<slug> 返回 Project JSON
// PATCH → 设 tier / variant_count / state 推进 · optimistic lock via version
//
// 对齐 Phase 6 v3 方案 §3.3

export const config = { runtime: "edge" };

const KV_URL = process.env.UPSTASH_REDIS_REST_URL;
const KV_TOKEN = process.env.UPSTASH_REDIS_REST_TOKEN;

async function kv(cmd, ...args) {
  const path = [cmd, ...args.map(a => encodeURIComponent(String(a)))].join("/");
  const r = await fetch(`${KV_URL}/${path}`, {
    headers: { Authorization: `Bearer ${KV_TOKEN}` },
  });
  if (!r.ok) throw new Error(`KV ${cmd}: HTTP ${r.status}`);
  return (await r.json()).result;
}

async function getProject(slug) {
  const v = await kv("get", K.project(slug));
  return v ? JSON.parse(v) : null;
}

async function putProject(p, ttl) {
  const val = JSON.stringify(p);
  if (ttl) return kv("set", K.project(p.slug), val, "EX", ttl);
  await kv("set", K.project(p.slug), val);
  await kv("persist", K.project(p.slug));
  return true;
}

function json(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store" },
  });
}

// Phase 9 · brief must_fill 硬校验 · 对齐 spec L356 + schemas/brief-rules.json
// 跟 _build/arctura_mvp/chat/brief_engine.py::MUST_FILL_FOR_PLANNING 保持一致
import briefRules from "../_shared/brief-rules.json" with { type: "json" };

function _pathGet(obj, path) {
  if (!obj) return null;
  const keys = path.includes(".") ? path.split(".") : [path];
  let cur = obj;
  for (const k of keys) {
    if (cur == null || typeof cur !== "object") return null;
    cur = cur[k];
  }
  return cur;
}

function _nonempty(v) {
  if (v == null) return false;
  if (typeof v === "string" && v.length === 0) return false;
  if (Array.isArray(v) && v.length === 0) return false;
  if (typeof v === "object" && !Array.isArray(v) && Object.keys(v).length === 0) return false;
  return true;
}

function _missingMustFill(brief) {
  const must = briefRules.must_fill_for_planning || [];
  return must.filter(p => !_nonempty(_pathGet(brief, p)));
}

import { K } from "../_shared/kv-keys.js";
// state machine · 读 schemas/state-machine.json（单一真源 · Python state.py 也读它）
import stateMachine from "../_shared/state-machine.json" with { type: "json" };

const TRANSITIONS = Object.fromEntries(
  Object.entries(stateMachine.transitions).map(([s, arr]) => [s, new Set(arr)])
);

function canTransition(from, to) {
  return TRANSITIONS[from]?.has(to) || false;
}

function getSlug(req) {
  // Vercel Edge 从 URL 里提（dynamic route · [slug].js）
  const url = new URL(req.url);
  const m = url.pathname.match(/\/api\/projects\/([^/]+)/);
  return m ? decodeURIComponent(m[1]) : null;
}

export default async function handler(req) {
  const slug = getSlug(req);
  if (!slug) return json({ error: "bad slug" }, 400);

  if (req.method === "GET") {
    const p = await getProject(slug);
    if (!p) return json({ error: "not found" }, 404);
    return json(p);
  }

  if (req.method === "PATCH") {
    let body;
    try { body = await req.json(); } catch { return json({ error: "bad json" }, 400); }
    const { tier, variant_count, render_engine, state: newState, display_name, version } = body;

    const p = await getProject(slug);
    if (!p) return json({ error: "not found" }, 404);

    // optimistic lock
    if (version !== undefined && version !== p.version) {
      return json({ error: "version conflict", expected: version, current: p.version, retryable: false }, 409);
    }

    // state transition guard
    if (newState && newState !== p.state && !canTransition(p.state, newState)) {
      return json({ error: `illegal transition: ${p.state} → ${newState}` }, 400);
    }

    // Phase 9 · spec L356 硬校验 · 进 planning 前 brief must_fill 必须齐
    if (newState === "planning") {
      const missing = _missingMustFill(p.brief || {});
      if (missing.length > 0) {
        return json({
          error: "brief 必填字段缺失 · 无法进入选档位阶段",
          missing,
          hint: "先完成 brief · 覆盖 project / space.area_sqm / headcount / style.keywords / functional_zones",
        }, 400);
      }
    }

    // apply patch
    if (tier !== undefined) p.tier = tier;
    if (variant_count !== undefined) p.variant_count = variant_count;
    if (render_engine !== undefined) p.render_engine = render_engine;
    if (newState !== undefined) p.state = newState;
    if (display_name !== undefined) p.display_name = String(display_name).slice(0, 80);
    p.version = (p.version || 0) + 1;
    p.updated_at = new Date().toISOString();

    const ttl = p.state === "live" ? null : 7 * 86400;
    await putProject(p, ttl);
    return json(p);
  }

  if (req.method === "DELETE") {
    // 软删 · 30 天 TTL
    const p = await getProject(slug);
    if (!p) return json({ error: "not found" }, 404);
    await kv("zrem", K.projectsIndex(), slug);
    if (p.owner) await kv("zrem", K.sessionProjects(p.owner), slug);
    await kv("expire", K.project(slug), String(30 * 86400));
    return json({ deleted: true });
  }

  return json({ error: "method not allowed" }, 405);
}
