// POST /api/mvp/create · Phase 7 · Phase 10.5 错误结构化
// 入参 {slug, version} · 验 state=planning · 推 worker 队列 · 返 {job_id, stream_url}
import { K } from "../_shared/kv-keys.js";

export const config = { runtime: "edge" };

const KV_URL = process.env.UPSTASH_REDIS_REST_URL;
const KV_TOKEN = process.env.UPSTASH_REDIS_REST_TOKEN;

class KVError extends Error {
  constructor(msg, { op, key, status } = {}) {
    super(msg);
    this.code = "KV_ERROR";
    this.op = op; this.key = key; this.status = status;
  }
}

async function kv(cmd, ...args) {
  const path = [cmd, ...args.map(a => encodeURIComponent(String(a)))].join("/");
  let r;
  try {
    r = await fetch(`${KV_URL}/${path}`, {
      headers: { Authorization: `Bearer ${KV_TOKEN}` },
    });
  } catch (e) {
    // SSL EOF / network · Edge fetch 抛 TypeError
    throw new KVError(`Upstash network: ${e.message || e}`, { op: cmd, key: args[0] });
  }
  if (!r.ok) {
    const text = await r.text().catch(() => "");
    throw new KVError(`Upstash HTTP ${r.status}: ${text.slice(0, 200)}`,
                       { op: cmd, key: args[0], status: r.status });
  }
  return (await r.json()).result;
}

function errResp(where, code, message, status, ctx = {}) {
  return new Response(JSON.stringify({
    error: { where, code, message, context: ctx, retryable: code === "KV_ERROR" }
  }), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store" },
  });
}

function json(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store" },
  });
}

export default async function handler(req) {
  if (req.method !== "POST") return errResp("api.mvp.create", "METHOD_NOT_ALLOWED", "method not allowed", 405);
  let body; try { body = await req.json(); } catch { body = {}; }
  const { slug, version } = body;
  if (!slug) return errResp("api.mvp.create.validate", "MISSING_SLUG", "missing slug", 400);

  // 读 project
  let raw;
  try { raw = await kv("get", K.project(slug)); }
  catch (e) {
    return errResp("api.mvp.create.kv_get_project", e.code || "KV_ERROR",
                   e.message, 503, { slug, op: e.op, key: e.key, kv_status: e.status });
  }
  if (!raw) return errResp("api.mvp.create.lookup", "PROJECT_NOT_FOUND",
                            "project not found", 404, { slug });
  let p;
  try { p = JSON.parse(raw); }
  catch (e) {
    return errResp("api.mvp.create.parse_project", "PROJECT_CORRUPT",
                   `JSON parse: ${e.message}`, 500, { slug });
  }

  if (version !== undefined && version !== p.version) {
    return errResp("api.mvp.create.version_check", "VERSION_CONFLICT",
                   `version conflict · current=${p.version} expected=${version}`,
                   409, { slug, current: p.version, expected: version });
  }
  if (p.state !== "planning") {
    return errResp("api.mvp.create.state_check", "BAD_STATE",
                   `state=${p.state} · 必须 planning 才能生成`,
                   400, { slug, state: p.state, hint: "回选档页重选档位" });
  }
  if (!p.tier) return errResp("api.mvp.create.tier_check", "MISSING_TIER",
                                "tier 未设", 400, { slug });

  // 生成 job_id
  const rand = (n) => {
    const b = new Uint8Array(n); crypto.getRandomValues(b);
    return Array.from(b).map(x => x.toString(16).padStart(2, "0")).join("");
  };
  const job_id = `job-${rand(5)}`;
  const job = {
    id: job_id,
    slug,
    tier: p.tier,
    variant_count: p.variant_count || 1,
    render_engine: p.render_engine,
    queued_at: new Date().toISOString(),
  };

  // 推 worker 队列
  try {
    await kv("rpush", K.jobsQueue(), JSON.stringify(job));
    await kv("set", K.job(job_id), JSON.stringify({ ...job, status: "queued" }));
    await kv("expire", K.job(job_id), String(7 * 86400));
  } catch (e) {
    return errResp("api.mvp.create.enqueue", e.code || "KV_ERROR",
                   `enqueue fail: ${e.message}`, 503,
                   { slug, job_id, op: e.op, key: e.key, kv_status: e.status,
                     hint: "Upstash KV 抖动 · 稍候重试 · 不会创建重复 job" });
  }

  // 推进 project state → generating（乐观更新 · worker 会再写一次）
  p.state = "generating";
  p.version = (p.version || 0) + 1;
  p.active_job_id = job_id;
  p.updated_at = new Date().toISOString();
  try {
    await kv("set", K.project(slug), JSON.stringify(p));
  } catch (e) {
    // job 已入队 · state 没翻 · 不致命（worker 会再翻）· 但要告诉前端
    return json({
      job_id, slug,
      stream_url: `/api/jobs/${job_id}/stream`,
      status: "queued",
      estimated_min: p.tier === "concept" ? 1 : p.tier === "deliver" ? 2 : 3,
      warning: { where: "api.mvp.create.update_state", code: e.code,
                 message: `state 更新失败但 job 已入队: ${e.message}`,
                 hint: "worker 会兜底重写 state · 一般不影响" },
    }, 201);
  }

  return json({
    job_id,
    slug,
    stream_url: `/api/jobs/${job_id}/stream`,
    status: "queued",
    estimated_min: p.tier === "concept" ? 1 : p.tier === "deliver" ? 2 : 3,
  }, 201);
}
