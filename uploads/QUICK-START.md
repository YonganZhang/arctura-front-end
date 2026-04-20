# Studio Copilot — 快速使用指南

> 你不需要记任何命令。直接用中文告诉 Claude 你想做什么。

> **已实装 Pipeline**：9 条 (P1/P2/P3/P6/P7/P8/P9/P10/P11)
> **待实装**：0 条（P4/P5 为未来预留占位）
>
> P11 narrative 段默认由 Claude（在 Claude Code workflow 内）直接生成（见 `playbooks/scripts/case-study/populate_narratives.py`）。如需程序化生成，`narrate.py` 也保留了 Gemini CLI fallback，失败自动写占位符。

---

## Pipeline 全景图

```
 ┌───────────────────────────────── 阶段 1 · 入口 ─────────────────────────────────┐
 │                                                                                │
 │                         ┌────────────────────────────┐                          │
 │                         │  P3 · Brief Intake          │                          │
 │                         │  客户一句话 / 多轮对话       │                          │
 │                         │  → brief.json (schema 合法) │                          │
 │                         └──────────────┬─────────────┘                          │
 │                                        │                                        │
 └────────────────────────────────────────┼────────────────────────────────────────┘
                                          ▼
 ┌───────────────────────────────── 阶段 2 · 设计 ─────────────────────────────────┐
 │                                                                                │
 │                    ┌───────────────────┴───────────────────┐                    │
 │                    ▼                                       ▼                    │
 │           ┌────────────────┐                      ┌────────────────┐            │
 │           │ P1 · Interior   │                      │ P2 · Architect  │            │
 │           │ 室内设计         │                      │ 建筑设计         │            │
 │           │ 单房间/店铺      │                      │ 整栋/多层        │            │
 │           │ ~15 文件产出     │                      │ ~25 文件产出     │            │
 │           └────────┬───────┘                      └────────┬───────┘            │
 │                    │   3D + 渲染 + 平面图 + PPT + 5 格式导出   │                    │
 │                    │         (DXF / GLB / OBJ / FBX / IFC4)   │                    │
 │                    └───────────────────┬───────────────────┘                    │
 │                                        │                                        │
 └────────────────────────────────────────┼────────────────────────────────────────┘
                                          ▼
 ┌────────────────────── 阶段 3 · 分析（主链 + 支链并行）──────────────────────┐
 │                                                                              │
 │           支链（IFC 路径）                        主链（Energy 路径）          │
 │      ┌──────────────────┐                ┌────────────────────────────┐      │
 │      │  IFC Enrich       │                │  P7 · Energy Sim            │      │
 │      │  补属性 / 材料     │                │  EnergyPlus → EUI           │      │
 │      └────────┬─────────┘                └──────────────┬─────────────┘      │
 │               ▼                                         ▼                    │
 │      ┌──────────────────┐                ┌────────────────────────────┐      │
 │      │  IFC Audit        │                │  P8 · Compliance            │      │
 │      │  质检 🟢 🟡 🔴    │                │  HK / CN / ASHRAE / JP       │      │
 │      └────────┬─────────┘                └──────────────┬─────────────┘      │
 │               │                                         │                    │
 │               ▼                                         │                    │
 │      ┌────────────────────────────────┐                 │                    │
 │      │  P6 · BOQ 报价 (双路径)           │ ◀───────────────┘                    │
 │      │   A: 从 enriched IFC (精确)      │                                      │
 │      │   B: 从 project.json / 模型 (快) │                                      │
 │      │  HK / CN / INTL 三套价            │                                      │
 │      └───────────────┬────────────────┘                                      │
 │                      │                                                        │
 └──────────────────────┼────────────────────────────────────────────────────────┘
                        ▼
 ┌──────────────────────────── 阶段 4 · 横向对比 ────────────────────────────┐
 │                                                                            │
 │      ┌──────────────────────────┐           ┌──────────────────────────┐   │
 │      │  P9 · What-If             │           │  P10 · A/B/C              │   │
 │      │  同方案 · 参数轴           │           │  不同设计方案 · 风格/布局/ │   │
 │      │  (围护/HVAC/照明参数)      │           │  预算轴                    │   │
 │      │  → 参数敏感性 · 升级 ROI   │           │  → 方案选型 · 决策矩阵     │   │
 │      └──────────────────────────┘           └──────────────┬───────────┘   │
 │                                                            │               │
 └────────────────────────────────────────────────────────────┼───────────────┘
                                                              ▼
 ┌─────────────────────────────── 阶段 5 · 出口 ───────────────────────────────┐
 │                                                                              │
 │                       ┌──────────────────────────────┐                        │
 │                       │  P11 · Case Study             │                        │
 │                       │  portfolio / impact / sales   │                        │
 │                       │  三模板 + metrics.json         │                        │
 │                       └──────────────────────────────┘                        │
 │                                                                              │
 └──────────────────────────────────────────────────────────────────────────────┘

脚注：P4 / P5 为预留编号（未来扩展位），当前未分配 pipeline。
```

