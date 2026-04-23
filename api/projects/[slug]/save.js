// Vercel Edge Function · POST /api/projects/<slug>/save
// Phase 6.D KV 持久化 + Phase 7.3 真 git commit 到 YonganZhang/arctura-front-end
//
// body: { version?: number, pending_edits?: [] }
// response: { ok, pending_cleared: N, commit_sha: null | "abc123" }

export const config = { runtime: "edge" };
import { K } from "../../_shared/kv-keys.js";

const KV_URL = process.env.UPSTASH_REDIS_REST_URL;
const KV_TOKEN = process.env.UPSTASH_REDIS_REST_TOKEN;
const GITHUB_TOKEN = process.env.GITHUB_TOKEN;

const GH_OWNER = "YonganZhang";
const GH_REPO = "arctura-front-end";
const GH_BRANCH = "main";

// 安全红线：
// - slug 只允许 [a-zA-Z0-9-_] · 防路径穿越
// - 只动 data/mvps/<slug>.json · 不是白名单路径直接拒
// - 文件 max 1 MB · 防误推大 blob
const SLUG_SAFE = /^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$/;
const MAX_FILE_BYTES = 1024 * 1024;

async function kv(cmd, ...args) {
  const path = [cmd, ...args.map(a => encodeURIComponent(String(a)))].join("/");
  const r = await fetch(`${KV_URL}/${path}`, { headers: { Authorization: `Bearer ${KV_TOKEN}` } });
  if (!r.ok) throw new Error(`KV ${cmd}: HTTP ${r.status}`);
  return (await r.json()).result;
}

function json(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store" },
  });
}

function getSlug(req) {
  const m = new URL(req.url).pathname.match(/\/api\/projects\/([^/]+)\/save/);
  return m ? decodeURIComponent(m[1]) : null;
}

export default async function handler(req) {
  if (req.method !== "POST") return json({ error: "method not allowed" }, 405);
  const slug = getSlug(req);
  if (!slug) return json({ error: "bad slug" }, 400);

  let body = {};
  try { body = await req.json(); } catch {}

  // 读 project
  const key = K.project(slug);
  const pRaw = await kv("get", key);
  if (!pRaw) return json({ error: "not found" }, 404);
  const p = JSON.parse(pRaw);

  if (body.version !== undefined && body.version !== p.version) {
    return json({ error: "version conflict", expected: body.version, current: p.version }, 409);
  }
  // 老 MVP（legacy · migrated from static）state=live 但没 pending · 允许"pass-through"保存（供 SaveButton 走完流程）
  if (p.state !== "live" && p.state !== "briefing" && p.state !== "planning") {
    return json({ error: `state=${p.state} · 不允许保存` }, 400);
  }

  // Phase 6.D · 前端传 pending_edits list · 合并后端已存的 · 写入 KV
  const frontendPending = Array.isArray(body.pending_edits) ? body.pending_edits : [];
  if (frontendPending.length === 0 && (!p.pending_count || p.pending_count === 0)) {
    return json({ ok: true, pending_cleared: 0, already_saved: true });
  }

  // 存 pending_edits 供后续 git commit 读（如有 GITHUB_TOKEN）
  if (frontendPending.length > 0) {
    await kv("set", K.pendingEdits(slug),
             JSON.stringify(frontendPending), "EX", String(7 * 86400));
  }

  const pendingCleared = frontendPending.length || p.pending_count || 0;
  p.pending_count = 0;
  p.version = (p.version || 0) + 1;
  p.updated_at = new Date().toISOString();

  // git commit · 有 token + slug 合规 + scene 有内容才尝试
  let commitSha = null;
  let commitError = null;
  if (GITHUB_TOKEN && SLUG_SAFE.test(slug) && p.scene) {
    try {
      commitSha = await commitMvpFile(slug, p);
      p.last_save_ref = commitSha;
    } catch (e) {
      commitError = String(e.message || e);
      // 不 abort · KV 已持久化 · 用户数据不丢 · 只少个 commit
    }
  }

  // two-phase：写 project → 删 pending_edits list
  await kv("set", key, JSON.stringify(p));
  await kv("del", K.pendingEdits(slug));

  return json({
    ok: true,
    pending_cleared: pendingCleared,
    commit_sha: commitSha,
    commit_error: commitError,
    last_save_ref: p.last_save_ref || null,
    version: p.version,
  });
}

