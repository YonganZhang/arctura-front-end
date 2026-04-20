---
marp: true
theme: studio
paginate: true
size: 16:9
footer: Studio Copilot · Internal Handbook v2.0 · 2026-04-18
style: |
  pre { font-size: 14px !important; line-height: 1.3 !important; }
  code { font-size: 14px !important; }
  section.dense pre { font-size: 13px !important; }
  section.dense code { font-size: 13px !important; }
  section.xtiny { font-size: 15px; padding: 35px 45px 65px 45px; line-height: 1.25; }
  section.xtiny h2 { font-size: 24px; }
  section.xtiny table { font-size: 14px; }
  section.xtiny pre { font-size: 12px !important; }
  section.xtiny code { font-size: 12px !important; }
  section.xtiny td, section.xtiny th { padding: 4px 8px; }
  section.xtiny li { margin: 2px 0; }
---

<!-- _class: lead -->

# Studio Copilot
## 内部手册 — 套餐体系 & Pipeline 全景

**目标受众**: 内部团队成员
**版本**: v2.0 · 2026-04-18
**内容**: 5 档产物套餐 + 9 条 Pipeline + marp-deck 多角色 PPT + IFC 校验门禁

---

## 这份手册讲什么

1. **5 档产物套餐** — 概念 / 交付 / 报价 / 全案 / 甄选
2. **9 条 Pipeline** — P1~P11 每条的输入、输出、原理、命令
3. **Pipeline 之间的关系** — 谁依赖谁、数据怎么流转
4. **两步确认流程** — Brief 快问 + 产物选择器
5. **marp-deck 多角色 PPT** — 8 份 stakeholder 定制交付
6. **IFC 校验门禁** — 防止裸 IFC 流入下游
7. **实操速查** — 客户说什么 → 跑什么

**适用角色**: 设计师 / 销售 / 实习生 / 技术合伙人

---

<!-- _class: lead -->

# 第一部分
## 产物套餐体系（5 档）

---

## 为什么要分档

**问题**: 不是每个客户都需要全套产物

| 客户场景 | 需要什么 |
|---------|---------|
| "先看看效果" | 3D + 渲染 + 平面图 |
| "发给老板看" | 加 PPT + 客户文档 |
| "这方案多少钱" | 加能耗模拟 + 报价单 |
| "要对接施工方" | 加 BIM 导出 + 合规 + IFC 质检 |
| "给我 3 个方案选" | 以上 × 3 + 对比拼图 |

**解法**: 5 档套餐，层层递进，按需选择
**核心思路**: 每档 = 上一档 + 新增模块

---

<!-- _class: dense -->

## 5 档套餐一览（P1 室内版）

```
  [概念]  看效果 — brief + 3D + 渲染 + 平面图                        ~3 min
  [交付]  给客户 — 以上 + 方案 PPT + 客户文档                        ~5 min
  [报价]  多少钱 — 以上 + 能耗模拟 + 工料报价                        ~6 min
  [全案]  工程对接 — 以上 + BIM 导出 + 合规 + IFC 质检 + 8份定制PPT   ~10 min
  [甄选]  选方案 — 3 方案 × 全案 + 对比拼图 + 决策矩阵               ~30 min
```

| 档位 | 包含编号 | 核心受众 | 典型场景 |
|------|---------|---------|---------|
| **概念** | 1-5 | 内部讨论 | "先出个效果图" |
| **交付** | 1-7 | 客户决策 | "发给客户看" |
| **报价** | 1-9 | 客户问价 | "多少钱" |
| **全案** | 1-13 (默认) | 施工对接 | "要对接工程方" |
| **甄选** | 3×(1-13) + 拼图 | 多方案选型 | "3 个方案选" |

**按需项**: `[14] What-If` 和 `[15] Case Study` 任何档位都可追加

---

<!-- _class: dense -->

## 5 档套餐一览（P2 建筑版）

```
  [概念]  看效果 — brief + 3D + 渲染 + 全套制图                      ~5 min
  [交付]  给客户 — 以上 + 方案 PPT + 客户文档                        ~8 min
  [报价]  多少钱 — 以上 + 能耗模拟 + 工料报价                        ~9 min
  [全案]  工程对接 — 以上 + BIM 导出 + 合规 + IFC 质检 + 8份定制PPT   ~14 min
  [甄选]  选方案 — 3 方案 × 全案 + 对比拼图 + 决策矩阵               ~40 min
```

**P2 比 P1 慢**: 建筑需要多层平面 + 4 立面 + 剖面 + 总平面，图纸量大 5 倍

**编号微调示例**:

| 客户说 | 实际执行 |
|--------|---------|
| "全案，去掉 11" | 编号 1-13 去掉 IFC 质检 |
| "交付，加 8" | 编号 1-7 + 能耗模拟 |
| "概念，加 14 15" | 编号 1-5 + What-If + Case Study |

---

<!-- _class: xtiny -->

## 产物编号清单（15 项）

| # | 产物 | 概念 | 交付 | 报价 | 全案 | 按需 |
|:-:|------|:---:|:---:|:---:|:---:|:---:|
| 1 | brief.json 设计简报 | ✅ | ✅ | ✅ | ✅ | |
| 2 | moodboard.png 风格板 | ✅ | ✅ | ✅ | ✅ | |
| 3 | 3D 场景 (room/building.json) | ✅ | ✅ | ✅ | ✅ | |
| 4 | 渲染 × 8 视角 (P1) / 3 视角 (P2) | ✅ | ✅ | ✅ | ✅ | |
| 5 | 平面图 SVG+PNG / 全套制图 (P2) | ✅ | ✅ | ✅ | ✅ | |
| 6 | 方案 PPT (Marp) | | ✅ | ✅ | ✅ | |
| 7 | CLIENT-README 客户文档 | | ✅ | ✅ | ✅ | |
| 8 | 能耗模拟 P7 → EUI | | | ✅ | ✅ | |
| 9 | BOQ 报价 P6 → HK$ | | | ✅ | ✅ | |
| 10 | BIM 导出 4/5 格式 | | | | ✅ | |
| 11 | IFC Enrich + Audit | | | | ✅ | |
| 12 | 合规检查 P8 | | | | ✅ | |
| 13 | 8 份定制 PPT (stakeholder) | | | | ✅ | |
| 14 | What-If P9 参数敏感性 | | | | | ☐ |
| 15 | Case Study P11 作品集素材 | | | | | ☐ |

