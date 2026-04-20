// playwright.config.mjs · Arctura 前端冒烟测
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./_tests",
  // 每个测试超时 30s · 整套跑 10 min 上限
  timeout: 30_000,
  expect: { timeout: 5_000 },
  fullyParallel: true,
  retries: 0,
  workers: 4,
  reporter: "line",
  use: {
    baseURL: "http://localhost:8880",
    actionTimeout: 10_000,
    trace: "retain-on-failure",
  },
  // 自动起本地 server · 测完自动停
  webServer: {
    command: "python3 -m http.server 8880",
    port: 8880,
    reuseExistingServer: !process.env.CI,
    timeout: 10_000,
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
