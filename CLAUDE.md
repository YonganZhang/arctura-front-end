# Arctura-Front-end · Claude 必读

> 本文件是 Claude Code 的 session 启动指引。Front-end 是 Arctura 生态的**展示层**，不是产物源头。

## 🔴 做 MVP / 新设计 / 新项目前 · 必读上游权威规则

**第一动作必须是**（不可跳过）：

```
Read /home/yongan/projects/公司项目/Building-CLI-Anything/StartUP-Building/CLAUDE.md
```

这份 434 行文件对应 GitHub `Arctura-Lab/Pipelines/blob/main/CLAUDE.md` · 是 Arctura 整个生态的业务法。核心条款：

- **Step 0a Brief 快问**（L405）· 面积/功能/人数不足必问 · 禁止猜测
- **Step 0b 产物选择器 5 档**（L410）· 概念 / 交付 / 报价 / 全案 / 甄选 · 让用户选
- **MVP 必含产物清单**（L434）· brief + moodboard + room + renders×8 + floorplan + decks + CLIENT-README + exports + energy + case-study
- **执行纪律**（L350）· 做不到就说 · 禁止静默跳过
- **归属规则**（L65）· MVP 真产物在 `StartUP-Building/studio-demo/mvp/<NN>-<slug>/` · Front-end 只存展示用 JSON

读完 · 在回复开头输出合规自检：

```
📋 CLAUDE.md 合规自检
☑ 已读 StartUP-Building/CLAUDE.md
☑ Step 0a Brief 快问：<用户 brief>
☑ Step 0b 档位：<用户选的档位>
☑ 本任务对应 CLAUDE.md 哪几条：<具体引用>
☐ 做不到的产物：<明确说 · 不静默跳过>
```

## Arctura 生态 · 两条路径分工

```
brief
  │
  ├─ [FULL pipeline] StartUP-Building/  ← 权威产物源
  │    P1/P7/P8/P6/P10 ...
  │    → studio-demo/mvp/<slug>/
  │      含：8 renders · moodboard · room.json · floorplan.svg
  │          decks/deck-client.pptx · CLIENT-README · exports(glb/fbx/ifc)
  │          energy (真 EnergyPlus) · case-study · variants
  │    → _build/build_mvp_data.py 扫这里 → Front-end/data/mvps/<slug>.json
  │
  └─ [LIGHT pipeline] Arctura-Front-end/   ← 前端 demo 捷径（本仓）
       _build/create_mvp_from_brief.py
       + _build/materialize_full_mvp.py  ← 产出 FULL 需要的文本/SVG 部分
       → data/mvps/<slug>.json + assets/mvps/<slug>/bundle.zip
       → StartUP-Building/studio-demo/mvp/<slug>/ 文本产物

       ⚠ 不产 Blender 3D 渲染 · 不产真 EnergyPlus · 只是展示骨架
       ⚠ 真交付必走 FULL pipeline
```

**用户说"做 MVP"时默认走哪条**：
- 明确说"demo / 快速 / 展示" → LIGHT
- 明确说"客户交付 / 正式" → FULL（需 Mac + Blender + OpenStudio）
- 不明说 → **问**一句："要 demo 骨架（5-10 分钟 · 前端可展示）还是正式交付（45 分钟 + · 含渲染/IFC/PPT）"

## 本仓关键入口

### API 端点（部署在 Vercel Edge）
- `POST /api/chat-edit` · Plan mode 对话式编辑（LLM plan + dry-run + self-correct + action=apply）
- `POST /api/scene/ops` · 直接 op 应用（点击卡片保存走这里 · 13 op）
- **`GET /api/projects`** 🆕 Phase 6.A · 动态画廊（Upstash KV ZSET · cursor 分页 · fallback static mvps-index.json）
- **`POST /api/projects`** 🆕 Phase 6.A · 创建 empty project · anon cookie + rate limit（IP 10/h · session 20/day）
- **`POST /api/brief/chat`** 🆕 Phase 6.B · Brief 对话 SSE · GPT-5.4 · events: start/reply/brief_update/heartbeat/complete/error · state empty→briefing 自动推
- **`GET/PATCH/DELETE /api/projects/<slug>`** 🆕 Phase 6.C · 单 project 读/改/软删 · optimistic lock + state transition 白名单
- **`POST /api/projects/<slug>/save`** 🆕 Phase 6.D/7.3 · KV 持久化 + **真 git commit** · GitHub Contents API · 路径白名单 `data/mvps/<slug>.json` · 1 MB 上限
- **`POST /api/mvp/create`** 🆕 Phase 7 · 验 state=planning + tier 已设 · rpush jobs:queue · 返 `{job_id, stream_url}`
- **`GET /api/jobs/<id>/stream`** 🆕 Phase 7 · Edge SSE · lrange 游标 · heartbeat · worker_offline 探活 · 15min timeout
- 前端 **`/new`** 路由 🆕 Phase 6.C/7 · Wizard 3 step（Brief Chat / TierPicker / GenerateProgress-SSE）· app.jsx 3300+ 行