**依赖链自动补齐**: 选了 12（合规）但没选 8（能耗）→ 自动补选 8 并提示

---

## 两步确认流程（执行前必做）

```
用户："帮我设计一个 XXX"
         │
         ▼
  ┌─ Step 0a: Brief 快问 ──┐
  │  检查关键信息是否充足     │  ← 不足则一次性问完
  │  确认后生成 brief.json   │
  └──────────┬──────────────┘
             ▼
  ┌─ Step 0b: 产物选择器 ───┐
  │  概念/交付/报价/全案/甄选  │  ← 用户选档位
  └──────────┬───────────────┘
             ▼
          开始执行
```

- **Brief 快问不可跳过**（除非信息已充足）
- 用户明确说了档位 → 跳过选择器直接执行
- 信息不足 → 一次性把所有缺失项问完，不要一项一项追问

---

<!-- _class: dense -->

## Brief 快问 — 必填项 & 可选项

**必填项**（缺任何一项必须问）:

| # | 字段 | P1 室内 | P2 建筑 | 示例 |
|---|------|:------:|:------:|------|
| A | **空间类型** | ✅ | ✅ | 自习室 / 咖啡店 / 住宅 |
| B | **面积或尺寸** | ✅ | ✅ | 80m² / 10×8m |
| C | **容纳人数或核心功能** | ✅ | ✅ | 16 人 / 3 间卧室 |
| D | **层数** | — | ✅ | 2 层 / 3F+地下 |

**可选项**（缺失用默认值）:

| 字段 | 默认策略 |
|------|---------|
| 风格偏好 | 推荐 1 默认 + 2 备选 |
| 预算区间 | 按 HK 市场均价 × 面积估算 |
| 地点/城市 | 默认 HK |
| 特殊需求 | 不问 |

---

## 8 份 Stakeholder 定制 PPT（marp-deck skill）

全案档及以上会自动生成 **8 份差异化 PPT**，每份按受众定制内容、语气、重点：

| 受众 | 页数 | 侧重 | CSS Class |
|------|:----:|------|-----------|
| **client** 客户 | 8-11 | 渲染效果、材质故事、决策引导 | `client` |
| **investor** 投资人 | 10-12 | ROI、单位经济、竞品对标 | `investor` |
| **designer** 设计师 | 10-14 | PBR 参数、尺寸、源文件清单 | `designer` |
| **contractor** 施工方 | 8-10 | BOQ、关键节点、Gantt | `contractor` |
| **bim** BIM 团队 | 6-8 | IFC Schema、IfcProduct、MEP | `bim` |
| **school-leader** 学术 | 8-10 | 研究命题、方法论、可发表方向 | `school-leader` |
| **operations** 运营 | 8-10 | 容量、动线、能耗、维保 | `operations` |
| **marketing** 营销 | 6-8 | 人群画像、卖点、社媒素材 | `marketing` |

**配色自适应**: 每个项目从 `brief.json → style.palette` 提取色板，自动映射到 CSS 变量 → 不同风格项目的 PPT 配色自动匹配

---

## IFC 校验门禁（04-18 新增）

**问题**: 子智能体可能跳过 `enrich-ifc`，用裸 IFC 直接喂入 P7/P6

**解法**: `verify_ifc_enriched.py` 硬拦 — 检查 3 项：

| 检查项 | 合格标准 | 不合格后果 |
|--------|---------|-----------|
| PropertySet | 有 Pset_WallCommon 等标准属性 | ❌ 阻断 |
| Material | 有 IfcRelAssociatesMaterial | ❌ 阻断 |
| TypedElements | IfcWall/IfcSlab 有实际类型 | ❌ 阻断 |

P1/P2/P10 的 verification 步骤已集成此校验，裸 IFC 无法通过。

---

<!-- _class: lead -->

# 第二部分
## Pipeline 全景图

---

<!-- _class: dense -->

## 10 条 Pipeline + 2 个占位

| # | Pipeline | 阶段 | 一句话定位 | 耗时 |
|---|----------|------|-----------|------|
| **P0** | **Asset Intake** | **入口** | **客户已有文件 → 标准格式 → 路由** | **1-5 min** |
| P1 | 室内设计 | 设计 | 单房间/店铺 → 3D + 渲染 + 图纸 | 5-15 min |
| P2 | 建筑设计 | 设计 | 整栋多层 → 3D + 制图全套 | 10-20 min |
| P3 | Brief Intake | 入口 | 客户一句话 → 合法 brief.json | 1-3 min |
| P4 | *预留* | — | — | — |
| P5 | *预留* | — | — | — |
| P6 | BOQ 报价 | 分析 | 工程量 × 单价 → 造价 | 2 秒 |
| P7 | 能耗模拟 | 分析 | EnergyPlus → EUI | 2-30 秒 |
| P8 | 合规检查 | 分析 | 对标法规 → 红绿灯 | 1 秒 |
| P9 | What-If | 横向对比 | 同方案扫工程参数 | 15-60 秒 |
| P10 | A/B/C 对比 | 横向对比 | 不同设计方案选型 | 15-60 min |
| P11 | Case Study | 出口 | MVP → 三用素材库 | 30 秒/MVP |

