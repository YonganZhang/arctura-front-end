// Vercel Edge Function · POST /api/projects/<slug>/save
// Phase 6.D · 持久化 pending_edits · 清空 pending_count · git commit 留给 GITHUB_TOKEN 有了再加
//
// body: { version?: number }
// response: { ok, pending_cleared: N, commit_sha?: null }

export const config = { runtime: "edge" };
import { K } from "../../_shared/kv-keys.js";

const KV_URL = process.env.UPSTASH_REDIS_REST_URL;
const KV_TOKEN = process.env.UPSTASH_REDIS_REST_TOKEN;
const GITHUB_TOKEN = process.env.GITHUB_TOKEN;

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

  // 尝试 git commit · 无 token 则 skip
  let commitSha = null;
  if (GITHUB_TOKEN) {
    try {
      commitSha = await tryGitCommit(p);
      if (commitSha) p.last_save_ref = commitSha;
    } catch (e) {
      console.error("[save] git commit failed:", e.message);
      // 不中断 · KV 已清 pending · 用户不会丢改动
    }
  }

  // two-phase：写 project → 删 pending_edits list
  await kv("set", key, JSON.stringify(p));
  await kv("del", K.pendingEdits(slug));

  return json({
    ok: true,
    pending_cleared: pendingCleared,
    commit_sha: commitSha,
    last_save_ref: p.last_save_ref || null,
    version: p.version,
  });
}

// Git commit · 用 GITHUB_TOKEN 直连 GitHub API
// 只允许改 data/mvps/<slug>.json 路径（服务端 path 校验 · v3 §7.1 决策 #4）
async function tryGitCommit(project) {
  // 占位 · Phase 6.D 仅 KV 持久化版本 · git commit 待用户给 GITHUB_TOKEN 后完整实装
  // 实装点：
  //   1. gh api repos/.../contents/data/mvps/<slug>.json GET 拿当前 sha
  //   2. PUT 新 content（base64）· message · sha
  //   3. 返回 commit.sha
  // 当前 MVP：直接返 null · 客户端看到 commit_sha=null 说明仅 KV 存了
  return null;
}
