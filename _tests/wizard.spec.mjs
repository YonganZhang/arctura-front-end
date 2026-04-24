// Phase 6.C Wizard E2E · 新建 project 完整流程（不含生成 · 生成待 6.D）
// 跑：env HTTP_PROXY= HTTPS_PROXY= npx playwright test _tests/wizard.spec.mjs --reporter=line

import { test, expect } from "@playwright/test";

const BASE = process.env.BASE_URL || "https://arctura-front-end.vercel.app";

test.describe("Wizard · Phase 6.C", () => {
  test("主页 → /new · 自动创建 draft · URL 加 slug", async ({ page }) => {
    await page.goto(`${BASE}/`, { waitUntil: "networkidle" });
    // 点 "+ 新建项目" 按钮
    const newBtn = page.locator('a[href="/new"]').first();
    await expect(newBtn).toBeVisible();
    await newBtn.click();
    // 等 draft 创建 · URL 变 /new?slug=draft-xxx
    await page.waitForURL(/\/new\?slug=draft-[a-f0-9]+/, { timeout: 15000 });
    // Wizard 头部显示
    await expect(page.locator("text=Arctura · 新建项目")).toBeVisible();
    await expect(page.locator("text=Brief 对话")).toBeVisible();
    // 初始 assistant 打招呼
    await expect(page.locator("text=/说一下你想做什么项目/").first()).toBeVisible({ timeout: 10000 });
  });

  test("Wizard Step 1 · Brief Chat 发一句话 · SSE 更新进度", async ({ page }) => {
    await page.goto(`${BASE}/new`, { waitUntil: "networkidle" });
    await page.waitForURL(/slug=draft-/, { timeout: 15000 });
    await page.waitForSelector("textarea");

    // 输入 + 发送
    await page.locator("textarea").fill("帮我设计校长办公室 · 30 平米 · 日式禅风");
    await page.locator('button:has-text("发送")').click();

    // 等 brief_update SSE · 进度 > 0
    await page.waitForFunction(() => {
      const t = document.body.innerText;
      return t.match(/(\d+)% 完成/) && parseInt(t.match(/(\d+)% 完成/)[1], 10) > 0;
    }, null, { timeout: 60000 });

    // 进度文本可见
    const progressText = await page.locator("text=/%完成|完成/").first();
    await expect(progressText).toBeVisible();
  });

  test("非法 state transition 被后端挡", async ({ request }) => {
    const created = await request.post(`${BASE}/api/projects`, {
      data: { display_name: "Test transition" },
    });
    const { slug } = await created.json();

    const bad = await request.patch(`${BASE}/api/projects/${slug}`, {
      data: { state: "live", version: 1 },
    });
    expect(bad.status()).toBe(400);
    const err = await bad.json();
    expect(err.error).toMatch(/illegal transition/);

    // 清理
    await request.delete(`${BASE}/api/projects/${slug}`);
  });

  // Phase 9 加 brief must_fill 硬校验后 · 此 test 需要先走 /api/brief/chat SSE 才能
  // 让 brief 进 KV · 没法用 PATCH mock（PATCH 不接受 brief 字段 · 刻意如此）。
  // 要真测：要么走 SSE（复杂）· 要么改 PATCH 支持 brief（破坏 API 契约）。
  // TODO: Phase 10 给 tests/ 加 sse-mock helper · 先 skip
  test.skip("Tier picker · 5 档可见（Phase 9 后需 brief SSE · TODO helper）", async ({ page }) => {
    // 直接跳 planning state 的 URL（需先建 + 推进）
    const resp = await page.request.post(`${BASE}/api/projects`, {
      data: { display_name: "Tier test" },
    });
    expect([200, 201]).toContain(resp.status());  // 创建成功
    const { slug, version: v1 } = await resp.json();

    const r1 = await page.request.patch(`${BASE}/api/projects/${slug}`, {
      data: { state: "briefing", version: v1 },
    });
    expect(r1.status(), `PATCH → briefing failed ${await r1.text().catch(()=>'')}`).toBe(200);
    const { version: v2 } = await r1.json();

    // Phase 9 · brief must_fill 硬校验 · 见 _shared/brief-rules.json
    const r2 = await page.request.patch(`${BASE}/api/projects/${slug}`, {
      data: {
        brief: {
          project: "Tier test room",
          space: { area_sqm: 30, type: "study" },
          headcount: 2,
          style: { keywords: ["modern", "warm"] },
          functional_zones: [{ name: "work", area_sqm: 20 }],
        },
        version: v2,
      },
    });
    expect(r2.status(), `PATCH brief failed ${await r2.text().catch(()=>'')}`).toBe(200);
    const { version: v3 } = await r2.json();

    const r3 = await page.request.patch(`${BASE}/api/projects/${slug}`, {
      data: { state: "planning", version: v3 },
    });
    expect(r3.status(), `PATCH → planning failed ${await r3.text().catch(()=>'')}`).toBe(200);

    await page.goto(`${BASE}/new?slug=${slug}`, { waitUntil: "networkidle" });
    // UI 文案 "选产物档位"（h2）· 找不到说明 Wizard 没进到 step 2（state=planning 条件不对？）
    await expect(page.locator("text=选产物档位")).toBeVisible({ timeout: 10000 });
    for (const label of ["概念", "交付", "报价", "全案", "甄选"]) {
      await expect(page.locator(`text=${label}`).first()).toBeVisible();
    }

    // 清理
    await page.request.delete(`${BASE}/api/projects/${slug}`);
  });
});