---

## Pipeline 数据流全景图

```
┌──────────────────── 阶段 1 · 入口 ───────────────────┐
│  P0 · Asset Intake          P3 · Brief Intake         │
│  客户有文件(IFC/3D/图纸)     客户只有想法/一句话          │
│  → 格式转换+质检+路由        → brief.json               │
│       │                          │                    │
│       ├── 有 IFC → 直接进分析 ────┤                    │
│       └── 有图片 → brief → 设计 ──┘                    │
└─────────────────────┬─────────────────────────────────┘
                      ▼
┌──────────────────── 阶段 2 · 设计 ───────────────────┐
│     P1 · 室内设计    ←→    P2 · 建筑设计               │
│     3D + 渲染 + 平面图 + PPT + 5 格式导出               │
└─────────────────────┬─────────────────────────────────┘
                      ▼
┌──────────── 阶段 3 · 分析 ───────────────────────────┐
│  IFC Enrich/Audit    P7 Energy → P8 Compliance        │
│        ↘                  ↓                           │
│            P6 BOQ 报价 ◄──┘                           │
└─────────────────────┬─────────────────────────────────┘
                      ▼
┌──────────── 阶段 4 · 横向对比 ───────────────────────┐
│  P9 · What-If (参数轴)    P10 · A/B/C (方案轴)        │
└─────────────────────┬─────────────────────────────────┘
                      ▼
┌──────────── 阶段 5 · 出口 ───────────────────────────┐
│              P11 · Case Study 三用素材                 │
└───────────────────────────────────────────────────────┘
```

---

<!-- _class: lead -->

# Pipeline 0 · Asset Intake
## 客户带着文件来 — 资产入口

---

## P0 Asset Intake — 定位

**解决的问题**: 客户已有文件（IFC / 3D 模型 / 图纸 / brief），需要转化为标准格式再路由到后续 pipeline

**与 P3 的区分**:

| | P0 Asset Intake | P3 Brief Intake |
|---|---|---|
| 客户给的是 | **文件**（IFC / GLB / OBJ / FBX / PDF / 图片） | **一句话 / 需求描述** |
| 产出 | enriched IFC + brief 骨架 | brief.json |
| 可路由到 | P1/P2（设计）或 **P6/P7/P8**（有 3D 可直接分析） | 只能进 P1/P2（需要建模） |

**产物位置**: `studio-demo/intake-inbox/<intake-id>/`

---

<!-- _class: dense -->

## P0 支持的 7 种格式

| 格式 | 扩展名 | 处理路径 | 状态 |
|------|--------|---------|------|
| **IFC** | `.ifc` | 3D 路径：audit → enrich → 反推 brief → 路由 | ✅ |
| **GLB** | `.glb` | 3D 路径：Blender 导入 → 导出 IFC → 同上 | ✅ |
| **OBJ** | `.obj` | 3D 路径：同上 | ✅ |
| **FBX** | `.fbx` | 3D 路径：同上 | ✅ |
| **brief.json** | `.json` | 直接路径：Schema 校验 → 路由到 P1/P2 | ✅ |
| **PDF 图纸** | `.pdf` | Path B：Claude 视觉提取 → brief.json | ✅ |
| **图片** | `.png/.jpg/.webp` | Path B：同上 | ✅ |

**未来扩展**: DWG/DXF · SketchUp (.skp) · Revit (.rvt)

---

## P0 两条处理路径

```
                    ┌─ IFC / GLB / OBJ / FBX
                    │   → 格式转换 → 质检 → 补属性 → 反推 brief
客户文件 → 识别格式 ─┤   → 可直接路由到 P6/P7/P8（有精确几何）
                    │
                    ├─ PDF / 图片
                    │   → Claude 视觉提取 → brief.json
                    │   → 只能路由到 P1/P2（需重新建模）
                    │
                    └─ brief.json → 直接路由
```

**3D 路径 6 步**: 格式识别 → 格式转换 → 质检(audit) → 补属性(enrich) → 反推 brief → 路由

**Path B 3 步**: 格式识别 → 视觉提取(Claude Read 图片) → 路由

---

<!-- _class: dense -->

## P0 路由菜单 & 命令速查

资产处理完成后，展示菜单让客户选择下一步：

| 选项 | 执行 | 需要 IFC？ |
|------|------|:---------:|
| 跑能耗模拟 | P7 | ✅ |
| 做合规检查 | P7 → P8 | ✅ |
| 出工料报价 | P6 | ✅ |
| 全套（能耗+合规+报价） | P7 → P8 → P6 | ✅ |
| 基于此文件重新设计 | P1/P2 | ❌ |
| 参数调优 | P7 → P9 | ✅ |

**Path B（图片入口）只能选"重新设计"**（无 3D 模型，不能跑分析）

**命令速查**:

```bash
INBOX=studio-demo/intake-inbox
mkdir -p $INBOX/<id> && cp <客户文件> $INBOX/<id>/original.<ext>

# IFC 质检 + 补属性
$BLENDER_CLI model audit-ifc $INBOX/<id>/original.ifc
$BLENDER_CLI model enrich-ifc $INBOX/<id>/original.ifc --code HK --profile residential

# 路由到全套分析（IFC+brief 合并模式）
$EP_CLI project new -n "<name>" --from-brief $INBOX/<id>/brief.json \
  --from-ifc $INBOX/<id>/enriched.ifc --code HK -o $INBOX/<id>/energy/project.json
```

---

<!-- _class: lead -->

# Pipeline 3 · Brief Intake
## 客户进件 — 一切的起点

---

## P3 Brief Intake — 定位与模式

**解决的问题**: 下游所有 pipeline 都需要 brief.json，但手写 50+ 字段不现实

**三种输入模式**:

