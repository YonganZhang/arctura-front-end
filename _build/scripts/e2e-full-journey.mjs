#!/usr/bin/env node
// e2e-full-journey.mjs · Phase 10 端到端真用户走查
//
// 流程：
//   1. 打开 / · 点 "+ 新建项目"
//   2. URL 变 /project/draft-xxx · BriefChatStep 出现
//   3. 一句话 brief（含所有 must_fill 字段 + "其他你看着办" 触发 smart fill）
//   4. 等 readyForTier=true · 点 "进入选档"
//   5. 选 "报价" 档（最快真产 · ~12-18 min）
//   6. 点 "开始生成" · poll SSE 进度
//   7. 等 state=live · 截 4 个关键 tab 发 Telegram
//
// Telegram 全程 progress 通报 · 用户能跟进度。

import { chromium } from "playwright";
import fs from "node:fs";
import { execFileSync } from "node:child_process";

const BASE = process.env.BASE_URL || "https://arctura-front-end.vercel.app";
const TG_TOKEN = fs.readFileSync(`${process.env.HOME}/.claude/channels/telegram/.env`, "utf8")
  .match(/TELEGRAM_BOT_TOKEN=(.+)/)[1].trim();
const CHAT_ID = "8412636443";
const TMP = "/tmp/arctura-e2e";
fs.mkdirSync(TMP, { recursive: true });

function tg(text) {
  try {
    execFileSync("curl", ["-sS", "--max-time", "20",
      `https://api.telegram.org/bot${TG_TOKEN}/sendMessage`,
      "-d", `chat_id=${CHAT_ID}`,
      "-d", `text=${text}`,
    ], { stdio: ["ignore", "pipe", "pipe"] });
  } catch (e) { console.error("[tg]", e.message); }
}

function tgPhoto(pngPath, caption) {
  try {
    execFileSync("curl", ["-sS", "--max-time", "30",
      `https://api.telegram.org/bot${TG_TOKEN}/sendPhoto`,
      "-F", `chat_id=${CHAT_ID}`,
      "-F", `photo=@${pngPath}`,
      "-F", `caption=${caption}`,
    ], { stdio: ["ignore", "pipe", "pipe"] });
  } catch (e) { console.error("[tg]", e.message); }
}

async function shot(page, label) {
  const p = `${TMP}/e2e-${Date.now()}-${label}.png`;
  await page.screenshot({ path: p, fullPage: false });
  return p;
}