// ─────── Git commit 实装（Phase 7.3）───────

// 把 project KV 记录变成 /data/mvps/<slug>.json 的标准形状
// 对齐 pilot 01-study-room.json · 对齐 worker scene artifact 写的本机文件
function buildMvpFileContent(slug, p) {
  const brief = p.brief || {};
  const scene = p.scene || {};
  const artifacts = p.artifacts || {};
  const urls = artifacts.urls || {};

  return {
    slug,
    cat: "workplace",
    type: "P1-interior",
    complete: p.state === "live",
    project: {
      name: p.display_name || slug,
      zh: p.display_name || "",
      area: (brief.space || {}).area_sqm || 30,
      location: "Hong Kong",
      budgetHKD: brief.budget_hkd || 0,
      style: ((brief.style || {}).keywords || []).join(", "),
      palette: [],
    },
    renders: [],
    floorplan: urls.floorplan || null,
    moodboard: urls.moodboard || null,
    hero_img: urls.hero_img || null,
    thumb_img: null,
    zones: brief.functional_zones || [],
    furniture: [],
    pricing: { HK: { label: "Hong Kong", currency: "HKD", perM2: 0, rows: [], total: "HKD 0" } },
    energy: { eui: 45, limit: 150, annual: 0, engine: "EnergyPlus" },
    compliance: { HK: { code: "HK_BEEO_BEC_2021", verdict: "pass", checks: [] } },
    variants: { list: [] },
    timeline: [], decks: [], downloads: [],
    editable: {
      area_m2: (brief.space || {}).area_sqm || 30,
      insulation_mm: 60, glazing_uvalue: 2.0, lighting_cct: 3000,
      lighting_density_w_m2: 8, wwr: 0.25, region: "HK",
    },
    derived: { eui_kwh_m2_yr: 45, cost_total: 0, cost_per_m2: 0, co2_t_per_yr: 0 },
    scene,
    _saved_at: p.updated_at,
    _saved_from: "api/projects/[slug]/save",
  };
}

async function ghApi(path, { method = "GET", body = null } = {}) {
  const resp = await fetch(`https://api.github.com${path}`, {
    method,
    headers: {
      "Authorization": `Bearer ${GITHUB_TOKEN}`,
      "Accept": "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
      "User-Agent": "arctura-front-end-save",
      ...(body ? { "Content-Type": "application/json" } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  const text = await resp.text();
  if (!resp.ok) {
    throw new Error(`gh ${method} ${path} → ${resp.status}: ${text.slice(0, 200)}`);
  }
  return JSON.parse(text);
}

function toBase64(str) {
  // Edge runtime 用 TextEncoder + btoa（不能直接 btoa 中文）
  const bytes = new TextEncoder().encode(str);
  let binary = "";
  for (const b of bytes) binary += String.fromCharCode(b);
  return btoa(binary);
}

async function commitMvpFile(slug, p) {
  const content = buildMvpFileContent(slug, p);
  const contentStr = JSON.stringify(content, null, 2);
  if (contentStr.length > MAX_FILE_BYTES) {
    throw new Error(`file too large (${contentStr.length} > ${MAX_FILE_BYTES})`);
  }

  // 白名单路径 · 不接受任何其他路径（防未来 bug 逃逸）
  const filePath = `data/mvps/${slug}.json`;
  if (!filePath.startsWith("data/mvps/") || filePath.includes("..")) {
    throw new Error(`path not whitelisted: ${filePath}`);
  }

  // 1. GET 拿现有文件 sha（404 = 新文件 · sha 留空）
  let existingSha = null;
  try {
    const meta = await ghApi(`/repos/${GH_OWNER}/${GH_REPO}/contents/${filePath}?ref=${GH_BRANCH}`);
    existingSha = meta.sha;
  } catch (e) {
    if (!String(e).includes("→ 404")) throw e;
  }

  // 2. PUT 新 content
  const result = await ghApi(
    `/repos/${GH_OWNER}/${GH_REPO}/contents/${filePath}`,
    {
      method: "PUT",
      body: {
        message: `[auto-save] ${slug} · v${p.version}`,
        content: toBase64(contentStr),
        branch: GH_BRANCH,
        ...(existingSha ? { sha: existingSha } : {}),
        committer: {
          name: "Arctura Auto-Save",
          email: "noreply@arctura-front-end.vercel.app",
        },
      },
    }
  );
  return result.commit?.sha || null;
}