---

## 你能说什么 → Claude 会做什么

### 🏗 设计类

| 你说 | Claude 做什么 |
|------|-------------|
| "帮我设计一个咖啡店" | 读 studio-copilot-pipeline → 全套室内 MVP |
| "设计一栋两层住宅" | 读 architecture-pipeline → 全套建筑 MVP |
| "再出 8 份 stakeholder PPT" | 调 marp-deck skill → 8 份定制 PPTX |

### 💰 报价类

| 你说 | Claude 做什么 |
|------|-------------|
| "这个方案多少钱" | BOQ Pipeline 6 → Markdown + CSV 报价单 |
| "用内地价格算一下" | BOQ `--region CN` → 人民币报价 |
| "从这个 IFC 出个报价" | BOQ from IFC → 基于实际构件量的精确报价 |

### ⚡ 能耗类

| 你说 | Claude 做什么 |
|------|-------------|
| "跑一下能耗模拟" | Pipeline 7 → EnergyPlus → EUI (kWh/m²·yr) |
| "能不能过香港审批" | Pipeline 8 → HK BEEO 合规检查 → 红绿灯 |
| "用北京标准看看" | Pipeline 8 `--code CN_COLD` → GB 50189 检查 |
| "日本标准呢" | Pipeline 8 `--code JP` → 省エネ法检查 |
| "出全套报告" | Pipeline 7→8→6 依次执行 |

### 🎯 方案对比类

**辨析（硬约束）**：
- **P9 What-If** = 同一设计方案，扫工程参数（围护 U 值 / HVAC 类型·设定点 / 照明·设备功率密度）。**不含 budget 轴**。
- **P10 A/B/C** = 不同设计方案对比（风格轴 / 布局轴 / **budget 轴归 P10**）。内部对每个 variant 调用 P1/P2 + 聚合 P6/P7/P8 结果做决策。
- 关键词模糊时 Claude **必须先反问**："调同一方案的参数（→P9）还是对比不同方案（→P10）？"

| 你说 | Claude 做什么 |
|------|-------------|
| "加保温值不值" | P9 What-If `wall_u=0.4,roof_u=0.3` vs baseline |
| "换 VRF 空调看看" | P9 What-If preset `hvac-upgrade` |
| "LED 灯能省多少" | P9 What-If preset `lighting-equipment` |
| "围护 vs HVAC vs 照明，哪个升级值" | P9 What-If preset 三选 |
| "给我 3 个风格方案（现代/工业/北欧）" | P10 A/B/C · 风格轴 |
| "做三档预算 Economy/Mid/Premium" | P10 A/B/C · 预算轴（**budget 归 P10，不走 P9**） |
| "开放布局 vs 封闭布局" | P10 A/B/C · 布局轴 |
| "给我 3 个方案对比"（模糊） | **先反问**："调同一方案的参数（→P9）还是对比不同方案（→P10）？" |

### 🔧 IFC 工具类

| 你说 | Claude 做什么 |
|------|-------------|
| "补一下 IFC 属性" | `enrich-ifc` → 加 U 值/材料/面积 |
| "检查一下 IFC 质量" | `audit-ifc` → 红绿灯报告 |

### 🔄 调参类

| 你说 | Claude 做什么 |
|------|-------------|
| "把墙 U 值改成 0.4 重跑" | 改参数 → 重跑模拟 → 对比前后 |
| "换成 VRF 空调看看" | 改 HVAC → 重跑 → 对比 |
| "如果加 60mm 保温呢" | 改围护 → 重跑能耗+合规 |

### 📥 客户进件类

| 你说 | Claude 做什么 |
|------|-------------|
| "帮客户把需求整理成 brief" | Brief-Intake Pipeline · 对话式问答补 brief.json |
| "客户只有一句话，你来补" | from-text 模式 · LLM 推断 HK 市场默认值 |
| "这段需求是室内还是建筑" | classify 子命令 · 自动分派 schema |
| "检查这个 brief 能不能跑下游" | validate 子命令 · schema + parser 兼容检查 |

