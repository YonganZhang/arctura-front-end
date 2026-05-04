// Vercel Edge Function · /api/projects/<slug>/overrides
//
// Phase 11.4 · ADR-001 §"差量 SSOT" · scene-ops 持久化
//
// GET    → 读 K.projectOverrides(slug) · 返当前 overrides JSON
// POST   → body: {ops: [...]} · 把 ops 转 delta 合并进现有 overrides
//          body: {overrides: {...}} · 直接 set（覆盖式 · 高级用户用）
// DELETE → query ?ns=<layout|structural|appearance|lighting|tombstones|all>
//          按 namespace reset · 默认 ?ns=all 清全部

export const config = { runtime: "edge" };

import { K } from "../../_shared/kv-keys.js";
import { opsToOverridesDelta, mergeOverridesDelta, resetOverrides } from "../../_shared/scene-ops-mapping.js";
import { validateOverrides } from "../../_shared/overrides-apply.js";
import { readAnonCookie, ANON_COOKIE_NAME } from "../../_shared/project-name.js";

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

async function readProject(slug) {
  const v = await kv("get", K.project(slug));
  return v ? JSON.parse(v) : null;
}

async function readOverrides(slug) {
  const v = await kv("get", K.projectOverrides(slug));
  return v ? JSON.parse(v) : {};
}

/**
 * 写 overrides · TTL 跟 project 状态对齐（Codex 三审 #7）
 *  - project.state == "live"      → PERSIST（不过期 · 跟 K.project 一致）
 *  - 其他 state 或 project 不存在 → 30 天 TTL（草稿期可丢）
 */
async function writeOverrides(slug, ov, projectState) {
  const val = JSON.stringify(ov);
  if (projectState === "live") {
    await kv("set", K.projectOverrides(slug), val);
    await kv("persist", K.projectOverrides(slug));
  } else {
    await kv("set", K.projectOverrides(slug), val, "EX", 30 * 86400);
  }
}

/** Owner 校验：cookie ANON_COOKIE_NAME（"arctura_anon"）必须等于 project.owner
 *  - 匿名 project（无 owner）允许任意人编辑（保留 demo 行为）
 *  - cookie 读取走 _shared/project-name.js 单一真源（防 cookie 名 drift）
 *  - body size cap 100KB（POST 双校验 · TextEncoder + content-length）
 */

const SLUG_RE = /^[a-zA-Z0-9_-]{1,64}$/;
const MAX_BODY = 100 * 1024;

function sluggify(req) {
  const url = new URL(req.url);
  const m = url.pathname.match(/\/api\/projects\/([^\/]+)\/overrides/);
  return m ? decodeURIComponent(m[1]) : null;
}

function jsonResp(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json", "Cache-Control": "no-store" },
  });
}

async function checkOwnership(slug, req) {
  /** 返 {project, error?} · error 非 null = 拒绝
   *  - project 不存在 → 404
   *  - project 有 owner 且 cookie arctura_anon 不匹配 → 403
   *  - project 无 owner 或匹配 → 通过
   */
  const project = await readProject(slug);
  if (!project) return { project: null, error: { status: 404, body: { error: "project not found" } } };
  const owner = project.owner;
  if (owner) {
    const anon = readAnonCookie(req);
    if (anon !== owner) return { project, error: { status: 403, body: { error: "forbidden · not owner" } } };
  }
  return { project, error: null };
}


export default async function handler(req) {
  const slug = sluggify(req);
  if (!slug || !SLUG_RE.test(slug)) return jsonResp({ error: "invalid slug" }, 400);

  if (req.method === "GET") {
    // GET 只要 slug 存在就允许（公开展示场景）· owner 校验只对写操作
    try {
      const ov = await readOverrides(slug);
      return jsonResp({ slug, overrides: ov });
    } catch (e) {
      return jsonResp({ error: String(e.message || e) }, 500);
    }
  }

  // 写操作：先 owner 校验
  const { project, error: ownErr } = await checkOwnership(slug, req);
  if (ownErr) return jsonResp(ownErr.body, ownErr.status);

  if (req.method === "POST") {
    // body size cap · 不能只信任 content-length（分块请求可绕过 · Codex 终审 #1）
    let raw;
    try { raw = await req.text(); }
    catch { return jsonResp({ error: "failed to read body" }, 400); }
    if (new TextEncoder().encode(raw).byteLength > MAX_BODY) {
      return jsonResp({ error: `body too large (>${MAX_BODY} bytes)` }, 413);
    }
    let body;
    try { body = JSON.parse(raw); }
    catch { return jsonResp({ error: "invalid JSON" }, 400); }

    let delta;
    if (Array.isArray(body.ops)) {
      delta = opsToOverridesDelta(body.ops);
    } else if (body.overrides && typeof body.overrides === "object") {
      delta = body.overrides;
    } else {
      return jsonResp({ error: "body must contain ops[] or overrides{}" }, 400);
    }

    const errs = validateOverrides(delta);
    if (errs.length) return jsonResp({ error: "validation failed", errors: errs }, 400);

    try {
      const cur = await readOverrides(slug);
      const merged = mergeOverridesDelta(cur, delta);
      await writeOverrides(slug, merged, project?.state);
      return jsonResp({ slug, overrides: merged, applied_ops: (body.ops || []).length });
    } catch (e) {
      return jsonResp({ error: String(e.message || e) }, 500);
    }
  }

  if (req.method === "DELETE") {
    const url = new URL(req.url);
    const ns = url.searchParams.get("ns") || "all";
    const ALLOWED = ["all", "layout", "structural", "appearance", "lighting", "tombstones"];
    if (!ALLOWED.includes(ns)) {
      return jsonResp({ error: `ns must be one of ${ALLOWED.join("|")}` }, 400);
    }
    try {
      const cur = await readOverrides(slug);
      const next = resetOverrides(cur, ns);
      if (Object.keys(next).length === 0) {
        await kv("del", K.projectOverrides(slug));
      } else {
        await writeOverrides(slug, next, project?.state);
      }
      return jsonResp({ slug, overrides: next, reset_namespace: ns });
    } catch (e) {
      return jsonResp({ error: String(e.message || e) }, 500);
    }
  }

  return jsonResp({ error: "method not allowed" }, 405);
}