| 模式 | 客户付出 | LLM 调用 | 适用场景 |
|------|---------|---------|---------|
| **A · Free-text** | 一句话 ≤50 字 | 1-2 次 | 展会 / 朋友圈 |
| **B · Turn-based** | 5-7 轮问答 | 每 slot 1 次 | 正式 onboarding |
| **C · Form-filling** | 填 10-15 字段 | 0 次 | Web/小程序 |

**产出**: `brief.json`（合法 schema）+ `intake-report.json`

**契约**: 任何下游 pipeline 只消费 brief.json 的子集

---

## P3 数据流与命令

```
客户输入 → Brief Intake Orchestrator → brief.json
                │
  1. 场景分类（室内 / 建筑）
  2. 语言检测（zh / en）
  3. Slot 填充（LLM + 问答 + 默认值）
  4. Schema 校验 + brief_parser 兼容检查
```

**命令速查**:

```bash
PY=/opt/anaconda3/envs/mini-2025/bin/python
SCHEMA=playbooks/schemas/brief-interior.schema.json
cd /Users/kaku/Desktop/Work/CLI-Anything/llm-intake/agent-harness

# A: 从自由文本生成 brief
$PY -m cli_anything.llm_intake.llm_intake_cli from-text \
  --schema $SCHEMA --input "铜锣湾 80 平咖啡店" -o brief.json

# B: 多轮问答
$PY -m cli_anything.llm_intake.llm_intake_cli turn-based \
  --schema $SCHEMA -o brief.json

# 自动分类
$PY -m cli_anything.llm_intake.llm_intake_cli classify --input "两层别墅"
```

---

<!-- _class: lead -->

# Pipeline 1 · 室内设计
## 单房间 / 店铺 → 完整交付

---

<!-- _class: dense -->

## P1 室内设计 — 流程步骤

**输入**: 中文需求描述 → brief.json
**输出**: ~15 文件
**耗时**: 5-15 分钟（视档位）

| Step | 做什么 | 工具 | 产物 |
|:----:|--------|------|------|
| 0 | Brief 快问 + 产物选择 | — | brief.json |
| 1 | 风格板 | Python helper | moodboard.png |
| 2 | 3D 场景建模 | Blender CLI | room.json (60+ 物件) |
| 3 | 材质分配 | Blender CLI | 含颜色的场景 |
| 4 | 多角度渲染 | Blender Cycles | renders/ (8 张) |
| 5 | 平面图 | Inkscape CLI | floorplan.svg + .png |
| 6 | 方案 PPT | Marp | decks/deck-client.pptx |
| 7 | 客户文档 | 手写 | CLIENT-README.md |

**注意**: 材质分配必须在导出/渲染之前完成，渲染后必须检查颜色

---

<!-- _class: xtiny -->

## P1 已有的室内 MVP（19 个场景 + 12 建筑）

| 编号 | 场景 | 面积 | 编号 | 场景 | 面积 |
|------|------|------|------|------|------|
| 01 | 书房 | 15m² | 10 | 牙科诊所 | 130m² |
| 02 | 会议室 | 30m² | 11 | 餐厅 | 150m² |
| 03 | 咖啡店 | 80m² | 12 | 录音棚 | 100m² |
| 04 | 联合办公 | 120m² | 13 | AI 办公室 | 130m² |
| 05 | 健身工作室 | 100m² | 14 | 日式咖啡烘焙 | — |
| 06 | 儿童日托 | 150m² | 15 | 花艺工作室 | — |
| 07 | 书店 | 100m² | 16 | 适老化居家 | — |
| 08 | 美发沙龙 | 90m² | 17 | 五星泳池 | 850m² |
| 09 | 画廊 | 100m² | 18 | 学生自习室 | 80m² |
| | | | 19 | 工业风住宅客厅 | 60m² |

覆盖 **10+ 垂直行业**: 餐饮 / 办公 / 医疗 / 教育 / 休闲 / 零售 / 文化 / 住宅 / 酒店 / 健身

参考 MVP: `studio-demo/mvp/03-coffee-shop/`（完整结构）

---

<!-- _class: lead -->

# Pipeline 2 · 建筑设计
## 整栋 / 多层建筑 → 全套制图

---

<!-- _class: dense -->

## P2 建筑设计 — 比 P1 多什么

**输入**: 中文需求（需含层数）· **输出**: ~20-25 文件 · **耗时**: 10-20 min

**P2 比 P1 新增的产物**:

| 产物 | 数量 | 工具 | 给谁 |
|------|:----:|------|------|
| 总平面图 (Site Plan) | 1 | Inkscape | 规划审批 |
| 多层平面 (Floor Plans) | N 层 | Inkscape | 设计+施工 |
| 4 向立面 (Elevations) | 4 | Inkscape | 审美评审 |
| 剖面 (Section) | 1-2 | Inkscape | 结构/机电 |
| 3D 体量渲染 | 3 视角 | Blender | 客户决策 |
| DXF 导出 | 额外 | ezdxf | AutoCAD/Rhino |

**共用**: CLI 工具集、export 5 件套、brief.json 起点

---

## P2 已有的建筑 MVP（12 个）

| 编号 | 场景 | 编号 | 场景 |
|------|------|------|------|
| arch-01 | 独栋住宅 (2 层) | arch-07 | Loft 联合办公 |
| arch-02 | 办公楼 (4 层) | arch-08 | 小型诊所 |
| arch-03 | 精品酒店 (3 层) | arch-09 | 混合用途 |
| arch-04 | 社区中心 (大跨度) | arch-10 | 体育综合体 (5 层) |
| arch-05 | 中式现代住宅 (2 层) | arch-11 | 新界家庭住宅 |
| arch-06 | 小型图书馆 | arch-12 | 东北乡村住宅 |

**图纸比例规范**:
- 总平面: 1:200 ~ 1:500
- 多层平面: 1:50 ~ 1:100
- 立面: 1:100
- 剖面: 1:100