### 📂 作品集 / Case Study 类

| 你说 | Claude 做什么 |
|------|-------------|
| "更新作品集" | 23 MVP 批处理 → portfolio 页 + impact dashboard |
| "出一份 tenure impact case" | Impact 模板 · 对齐 RAE framework |
| "给客户一份 pitch 页" | Sales one-pager · 痛点/方案/结果 |
| "某 MVP 出一份官网展示页" | Portfolio 单页 · Hero + 4 指标卡 + 100 字叙事 |

---

## 每条 Pipeline 的输入和输出

| Pipeline | 输入 | 输出 | 耗时 |
|----------|------|------|------|
| **1. 室内设计** | 中文需求描述 | brief.json + 3D + 渲染 + 平面 + PPT + 5 格式导出 | 5-15 分钟 |
| **2. 建筑设计** | 中文需求描述 | brief.json + 多层平面 + 4 立面 + 剖面 + 体量 + 5 格式导出 | 10-20 分钟 |
| **IFC Enrich** | 原始 .ifc | enriched .ifc（加属性+材料+面积） | 2 秒 |
| **IFC Audit** | .ifc | 红绿灯质检报告 | 1 秒 |
| **6. BOQ 报价** | project.json 或 enriched .ifc | Markdown 报价单 + CSV | 2 秒 |
| **7. 能耗模拟** | brief.json + EPW 气象 | EUI + 能耗分解 | 2-30 秒 |
| **8. 合规检查** | 模拟结果 | 红绿灯合规报告 + 整改建议 | 1 秒 |
| **9. What-If 对比** | project.json + 参数变体 | 多方案并排对比表 | 10-60 秒 |
| **Brief Intake** | 客户一句话 / 多轮对话 | 合法 brief.json + intake-report.json | 1-3 分钟（含 LLM 往返） |
| **A/B/C 对比** | base brief + variant 轴 | N variant MVP + 拼图 + 差异矩阵 + 决策 deck | 15-60 分钟（并行） |
| **Case Study** | MVP folder（单/批量） | portfolio.md / impact.md / sales.md + metrics.json | 30 秒/MVP |

---

## 支持的区域和法规

### 报价区域

| 代号 | 地区 | 币种 | 典型单价 |
|------|------|------|---------|
| `HK` | 香港 | HKD | HK$8,000–15,000/m² |
| `CN` | 中国大陆 | RMB | ¥2,500–5,000/m² |
| `INTL` | 国际 | USD | $800–2,000/m² |

### 合规法规

| 代号 | 法规 | 适用地区 | 严格度 |
|------|------|---------|--------|
| `HK` | BEEO / BEC 2021 | 香港 | ★★☆ |
| `CN_HOT` | GB 50189（夏热冬暖） | 广州/深圳 | ★★★ |
| `CN_COLD` | GB 50189（寒冷区） | 北京/天津 | ★★★★ |
| `ASHRAE` | ASHRAE 90.1-2022 | 国际 | ★★★ |
| `JP` | 省エネ法 2025 | 日本 | ★★★★★ |

### 气象文件

| 文件 | 适用 |
|------|------|
| `HKG_Hong.Kong.Intl.AP.epw` | 香港（默认） |
| `HKG_Hong.Kong.Obs.epw` | 香港市区 |
| `CHN_Beijing.Capital.AP.epw` | 北京 |
| EnergyPlus 自带 5 个美国城市 | 美国项目 |

需要其他城市 → 告诉 Claude "下载上海/东京的气象数据"，会自动从 climate.onebuilding.org 下载。

---

## 已有的 MVP 资产

### 室内 MVP（studio-demo/mvp/）

| 编号 | 场景 | 面积 |
|------|------|------|
| 01 | 书房 | 15m² |
| 02 | 会议室 | 30m² |
| 03 | 咖啡店 | 80m² |
| 04 | 联合办公 | 120m² |
| 05 | 健身工作室 | 100m² |
| 06 | 儿童日托 | 150m² |
| 07 | 书店 | 100m² |
| 08 | 美发沙龙 | 90m² |
| 09 | 画廊 | 100m² |
| 10 | 牙科诊所 | 130m² |
| 11 | 餐厅 | 150m² |
| 12 | 录音棚 | 100m² |
| 13 | AI 办公室 | 130m² |
| 14 | 日式咖啡烘焙店 | — |
| 15 | 花艺工作室 | — |
| 16 | 适老化居家 | — |
| 17 | 五星酒店泳池 | 850m² |

