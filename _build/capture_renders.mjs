// Playwright 截 Three.js canvas · 8 个视角 · 替代 Blender 预渲染
// 纯浏览器操作 OrbitControls 拖拽 · 零代码改动 · 连 prod 或本地
//
// 用法：
//   node _build/capture_renders.mjs --slug 50-principal-office [--url https://arctura-front-end.vercel.app]

import { chromium } from "playwright";
import { mkdirSync, writeFileSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, "..");

const args = Object.fromEntries(
  process.argv.slice(2).reduce((acc, a, i, arr) => {
    if (a.startsWith("--")) acc.push([a.slice(2), arr[i + 1]]);
    return acc;
  }, [])
);
const slug = args.slug || "50-principal-office";
const baseUrl = args.url || "https://arctura-front-end.vercel.app";
const outDir = resolve(ROOT, "assets/mvps", slug, "renders");

// 8 个相机角度（OrbitControls 鼠标拖拽 dx dy · 累计从原位置）
const views = [
  { id: "01", name: "01_hero_corner", desc: "Hero 角度", dx: 0, dy: 0 },
  { id: "02", name: "02_front_view", desc: "正面", dx: -260, dy: 0 },
  { id: "03", name: "03_back_view", desc: "背面", dx: 260, dy: 0 },
  { id: "04", name: "04_left_side", desc: "左侧", dx: -180, dy: 0 },
  { id: "05", name: "05_right_side", desc: "右侧", dx: 180, dy: 0 },
  { id: "06", name: "06_top_down", desc: "俯视", dx: 0, dy: -250 },
  { id: "07", name: "07_eye_level", desc: "人眼视角", dx: -80, dy: 60 },
  { id: "08", name: "08_corner_detail", desc: "角落细节", dx: 120, dy: -80, zoomDelta: -200 },
];

async function main() {
  mkdirSync(outDir, { recursive: true });
  console.log(`▸ 输出到 ${outDir}`);
  console.log(`▸ 加载 ${baseUrl}/project/${slug}\n`);

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1600, height: 1000 },
    deviceScaleFactor: 2,
  });
  const page = await context.newPage();

  page.on("console", msg => {
    if (msg.type() === "error") console.log(`[browser err] ${msg.text().slice(0, 200)}`);
  });

  await page.goto(`${baseUrl}/project/${slug}`, { waitUntil: "networkidle", timeout: 30000 });
  console.log("✓ 页面加载");

  // Sidebar 的 3D Viewer · 文字找 · 有多个「3D」候选 · 用 "3D Viewer" 精确
  await page.waitForTimeout(2000);
  const sidebarItems = await page.locator("nav, aside, .sidebar, [class*='side']").first().locator("*").filter({ hasText: /^3D Viewer/ }).all();
  console.log(`  sidebar 3D items: ${sidebarItems.length}`);

  // 直接点所有显示 "3D Viewer" 文字的元素
  const tab3d = page.getByText("3D Viewer", { exact: false }).first();
  try {
    await tab3d.click({ timeout: 5000 });
    console.log("✓ 点 3D Viewer tab");
  } catch (e) {
    console.log("⚠ 点 3D Viewer 失败 · fallback screenshot 整页");
    await page.screenshot({ path: resolve(outDir, "_debug_page.png"), fullPage: true });
  }

  await page.waitForTimeout(4000);
  await page.waitForSelector("canvas", { state: "attached", timeout: 20000 });
  await page.waitForTimeout(3000);
  const canvases = await page.locator("canvas").all();
  console.log(`  找到 ${canvases.length} 个 canvas`);

  // 取最大的 canvas（3D viewer）
  let targetCanvas = null, maxArea = 0;
  for (const c of canvases) {
    const box = await c.boundingBox();
    if (!box) continue;
    const area = box.width * box.height;
    if (area > maxArea) { maxArea = area; targetCanvas = c; }
  }
  if (!targetCanvas) throw new Error("没找到 3D canvas");
  const box = await targetCanvas.boundingBox();
  console.log(`  目标 canvas ${Math.round(box.width)}×${Math.round(box.height)}`);

  const cx = box.x + box.width / 2;
  const cy = box.y + box.height / 2;

  for (const v of views) {
    // 每张从 hero 起始 · 回到默认视角 · 再拖到目标
    // 简化：直接连续拖（累计到下一个） · 默认 OrbitControls 不会自动回弹
    // 先回 hero（刷新页面最稳 · 但慢） → 改用 keyboard Home 如果有 · 没有就累计
    if (v.dx !== 0 || v.dy !== 0) {
      await page.mouse.move(cx, cy);
      await page.mouse.down();
      await page.mouse.move(cx + v.dx, cy + v.dy, { steps: 15 });
      await page.mouse.up();
      await page.waitForTimeout(400);
    }
    // Zoom (scroll)
    if (v.zoomDelta) {
      await page.mouse.move(cx, cy);
      await page.mouse.wheel(0, v.zoomDelta);
      await page.waitForTimeout(300);
    }

    const pngPath = resolve(outDir, `${v.name}.png`);
    // 不等 stable · 直接 evaluate 取 canvas.toDataURL · 最快
    const dataUrl = await page.evaluate(() => {
      const canvases = Array.from(document.querySelectorAll("canvas"));
      let biggest = null, maxA = 0;
      for (const c of canvases) {
        const b = c.getBoundingClientRect();
        const a = b.width * b.height;
        if (a > maxA) { maxA = a; biggest = c; }
      }
      if (!biggest) return null;
      return biggest.toDataURL("image/png");
    });
    if (!dataUrl) { console.log(`  ⚠ ${v.name} canvas.toDataURL 失败`); continue; }
    const b64 = dataUrl.split(",")[1];
    writeFileSync(pngPath, Buffer.from(b64, "base64"));
    console.log(`  ✓ ${v.name}.png (${v.desc})`);
  }

  await browser.close();
  console.log(`\n✓ 8 张截图完成 · ${outDir}`);
}

main().catch(e => { console.error(e); process.exit(1); });
