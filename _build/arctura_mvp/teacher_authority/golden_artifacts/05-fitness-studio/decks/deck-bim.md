---
marp: true
theme: studio
paginate: true
size: 16:9
class: bim
header: 'Lift Studio · 精品健身工作室 · v1'
footer: 'Studio Copilot · 2026-04-15 · for BIM 工程师'
---

<!-- _class: lead bim -->

# Lift Studio · BIM 协同包
## IFC4 ISO + 多格式 fallback
### 给 BIM 工程师 / 机电协同

---

## IFC4 Schema 概览

```
Schema     : IFC4 (ISO 16739:2017)
Project    : Lift Studio · Boutique Fitness v1
Site       : 底商单层，假设北向参考
Building   : 1-storey
Storey     : F1, elevation 0.0 m, height 3.5 m
Units      : SI (METRE, KILOGRAM, DEGREE)
Area       : 100 m² (10 × 10)
Export     : exports/05-fitness-studio.ifc
```

---

<!-- _class: split bim -->

![w:100%](../renders/08_birds_eye_3d.png)

## IfcProduct 拆分统计
- **IfcWall** × 6（外墙 + 半高声隔墙 + 淋浴隔墙）
- **IfcSlab** × 2（楼板 + 天花）
- **IfcSpace** × 8（功能分区映射）
- **IfcFurniture** × 60+（器械 + 瑜伽垫 + 储物柜）
- **IfcDoor** × 3（入口 + 淋浴 × 2）
- **IfcLightFixture** × 13（轨道射灯 + 线灯 + 吊灯）
- **IfcMirror/IfcWindow** × 5（镜面墙分块）

---

<!-- _class: split bim -->

![w:100%](../renders/07_top_ortho.png)

## 导入校验记录
- **Revit 2024** — 通过（link IFC）
- **ArchiCAD 27** — 通过（IFC open）
- **BlenderBIM 0.7** — 通过（原生）
- **Solibri Office** — 通过（无 critical issue）
- **Navisworks 2024** — 通过（fbx 转 nwc）

---

<!-- _class: split bim -->

![w:100%](../renders/03_main_zone.png)

## 结构关注：力量区楼板加固
- **峰值荷载**：深蹲架 + 人 + 杠铃 ≈ **350 kg 点载**
- **动荷载**：硬拉甩放瞬间冲击 × **2.5 安全系数**
- **要求楼板承重**：≥ **800 kg/m²**（力量区 24 m²）
- **原楼板**：需现场复测，< 500 kg/m² 则底部加钢梁
- **BIM 标注**：`Pset_LoadBearing: reinforced=true, design_load=800kg/m²`

---

<!-- _class: split bim -->

![w:100%](../renders/04_feature_zone.png)

## MEP 协同关键点
1. **瑜伽区独立 VRV 支路**（温控 24°C，与力量区分离）
2. **力量区强排风** 500 CFM（除汗味 + 降 CO₂）
3. **新风** 300 m³/h（≥ 30 m³/h/人，峰值 10 人）
4. **淋浴区给排水**：热水 DN20 × 2、排水 DN75 × 2
5. **镜面墙顶部线灯**与结构梁避让 ≥ 50 mm
6. **每器械位预留** 220V × 1（音响/拉伸枪）

---

## Fallback 格式

| 格式 | 用途 | 目标软件 |
|---|---|---|
| `.ifc` | BIM 原生 | Revit / ArchiCAD / BlenderBIM / Solibri |
| `.glb` | Web 预览 | Three.js / Babylon.js / Gltf-Viewer |
| `.obj` | 经典 3D | SketchUp / Rhino / 3ds Max |
| `.fbx` | 动画渲染 | Maya / Unity / Unreal |
| `.dxf` | 2D 平面 | AutoCAD / Rhino / QCAD |

---

## 验证脚本

```bash
# IFC 完整性校验
python -c "
import ifcopenshell
m = ifcopenshell.open('exports/05-fitness-studio.ifc')
print('IfcProduct:', len(m.by_type('IfcProduct')))
print('IfcWall   :', len(m.by_type('IfcWall')))
print('IfcSpace  :', len(m.by_type('IfcSpace')))
print('Schema    :', m.schema)
"
```

---

## 建议碰撞检测

| 检测对 | 优先级 | 工具 |
|---|---|---|
| 镜面墙 vs 顶部线灯（50 mm 净距） | 高 | Solibri |
| 哑铃架 vs 天花高度（3.4 m 净高） | 高 | Navisworks |
| 瑜伽区吊顶 vs 新风管 | 中 | BlenderBIM |
| 淋浴给排水 vs 电路 | 高 | Revit |
| 镜面结构胶挂装 vs 墙体预埋 | 中 | Revit |

---

<!-- _class: lead bim -->

# 下一步协同

- **LOD 350 深化**：器械精确模型 + 固定锚点
- **力量区楼板加固 BIM**：钢梁/加厚层族
- **MEP 详图**：新风/强排/空调独立子模型
- **Solibri 规则集**：健身空间专用（承重/净高/新风）

📦 交付：`exports/05-fitness-studio.ifc` + 本 PPTX