---

<!-- _class: lead -->

# Pipeline 7 · 能耗模拟
## EnergyPlus · 全年 8760 小时

---

## P7 能耗模拟 — 原理

**EnergyPlus**: 全球最权威的建筑能耗模拟引擎（美国 DOE 开源）

**输入 → 引擎 → 输出**:

| 输入 | 来源 |
|------|------|
| 建筑几何 | 从 brief.json 自动生成 |
| 围护热性能 | 墙 U 值、窗 SHGC、屋顶 |
| 气象数据 EPW | 全年 8760 小时温湿度 |
| HVAC 系统 | 空调类型 + 设定温度 |
| 使用排程 | 人员/灯/设备开关时间 |

**引擎**: 热平衡计算 × 8760 小时 × 所有热区（解偏微分方程）

**输出**: 年度 EUI (kWh/m²·yr) + 冷热负荷峰值 + 逐月分项

**传统**: 外包 2 周 + HK$50K → **Studio Copilot**: 2-30 秒 + 免费

---

## P7 三种建模模式

| 模式 | 输入 | U 值来源 | HVAC 来源 | 场景 |
|------|------|---------|---------|------|
| **A: 仅 brief** | brief.json | 默认值 | brief | 快速估算 |
| **B: 仅 IFC** | enriched.ifc | IFC Pset | 默认 | 有现成 BIM |
| **C: IFC+brief** | 两者合并 | IFC 优先 | brief 优先 | **推荐** |

**EnergyPlus 输出产物**:
- `eplustbl.htm` — HTML 报告（浏览器打开）
- `eplusout.csv` — 逐时逐区数据（Excel/Grafana）
- `in.idf` — 输入文件（给专业工程师微调）

---

## P7 命令速查

```bash
PY=/opt/anaconda3/envs/mini-2025/bin/python
EP_CLI="$PY -m cli_anything.openstudio.openstudio_cli"
cd /Users/kaku/Desktop/Work/CLI-Anything/openstudio/agent-harness
EPW=cli_anything/openstudio/data/weather/HKG_Hong.Kong.Intl.AP.epw

# 1. 建项目（推荐模式 C: IFC+brief 合并）
$EP_CLI project new -n "项目名" \
  --from-brief <brief.json> --from-ifc <enriched.ifc> \
  --code HK -o <MVP>/energy/project.json

# 2. 跑模拟
$EP_CLI -p <project.json> run simulate --weather $EPW

# 3. 看结果
$EP_CLI -p <project.json> report eui
```

---

## P7 气象数据库 & 调参

**可用气象文件**:

| 文件 | 适用地区 |
|------|---------|
| `HKG_Hong.Kong.Intl.AP.epw` | 香港（默认） |
| `HKG_Hong.Kong.Obs.epw` | 香港市区（热岛效应） |
| `CHN_Beijing.Capital.AP.epw` | 北京 |
| EnergyPlus 自带 | 5 个美国城市 |

其他城市 → 从 climate.onebuilding.org 下载 EPW

**调参命令**:

```bash
$EP_CLI -p <project.json> model set-construction wall --u-value 0.4
$EP_CLI -p <project.json> model set-construction window --u-value 1.6 --shgc 0.4
$EP_CLI -p <project.json> model set-hvac vrf
```

---

<!-- _class: lead -->

# Pipeline 8 · 合规检查
## 对标法规 → 能不能过审批

---

## P8 合规检查 — 原理

**输入**: P7 产出的 project.json（含 EUI + 围护参数）
**输出**: 红绿灯合规报告 + 整改建议
**前置**: P7 必须先跑完

**规则引擎** (Python + codes.json):

```python
rules = load_codes(code='HK')     # 从 codes.json 加载法规
for rule_name, rule in rules.items():
    actual = get_from_project(rule['path'])  # 读实际值
    passed = actual <= rule['limit']          # 对标限值
    report.add(CheckItem(name, actual, limit, passed))
```

**新法规 → 只改 JSON，不改代码**

---

## P8 支持 5 部法规

| Code | 法规 | 适用地区 | 严格度 |
|------|------|---------|--------|
| `HK` | BEEO / BEC 2021 | 香港 | ★★☆ |
| `CN_HOT` | GB 50189 (夏热冬暖) | 广州/深圳 | ★★★ |
| `CN_COLD` | GB 50189 (寒冷区) | 北京/天津 | ★★★★ |
| `ASHRAE` | ASHRAE 90.1-2022 | 国际 | ★★★ |
| `JP` | 省エネ法 2025 | 日本 | ★★★★★ |

**命令**:

```bash
$EP_CLI -p <project.json> report compliance --code HK
$EP_CLI -p <project.json> report compliance --code CN_COLD
$EP_CLI -p <project.json> report compliance --code JP
# 保存报告
$EP_CLI -p <project.json> report compliance --code HK \
  -o <MVP>/energy/compliance-HK.md
```

---

<!-- _class: dense -->

## P8 合规报告示例

| 检查项 | 实际值 | 限值 | 状态 |
|--------|--------|------|------|
| **EUI** | 103.0 | 200 | ✅ 51% |
| 外墙 U 值 | 0.555 | 1.8 | ✅ |
| 屋顶 U 值 | 0.498 | 0.8 | ✅ |
| 窗 U 值 | 2.0 | 5.8 | ✅ |
| 窗 SHGC | 0.6 | 0.6 | ✅ 临界 |
| 照明功率 | 8.0 W/m² | 12.0 | ✅ |
| 新风 ACH | 0.7 | 0.7 | ✅ |
| OTTV | 待详算 | 25 | ⚠️ |

**综合评级**: ✅ COMPLIANT / ⚠️ WARNING / ❌ FAIL

