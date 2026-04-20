#!/usr/bin/env node
// test-models.js — 遍历 13 候选模型调智增增 API，筛出可用的
// 用 curl 调，自动走 HTTP_PROXY/HTTPS_PROXY 环境变量
// Usage:
//   export ZHIZENGZENG_API_KEY=sk-zk2bb4f82...
//   export HTTPS_PROXY=http://127.0.0.1:7890   # 本机 China 节点需要
//   node _build/test-models.js

const { execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const API_KEY = process.env.ZHIZENGZENG_API_KEY;
if (!API_KEY) {
  console.error('❌ 缺 ZHIZENGZENG_API_KEY env');
  console.error('  export ZHIZENGZENG_API_KEY=sk-zk2bb4f82464dae8e270d6617131985ae7b694b5caf9dc15');
  process.exit(1);
}

const CANDIDATES = [
  { id: 'claude-opus-4-6',           label: 'Claude Opus 4.6 ⭐',    vendor: 'Anthropic', tier: 'flagship' },
  { id: 'claude-sonnet-4-5',         label: 'Claude Sonnet 4.5',      vendor: 'Anthropic', tier: 'balanced' },
  { id: 'claude-haiku-4-5',          label: 'Claude Haiku 4.5',       vendor: 'Anthropic', tier: 'fast' },
  { id: 'gpt-5.4',                   label: 'GPT-5.4 ⭐',              vendor: 'OpenAI',    tier: 'flagship' },
  { id: 'gpt-5.4-nano',              label: 'GPT-5.4 nano',           vendor: 'OpenAI',    tier: 'fast' },
  { id: 'gpt-4o-mini',               label: 'GPT-4o-mini',            vendor: 'OpenAI',    tier: 'balanced' },
  { id: 'gemini-3.1-pro-preview',    label: 'Gemini 3.1 Pro ⭐',       vendor: 'Google',    tier: 'flagship' },
  { id: 'gemini-2.5-flash',          label: 'Gemini 2.5 Flash',       vendor: 'Google',    tier: 'fast' },
  { id: 'deepseek-v3.2',             label: 'DeepSeek V3.2 🇨🇳',       vendor: 'DeepSeek',  tier: 'balanced', default: true },
  { id: 'qwen3-max',                 label: 'Qwen3 Max',              vendor: '阿里',       tier: 'balanced' },
  { id: 'glm-4-flash',               label: 'GLM 4 Flash 🆓',          vendor: '智谱',       tier: 'free' },
  { id: 'grok-4',                    label: 'Grok-4',                 vendor: 'xAI',       tier: 'flagship' },
  { id: 'llama-4-maverick',          label: 'Llama 4 Maverick',       vendor: 'Meta',      tier: 'balanced' },
];

function callOnce(modelId, tokenParam = 'max_tokens') {
  const payload = JSON.stringify({
    model: modelId,
    messages: [{ role: 'user', content: 'Say "hello" in one word only. No explanations.' }],
    [tokenParam]: 30,
    temperature: 0,
  });

  const start = Date.now();
  try {
    const out = execFileSync('curl', [
      '-sS',
      '--max-time', '45',
      '-w', '\n__HTTP_STATUS__:%{http_code}',
      '-X', 'POST',
      'https://api.zhizengzeng.com/v1/chat/completions',
      '-H', `Authorization: Bearer ${API_KEY}`,
      '-H', 'Content-Type: application/json',
      '-d', payload,
    ], { encoding: 'utf8', timeout: 50000 });

    const latency = Date.now() - start;
    const match = out.match(/__HTTP_STATUS__:(\d+)$/);
    const status = match ? parseInt(match[1], 10) : 0;
    const body = match ? out.slice(0, out.length - match[0].length).trim() : out.trim();

    return { status, latency, body };
  } catch (e) {
    return { status: 0, latency: Date.now() - start, body: e.message };
  }
}

function callModel(modelId) {
  // retry 3 次处理代理瞬断 SSL_ERROR_SYSCALL
  let last;
  for (let i = 0; i < 3; i++) {
    const r = callOnce(modelId);
    last = r;
    if (r.status === 200) {
      try {
        const j = JSON.parse(r.body);
        const text = (j.choices?.[0]?.message?.content || '').trim();
        if (text.length > 0) return { ok: true, status: 200, latency: r.latency, text, usage: j.usage };
      } catch {}
    }
    // 如果是 400 告知 max_tokens 问题，换 max_completion_tokens 重试
    if (r.status === 400 && /max_tokens.*not supported|max_completion_tokens/i.test(r.body)) {
      const r2 = callOnce(modelId, 'max_completion_tokens');
      if (r2.status === 200) {
        try {
          const j = JSON.parse(r2.body);
          const text = (j.choices?.[0]?.message?.content || '').trim();
          if (text.length > 0) return { ok: true, status: 200, latency: r2.latency, text, usage: j.usage, note: 'uses max_completion_tokens' };
        } catch {}
      }
      last = r2;
      break;
    }
    // SSL_ERROR_SYSCALL / timeout 前两次重试
    if (i < 2 && (r.status === 0 || /SSL|timeout|Connection/i.test(r.body))) {
      continue;
    }
    break;
  }
  return {
    ok: false,
    status: last.status,
    latency: last.latency,
    error: (last.body || '').slice(0, 200),
  };
}

(async () => {
  console.log('Testing 13 models via 智增增 (https://api.zhizengzeng.com/v1)');
  console.log('HTTPS_PROXY:', process.env.HTTPS_PROXY || '(none)');
  console.log();

  const results = [];
  for (const m of CANDIDATES) {
    process.stdout.write(`  ${m.id.padEnd(30)} ... `);
    const r = callModel(m.id);
    if (r.ok) {
      console.log(`✅ ${String(r.latency).padStart(5)}ms  "${r.text.slice(0, 40)}"`);
      results.push({ ...m, ok: true, latency: r.latency, sample: r.text.slice(0, 40), usage: r.usage });
    } else {
      console.log(`❌ [${r.status || 'err'}] ${String(r.latency).padStart(5)}ms  ${(r.error || '').slice(0, 80)}`);
      results.push({ ...m, ok: false, latency: r.latency, error: (r.error || '').slice(0, 300) });
    }
  }

  const passed = results.filter(r => r.ok);
  console.log(`\n📊 ${passed.length}/${results.length} 模型通过`);

  const output = passed.map(m => ({
    id: m.id,
    label: m.label,
    vendor: m.vendor,
    tier: m.tier,
    default: m.default || false,
    latency_ms: m.latency,
  }));

  const outDir = path.join(__dirname, '..', 'data');
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(path.join(outDir, 'models.json'), JSON.stringify(output, null, 2));
  fs.writeFileSync(path.join(outDir, 'models-debug.json'), JSON.stringify(results, null, 2));

  console.log(`✏️  data/models.json (通过的 ${passed.length} 个)`);
  console.log(`✏️  data/models-debug.json (完整测试日志)`);
})();