### 单一真源（改这里就够 · 不要散写）
- `_build/arctura_mvp/schemas/brief-rules.json` + `api/_shared/brief-rules.json`（对称副本 · 测试锁定一致）
- `_build/arctura_mvp/schemas/state-machine.json` + `api/_shared/state-machine.json`
- `_build/arctura_mvp/store/keys.py` (Python K.xxx) + `api/_shared/kv-keys.js` (JS K.xxx)

### 测试（Phase 7.1 · 2026-04-23）
- 单元：`npm run test:unit` · pytest **78 test** · 0.24s · 覆盖 tiers / state / brief_engine / _core / cross-lang / **scene generator / artifacts meta / enqueue_job**
- E2E：`npm test` · Playwright Wizard 4 + Phase6D 4 = 8 test
- 全量：`npm run test:all`

### MCP Server（Phase 7.1 · 真接 worker）
- `_build/arctura_mvp/mcp_server.py` · 9 tools · stdio JSON-RPC 2.0
- `arctura_generate_mvp` **真入队** Upstash jobs:queue · 返真 job_id + stream_url（不再撒谎）
- 运行：`python3 -m _build.arctura_mvp.mcp_server --stdio` · schema：不带参跑
- 升级：`pip install mcp` 后改用 SDK · tool 定义复用

### Worker（Phase 7.2 · systemd 常驻）
- 本机 tencent-hk 走 `systemctl --user arctura-worker`（`_build/systemd/`）
- Heartbeat 每 30s 写 `worker:<host>:heartbeat`（TTL 120s）· SSE 端点探 job 排队 >45s 无心跳 → `worker_offline` 事件
- Worker 自起 localhost static server（`_build/arctura_mvp/local_server.py`）· Playwright 调 localhost 不依赖 Vercel static snapshot · 解决 "新 MVP 数据未 deploy 导致 renders 404"
- `render_base_url` 独立于公开 `base_url` · 产物里填 prod URL · 渲染调 localhost

### 环境变量（Vercel prod 已设）
- `UPSTASH_REDIS_REST_URL` · `UPSTASH_REDIS_REST_TOKEN`（Phase 6.A）
- `ZHIZENGZENG_API_KEY`（LLM gateway）
- `GITHUB_TOKEN` ✅ 已设（Phase 7.3 · 复用 gh CLI 全权限 PAT · save.js 路径白名单限 data/mvps/ · 低爆炸半径）

本机同名 env：`~/.arctura-env`（chmod 600）· worker/CLI/迁移脚本读。凭据加密版在 `~/.claude/skills/share-docx/references/api-credentials.md.age`（csync 共享）。

### 创建/补齐 MVP（Phase 5）
```bash
# 从 brief 起新 MVP · 默认 LIGHT（--mode 可选）
python3 _build/create_mvp_from_brief.py --brief brief.json --slug 50-xxx --mode light
# 未来 FULL 模式（需 Blender 渲染脚本 · 当前回退到 LIGHT）
python3 _build/create_mvp_from_brief.py --brief brief.json --slug 50-xxx --mode full

# 已有 MVP 补齐 variants + bundle + index
python3 _build/create_mvp_from_brief.py --retrofit 50-xxx --mode light

# 按 CLAUDE.md 必含产物清单完整补齐（SVG / moodboard / CLIENT-README / deck / variants / case-study）
python3 _build/materialize_full_mvp.py --slug 50-xxx

# 截 N 张 Three.js renders（LIGHT 模式 · Playwright + window.__arcturaRenderer）
node _build/capture_renders.mjs --slug 50-xxx
```