### 建筑 MVP（studio-demo/arch-mvp/）

| 编号 | 场景 | 层数 |
|------|------|------|
| arch-01 | 独栋住宅 | 2 层 |
| arch-02 | 办公楼 | 4 层 |
| arch-03 | 精品酒店 | 3 层 |
| arch-04 | 社区中心 | 大跨度 |
| arch-05 | 中式现代住宅 | 2 层 |
| arch-06 | 小型图书馆 | — |
| arch-07 | Loft 联合办公 | — |
| arch-08 | 小型诊所 | — |
| arch-09 | 混合用途 | — |
| arch-10 | 体育综合体 | — |
| arch-11 | 新界家庭住宅 | — |
| arch-12 | 东北乡村住宅 | — |

---

## 典型工作流示例

### 示例 1：客户问"这个住宅方案多少钱，能不能过审"

```
你：arch-01 跑一下能耗和报价，顺便看看能不能过香港审批

Claude 自动执行：
  1. 从 brief.json 建热模型 (14 zones, 138m²)
  2. 用 HK 气象跑 EnergyPlus → EUI 113 kWh/m²·yr
  3. 对标 HK BEEO → 7/9 pass ⚠️
  4. 跑 BOQ → HK$1,516,548 (HK$10,989/m²)
  5. 汇总给你看
```

### 示例 2：对比不同地区标准

```
你：这个方案分别用香港、北京、日本标准检查一下

Claude 自动执行：
  1. compliance --code HK  → 7/9 ⚠️
  2. compliance --code CN_COLD → 3/7 ❌
  3. compliance --code JP → 3/7 ❌
  4. 列表对比 + 整改建议
```

### 示例 3：只要一份报价

```
你：这个 IFC 出一份内地价格的报价单

Claude 自动执行：
  1. enrich-ifc（补面积数据）
  2. boq-from-ifc --region CN
  3. 输出 Markdown + CSV
```

---

## Tier 1 新 Pipeline（2026-04-16 实装）

| Pipeline | Playbook 文件 | 依赖 Harness | 状态 |
|----------|--------------|--------------|------|
| **Brief Intake**（客户进件漏斗） | [brief-intake-pipeline.md](brief-intake-pipeline.md) | `cli-anything-llm-intake` | Harness ✅ · AEC 资产待补 |
| **A/B/C 方案对比**（视觉决策） | [ab-comparison-pipeline.md](ab-comparison-pipeline.md) | `cli-anything-image-grid` | Harness ✅ · AEC 资产待补 |
| **Case Study 自动生成**（三用素材库） | [case-study-autogen-pipeline.md](case-study-autogen-pipeline.md) | Pillow（缩略图）+ Claude 原生生成（narrative）+ `playbooks/scripts/case-study/*.py` | **实装 ✅ 2026-04-16**（首批 23/23 MVP 跑通；当前共 29 MVP 待重跑） |

### 下一步（AEC 特化资产落地）

1. **Brief Intake 资产**：`playbooks/schemas/brief-{interior,architecture}.schema.json` ✅ + `playbooks/prompts/brief-intake/*.md` ✅ + `playbooks/defaults/hk_market.json` ✅
2. **A/B/C 资产**：`playbooks/scripts/ab-comparison/` ✅ · `playbooks/variants/` 风格/布局/预算预设库 ❌ 未创建
3. **Case Study 资产**：`playbooks/scripts/case-study/*.py` ✅ · `playbooks/templates/{portfolio,impact,sales}.md` ❌ 未创建（当前模板硬编码在脚本中）· `playbooks/prompts/case-study/narrative.md` ❌ 未创建

### 归属分层

| 层 | 放哪 |
|----|------|
| 通用 CLI 能力 | CLI-Anything（`llm-intake` / `image-grid` / `anygen`） |
| Playbook 流程文档 | 本项目 `playbooks/*.md` |
| AEC 特化 schema / prompt / 默认值 | 本项目 `playbooks/{schemas,prompts,defaults}/` |
| Case Study 模板 | 本项目 `playbooks/templates/` |
| Orchestration 胶水脚本 | 本项目 `playbooks/scripts/<name>/` |
| 产物 | 本项目 `studio-demo/` 或 `case-studies/` |