不合规项 → 自动给出整改建议（如 "窗户换 Low-E 双玻 SHGC≤0.4"）

---

<!-- _class: lead -->

# Pipeline 6 · BOQ 报价
## 工程量 × 单价 = 造价

---

## P6 两条路径

**路径 A: 从 thermal model（快速 · 2 秒）**

```
zones × 面积 → 墙/楼板/窗数量（估算）→ prices.json 查询 → BOQ 表
+ 20% MEP + 12% 前期 + 10% 不可预见
```

**路径 B: 从 enriched IFC（更精确）**

```
IfcWall.Qto → 精确墙面积
IfcSlab.Qto → 精确楼板面积
IfcRelAssociatesMaterial → 精确材料 → prices.json → BOQ 表
```

**推荐**: 先跑 A 做快速估价，需精确量再跑 B

---

## P6 三区域单价库 & 命令

| 代号 | 地区 | 币种 | 典型单价 |
|------|------|------|---------|
| `HK` | 香港 | HKD | HK$8,000-15,000/m² |
| `CN` | 中国大陆 | RMB | ¥2,500-5,000/m² |
| `INTL` | 国际 | USD | $800-2,000/m² |

**命令**:

```bash
# 路径 A: 从 thermal model
$EP_CLI -p <project.json> report boq --region HK
$EP_CLI -p <project.json> report boq --region HK \
  -o boq-HK.md --csv boq-HK.csv

# 路径 B: 从 IFC（建议先 enrich）
$EP_CLI report boq-from-ifc <enriched.ifc> --region HK

# 换区域
$EP_CLI -p <project.json> report boq --region CN    # 人民币
```

---

<!-- _class: lead -->

# IFC Enrich + Audit
## BIM 补属性 + 质检

---

## IFC Enrich & Audit

**为什么需要 Enrich**:

| | 原始 IFC | Enriched IFC |
|---|---------|-------------|
| 几何 | ✅ | ✅ |
| 热性能 (U 值) | ❌ | ✅ |
| 工程量 (面积/体积) | ❌ | ✅ |
| 材料标识 | ❌ | ✅ + 防火等级 |

**Audit 红绿灯**: 🟢 全部完整 → 进下一步 / 🟡 缺属性 → 精度降低 / 🔴 缺几何 → 需修复

**命令**:

```bash
BLENDER_CLI="$PY -m cli_anything.blender.blender_cli"
cd /Users/kaku/Desktop/Work/CLI-Anything/blender/agent-harness

# Enrich（补属性 + 材质 + 着色）
$BLENDER_CLI model enrich-ifc <file.ifc> --code HK --profile residential

# Audit（质检）
$BLENDER_CLI model audit-ifc <file.ifc>
```

**典型流程**: `enrich-ifc` → `audit-ifc` → 🟢 → 进入 P7 / P6

---

<!-- _class: lead -->

# Pipeline 9 · What-If
## 同方案 · 扫工程参数

---

## P9 What-If — 定位

**做什么**: 同一设计方案，只改工程参数，对比能耗/合规/报价

```
project.json (baseline)
     ├── 变体 A: wall_u=0.4, roof_u=0.3  (加保温)
     ├── 变体 B: window_u=1.2, SHGC=0.3  (换 Low-E)
     └── 变体 C: 全部升级
              ↓
     每变体: EnergyPlus + 合规 + BOQ（全自动）
              ↓
     并排对比表 + 自动推荐最优
```

**耗时**: 15 秒 ~ 2 分钟
**销售心理学**: 给 1 个方案是"卖"，给 3 个方案是"帮他决策"

---

<!-- _class: dense -->

## P9 允许的参数轴 & 命令

**白名单**（不在此列的轴走 P10）:

| 类别 | 参数 | 单位 |
|------|------|------|
| 围护 | `wall_u` / `roof_u` / `window_u` / `window_shgc` | W/m²K |
| HVAC | `hvac_type` | ideal_loads / split_ac / vrf / central_ac |
| 内部负荷 | `lighting_wperm2` / `equipment_wperm2` | W/m² |

**3 个内置 preset**: `envelope-upgrade` / `hvac-upgrade` / `lighting-equipment`

**命令**:

```bash
# 用 preset（最简单）
$EP_CLI -p <project.json> report whatif \
  --preset envelope-upgrade --weather $EPW

# 自定义变体
$EP_CLI -p <project.json> report whatif \
  -v baseline -v "upgrade:wall_u=0.4,window_u=1.2" --weather $EPW
```

---

<!-- _class: lead -->

# Pipeline 10 · A/B/C 方案对比
## 不同设计方案 · 视觉选型

---

## P10 vs P9 — 核心区别

| 维度 | P9 What-If | P10 A/B/C |
|------|-----------|-----------|
| 对比什么 | 同一设计的**工程参数** | 同一需求的**不同设计方案** |
| 允许的轴 | 围护 / HVAC / 照明 | **风格 / 布局 / budget** |
| 每个变体 | 同几何，换参数 | **不同几何 + 渲染 + 风格** |
| 关键产出 | 数值对比表 | **视觉拼图 + 差异矩阵** |
| 典型耗时 | 15 秒 ~ 2 分钟 | 15 ~ 60 分钟 |
| 客户场景 | "加保温值不值" | "3 个风格看看" |

**budget 轴归 P10，不走 P9**
Economy/Mid/Premium 涉及材料档次 + moodboard + 单价区间

---

<!-- _class: dense -->

## P10 产物清单 & 视觉约束

**产物**:

| 产物 | 说明 |
|------|------|
| 每方案 `v*/hero.png` + `v*/renders/` | 主图 + 4 统一视角渲染 |
| `comparison-grid-4x3.png` | 4×3 总拼图 |
| `grid-row-*.png` × 4 | 每视角单行拼图 |
| `report.json` + `diff-matrix.md` | 结构化报告 + 6 维差异矩阵 |
| `whatif-3variants.md` | 能耗参数对比 |

