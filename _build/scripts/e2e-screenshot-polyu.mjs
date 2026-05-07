// e2e screenshot · PolyU 自测 · 2026-05-07
// 1. 打开 prod /project/<slug>
// 2. 等 viewer 加载
// 3. 点"全隐"按钮(墙+天花板透明)
// 4. 截图发 Telegram
import { chromium } from 'playwright';
import fs from 'node:fs';

const SLUG = process.argv[2] || 'draft-744b21d9';  // 默认我修复后的图书馆房间
const PROD = 'https://arctura-front-end.vercel.app';
const URL = `${PROD}/project/${SLUG}`;
const OUT = `/tmp/e2e-shot-${SLUG}-${Date.now()}.png`;

console.log(`[e2e] open ${URL}`);
const browser = await chromium.launch({ headless: true });
const ctx = await browser.newContext({ viewport: { width: 1600, height: 900 }, deviceScaleFactor: 2 });
const page = await ctx.newPage();
page.on('console', msg => {
  const t = msg.text();
  if (t.includes('toggleAll') || t.includes('renderer') || t.includes('error') || t.includes('Error')) {
    console.log(`[browser] ${msg.type()}: ${t.slice(0,200)}`);
  }
});
page.on('pageerror', e => console.log(`[pageerror] ${e.message}`));

await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
console.log('[e2e] domcontentloaded · 等 React render');
await page.waitForLoadState('networkidle', { timeout: 30000 }).catch(()=>{});
console.log('[e2e] networkidle');

await page.waitForTimeout(8000);

// 点 3D Viewer tab 切换到 viewer
console.log('[e2e] 点击 3D Viewer tab');
const viewerTab = page.locator('text=/^3D Viewer$/').first();
const tc = await viewerTab.count();
console.log(`[e2e] 3D Viewer tab 命中: ${tc}`);
if (tc > 0) {
  await viewerTab.click();
  await page.waitForTimeout(4000);  // 等 viewer 加载
}

// 等 model-viewer 真出现
await page.waitForSelector('model-viewer, canvas', { state: 'attached', timeout: 30000 }).catch(e => {
  console.log(`[e2e] viewer 等不到: ${e.message.slice(0,100)}`);
});
await page.waitForTimeout(8000);  // GLB 加载时间

// 点"全透"按钮(把所有墙+天花板设透明 · Three.js renderer 路径)
const btnAll = page.locator('button').filter({ hasText: /^全透$|全部透明|全显|全部显示/ }).first();
const btnCount = await btnAll.count();
console.log(`[e2e] 全透 按钮命中数: ${btnCount}`);
if (btnCount > 0) {
  await btnAll.click();
  console.log('[e2e] clicked 全透');
  await page.waitForTimeout(3000);
} else {
  // fallback: 直接 inject 调 renderer.setTransparency
  console.log('[e2e] 用 inject JS · 直接调 rendererRef.setTransparency');
  const r = await page.evaluate(() => {
    const renderer = window.__arcturaRenderer;
    if (!renderer) return 'no renderer';
    if (renderer.setTransparency) {
      renderer.setTransparency({ wall_N: true, wall_S: true, wall_E: true, wall_W: true, ceiling: true });
      return 'setTransparency called';
    }
    // 老路径:遍历 wallObjs / ceilingObj 设 visible=false
    let hidden = 0;
    if (renderer.wallObjs) {
      renderer.wallObjs.forEach(g => g.traverse(o => { if (o.isMesh) { o.visible = false; hidden++; }}));
    }
    if (renderer.ceilingObj) renderer.ceilingObj.traverse(o => { if (o.isMesh) { o.visible = false; hidden++; }});
    return `hidden=${hidden}`;
  });
  console.log(`[e2e] inject result: ${r}`);
  await page.waitForTimeout(2000);
}

// 等渲染稳定 + 摄像机自动旋转停 / 调好角度
await page.waitForTimeout(2000);

// 切到"俯视" 视角(从上往下看 grid 排布最清楚)
const view = page.locator('button').filter({ hasText: /^俯视$/ }).first();
if (await view.count() > 0) {
  await view.click();
  console.log('[e2e] clicked 俯视');
  await page.waitForTimeout(2500);
}

await page.screenshot({ path: OUT, fullPage: false });
console.log(`[e2e] saved ${OUT}`);

// 同时截一份顶层 viewer 部分(裁剪到 3D 区域)
const viewer = page.locator('model-viewer, canvas').first();
const v2 = OUT.replace('.png', '-viewer.png');
try {
  await viewer.screenshot({ path: v2 });
  console.log(`[e2e] viewer-only saved ${v2}`);
} catch (e) {
  console.log(`[e2e] viewer crop fail: ${e.message}`);
}

await browser.close();
console.log('[e2e] DONE');
console.log('OUT_FULL=' + OUT);
console.log('OUT_VIEWER=' + v2);
