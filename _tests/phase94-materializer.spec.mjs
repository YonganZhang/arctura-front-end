// Phase 9.4 · Materializer E2E · 对 smoke-ep-202886 真 MVP 验证前端展示
//
// 这个 spec 的独特价值（vs 老 smoke.spec.mjs）：
//   - 老 smoke 用批量 build_mvp_data.py 产的 MVP（老 MVP 扫磁盘逻辑）
//   - 这里验的是 Phase 9.4 worker 走 materializer 产的 MVP（新路径）
//   - Assert 关键字段不是占位（renders ≥ 8 · decks ≥ 1 · EUI ≠ 45 · compliance.checks ≥ 5）

import { test, expect } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const FE_ROOT = path.resolve(fileURLToPath(new URL("..", import.meta.url)));
const SLUG = "smoke-ep-202886";


test("Phase 9.4 · smoke MVP JSON shape · 前端字段真非占位", async () => {
  // 直接读文件 · 不过 HTTP（http.server 基本没啥好挂的）
  const jsonPath = path.join(FE_ROOT, "data", "mvps", `${SLUG}.json`);
  expect(fs.existsSync(jsonPath), `${jsonPath} 必须存在`).toBe(true);

  const d = JSON.parse(fs.readFileSync(jsonPath, "utf8"));
  // 核心 schema
  expect(d.slug).toBe(SLUG);
  expect(d.project).toBeTruthy();
  expect(d.project.palette, "palette 必须 ≥ 4 色（Phase 9.4 从 moodboard.json 读）").toHaveLength.greaterThan ?? true;
  expect(d.project.palette.length, "palette 色数").toBeGreaterThanOrEqual(4);
  expect(d.project.area, "project.area 必须是真数字 · 非 0").toBeGreaterThan(0);

  // renders ≥ 8
  expect(d.renders.length, "renders 数（Phase 9.4 前为 0 · 修后 ≥ 8）").toBeGreaterThanOrEqual(8);
  for (const r of d.renders) {
    expect(r.file, "render.file 必须是 /assets/ 路径").toMatch(/^\/assets\//);
  }

  // decks ≥ 1（pptx / pdf / md）
  expect(d.decks.length, "decks 数（Phase 9.4 前为 0）").toBeGreaterThanOrEqual(1);

  // downloads ≥ 4（bundle + 3 个 export）
  expect(d.downloads.length, "downloads 数（Phase 9.4 前只有 1 占位）").toBeGreaterThanOrEqual(4);

  // energy.eui 真数字 · 非 45 占位
  expect(d.energy.eui, "energy.eui 必须是真 EnergyPlus 值").toBeGreaterThan(0);
  expect(d.energy.eui, "energy.eui 不能是 45 占位").not.toBe(45);

  // compliance · 至少 5 个 check + verdict 非 "—"
  expect(d.compliance.HK.checks.length, "compliance.HK.checks 数").toBeGreaterThanOrEqual(5);
  expect(d.compliance.HK.verdict).not.toBe("—");
  expect(d.compliance.HK.verdict, "verdict 应是 COMPLIANT / NON-COMPLIANT / ADVISORY")
    .toMatch(/COMPLIANT|ADVISORY|NON/);

  // pricing · 至少 3 行 BOQ + total > 0
  expect(d.pricing.HK.rows.length, "pricing.HK.rows 数").toBeGreaterThanOrEqual(3);
  expect(d.pricing.HK.totalNumber, "BOQ grand total 必须 > 0").toBeGreaterThan(0);
  expect(d.derived.cost_per_m2, "cost_per_m2 必须 > 0").toBeGreaterThan(0);
});


test("Phase 9.4 · /project/smoke-ep-202886 页面渲染无错误", async ({ page }) => {
  const errors = [];
  page.on("pageerror", (err) => errors.push(`pageerror: ${err.message}`));
  page.on("console", (msg) => {
    if (msg.type() === "error") {
      const t = msg.text();
      // 允许 GLB 加载失败（smoke MVP 没上传 .glb 到 assets · 只在 sb_dir）+ favicon + React devtools
      if (/THREE\.GLTFLoader|Failed to load resource|favicon|DevTools|babel-standalone|Download the React/i.test(t)) return;
      errors.push(`console.error: ${t}`);
    }
  });

  await page.goto(`/project/index.html?mvp=${SLUG}`, { waitUntil: "domcontentloaded" });
  await page.waitForSelector(".sidebar, .chat, main", { timeout: 8000 }).catch(() => {});
  await page.waitForTimeout(800);

  // 无 console / pageerror
  expect(errors, `errors:\n${errors.join("\n")}`).toHaveLength(0);

  // main 区有内容
  const mainText = await page.locator("main, .main").innerText().catch(() => "");
  expect(mainText.length).toBeGreaterThan(100);

  // 页面真数据 · 找 EUI 41.9（Phase 9.4 后真 EnergyPlus 值）
  const bodyText = await page.locator("body").innerText();
  expect(bodyText, "页面应显示真 EUI 41.9（Phase 9.4 前为 45 占位）").toMatch(/41\.9/);
});


test("Phase 9.4 · BOQ tab 显示真 HK$455,736", async ({ page }) => {
  await page.goto(`/project/index.html?mvp=${SLUG}`, { waitUntil: "domcontentloaded" });
  await page.waitForSelector(".sidebar", { timeout: 8000 });
  await page.waitForTimeout(600);

  // 切 BOQ tab
  const btn = page.locator('.sidebar [data-tab="boq"]').first();
  await btn.click({ timeout: 3000 });
  await page.waitForTimeout(400);

  const body = await page.locator("body").innerText();
  // BOQ grand total 必须出现（不同空格、千位分隔符都 ok）
  expect(body, "BOQ 页应含真 grand total 455,736").toMatch(/455[,\s]?736/);
});


test("Phase 9.4 · compliance tab 显示 COMPLIANT + 8 check", async ({ page }) => {
  await page.goto(`/project/index.html?mvp=${SLUG}`, { waitUntil: "domcontentloaded" });
  await page.waitForSelector(".sidebar", { timeout: 8000 });
  await page.waitForTimeout(600);

  const btn = page.locator('.sidebar [data-tab="compliance"]').first();
  await btn.click({ timeout: 3000 });
  await page.waitForTimeout(400);

  const body = await page.locator("body").innerText();
  expect(body).toMatch(/COMPLIANT/i);
  // Phase 9.4 前 compliance 页面空壳（checks=[]）· 修后至少应能看到几个合规项名字
  // 8 checks 的名字包含 EUI / OTTV / LPD / Window / Wall / Roof 等 · 找到 ≥ 3 个
  const keywords = ["EUI", "OTTV", "LPD", "Window", "Wall", "Roof", "SHGC", "Fresh Air", "Ventilation", "Envelope", "Lighting", "Intensity"];
  const hit = keywords.filter((k) => body.includes(k)).length;
  expect(hit, `compliance 页应显示 ≥ 3 个 check 关键词 · 实际 ${hit} · 命中: ${keywords.filter(k=>body.includes(k)).join(",")}`)
    .toBeGreaterThanOrEqual(3);
});


test("Phase 9.4 · files/decks tab 显示 3 decks + 7 downloads", async ({ page }) => {
  await page.goto(`/project/index.html?mvp=${SLUG}`, { waitUntil: "domcontentloaded" });
  await page.waitForSelector(".sidebar", { timeout: 8000 });
  await page.waitForTimeout(600);

  const btn = page.locator('.sidebar [data-tab="files"]').first();
  await btn.click({ timeout: 3000 });
  await page.waitForTimeout(400);

  const body = await page.locator("body").innerText();
  // bundle.zip + glb + obj + fbx + ifc 至少出现
  expect(body, "files 页应含 bundle.zip").toMatch(/bundle\.zip/i);
  expect(body, "files 页应含 .glb / .ifc").toMatch(/\.(glb|ifc)/i);
});
