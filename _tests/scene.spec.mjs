// scene.spec.mjs — Phase 2.0 pilot specific tests
// Covers: 01-study-room rendered with Three.js scene · FloorplanScene SVG
// · no console errors · ops API roundtrip
//
// 不覆盖（留给未来）：
//   · chat "删衣柜" e2e（需要 LLM API key）
//   · 41 非 pilot MVP 全量回归（smoke.spec.mjs 已覆盖）

import { test, expect } from "@playwright/test";

const PILOT = "01-study-room";

const CONSOLE_ALLOWLIST = [
  /Download the React DevTools/,
  /babel-standalone/,
  /DEVTOOLS/,
  /favicon\.ico/i,
  /THREE\.GLTFLoader/,
  /GLB load failed/,
  /HDRI load failed/,
  // Pilot scene 引用的 GLB / HDRI / bundle 可能 404（设计内建的 fallback）
  // 浏览器的 "Failed to load resource" 通用消息不带 URL · 只能 broad match 404
  /Failed to load resource.*404/,
  /Failed to load resource.*File not found/,
];

function isIgnorable(text) {
  return CONSOLE_ALLOWLIST.some(rx => rx.test(text));
}

test(`pilot · ${PILOT} · scene field exists and canvas renders`, async ({ page }) => {
  const errors = [];
  page.on("console", msg => { if (msg.type() === "error" && !isIgnorable(msg.text())) errors.push(msg.text()); });
  page.on("pageerror", e => errors.push(`pageerror: ${e.message}`));

  await page.goto(`/project/index.html?mvp=${PILOT}`, { waitUntil: "domcontentloaded" });
  await expect(page.locator(".main")).toBeVisible({ timeout: 10_000 });

  // 切到 3D tab
  await page.locator('.sidebar [data-tab="3d"]').first().click({ timeout: 5_000 });
  await page.waitForTimeout(3000);  // Three.js 加载 + 构建

  // Canvas 存在且非空
  const canvas = page.locator("canvas").first();
  await expect(canvas).toBeVisible({ timeout: 8_000 });
  const size = await canvas.evaluate(el => ({ w: el.width, h: el.height }));
  expect(size.w, "canvas width > 0").toBeGreaterThan(10);
  expect(size.h, "canvas height > 0").toBeGreaterThan(10);

  // console 无致命 error
  expect(errors, `pilot ${PILOT} should have no console errors · got: ${errors.join(" || ")}`).toEqual([]);
});

test(`pilot · ${PILOT} · Floorplan SVG with walls + objects`, async ({ page }) => {
  await page.goto(`/project/index.html?mvp=${PILOT}`, { waitUntil: "domcontentloaded" });
  await expect(page.locator(".main")).toBeVisible({ timeout: 10_000 });
  await page.locator('.sidebar [data-tab="floorplan"]').first().click({ timeout: 5_000 });
  await page.waitForTimeout(1200);

  const svg = page.locator("svg").first();
  await expect(svg).toBeVisible({ timeout: 5_000 });

  const rectCount = await svg.locator("rect").count();
  expect(rectCount, "at least 15 object rects").toBeGreaterThanOrEqual(15);

  const lineCount = await svg.locator("line").count();
  expect(lineCount, "walls + grid lines").toBeGreaterThanOrEqual(2);
});

test(`pilot · ${PILOT} · data has scene field with 18 objects / 4 walls / 3 lights`, async ({ page }) => {
  const r = await page.request.get(`/data/mvps/${PILOT}.json`);
  expect(r.status()).toBe(200);
  const data = await r.json();
  expect(data.scene, "scene field present").toBeDefined();
  expect(data.scene.schema_version).toBe("1.0");
  expect(data.scene.objects.length).toBe(18);
  // Phase 7.1+ · scene generator 4 墙（原 2 墙为老 Phase 1 · 简化布局）
  expect(data.scene.walls.length).toBe(4);
  expect(data.scene.lights.length).toBe(3);
  expect(data.scene.bounds).toEqual({ w: 5.0, d: 4.0, h: 2.8 });
});

// /api/scene/ops 是 Vercel Edge Function · 本地 python server 跑不了
// 如果用户想测 · 指向 prod：PROD_URL=https://arctura-front-end.vercel.app npx playwright test
const PROD_URL = process.env.PROD_URL;
(PROD_URL ? test : test.skip)(`pilot · /api/scene/ops · move_object end-to-end (prod)`, async ({ request }) => {
  const r0 = await request.get(`${PROD_URL}/data/mvps/${PILOT}.json`);
  const data = await r0.json();
  const originalPos = data.scene.objects.find(o => o.id === "obj_desk").pos;

  const r = await request.post(`${PROD_URL}/api/scene/ops`, {
    data: {
      slug: PILOT,
      scene: data.scene,
      ops: [{ op: "move_object", id: "obj_desk", pos: [0.5, 0, 0.75] }],
    },
  });
  expect(r.status()).toBe(200);
  const body = await r.json();
  expect(body.applied.length).toBe(1);
  expect(body.rejected.length).toBe(0);
  expect(body.newScene.objects.find(o => o.id === "obj_desk").pos).toEqual([0.5, 0, 0.75]);
  expect(body.derived.object_count).toBe(18);
});
