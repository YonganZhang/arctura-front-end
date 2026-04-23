// POST /api/mvp/create · Phase 7
// 入参 {slug, version} · 验 state=planning · 推 worker 队列 · 返 {job_id, stream_url}
import { K } from "../_shared/kv-keys.js";

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

function json(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store" },
  });
}

export default async function handler(req) {
  if (req.method !== "POST") return json({ error: "method not allowed" }, 405);
  let body; try { body = await req.json(); } catch { body = {}; }
  const { slug, version } = body;
  if (!slug) return json({ error: "missing slug" }, 400);

  // 读 project
  const raw = await kv("get", K.project(slug));
  if (!raw) return json({ error: "project not found" }, 404);
  const p = JSON.parse(raw);

  if (version !== undefined && version !== p.version) {
    return json({ error: "version conflict", current: p.version }, 409);
  }
  if (p.state !== "planning") {
    return json({ error: `state=${p.state} · 必须 planning 才能生成` }, 400);
  }
  if (!p.tier) return json({ error: "tier 未设" }, 400);

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
    // 记 job meta（供 stream 显示）· 7 天 TTL
    await kv("set", K.job(job_id), JSON.stringify({ ...job, status: "queued" }));
    await kv("expire", K.job(job_id), String(7 * 86400));
  } catch (e) {
    return json({ error: "queue fail", detail: String(e.message || e) }, 503);
  }

  // 推进 project state → generating（乐观更新 · worker 会再写一次）
  p.state = "generating";
  p.version = (p.version || 0) + 1;
  p.active_job_id = job_id;
  p.updated_at = new Date().toISOString();
  await kv("set", K.project(slug), JSON.stringify(p));

  return json({
    job_id,
    slug,
    stream_url: `/api/jobs/${job_id}/stream`,
    status: "queued",
    estimated_min: p.tier === "concept" ? 1 : p.tier === "deliver" ? 2 : 3,
  }, 201);
}
