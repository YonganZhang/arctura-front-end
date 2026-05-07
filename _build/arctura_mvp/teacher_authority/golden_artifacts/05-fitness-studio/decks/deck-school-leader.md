---
marp: true
theme: studio
paginate: true
size: 16:9
class: school
header: 'Lift Studio · 精品健身工作室 · v1'
footer: 'Studio Copilot · 2026-04-15 · for 学校领导'
---

<!-- _class: lead school -->

# AI 驱动室内 / 建筑设计研究
## 精品健身工作室 MVP 演示
### 给 学校领导 / 研究生导师

---

<!-- _class: split school -->

![w:100%](../renders/01_hero_corner.png)

## 研究背景
- 传统室内设计周期 **2-4 周**
- 建筑方案从 concept → 施工图涉及 5+ 专业
- 问题：**AI 能否压缩到分钟级且保证工程质量？**
- 健身空间是优质测试场景：功能明确 + 专业要求高（承重/声学/通风）

---

<!-- _class: split school -->

![w:100%](../renders/08_birds_eye_3d.png)

## 核心命题
- **CLI Agent + 多模态生成 pipeline**
- 端到端：需求 JSON → 3D 场景 → 2D 图 → BIM → 多 stakeholder PPT
- 覆盖 8 个专业视角（业主/投资/施工/BIM/运营/营销/学术/设计）
- 健身场景验证：承重 800 kg/m² + 声学 35 dB + 全反射镜面

---

## 关键指标

<div class="kpi-grid">
<div><div class="big-number">9'29"</div>端到端生成</div>
<div><div class="big-number">95+</div>3D 物体</div>
<div><div class="big-number">5</div>工业标准格式</div>
<div><div class="big-number">8</div>stakeholder 差异化 PPT</div>
</div>

---

<!-- _class: split school -->

![w:100%](../renders/07_top_ortho.png)

## 方法论
1. **参数化场景** `room.json` → 可解释、可编辑
2. **Blender headless** 自动渲染 8 角度
3. **Inkscape CLI** 生成施工 DXF
4. **BlenderBIM** 导出 IFC4 (ISO 16739)
5. **Marp** 生成 stakeholder-aware PPT
6. **全程 CLI 化** → LLM 可完整调度

---

<!-- _class: split school -->

![w:100%](../renders/04_feature_zone.png)

## 可重复实验
- **13 业态 MVP**：办公 / 咖啡 / 书店 / 牙科 / 美发 / **健身** / 录音棚 / 托育 ...
- 同一 pipeline 跑不同业态
- 平均生成时间 9-12 分钟
- 失败率 < 5%（主要因渲染器内存）

---

## 可发表方向

| 会议 / 期刊 | 方向 |
|---|---|
| **CHI / UIST** | Multi-Stakeholder AI Presentation Generation |
| **CAAD Futures / eCAADe** | AI-driven Architecture Design Pipeline |
| **Automation in Construction** | BIM-LLM Interoperability (IFC4) |
| **Building and Environment** | AI 空间性能仿真（声学/承重/气流） |
| **CHI'27 LBW** | Studio Copilot 用户研究 |

---

## 教学价值

| 方向 | 场景 |
|---|---|
| 《计算性设计》 | 研究生必修素材 |
| 跨学科 Capstone | 建筑 + CS + 商业 |
| 《数字孪生》 | BIM 模型现成库 |
| 创业孵化器 | StartUP-Building 孵化项目 |
| 顶会投稿 | 研究生一作论文 |

---

## 本年度计划

| 季度 | 目标 |
|---|---|
| **Q2** | 13 业态 MVP 全部打通，含健身 / 牙科 / 托育 |
| **Q3** | 投 CHI / CAAD Futures · 撰写 JCR Q1 期刊 |
| **Q4** | 申请发明专利 2 件 · 与 1-2 家企业签订合作 |
| **2027 Q1** | 联合实验室 + 博士课题方向建立 |

---

<!-- _class: lead school -->

# 争取支持

- **算力**：2 块 A100 或等效（Blender GPU 渲染）
- **孵化空间**：1 间小型实验空间做真实落地（可用健身 MVP）
- **跨院系合作**：建筑学院 + 计算机学院 + 商学院
- **研究生名额**：2-3 名一作论文 + 2 名专利发明人