**视觉硬约束**:
- 所有 variant **必须用同一组 camera 参数**渲染
- 所有 variant **共用同一 footprint 和层高**（来自 base brief）
- 标准 4 视角: street-corner / front-elevation / birds-eye / interior

**diff-matrix 6 维度**: 风格定调 / EUI / 工料报价 / 年维护成本 / 合规状态 / 决策推荐

**典型旅程**: P10 选大方向 → P9 调参数（分界线 = "方案定型"）

---

<!-- _class: lead -->

# Pipeline 11 · Case Study
## MVP → 三用素材库

---

## P11 Case Study — 三种模板

**问题**: MVP 产物是给内部看的，不能直接贴到官网/tenure/sales

| 模板 | 受众 | 篇幅 | 用途 |
|------|------|------|------|
| **Portfolio** | 官网/销售 | 1 页 | Hero + 4 指标卡 + 100 字叙事 |
| **Impact** | 学术/tenure | 2-3 页 | IMRAD 格式 · 对齐 RAE |
| **Sales** | 客户 pitch | 1 页 | 痛点-方案-结果 |

**聚合产物**:
- `portfolio-index.md` — 全部 MVP 总览
- `impact-dashboard.json` — 跨 MVP 指标汇总
- `metrics.json` — 每个 MVP 的结构化指标

**边界**: 只消费已有产物，不重新建模、不重渲染

---

## P11 数据流

```
23 × MVP folders (scan + parse)
         │
         ▼
  STEP 1 · EXTRACT
  brief.json + energy/* + renders/ → metrics.json + thumbs/
         │
    ┌────┼────┬────┐
    ▼    ▼    ▼    ▼
 Portfolio  Impact  Sales    ← 三模板并行生成
   .md       .md     .md
    │         │       │
    └────┬────┘───────┘
         ▼
  STEP 3 · AGGREGATE
  portfolio-index.md + impact-dashboard.json
```

**三用**: 商业 GTM + 学术 tenure + PolyU Spinoff IP 证据

---

<!-- _class: lead -->

# 第三部分
## 实操速查 & 常见场景

---

<!-- _class: dense -->

## 客户说什么 → 跑什么（设计 & 分析）

### 设计类

| 客户说 | 执行什么 | 耗时 |
|--------|---------|------|
| "帮我设计一个咖啡店" | Step 0 → P1 全流程 | 5-15 min |
| "设计一栋两层住宅" | Step 0 → P2 全流程 | 10-20 min |
| "快速出个效果图" | P1/P2 概念档 (1-5) | 3-5 min |
| "全案跑一遍" | P1/P2 全案档 (1-13) | 10-14 min |

### 报价 & 分析类

| 客户说 | 执行什么 | 耗时 |
|--------|---------|------|
| "这个方案多少钱" | P6 BOQ | 2 秒 |
| "跑一下能耗" | P7 Energy-Sim | 2-30 秒 |
| "能不能过审批" | P8 Compliance | 1 秒 |
| "出全套报告" | P7 → P8 → P6 | < 1 min |
| "用内地价格算" | P6 `--region CN` | 2 秒 |

---

<!-- _class: dense -->

## 客户说什么 → 跑什么（对比 & 工具）

### 对比类（注意 P9 vs P10 区分）

| 客户说 | 执行什么 | 走哪个 |
|--------|---------|--------|
| "加保温值不值" | What-If | **P9** |
| "换 VRF 空调看看" | preset hvac-upgrade | **P9** |
| "给 3 个风格方案" | A/B/C 风格轴 | **P10** |
| "做三档预算对比" | A/B/C 预算轴 | **P10** |
| "给 3 个方案对比"（模糊） | **先反问** | ? |

### 资产接入（P0）

| 客户说 | 执行什么 | 走哪个 |
|--------|---------|--------|
| "我有个 IFC 文件" | Asset Intake → 质检 → 补属性 → 路由 | **P0** 3D路径 |
| "这是户型图/平面图" | Claude 视觉提取 → brief → P1/P2 | **P0** Path B |
| "帮我转成 IFC" | 格式转换 → enrich → audit | **P0** Step 2-4 |
| "检查这个 IFC 质量" | audit-ifc | **P0** Step 3 |

### 工具 & 其他

| 客户说 | 执行什么 |
|--------|---------|
| "补一下 IFC 属性" | enrich-ifc → audit-ifc |
| "用北京标准看看" | P8 `--code CN_COLD` |
| "帮客户整理需求" | P3 Brief Intake |
| "更新作品集" | P11 Case Study 批处理 |
| "所有 MVP 都更新" | `batch_all_mvps.py` |

---

## 一条龙流程（设计完成后）

**IFC 补属性 → 能耗 → 合规 → 报价**:

```bash
PY=/opt/anaconda3/envs/mini-2025/bin/python
CLI=/Users/kaku/Desktop/Work/CLI-Anything
EPW=$CLI/openstudio/agent-harness/cli_anything/openstudio/data/weather/HKG_Hong.Kong.Intl.AP.epw

# Step 1: IFC 补属性 + 质检
cd $CLI/blender/agent-harness
$PY -m cli_anything.blender.blender_cli model enrich-ifc <f.ifc> --code HK
$PY -m cli_anything.blender.blender_cli model audit-ifc <f.ifc>

# Step 2: 建项目 + 跑能耗
cd $CLI/openstudio/agent-harness
EP_CLI="$PY -m cli_anything.openstudio.openstudio_cli"
$EP_CLI project new -n "X" --from-brief <brief.json> \
  --from-ifc <enriched.ifc> --code HK -o project.json
$EP_CLI -p project.json run simulate --weather $EPW

# Step 3: 合规 + 报价
$EP_CLI -p project.json report compliance --code HK -o compliance.md
$EP_CLI -p project.json report boq --region HK -o boq.md
```

