#!/usr/bin/env node
// screenshot-telegram.mjs · Playwright headless 截图 + Telegram 发给用户
//
// 用途: 网页 debug 配合 · 代替"让用户看 preview"· Claude 几秒截图 · 用户肉眼 2 秒判断
//
// 用法:
//   node _build/scripts/screenshot-telegram.mjs <slug> [--tabs overview,boq,3d,files,compliance]
//   node _build/scripts/screenshot-telegram.mjs smoke-ep-202886
//   node _build/scripts/screenshot-telegram.mjs 01-study-room --tabs 3d,boq
//   node _build/scripts/screenshot-telegram.mjs home   # 特殊值 · 截主页
//
// Env:
//   TELEGRAM_BOT_TOKEN · 从 ~/.claude/channels/telegram/.env 读
//   BASE_URL · 默认 https://arctura-front-end.vercel.app
//
// 产物:
//   /tmp/arctura-shots/<slug>-<tab>-<ts>.png  本地保存
//   + Telegram 发给 chat_id 8412636443（yongan 用户）

import { chromium } from "playwright";
import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";

const CHAT_ID = "8412636443";
const DEFAULT_TABS = ["overview", "renders", "3d", "boq", "compliance", "files"];
const TMP_DIR = "/tmp/arctura-shots";

function loadEnv() {
  const envPath = `${process.env.HOME}/.claude/channels/telegram/.env`;
  if (!fs.existsSync(envPath)) throw new Error(`Telegram env not found: ${envPath}`);
  const content = fs.readFileSync(envPath, "utf8");
  const token = (content.match(/TELEGRAM_BOT_TOKEN=(.+)/) || [])[1]?.trim();
  if (!token) throw new Error(`TELEGRAM_BOT_TOKEN not in ${envPath}`);
  return { token };
}

function parseArgs() {
  const argv = process.argv.slice(2);
  if (argv.length === 0) {
    console.error("usage: node screenshot-telegram.mjs <slug|home> [--tabs a,b,c]");
    process.exit(1);
  }
  const slug = argv[0];
  const tabsFlag = argv.find((a) => a.startsWith("--tabs="));
  const tabs = tabsFlag
    ? tabsFlag.split("=")[1].split(",").map((s) => s.trim()).filter(Boolean)
    : slug === "home"
    ? ["home"]
    : DEFAULT_TABS;
  const base = process.env.BASE_URL || "https://arctura-front-end.vercel.app";
  return { slug, tabs, base };
}

async function sendTelegram(token, pngPath, caption, asDoc = false) {
  // sendPhoto 对尺寸敏感（fullPage 太长会 PHOTO_INVALID_DIMENSIONS）
  // 大图 / 长图自动 fallback sendDocument
  const api = asDoc ? "sendDocument" : "sendPhoto";
  const field = asDoc ? "document" : "photo";
  const form = [
    "-F", `chat_id=${CHAT_ID}`,
    "-F", `${field}=@${pngPath}`,
    "-F", `caption=${caption}`,
  ];
  try {
    const out = execFileSync(
      "curl",
      ["-sS", "--max-time", "30", `https://api.telegram.org/bot${token}/${api}`, ...form],
      { stdio: ["ignore", "pipe", "pipe"] },
    );
    const r = JSON.parse(out.toString());
    if (!r.ok) {
      // PHOTO_INVALID_DIMENSIONS 时 fallback 到 sendDocument
      if (!asDoc && /PHOTO_INVALID_DIMENSIONS|too big/i.test(r.description || "")) {
        return sendTelegram(token, pngPath, caption, true);
      }
      throw new Error(`Telegram API: ${r.description}`);
    }
    return r.result.message_id;
  } catch (e) {
    console.error(`[tg] send fail: ${e.message}`);
    return null;
  }
}

async function screenshotPage(browser, { slug, tab, base }) {
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();
  const url =
    slug === "home"
      ? `${base}/`
      : `${base}/project/${encodeURIComponent(slug)}`;

  const errors = [];
  page.on("pageerror", (err) => errors.push(`pageerror: ${err.message.slice(0, 120)}`));
  page.on("console", (msg) => {
    if (msg.type() === "error") {
      const t = msg.text();
      if (!/favicon|DevTools|babel-standalone|Download the React/i.test(t)) {
        errors.push(`console: ${t.slice(0, 120)}`);
      }
    }
  });

  await page.goto(url, { waitUntil: "domcontentloaded", timeout: 30_000 });

  if (slug === "home") {
    // 等主页 gallery 加载
    await page.waitForSelector(".mvp, main, body", { timeout: 10_000 }).catch(() => {});
    await page.waitForTimeout(1500);
  } else {
    // 等 React mount
    await page.waitForSelector(".sidebar, main", { timeout: 10_000 }).catch(() => {});
    await page.waitForTimeout(1200);
    // 切 tab
    if (tab !== "overview" && tab !== "home") {
      const btn = page.locator(`.sidebar [data-tab="${tab}"]`).first();
      await btn.click({ timeout: 3000 }).catch(() => {});
      await page.waitForTimeout(800);
    }
    // 3D 视口再多等（model-viewer 加载 GLB + Three.js render）
    if (tab === "3d") {
      // 等 model-viewer 的 load event · 最多 15s
      await page.evaluate(() => new Promise((resolve) => {
        const mv = document.querySelector("model-viewer");
        if (!mv) return resolve(null);
        if (mv.loaded) return resolve("already-loaded");
        mv.addEventListener("load", () => resolve("loaded"), { once: true });
        setTimeout(() => resolve("timeout"), 15000);
      })).catch(() => null);
      await page.waitForTimeout(1500);  // 额外 animation 帧
    }
  }

  fs.mkdirSync(TMP_DIR, { recursive: true });
  const ts = Date.now();
  const safeSlug = slug.replace(/[^a-zA-Z0-9_-]/g, "_");
  const pngPath = path.join(TMP_DIR, `${safeSlug}-${tab}-${ts}.png`);
  // home 页截 fullPage · MVP 页 viewport 即可（避免太长）
  const fullPage = slug === "home";
  await page.screenshot({ path: pngPath, fullPage });
  const size = fs.statSync(pngPath).size;
  await ctx.close();
  return { pngPath, size, url, errors };
}

async function main() {
  const { slug, tabs, base } = parseArgs();
  const { token } = loadEnv();
  console.log(`▶ slug=${slug} · tabs=${tabs.join(",")} · base=${base}`);

  const browser = await chromium.launch({ headless: true });
  try {
    for (const tab of tabs) {
      process.stdout.write(`  ▸ ${tab} ... `);
      try {
        const { pngPath, size, url, errors } = await screenshotPage(browser, { slug, tab, base });
        const errHint = errors.length ? ` · ⚠ ${errors.length} console errors` : "";
        const caption =
          `🖼 ${slug}/${tab}\n` +
          `📍 ${url}\n` +
          `📦 ${(size / 1024).toFixed(1)} KB${errHint}` +
          (errors.length ? `\n${errors.slice(0, 3).map((e) => "• " + e).join("\n")}` : "");
        const msgId = await sendTelegram(token, pngPath, caption);
        console.log(msgId ? `✅ 发 Telegram (${(size / 1024).toFixed(0)}KB · msg ${msgId})` : "❌ Telegram 失败");
      } catch (e) {
        console.log(`❌ ${e.message}`);
      }
    }
  } finally {
    await browser.close();
  }
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
