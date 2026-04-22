import { chromium } from "playwright";
(async () => {
  const browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext();
  const page = await ctx.newPage();
  page.on("console", m => console.log("[CONSOLE]", m.type(), m.text().slice(0,200)));
  page.on("pageerror", e => console.log("[PAGEERROR]", e.message.slice(0,300)));
  page.on("requestfailed", r => console.log("[REQFAIL]", r.url(), r.failure()?.errorText));
  await page.goto("https://arctura-front-end.vercel.app/new", { waitUntil: "load", timeout: 30000 });
  await page.waitForTimeout(8000);
  console.log("[URL]", page.url());
  console.log("[TEXT]", (await page.locator("body").innerText()).slice(0, 400));
  await page.screenshot({ path: "/tmp/new-page.png" });
  await browser.close();
})();
