// Vercel Edge Function · /api/projects
// GET  → 动态画廊（KV projects:index ZSET · cursor 分页 · fallback static mvps-index.json）
// POST → 创建 empty project · 返回 {slug, state}
//
// 设计：Edge 直接调 Upstash REST（fetch）· 不 spawn Python · 最低延迟
// 对齐 v3 方案 §3.1 · §3.8

export const config = { runtime: "edge" };

import { K } from "./_shared/kv-keys.js";
const KV_URL = process.env.UPSTASH_REDIS_REST_URL;
const KV_TOKEN = process.env.UPSTASH_REDIS_REST_TOKEN;

// ─────── Upstash REST helpers ───────

async function kv(cmd, ...args) {
  if (!KV_URL || !KV_TOKEN) throw new Error("UPSTASH env not set");
  const path = [cmd, ...args.map(a => encodeURIComponent(String(a)))].join("/");
  const r = await fetch(`${KV_URL}/${path}`, {
    headers: { Authorization: `Bearer ${KV_TOKEN}` },
  });
  if (!r.ok) throw new Error(`KV ${cmd} failed: ${r.status}`);
  const j = await r.json();
  return j.result;
}

async function kvGetJson(key) {
  const v = await kv("get", key);
  return v ? JSON.parse(v) : null;
}

async function kvSetJson(key, obj, { ex } = {}) {
  const val = JSON.stringify(obj);
  if (ex) return kv("set", key, val, "EX", ex);
  return kv("set", key, val);
}

async function kvZrevrange(key, start, stop) {
  return (await kv("zrevrange", key, start, stop)) || [];
}

async function kvZadd(key, score, member) {
  return kv("zadd", key, score, member);
}

async function kvZcard(key) {
  return (await kv("zcard", key)) || 0;
}

async function kvIncrExpire(key, windowS) {
  const n = await kv("incr", key);
  if (n === 1) await kv("expire", key, windowS);
  return n;
}

// ─────── Utils ───────

function json(body, status = 200, extraHeaders = {}) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": status === 200 ? "public, max-age=0, s-maxage=60" : "no-store",
      ...extraHeaders,
    },
  });
}

function getIp(req) {
  return req.headers.get("x-forwarded-for")?.split(",")[0]?.trim()
      || req.headers.get("x-real-ip")
      || "unknown";
}

function ensureAnonCookie(req) {
  const cookie = req.headers.get("cookie") || "";
  const match = cookie.match(/arctura_anon=([a-z0-9]+)/);
  if (match) return { anon: match[1], setCookie: null };
  const anon = (crypto.randomUUID?.() || Math.random().toString(36).slice(2)).replace(/-/g, "").slice(0, 16);
  const setCookie = `arctura_anon=${anon}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=${365 * 86400}`;
  return { anon, setCookie };
}

// ─────── Handlers ───────