async function main() {
  const t0 = Date.now();
  tg(`🤖 Claude E2E 全程测试启动 · ${new Date().toISOString()}\n• 主页 → 新建 → Brief → 报价档 → 生成 → 验 tab\n• ZHIZENGZENG 真 LLM · ~12-18 min`);

  const browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();

  const errors = [];
  page.on("pageerror", e => errors.push(`pageerror: ${e.message.slice(0, 150)}`));
  page.on("console", m => {
    if (m.type() === "error") {
      const t = m.text();
      if (!/favicon|DevTools|babel|GLTFLoader|Failed to load resource/i.test(t)) {
        errors.push(`console: ${t.slice(0, 150)}`);
      }
    }
  });

  let slug = null;
  try {
    // ── Step 1 · 主页 ─────────────────────────────
    tg("Step 1/7 · 打开主页");
    await page.goto(BASE + "/", { waitUntil: "domcontentloaded" });
    await page.waitForSelector("#my-projects", { timeout: 15000 });
    await page.waitForTimeout(2000);
    tgPhoto(await shot(page, "1-home"), `Step 1 · 主页 · 应见 '我的项目' section`);

    // ── Step 2 · 点 "+ 新建项目" ──────────────────
    tg("Step 2/7 · 点 '+ 新建项目'");
    // 优先用 my-projects-grid 里的 + 卡 · fallback Hero 按钮
    await page.locator(".my-project-card.my-new, a[href='/project/new']").first().click();
    await page.waitForURL(/\/project\/(draft-|new)/, { timeout: 15000 });
    // /project/new 会被 Wizard 内部 replaceState 到 /project/<slug>
    await page.waitForFunction(() => /^\/project\/draft-/.test(window.location.pathname), { timeout: 15000 });
    slug = await page.evaluate(() => window.location.pathname.split("/").pop());
    tg(`  → URL: /project/${slug}`);

    // 等 Brief Chat UI mount
    await page.waitForSelector("textarea", { timeout: 15000 });
    await page.waitForTimeout(2500);
    tgPhoto(await shot(page, "2-brief-init"), `Step 2 · /project/${slug} · BriefChatStep 出现`);

    // ── Step 3 · 一次性发 brief（含 must_fill）+ "你看着办" ───────
    tg("Step 3/7 · 发 brief 给 LLM · 等 readyForTier");
    const briefMsg = "学生办公室 Student Office · 香港 · 35 平方米 · 6 人办公 · 现代奶油港风 · 功能分区：会议区 12m² + 工位区 18m² + 茶水区 5m² · 其他你看着办，帮我自动填默认值";
    await page.locator("textarea").first().fill(briefMsg);
    await page.keyboard.press("Control+Enter");

    // 等 readyForTier=true（"必填齐全" 文案出现 · Phase 10 修过）
    // 或 "进入选档 →" 按钮变 enabled
    const readyDeadline = Date.now() + 90000;  // 90s · LLM 单轮 30s 估
    let readyForTier = false;
    while (Date.now() < readyDeadline) {
      const has = await page.locator("text=必填齐全").count() > 0;
      if (has) { readyForTier = true; break; }
      await page.waitForTimeout(3000);
    }
    if (!readyForTier) {
      // 一句话不够 · 再说 "其他你定" 触发 smart fill
      tg("  ⚠ 第一轮没 ready · 再发 '其他你都定吧'");
      await page.locator("textarea").first().fill("其他你都定吧 · 帮我用合理默认填完");
      await page.keyboard.press("Control+Enter");
      const d2 = Date.now() + 60000;
      while (Date.now() < d2) {
        const has = await page.locator("text=必填齐全").count() > 0;
        if (has) { readyForTier = true; break; }
        await page.waitForTimeout(3000);
      }
    }
    if (!readyForTier) {
      tg("❌ Brief 2 轮后仍未 ready · 终止 E2E");
      tgPhoto(await shot(page, "3-brief-stuck"), `Brief 卡住 · 可能 LLM 不听话`);
      await browser.close();
      return;
    }
    tgPhoto(await shot(page, "3-brief-ready"), `Step 3 ✅ Brief 必填齐 · 可进入选档`);

    // ── Step 4 · 点 "进入选档" ──────────────────────
    tg("Step 4/7 · 进入选档");
    await page.locator("button:has-text('进入选档')").first().click();
    // 等 TierPicker mount
    await page.waitForSelector("text=选产物档位", { timeout: 15000 });
    await page.waitForTimeout(1500);

    // 选报价档
    await page.locator("text=报价").first().click();
    await page.waitForTimeout(800);
    tgPhoto(await shot(page, "4-tier"), `Step 4 · TierPicker · 已选 报价 档`);

    // ── Step 5 · 点 "开始生成" ────────────────────
    tg("Step 5/7 · 开始生成 · pipeline 跑 · 12-18 min · 期间会发进度通报");
    await page.locator("button:has-text('开始生成')").first().click();
    // 等 GenerateProgress mount · state=generating
    await page.waitForTimeout(3000);
    tgPhoto(await shot(page, "5a-generating"), `Step 5 · 生成开始 · SSE progress 应出现`);

    // ── Step 6 · 等 state=live ────────────────────
    tg("Step 6/7 · 等 pipeline 完成（每 2 min 通报一次进度）");
    const genDeadline = Date.now() + 25 * 60 * 1000;  // 25 min 上限
    let lastReport = Date.now();
    let live = false;

    while (Date.now() < genDeadline) {
      // 通过 API 查 state · 不依赖 DOM
      try {
        const resp = await page.request.get(`${BASE}/api/projects/${slug}`);
        if (resp.ok()) {
          const p = await resp.json();
          const state = p.state;
          if (state === "live" || state === "live_partial") {
            live = true;
            tg(`✅ 生成完成 · state=${state} · 用时 ${Math.round((Date.now()-t0)/60000)} min`);
            break;
          }
          if (state === "generating_failed") {
            tg(`❌ 生成失败 · state=generating_failed · ${p.error || ""}`);
            break;
          }
          // 每 2 min 通报一次
          if (Date.now() - lastReport > 120000) {
            const arts = p.artifacts?.produced || [];
            tg(`⏳ ${slug} · state=${state} · produced ${arts.length}/10 · ${arts.slice(-3).join(", ")}`);
            lastReport = Date.now();
          }
        }
      } catch (e) {
        console.error("[poll]", e.message);
      }
      await page.waitForTimeout(15000);
    }

    if (!live) {
      tg(`⚠ 25 min timeout · state 未 live · 终止`);
      tgPhoto(await shot(page, "6-timeout"), `生成超时`);
      await browser.close();
      return;
    }

    // 等前端 reload 切到 tab 视图
    await page.waitForTimeout(5000);
    await page.goto(`${BASE}/project/${slug}`, { waitUntil: "domcontentloaded" });
    await page.waitForSelector(".sidebar", { timeout: 15000 });
    await page.waitForTimeout(3000);

    // ── Step 7 · 截 4 个 tab 验真产 ──────────────
    tg(`Step 7/7 · 截图验真产物`);
    for (const tab of ["overview", "renders", "3d", "boq"]) {
      try {
        if (tab !== "overview") {
          await page.locator(`.sidebar [data-tab="${tab}"]`).first().click({ timeout: 3000 });
          await page.waitForTimeout(tab === "3d" ? 8000 : 2000);
        }
        tgPhoto(await shot(page, `7-${tab}`), `Step 7 · ${tab} tab`);
      } catch (e) {
        tg(`  ⚠ tab ${tab} 截失败: ${e.message.slice(0, 100)}`);
      }
    }

    // 总结
    const totalMin = Math.round((Date.now() - t0) / 60000);
    tg(
      `🎉 E2E 全程通过\n` +
      `  • slug: ${slug}\n` +
      `  • URL: ${BASE}/project/${slug}\n` +
      `  • 总耗时: ${totalMin} min\n` +
      `  • console errors: ${errors.length}\n` +
      (errors.length ? `  • 错误样例:\n    ${errors.slice(0, 3).join("\n    ")}` : "")
    );
  } catch (e) {
    console.error(e);
    tg(`❌ E2E 失败 · ${e.message.slice(0, 300)}`);
    try { tgPhoto(await shot(page, "error"), `失败截图`); } catch {}
  } finally {
    await browser.close();
  }
}

main().catch(e => { console.error(e); tg(`❌ E2E 异常: ${e.message}`); });
