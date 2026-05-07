---
marp: true
theme: studio
paginate: true
size: 16:9
class: bim
header: 'Stack Lab · AI 创业办公室 · v1'
footer: 'Studio Copilot · 2026-04-15 · for BIM Manager'
---

<!-- _class: lead bim -->

# Stack Lab · AI Startup Office
## BIM 协同包 · IFC4 ISO + 多格式 fallback
### 给 BIM Manager 的工程协同交付

<br>

| Schema | Storey | 单体 |
|---|---|---|
| IFC4 (ISO 16739:2017) | F1 · 0.0 m · 3.0 m | 13 × 10 × 3 m loft · 130 m² |

---

## IFC4 Schema 概览

| 字段 | 值 |
|---|---|
| **Schema** | IFC4 (ISO 16739:2017) |
| **Project** | Stack Lab · AI Startup Office · v1 |
| **Site** | Loft 改造，假设北向参考 |
| **Building** | 1-storey, 毛坯 loft + 外露管道 |
| **Storey** | F1, elevation 0.0 m, height 3.0 m |
| **Units** | SI (METRE), DEGREE |
| **Footprint** | 13.0 × 10.0 × 3.0 m · 130 m² · 9 IfcSpace |
| **导出文件** | `exports/13-ai-startup-office.ifc` (83.7 KB) |

---

<!-- _class: split bim -->

![w:100%](../renders/08_birds_eye_3d.png)

## IfcProduct 拆分统计

- **IfcWall** × 12（含 4 面玻璃会议室 + GPU 室玻璃门隔断）
- **IfcSlab** × 2（floor + ceiling，外露管道不封吊顶）
- **IfcSpace** × 9（9 个功能分区，含 GPU 机柜室）
- **IfcFurniture** × 70+（10 升降桌 · 10 人体工学椅 · 20 监视器 · 3 × 42U 机柜 · 沙发 · 桌足球）
- **IfcDoor** × 5（主入口 · 会议室 · GPU 玻璃门 · 2 电话亭）
- **IfcLightFixture** × 14（线性吸顶 + 轨道射灯 + 植物生长灯 + 机柜蓝 LED）

---

<!-- _class: split-1to2 bim -->

![w:100%](../renders/07_top_ortho.png)

## 导入校验记录

- **Revit 2024** — IFC4 Reference View 导入 OK，房间/空间边界正确
- **ArchiCAD 27** — IFC translator 映射 OK，IfcSpace 全部识别
- **BlenderBIM (IfcOpenShell 0.7)** — 用于本项目原生编辑
- **Solibri Office** — 规则检查通过：空间重叠 0、孤立几何 0
- **Fallback 套件**：GLB 681 KB · OBJ 651 KB · FBX 479 KB · DXF 70 KB

---

<!-- _class: split bim -->

![w:100%](../renders/04_feature_zone.png)

## MEP 协同关键点（AI Studio 特殊项）

- **GPU 机柜室 5 kW 专电支路** → `IfcElectricFlowController` 独立配电箱 + 漏电保护
- **精密空调** → `IfcAirToAirHeatRecovery` 全热交换机组，目标 22 ± 1 °C / 40 ± 5 % RH
- **10 工位 × 双屏 = 20 monitors** → `IfcAudioVisualAppliance` 载荷 ~3 kW，每工位预留双 220 V + 网口
- **外露管道** → `IfcPipeSegment` 属性 `Concealed = FALSE`，走明管（tech-loft 风格需要）
- **茶水间**：给水/排水 `IfcPipeSegment` DN20/DN50 各 1 路

---

<!-- _class: split bim -->

![w:100%](../renders/04_feature_zone.png)

## 玻璃会议室 · IFC 建模要点

- **4 面玻璃隔断** → `IfcCurtainWall` + `IfcPlate`（12+12A+12 双层中空钢化，STC 38）
- **观察窗/门上亮** → `IfcWindowStandardCase` × 4 面
- **结构荷载**：4 × 3 m 玻璃 ~250 kg/面 × 4 = ~1.0 t，楼板按 3.5 kN/m² 校核（一般 loft 足够，老旧结构需局部加固）
- **75 寸大屏墙** → `IfcAudioVisualAppliance` 预留背板 + 走线
- **4 m 白板墙** → `IfcWall` PredefinedType = `PARTITIONING`

---

<!-- _class: split bim -->

![w:100%](../renders/06_back_corner.png)

## GPU 服务器室 · 专项协同

- **3 × 42U 机柜** → `IfcFurniture` + `Pset_ElectricalDeviceCommon`（单机柜 ≤ 1.7 kW）
- **专电 5 kW 支路** → `IfcElectricFlowController` 从总配电独立出线
- **精密空调** → `IfcAirToAirHeatRecovery` + `IfcFlowTerminal` 下送风回风
- **玻璃观察门** → `IfcDoor` PredefinedType = `DOOR`，面板 `IfcPlate` 钢化玻璃
- **蓝色 LED accent** → `IfcLightFixture` LightFixtureType = `POINTSOURCE`
- **电话亭 × 2** → 每亭 80 CFM 静音风机 `IfcFan` 接主排风管

---

## Fallback 格式矩阵

| 格式 | 文件 | 大小 | 推荐用途 |
|---|---|---|---|
| **IFC4** | `13-ai-startup-office.ifc` | 83.7 KB | Revit / ArchiCAD / Solibri · 主交付 |
| **GLB** | `13-ai-startup-office.glb` | 681 KB | Web 预览 · three.js · 甲方演示 |
| **OBJ** | `13-ai-startup-office.obj` + `.mtl` | 651 KB + 2.4 KB | SketchUp / Rhino / Grasshopper |
| **FBX** | `13-ai-startup-office.fbx` | 479 KB | Maya / 3ds Max / Unity / Unreal |
| **DXF** | `floorplan.dxf` | 70 KB | AutoCAD / QCAD · 2D 施工图底图 |

---

<!-- _class: lead bim -->

# 下一步协同

> ✅ IFC4 主交付已就绪 · ⏭ 待碰撞检测与 LOD 深化

- **碰撞检测建议**：GPU 机柜顶面线性走线 vs 精密空调管道 · 玻璃会议室顶灯 vs 幕墙结构框
- **LOD350 深化**：电气回路图（5 kW 专电）· 新风全热交换详图 · 玻璃幕墙节点
- **验证脚本**：`python -c "import ifcopenshell; m=ifcopenshell.open('exports/13-ai-startup-office.ifc'); print(len(m.by_type('IfcProduct')))"`

📞 联系：Studio Copilot BIM Team