async function handleGet(req) {
  const url = new URL(req.url);
  const limit = Math.min(parseInt(url.searchParams.get("limit") || "20", 10), 100);
  const cursor = parseInt(url.searchParams.get("cursor") || "0", 10);
  const owner = url.searchParams.get("owner"); // 'me' | null
  // 默认只返 live 项目（主页画廊）· owner=me 时看全部 state · 也可显式 state=all
  const stateFilter = url.searchParams.get("state") || (owner === "me" ? "all" : "live");

  const { anon, setCookie } = ensureAnonCookie(req);
  const headers = setCookie ? { "Set-Cookie": setCookie } : {};

  try {
    const indexKey = (owner === "me") ? K.sessionProjects(anon) : K.projectsIndex();
    const total = await kvZcard(indexKey);
    // Phase 9.5 · 小 limit 也保证 live 缓冲足够
    // 老逻辑 limit*3 在 limit=3 时 fetchCount=9 · zset 顶部 empty/briefing draft 堆积 → 全被 filter → projects=[]
    // 新逻辑 · live filter 下固定 fetch 至少 50 条 · 基本够 · 大 limit 时也放宽到 limit*5
    const fetchCount = stateFilter === "all" ? limit : Math.min(Math.max(limit * 5, 50), 300);
    const slugs = await kvZrevrange(indexKey, cursor, cursor + fetchCount - 1);

    const rawProjects = await Promise.all(slugs.map(async slug => {
      const p = await kvGetJson(K.project(slug));
      if (!p) return null;
      return {
        slug: p.slug,
        display_name: p.display_name,
        state: p.state,
        tier: p.tier,
        hero_img: p.artifacts?.urls?.hero_img || null,
        updated_at: p.updated_at,
        visibility: p.visibility,
      };
    }));

    const filtered = rawProjects.filter(p => {
      if (!p) return false;
      if (stateFilter === "all") return true;
      if (stateFilter === "live") return p.state === "live";
      return p.state === stateFilter;
    }).slice(0, limit);

    return json({
      projects: filtered,
      next_cursor: null,  // 简化：前端要更多可加 cursor · 本版默认取 20
      total,
      state_filter: stateFilter,
      source: "kv",
    }, 200, headers);
  } catch (e) {
    // KV 失败 · fallback 到静态 mvps-index.json
    console.error("[projects GET] KV failed, fallback:", e.message);
    try {
      const origin = new URL(req.url).origin;
      const r = await fetch(`${origin}/data/mvps-index.json`);
      const list = await r.json();
      return json({
        projects: list.slice(cursor, cursor + limit).map(e => ({
          slug: e.slug,
          display_name: e.name_zh || e.name,
          state: "live",
          hero_img: e.hero,
          updated_at: null,
          visibility: "public",
        })),
        next_cursor: (cursor + limit < list.length) ? (cursor + limit) : null,
        total: list.length,
        source: "static-fallback",
      }, 200, headers);
    } catch (e2) {
      return json({ error: "kv + static both failed", detail: String(e2.message || e2) }, 500, headers);
    }
  }
}

async function handlePost(req) {
  const { anon, setCookie } = ensureAnonCookie(req);
  const ip = getIp(req);
  const headers = setCookie ? { "Set-Cookie": setCookie } : {};

  // Rate limit: per IP 50/h · per session 100/day（Phase 6 测试期放宽 · 后续可收紧）
  try {
    const ipCount = await kvIncrExpire(K.rateIp(ip), 3600);
    if (ipCount > 50) {
      return json({ error: "rate limit · per IP", retry_after_s: 3600, retryable: true }, 429, headers);
    }
    const sCount = await kvIncrExpire(K.rateSession(anon), 86400);
    if (sCount > 100) {
      return json({ error: "rate limit · per session", retry_after_s: 86400, retryable: true }, 429, headers);
    }
  } catch (e) {
    console.error("[rate limit check]", e);  // 不因 rate limit 检查失败阻塞
  }

  let body;
  try {
    body = await req.json();
  } catch {
    body = {};
  }
  const display_name = (body.display_name || "Untitled Project").slice(0, 80);

  // 生成 slug · draft-<rand8>
  const rand = () => {
    const bytes = new Uint8Array(4);
    crypto.getRandomValues(bytes);
    return Array.from(bytes).map(b => b.toString(16).padStart(2, "0")).join("");
  };
  const slug = `draft-${rand()}`;

  const now = new Date().toISOString();
  const project = {
    slug,
    state: "empty",
    version: 1,
    visibility: "private",
    owner: anon,
    display_name,
    brief: null,
    brief_schema_version: "v1",
    tier: null,
    variant_count: 1,
    render_engine: null,
    scene: null,
    scene_schema_version: "v1",
    artifacts: { produced: [], skipped: [], errors: [], partial: false, timing_ms: {}, urls: {} },
    pending_count: 0,
    last_save_ref: null,
    created_at: now,
    updated_at: now,
    _pii_fields: [],
  };

  try {
    await kvSetJson(K.project(slug), project, { ex: 7 * 86400 });
    const score = Math.floor(Date.now() / 1000);
    await kvZadd(K.projectsIndex(), score, slug);
    await kvZadd(K.sessionProjects(anon), score, slug);
    return json({
      slug,
      state: "empty",
      url: `/new?slug=${slug}`,
    }, 201, headers);
  } catch (e) {
    return json({ error: "kv write failed", detail: String(e.message || e) }, 503, headers);
  }
}

// ─────── Entry ───────

export default async function handler(req) {
  if (req.method === "OPTIONS") {
    return new Response(null, {
      status: 204,
      headers: {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
      },
    });
  }
  if (req.method === "GET") return handleGet(req);
  if (req.method === "POST") return handlePost(req);
  return json({ error: "method not allowed" }, 405);
}