### 渲染双模式（2026-04-22）
- **LIGHT**（默认）· Playwright + Three.js · 2 分钟出 8 张 · 近似光追（PBR+HDRI+ACES）
- **FULL**（待实装）· Blender + OpenStudio + Marp · 真 Cycles 照片级 + IFC/FBX 导出
  - Blender 已装：`~/.local/blender/blender-4.2.3-linux-x64/blender`
  - 渲染脚本 `_build/render_with_blender.py` 未写 · 下次 commit 补

### 默认路由
- `/project`（无 slug）→ `01-study-room`（唯一有完整 Phase 2/3/4 scene 的 pilot）· 定义在 `app.jsx::getSlugFromUrl`
- `/project/:slug` → `/project-space/index.html`（vercel.json rewrite）

### Cache bust（改文件必改版号 · 否则 Vercel CDN 缓存）
- `project/index.html` 的 `app.jsx?v=N` · `three-scene-renderer.js?v=N`

## Phase 进度速查（2026-04 · 最新在底下）

| Phase | 状态 | 关键文件 |
|---|---|---|
| 1.8 Chat → 真改数据 | ✅ | `/api/chat-edit` · `scene-ops.js` |
| 1.9 3D GLB + 围护切换 | ✅ | `three-scene-renderer.js` · 45 GLB |
| 2.0 家具级 chat 编辑 | ✅ | `scene-tools.js` · 13 op · pilot 01-study-room |
| 3 Assembly 层 + 点击卡片 + 美化 | ✅ | `assemblies[]` · `FurnitureCard` · 5 透明 |
| 4 Plan Mode | ✅ | `chat-edit.js` LLM plan + dry-run |
| 5 brief-driven MVP 创建 | ✅ | `create_mvp_from_brief.py` + `materialize_full_mvp.py` |
| 6 KV 动态 projects + Brief SSE + Wizard | ✅ | `api/projects.js` · `api/brief/chat.js` · `/new` Wizard |
| 7 Worker 队列 + SSE + 异步生成 | ✅ | `_build/arctura_mvp/worker.py` + `api/mvp/create.js` + `api/jobs/[id]/stream.js` |
| 7.1 brief→scene generator + MCP 真接 + meta 字段 | ✅ | `generators/scene.py` · `_core.enqueue_job` · `ArtifactResult.meta` |
| 7.2 Worker systemd + heartbeat + local render server | ✅ | `_build/systemd/` · `local_server.py` · `worker:<host>:heartbeat` |
| 7.3 save.js 真 git commit · Vercel GITHUB_TOKEN | ✅ | `api/projects/[slug]/save.js::commitMvpFile` · GitHub Contents API · 路径白名单 |
| 7.4 对齐严老师 spec · 6 skeleton · _TODO-INDEX · brief 必填 | ✅ | `artifacts/_unimplemented.py` + `{deck_client,client_readme,energy_report,exports,variants,case_study}.py` · 各返 skipped + 写 `_TODO-<name>.md` · bundle 顶层 `_TODO-INDEX.md` · brief_rules must_fill 加 headcount |
| 7.5 真集成严老师现成脚本 · 3 artifact 真产 | ✅ | client_readme 用 `templates/client-readme-template.md` · case_study 用 `vendor/case_study/render_templates.py` · variants 用 `vendor/score_variants.py` · `/api/projects/<slug>/history` 接 GitHub commits · 剩 3 skeleton _TODO 指真脚本路径 |
| 8 架构整合 · product_registry SSOT · MCP 命名空间 · 对齐严老师 Pipelines 完整仓 | ✅ | `product_registry.py`（15 产物 × 5 档 × LIGHT/FULL）· tiers.py 降级为 thin facade · `vendor/` 镜像严老师 11 脚本 + 3 schema + 3 defaults · artifacts 全 registry 驱动 · skeleton 删 3 文件 · MCP 新 7 namespace 17 tools + 9 legacy alias |
| 9 真集成严老师 harness · 3 skeleton 升真产 · LIGHT 10/11 | ✅ | 删 vendor/ copy 13 文件 改 sys.path import · `paths.py` 本机源路径常量 · `pip install -e` 4 个 agent-harness（llm-intake / image-grid / blender / openstudio）· `deck_client` 真产 Marp PPT + PDF · `exports` 真产 GLB/OBJ/FBX（Blender headless）· `energy_report` 真产 project.json + BOQ + CSV · brief 必填硬校验 L356 · moodboard 6 色 5 preset · case_study 真 LLM narrate（ZHIZENGZENG）· full 档 E2E 10/10 真产 0 skip |
| 9.2 scene clutter + floorplan m² + IFC4 via ifcopenshell + narrate gpt-5.4 fix | ✅ | `generators/scene.py` 加 decor clutter（5 must_have → 19 objects）· `floorplan.py` 加"面积 N m²"标注 · `exports.py` 加 IFC4 via `cli_anything.blender.core.ifc_export`（纯 ifcopenshell · 不需 Blender binary）· `case_study.py` gpt-5.4 `max_completion_tokens` fix |
| 9.3 EnergyPlus binary + 真能耗 simulate + compliance-HK.md | ✅ | 装 EnergyPlus 25.1 Ubuntu22.04 至 `~/.local/EnergyPlus-25.1.0/` · `~/.arctura-env` 加 PATH + `ENERGYPLUS_IDF_VERSION=25.1` · 修严老师 `idf_builder.py` 两处：Version 硬编码 → env 驱动、`For: Weekends Holidays` → `For: AllOtherDays`（EP 25.1 语法）· `energy_report.py` 加 Step 1.5 `run simulate --weather HK.epw` · 真 EUI 46 kWh/m²·yr · 真 compliance-HK.md 8 check（OTTV/LPD/SHGC…）· full 档 **磁盘** 11/11 真产（前端 JSON 断环 · 由 Phase 9.4 修） |
| 9.4 Materializer 断环修 + 发布门槛 + drift 收敛 | ✅ | Codex pre-push 审查发现 3 类问题根因 = 缺 materializer：(1) artifact 真产物落磁盘但 `data/mvps/<slug>.json` 占位（46 MVP 全 `decks=0`）(2) worker 无论 partial/errors 都 `state=live`（空壳上线）(3) `product_registry.py` "16 产物" 实际 15 · "11/11 真产" 在断环下不诚实 · 修：新 `materializer.py`（从 `build_mvp_data.py` 抽 470 行纯函数 · 单文件 520 行）· worker 加 materialize 步骤 + essential 门槛（full 档缺任一 → `state=generating_failed`）· `save.js::toFrontendShape()` 先读 `p.artifacts.fe_payload` fallback 占位 · 前端 `/project/<slug>` 真显示 EUI 41.9 / 真 PPT / 真 IFC 下载链接 |

