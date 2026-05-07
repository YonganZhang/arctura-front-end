---
marp: true
theme: studio
paginate: true
size: 16:9
class: bim
header: '极简书房改造 · BIM 协同包 · v1'
footer: 'Studio Copilot · 2026-04-15 · for BIM 工程师'
---

<!-- _class: lead bim -->

# 极简书房 · BIM 协同包
## IFC4 + Fallback 多格式
### 给 BIM 工程师 的协同说明

<br>

| Schema | Project | IfcProduct |
|---|---|---|
| IFC4 | Study20sqm · v1 | 21+ |

---

## IFC4 Schema 概览

```
Schema     : IFC4 (ISO 16739:2017)
Project    : 极简书房改造 v1 (Study20sqm)
Site       : 住宅套内，单室
Building   : 1-storey 住宅套房
Storey     : F1 · elevation 0.0 m · height 2.8 m
Units      : SI (METRE, DEGREE)
Coordinate : Local, +X 朝东, +Y 朝北
Source     : room.json → blender-cli → IFC4 export
```

数据源 `room.json` 是权威 single-source-of-truth，任何修改优先在 JSON 调整后重出 IFC。

---

<!-- _class: split bim -->

![w:100%](../renders/08_birds_eye_3d.png)

## IfcProduct 拆分统计 (v1)
```
IfcSlab           × 1   (Floor)
IfcWall           × 2   (BackWall, LeftWall)
IfcFurniture      × 17  (书墙 + 工作桌椅 + 沙发 + 储物 + 电子)
IfcLightFixture   × 2   (LampPole + LampShade)
IfcSpace          × 4   (书墙区 / 工作区 / 阅读角 / 储物角)
```
**Total IfcProduct**: 26（含 Space，排除外壳为 22）
**注**：v1 场景墙体只建 2 面（背 + 左），另 2 面假设为现状保留，进入施工图阶段补齐。

---

<!-- _class: split bim -->

![w:100%](../renders/07_top_ortho.png)

## 导入校验计划
| 工具 | 版本 | 状态 | 备注 |
|---|---|---|---|
| Revit | 2024 | 待验证 | 家具族用 IfcFurnishingElement |
| ArchiCAD | 27 | 待验证 | Library part 自动匹配 |
| BlenderBIM | 0.7+ | ✓ 源头生成 | 导出工具链 |
| Solibri | v9.13 | 待验证 | 规则检查 |
| FreeCAD | 0.21 | 待验证 | 开源校验 |

**建议**：开工前跑一遍 Solibri BCF → 问题回传到 room.json 修复

---

<!-- _class: split bim -->

![w:100%](../renders/04_feature_zone.png)

## MEP 协同点
1. **天花主光**：2 盏 600×600 面板嵌入天花（梁下净高 ≥2.7 m 方可）
2. **书墙洗墙**：顶部走轨道灯供电线，需天花预留 1 路 220V
3. **工作桌**：桌下预留 220V×2 + USB-C PD + Cat6 ×1
4. **阅读角**：沙发背墙脚预留 220V ×1
5. **弱电**：建议主干 Cat6 ×2 进书房（WiFi + 备用）
6. **无给排水**：书房不涉及水系统
7. **无 HVAC 独立**：共享全屋中央空调，仅需 1 个风口

---

<!-- _class: split bim -->

![w:100%](../renders/03_main_zone.png)

## 结构关注
- **书墙荷载**：满书按每层 50 kg × 4 层 = 200 kg 线荷载（5 m 跨度）
  → 分散约 40 kg/m · 轻载，木地板下无需加固
- **顶部抗倾倒**：书墙高度 2.4 m，L 角铁锁天花龙骨（2 点以上）
- **地板**：橡木多层 12+3 mm 浮铺，无结构影响
- **无幕墙 / 隔断**：全套内轻型装修

---

## Fallback 格式清单

| 格式 | 用途 | 生成工具 | 状态 |
|---|---|---|---|
| IFC4 (.ifc) | BIM 协同（权威） | blender-cli BIM export | v1 待生成 |
| GLB (.glb) | Web 预览 / Three.js | blender-cli glTF export | v1 待生成 |
| OBJ (.obj) | SketchUp / Rhino / Keyshot | blender-cli | v1 待生成 |
| FBX (.fbx) | Maya / 3ds Max / Unity | blender-cli | v1 待生成 |
| DXF (.dxf) | AutoCAD / Rhino / QCAD | inkscape-cli floorplan | v1 待生成 |
| SVG (.svg) | Illustrator / Inkscape | 已有 floorplan.svg | ✓ |

**一键生成**：`blender --python _render_script.py -- --export all`

---

## 验证脚本

```bash
# 快速验证 IFC 完整性
python << 'EOF'
import ifcopenshell
m = ifcopenshell.open('exports/01-study-room.ifc')
print(f"Products: {len(m.by_type('IfcProduct'))}")
print(f"Walls:    {len(m.by_type('IfcWall'))}")
print(f"Furniture:{len(m.by_type('IfcFurniture'))}")
print(f"Spaces:   {len(m.by_type('IfcSpace'))}")
for s in m.by_type('IfcSpace'):
    print(f"  · {s.Name} · {s.LongName}")
EOF
```

---

<!-- _class: lead bim -->

# 下一步协同

> LOD 升级路径

- **LOD200 → LOD300**：家具从包围盒 → 真实几何（加抽屉、板厚）
- **LOD300 → LOD350**：节点大样（书架 L 角 / 桌腿焊接 / 门轴）
- **碰撞检测建议**：天花灯具 vs 结构梁 · 书墙 vs 电箱 · 桌面 vs 窗台
- **标注与量表**：IfcPropertySet 补材料 / 供应商 / 单价

**对接人**：Studio Copilot BIM 组 · 修改 room.json 后 24h 重出 IFC
