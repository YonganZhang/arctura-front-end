// Vercel Edge Function — 智增增 gateway 代理
// POST /api/chat
// body: { model: string, messages: [{role, content}], system?: string, max_tokens?: number }
// response: { text: string, model: string, usage?: {...} }

export const config = { runtime: 'edge' };

const BASE = 'https://api.zhizengzeng.com/v1/chat/completions';

// GPT-5 / o1 / o4 系列用 max_completion_tokens 不是 max_tokens
function usesCompletionTokens(model) {
  return /^(gpt-5|o[1-9])/i.test(model);
}

export default async function handler(req) {
  if (req.method !== 'POST') {
    return new Response(JSON.stringify({ error: 'POST only' }), {
      status: 405,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  const key = process.env.ZHIZENGZENG_API_KEY;
  if (!key) {
    return new Response(
      JSON.stringify({ error: 'Server misconfigured: ZHIZENGZENG_API_KEY missing' }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    );
  }

  let body;
  try {
    body = await req.json();
  } catch {
    return new Response(JSON.stringify({ error: 'Invalid JSON body' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  const { model, messages, system, max_tokens } = body;
  if (!model || !Array.isArray(messages) || messages.length === 0) {
    return new Response(
      JSON.stringify({ error: 'Required: model (string) + messages (array)' }),
      { status: 400, headers: { 'Content-Type': 'application/json' } }
    );
  }

  const fullMessages = system
    ? [{ role: 'system', content: system }, ...messages]
    : messages;

  const tokens = Math.min(Math.max(Number(max_tokens) || 1024, 1), 4096);
  const payload = {
    model,
    messages: fullMessages,
    temperature: 0.3,
  };
  if (usesCompletionTokens(model)) {
    payload.max_completion_tokens = tokens;
  } else {
    payload.max_tokens = tokens;
  }

  // 调智增增 · 30s 超时
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 30000);

  try {
    const upstream = await fetch(BASE, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${key}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });
    clearTimeout(timer);

    const text = await upstream.text();
    if (!upstream.ok) {
      return new Response(
        JSON.stringify({
          error: 'Upstream error',
          status: upstream.status,
          detail: text.slice(0, 500),
        }),
        { status: upstream.status, headers: { 'Content-Type': 'application/json' } }
      );
    }

    let data;
    try {
      data = JSON.parse(text);
    } catch {
      return new Response(
        JSON.stringify({ error: 'Upstream returned non-JSON', raw: text.slice(0, 500) }),
        { status: 502, headers: { 'Content-Type': 'application/json' } }
      );
    }

    const reply = data?.choices?.[0]?.message?.content?.trim() || '';
    if (!reply) {
      return new Response(
        JSON.stringify({
          error: 'Empty reply',
          model,
          hint: 'Some flash / nano models return empty content for short prompts. Try Pro or Sonnet.',
        }),
        { status: 502, headers: { 'Content-Type': 'application/json' } }
      );
    }

    return new Response(
      JSON.stringify({
        text: reply,
        model: data.model || model,
        usage: data.usage || null,
      }),
      {
        status: 200,
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'no-store',
        },
      }
    );
  } catch (err) {
    clearTimeout(timer);
    const msg = err.name === 'AbortError' ? 'Upstream timeout (30s)' : String(err.message || err);
    return new Response(
      JSON.stringify({ error: msg }),
      { status: 504, headers: { 'Content-Type': 'application/json' } }
    );
  }
}
