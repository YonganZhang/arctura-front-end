# Arctura Labs Front-end

> **对外官网 + Project Space 演示前端** · 用户能用 AI 对话生成 3D 室内设计方案。
>
> 🌐 Live: https://arctura-front-end.vercel.app

## 📜 起源与版本

这个仓 **接续** `Arctura-Lab/Front-end` 2026-04-19 zip 版本（郭老师 Zhiling Guo 最初设计的"客户门户"雏形），在此基础上演进了 Phase 1-6 共 6 大阶段、98+ commits、~12000 行代码。

- 老师最初版本的定位：**客户门户**（M1 静态分享页 → M2 交互页）· 固定 zen-tea 演示数据
- 本版的定位：**对话式 AEC 设计平台**（用户跟 AI 说话 → 产 brief → 选档位 → 生成 3D MVP → 精修 → 保存）

## 🏗 Phase 进度（2026-04-20 → 2026-04-23）

| Phase | 状态 | 内容 |
|---|---|---|
| 1.7 | ✅ | 42 MVP 动态展示（Vercel · 6.8MB webp） |
| 1.8 | ✅ | Chat → 真改 JSON 数据 · 5 tool · 24 variants |
| 1.9 | ✅ | 真 3D GLB（45 文件）+ 围护切换 · schema+playwright |
| 2.0 | ✅ | 家具级 chat 编辑 · pilot `01-study-room` · 13 op |
| 3 | ✅ | Assembly 层 + 点击卡片 + 5 透明 + 美化 A-H |
| 4 | ✅ | Plan Mode · LLM plan + dry-run + self-correct |
| 5 | ✅ | brief-driven MVP 创建入口 + 渲染双模式（fast/formal） |
| 5.1-5.4 | ✅ | CLAUDE.md 对齐 + 视角持久化 + 子智能体审查修 |
| **6.0** | ✅ | arctura_mvp 包骨架 · TIER_CONFIG 5 档 · State machine |
| **6.A** | ✅ | Upstash Redis + Project CRUD + 43 MVP 幂等迁移 + `/api/projects` |
| **6.B** | ✅ | Brief Chat 后端 · `/api/brief/chat` SSE + GPT-5.4 |
| **6.C** | ✅ | Wizard UI · `/new` 路由 + useWizardProject hook + 4 组件 · e2e 4/4 |
| **6.D** | 🔶 | Save API 骨架（KV 版 · git commit 待 PAT） |
| 6.E | ⏳ | SaveButton UI + 测试补齐 + 动态画廊前端接入 |

## ✨ 核心功能（当前）

### 新建项目（7 步流程 · Phase 6）

```
主页"+新建项目" → /new (Wizard)
  Step 1 · BriefChat (多轮 LLM 对话 · 产 brief)
  Step 2 · TierPicker (5 档: 概念/交付/报价/全案/甄选)
  Step 3 · GenerateProgress (Phase 6.D 后真接 worker)
  → /project/<slug> 精修 (已有 Phase 3/4 全套 UI)
```

### 已有 43 MVP 展示

- https://arctura-front-end.vercel.app/project/01-study-room （pilot · 完整 scene）
- https://arctura-front-end.vercel.app/project/50-principal-office （日式禅风校长办公室 · 2026-04-22 新做）

### AI 对话改场景（Plan Mode）

project 页面右侧 chat · 说"删沙发" / "更温馨" / "切 v3 方案" · AI 产 plan → 用户勾选 → apply。

### 5 档 × 渲染双模式

- 概念/交付/报价 → **快速渲染**（Three.js + Playwright 截图 · 2min）
- 全案/甄选 → **正式渲染**（Blender · 待 worker 装完）

## 🧱 架构

```
前端（React + importmap + Babel in-browser · 无构建步骤）
  ├── index.html + Arctura Labs.html（官网）
  ├── project/index.html（Project Space 入口）
  └── project-space/app.jsx（2800+ 行 · Wizard/Project/Variants/3D/BriefChat 全部）

后端（Vercel Edge Functions）
  ├── /api/projects           GET list / POST create
  ├── /api/projects/<slug>    GET/PATCH/DELETE
  ├── /api/projects/<slug>/save  POST · pending 持久化
  ├── /api/brief/chat         POST SSE · 多轮 brief 对话
  ├── /api/chat-edit          POST · Plan Mode（Phase 4）
  └── /api/scene/ops          POST · 直接 op（Phase 2）

核心 Python 包（_build/arctura_mvp/）
  ├── tiers.py        # 5 档 TIER_CONFIG（单一真源）
  ├── state.py        # 5 state machine
  ├── store/kv.py     # Upstash REST client
  ├── chat/brief_engine.py  # schema-guided LLM
  └── ...

数据
  ├── Upstash Redis   KV 主存（实时 · 热数据 · 150-200 project）
  ├── data/mvps/*.json 静态（43 MVP · git tracked · fallback）
  └── assets/mvps/<slug>/ webp + bundle.zip

Worker（Phase 6.D 完整实装后）
  └── 本机 tencent-hk · systemd 服务 · 从 Upstash 队列 brpop 拉 job
```

## 🔧 开发

```bash
# 本地 serve
npm run serve   # python3 -m http.server 8880

# 测试
npm test        # Playwright e2e
npm run validate  # schema 校验 43 MVP

# 部署
vercel --prod
```

### 环境变量

```bash
# Vercel prod 已设
UPSTASH_REDIS_REST_URL=https://...upstash.io
UPSTASH_REDIS_REST_TOKEN=...
ZHIZENGZENG_API_KEY=sk-zk...  # LLM gateway (GPT-5.4 / deepseek-v3.2)

# 待设（Phase 6.D 真 git commit 需要）
GITHUB_TOKEN=ghp_...
```

## 📂 关键文档

- **AI 协作必读**：`CLAUDE.md`（本仓业务规则 + API 端点 + env）
- **设计愿景权威规则**：`../StartUP-Building/CLAUDE.md`（郭老师 434 行）· `Arctura-Lab/Pipelines` 仓
- **Phase 6 完整实装计划 v3**：`../../wiki-methodology/top/findings/arctura-phase6-complete-plan-v3-2026-04-22.md`

## 🤝 协作

- 主要作者：[@YonganZhang](https://github.com/YonganZhang)（张永安）
- 原始设计：[@zhilingguo](https://github.com/zhilingguo)（郭智凌 · `Arctura-Lab/Front-end` 原版 + `Arctura-Lab/Pipelines` 权威规则）

## 📦 Tech Stack

- React 18（UMD · importmap · 无构建步骤）
- Vercel Edge Functions（Node · SSE · ReadableStream）
- Upstash Redis（KV · sorted set 画廊 · jobs 队列）
- Three.js r165+（3D 实时 · PBR + HDRI + ACES · 近似光追）
- Playwright（E2E 测试 + fast 渲染）
- Blender 4.2.3 LTS（可选 · formal 渲染 · 本机 tencent-hk 已装）
- GPT-5.4 + deepseek-v3.2（via ZHIZENGZENG gateway）

## 📝 License

Proprietary · Arctura Labs 内部项目