---

<!-- _class: dense -->

## 开源工具栈全景（12 个核心 CLI）

### 设计/可视化类（6 个）

| # | 工具 | 用途 |
|:-:|------|------|
| 1 | **Blender** 4.x | 3D 建模 + 渲染 + IFC 导出 |
| 2 | **Inkscape** 1.3 | SVG 矢量图 + DXF 导出 |
| 3 | **GIMP** 2.10 | 光栅图 · moodboard |
| 4 | **Marp CLI** | PPT 生成（本文档就是它做的） |
| 5 | **Pascal Editor** | 建筑快速建模（浏览器） |
| 6 | **LibreOffice** 24.x | ODP/PPTX |

### 能耗/数据/粘合类（6 个）

| # | 工具 | 用途 |
|:-:|------|------|
| 7 | **EnergyPlus** 26.1 | 年度能耗模拟引擎 |
| 8 | **ifcopenshell** 0.8.5 | IFC4 BIM 读写 |
| 9 | **ezdxf** | DXF 文件 Python 库 |
| 10 | **pygltflib** | GLB 网页 3D |
| 11 | **Click** | CLI 框架（所有 harness 基座） |
| 12 | **rsvg-convert** | SVG → PNG |

---

## 传统 vs Studio Copilot

| 环节 | 传统 | Studio Copilot | 提速 |
|------|------|---------------|------|
| 做 1 套方案 | 2-4 周 | 10-30 分钟 | ~500× |
| 做 3 套方案对比 | 2-3 个月 | 30 秒-2 分钟 | ~45,000× |
| 能耗模拟 | 外包 2 周 HK$50K | 2-30 秒 · 免费 | ~80,000× |
| 合规检查 | 人工 3-5 天 | 1 秒 | ~400,000× |
| 报价单 | 造价师 3-5 天 | 2 秒 | ~200,000× |

**核心优势**:
1. **单一真相源** brief.json → 数据不可能对不上
2. **CLI 化** → 每步可脚本化、可复现
3. **开源引擎** → 免费、可编辑、可嵌入
4. **AI 原生** → agent 读 playbook 自己跑

---

<!-- _class: lead -->

# 附录

---

<!-- _class: xtiny -->

## 附录 A: Pipeline 输入输出速查

| Pipeline | 输入 | 输出 | 耗时 |
|----------|------|------|------|
| **P0 资产接入** | IFC/GLB/OBJ/FBX/PDF/图片 | enriched IFC + brief.json + 路由 | 1-5 min |
| **P1 室内** | 中文需求 | brief + 3D + 渲染 + 平面 + PPT + 5 格式 | 5-15 min |
| **P2 建筑** | 中文需求 | brief + 多层平面 + 4 立面 + 剖面 + 3D | 10-20 min |
| **P3 进件** | 客户一句话 | brief.json + intake-report.json | 1-3 min |
| **P6 BOQ** | project.json / IFC | Markdown + CSV 报价单 | 2 秒 |
| **P7 能耗** | brief.json + EPW | EUI + 能耗分解 | 2-30 秒 |
| **P8 合规** | P7 结果 | 红绿灯报告 + 整改建议 | 1 秒 |
| **P9 What-If** | project.json + 参数 | 并排对比表 | 15-60 秒 |
| **P10 A/B/C** | base brief + 变体轴 | N variant + 拼图 + diff-matrix | 15-60 min |
| **P11 Case Study** | MVP folder | portfolio + impact + sales | 30 秒/MVP |
| **IFC Enrich** | raw .ifc | enriched .ifc | 2 秒 |
| **IFC Audit** | .ifc | 红绿灯质检 | 1 秒 |

---

<!-- _class: xtiny -->

## 附录 B: 编号 → Pipeline 映射

| # | 产物 | 调用 | # | 产物 | 调用 |
|:-:|------|------|:-:|------|------|
| 1 | brief.json | P3 / 手写 | 9 | BOQ 报价 | **P6** |
| 2 | moodboard | Python helper | 10 | BIM 导出 4/5 格式 | Blender+ezdxf |
| 3 | 3D 场景 | Blender CLI | 11 | IFC Enrich+Audit | ifcopenshell |
| 4 | 渲染 | Blender Cycles | 12 | 合规检查 | **P8** |
| 5 | 平面图/制图 | Inkscape CLI | 13 | 8 份定制 PPT | marp-deck |
| 6 | 方案 PPT | Marp | 14 | What-If | **P9** (按需) |
| 7 | CLIENT-README | 手写 | 15 | Case Study | **P11** (按需) |
| 8 | 能耗模拟 | **P7** | | | |

## 附录 C: 区域法规总表

| 代号 | 报价币种/单价 | 合规法规 | 严格度 |
|------|-------------|---------|--------|
| `HK` | HKD · HK$8k-15k/m² | BEEO/BEC 2021 | ★★☆ |
| `CN_HOT` | RMB · ¥2.5k-5k/m² | GB 50189 (夏热冬暖) | ★★★ |
| `CN_COLD` | RMB · ¥2.5k-5k/m² | GB 50189 (寒冷区) | ★★★★ |
| `ASHRAE` | USD · $800-2k/m² | ASHRAE 90.1-2022 | ★★★ |
| `JP` | — | 省エネ法 2025 | ★★★★★ |

---

<!-- _class: lead -->

# The End
## 有问题找 Claude 或问团队

**文档位置**:
- 本手册: `deliverables/internal-handbook/`
- Pipeline 文档: `playbooks/*-pipeline.md`
- 产物选择器: `playbooks/product-selector.md`
- 快速指南: `playbooks/QUICK-START.md`

**版本**: v2.0 · 2026-04-18
