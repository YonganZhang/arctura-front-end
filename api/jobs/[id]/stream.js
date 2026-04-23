// GET /api/jobs/<id>/stream · Phase 7 · SSE 读 job:<id>:events
//
// Worker 把事件 rpush 到 job:<id>:events list · 本端点用 lrange 游标式拉 · SSE 推给前端。
// Upstash REST 无 subscribe · poll 间隔 800ms · 空响应靠 heartbeat 撑住连接。
//
// 事件（worker 推）:
//   job_picked · start · plan · artifact_start · artifact_done · artifact_error
//   artifact_skipped · complete · done · fatal · error
// 本端点额外推:
//   open (首 event · 回 job meta 快照)
//   heartbeat (每 12s · 带 elapsed_ms)
//   stream_end (终止事件 done/fatal/error 之后 · 客户端应断连)
//   timeout (>15min 无 done · 主动断)
//
// 前端应在收到 stream_end 时关闭 EventSource · 不要重连。

import { K } from "../../_shared/kv-keys.js";

export const config = { runtime: "edge" };

const KV_URL = process.env.UPSTASH_REDIS_REST_URL;
const KV_TOKEN = process.env.UPSTASH_REDIS_REST_TOKEN;

const POLL_MS = 800;
const HEARTBEAT_MS = 12000;
const MAX_DURATION_MS = 15 * 60 * 1000;  // 15 min 上限
const TERMINAL_EVENTS = new Set(["done", "fatal", "error"]);

async function kv(cmd, ...args) {
  const path = [cmd, ...args.map(a => encodeURIComponent(String(a)))].join("/");
  const r = await fetch(`${KV_URL}/${path}`, {
    headers: { Authorization: `Bearer ${KV_TOKEN}` },
  });
  if (!r.ok) throw new Error(`KV ${cmd}: HTTP ${r.status}`);
  return (await r.json()).result;
}

function sseMessage(event, data) {
  return `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`;
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

export default async function handler(req) {
  // 从 URL path 提 job_id · Vercel 注入 query.id
  const url = new URL(req.url);
  const jobId = url.pathname.split("/").filter(Boolean).pop() === "stream"
    ? url.pathname.split("/").filter(Boolean).at(-2)
    : url.searchParams.get("id");

  if (!jobId || !jobId.startsWith("job-")) {
    return new Response(JSON.stringify({ error: "missing or invalid job_id" }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  }

  const enc = new TextEncoder();
  const { readable, writable } = new TransformStream();
  const writer = writable.getWriter();
  const t0 = Date.now();

  (async () => {
    let closed = false;
    const safeWrite = async (s) => {
      if (closed) return;
      try { await writer.write(enc.encode(s)); }
      catch { closed = true; }
    };
    const heartbeat = setInterval(() => {
      safeWrite(sseMessage("heartbeat", { elapsed_ms: Date.now() - t0 }));
    }, HEARTBEAT_MS);

    try {
      // 1. job meta 快照
      const metaRaw = await kv("get", K.job(jobId));
      if (!metaRaw) {
        await safeWrite(sseMessage("error", { message: "job not found", code: 404 }));
        await safeWrite(sseMessage("stream_end", { reason: "not_found" }));
        return;
      }
      const meta = JSON.parse(metaRaw);
      await safeWrite(sseMessage("open", {
        job_id: jobId,
        slug: meta.slug,
        tier: meta.tier,
        status: meta.status,
      }));

      // 2. 如果已经是终止态 · 回放完整事件列表后直接结束
      if (["done", "error"].includes(meta.status)) {
        const all = await kv("lrange", K.jobEvents(jobId), "0", "-1");
        for (const raw of (all || [])) {
          try {
            const ev = JSON.parse(raw);
            await safeWrite(sseMessage(ev.event, ev.data));
          } catch {}
        }
        await safeWrite(sseMessage("stream_end", { reason: meta.status }));
        return;
      }

      // 3. 游标式 poll · cursor = 已推送的事件 index
      let cursor = 0;
      let terminalSeen = false;

      while (!closed && !terminalSeen) {
        if (Date.now() - t0 > MAX_DURATION_MS) {
          await safeWrite(sseMessage("timeout", { elapsed_ms: Date.now() - t0 }));
          await safeWrite(sseMessage("stream_end", { reason: "timeout" }));
          break;
        }

        let batch;
        try {
          batch = await kv("lrange", K.jobEvents(jobId), String(cursor), "-1");
        } catch (e) {
          // KV 偶发错误 · 不致命 · 下一轮重试
          await sleep(POLL_MS);
          continue;
        }

        for (const raw of (batch || [])) {
          try {
            const ev = JSON.parse(raw);
            await safeWrite(sseMessage(ev.event, ev.data));
            if (TERMINAL_EVENTS.has(ev.event)) {
              terminalSeen = true;
              await safeWrite(sseMessage("stream_end", { reason: ev.event }));
              break;
            }
          } catch {
            // 忽略 corrupt entry
          }
          cursor += 1;
        }

        if (terminalSeen) break;
        await sleep(POLL_MS);
      }
    } catch (e) {
      await safeWrite(sseMessage("error", { message: String(e.message || e) }));
      await safeWrite(sseMessage("stream_end", { reason: "exception" }));
    } finally {
      clearInterval(heartbeat);
      closed = true;
      try { await writer.close(); } catch {}
    }
  })();

  return new Response(readable, {
    status: 200,
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache, no-transform",
      "Connection": "keep-alive",
      "X-Accel-Buffering": "no",
    },
  });
}
