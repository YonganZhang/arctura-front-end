// Vercel Edge Function · POST /api/scene/ops
// 所有 scene 变更（chat / drag / 未来其他 client）的统一入口
// 契约见 api/scene/README.md

export const config = { runtime: "edge" };

import { applyOps } from "../../project-space/lib/scene-ops.js";

function jsonResponse(obj, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { "Content-Type": "application/json", "Cache-Control": "no-store" },
  });
}

export default async function handler(req) {
  if (req.method !== "POST") return jsonResponse({ error: "POST only" }, 405);

  let body;
  try {
    body = await req.json();
  } catch {
    return jsonResponse({ error: "Invalid JSON body" }, 400);
  }

  const { slug, scene, ops } = body || {};
  if (!slug) return jsonResponse({ error: "slug required" }, 400);
  if (!scene || typeof scene !== "object") return jsonResponse({ error: "scene object required" }, 400);
  if (!Array.isArray(ops) || ops.length === 0) return jsonResponse({ error: "ops must be non-empty array" }, 400);
  if (ops.length > 50) return jsonResponse({ error: "too many ops (max 50 per request)" }, 400);

  try {
    const result = applyOps(scene, ops);
    return jsonResponse({
      newScene: result.newScene,
      applied: result.applied,
      rejected: result.rejected,
      derived: result.derived,
      errors: [],
    });
  } catch (e) {
    return jsonResponse({
      error: "internal",
      detail: String(e.message || e).slice(0, 300),
    }, 500);
  }
}