## 编码纪律（Yongan 全局偏好）

- **一劳永逸不打补丁** · 架构级修 · 不加漏洞
- **诚实汇报** · 做不到就说 · 禁止"调用失败包装成成功"
- **Reuse first** · 复杂需求先搜 GitHub / wiki
- **方法论实验先 sandbox** · 不污染主 pipeline

## 相关文档

- 上游权威：`/home/yongan/projects/公司项目/Building-CLI-Anything/StartUP-Building/CLAUDE.md`
- 项目总索引：`/home/yongan/projects/公司项目/wiki-methodology/index.md`
- Front-end 代码档：`/home/yongan/projects/公司项目/wiki-methodology/code/mod-arctura-front-end.md`
- Phase 5 finding：`/home/yongan/projects/公司项目/wiki-methodology/top/findings/arctura-new-mvp-pipeline-2026-04-22.md`

---

**这份文件诞生原因**：2026-04-22 用户做"校长办公室 MVP"任务时，Claude 没读上游 CLAUDE.md 就动手，导致跳过 Step 0b 5 档选择器、MVP 产物缺 80%、套餐 404 等 4 次同类错误。用户明确要求"下次不再犯" · 此文件为 L2 机械防线（Claude Code 自动加载 working directory 的 CLAUDE.md）。

另有 L1 memory 规则、L4 回复自检 checklist 配合。L3 hook（全局 settings.json）暂未上。
