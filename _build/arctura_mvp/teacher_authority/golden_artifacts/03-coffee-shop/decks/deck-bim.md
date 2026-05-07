---
marp: true
theme: studio
paginate: true
size: 16:9
class: bim
header: 'Coffee Lab · 独立精品咖啡店 · v1'
footer: 'Studio Copilot · 2026-04-15 · for BIM Manager'
---

<!-- _class: lead bim -->

# Coffee Lab
## BIM 协同包 · IFC4 ISO
### Revit / ArchiCAD / BlenderBIM / Solibri ready

---

## IFC4 Schema 概览

```
Schema    : IFC4 (ISO 16739:2017)
Project   : Coffee Lab · Boutique Cafe · v1
Site      : 临街商铺，1 层独立
Building  : 1-storey, frontage 8.0 m (East)
Storey    : F1, elevation 0.0 m, height 3.5 m
Units     : SI (METRE, KILOGRAM, SECOND, DEGREE)
FileSize  : 56 KB (exports/cafe.ifc)
Coord Sys : local, origin = SW corner
```

---

<!-- _class: split bim -->

![bg right:55%](../renders/08_birds_eye_3d.png)

## IfcProduct 拆分统计
- **Total IfcProduct** ≈ 78（来自 room.json 78 objects）
- **IfcWall** × 6（外墙 3 + 后厨隔墙 1 + 卫生间隔墙 2）
- **IfcSlab** × 2（地面 + 天花）
- **IfcDoor** × 3（前门 + 后厨门 + 卫生间门）
- **IfcWindow** × 1（临街落地面）
- **IfcFurniture** × 50+（桌/椅/吧台/书架/设备）
- **IfcSpace** × 8（8 功能分区映射）

---

<!-- _class: split-1to2 bim -->

![w:100%](../renders/07_top_ortho.png)

## 导入校验
| 工具 | 版本 | 状态 |
|---|---|---|
| Revit | 2024 | 待测（建议 IFC4 import + link）|
| ArchiCAD | 27 | 待测（IFC4 Reference Model）|
| BlenderBIM | 0.8+ | ✓ export 源 |
| Solibri | Anywhere | 建议跑 clash check |

---

<!-- _class: split bim -->

![bg right:55%](../renders/02_reception.png)

## MEP 协同关键点
1. **后厨排烟**：UMC-I 净化器 + DN200 风管 → 屋顶（垂直对齐建筑结构）
2. **吧台咖啡机**：220V 专线 + 净水/软水预处理 + 地漏 DN50
3. **空调**：前厅开放区 VRV 主路 + 后厨独立支路（油烟环境）
4. **给排水**：后厨 + 卫生间 + 吧台 三路独立地漏
5. **燃气**：如用（轻食加热）需独立管线 + 探测器

---

<!-- _class: split bim -->

![bg right:55%](../renders/04_feature_zone.png)

## 结构关注点
- **书架墙** 4m × 5 层，总荷载 ~180 kg + 存储容量
  - M10 膨胀螺栓 × 12 点锚入承重墙
  - 若为轻钢龙骨墙需增加加强背板
- **长桌 4m 固定** + 三钢架，点荷载 ~80 kg × 3
- **吧台水磨石面** 40mm，自重约 110 kg/m²
- 后厨排烟管穿楼板（如涉及）需防火封堵 A 级

---

## Fallback 格式

| 格式 | 体积 | 用途 |
|---|---|---|
| `exports/cafe.ifc` | 56 KB | BIM 协同（首选）|
| `exports/cafe.glb` | — | Web 看板 / 小程序 3D 预览 |
| `exports/cafe.obj` + `.mtl` | — | SketchUp / Rhino 导入 |
| `exports/cafe.fbx` | — | Maya / Unity / Unreal / 动画 |
| `exports/floorplan.dxf` | 61 KB | AutoCAD / Rhino / QCAD 2D |

---

## F&B 专属 BIM 关注项

1. **油烟管道空间占用**：需在天花层预留净高 ≥ 300 mm
2. **隔油池**：室外或后厨独立位，地坪下埋深 ≥ 600 mm
3. **给排水立管**：后厨需至少 1 条 DN100 污水立管
4. **卫生间通风**：机械排风 ≥ 10 次/h
5. **消防喷淋**（如楼宇要求）：K80 喷头按 12 m² 覆盖布置

---

## 验证脚本

```bash
# 用 ifcopenshell 快速校验
python -c "
import ifcopenshell
m = ifcopenshell.open('exports/cafe.ifc')
print('IfcProduct   :', len(m.by_type('IfcProduct')))
print('IfcWall      :', len(m.by_type('IfcWall')))
print('IfcSlab      :', len(m.by_type('IfcSlab')))
print('IfcFurniture :', len(m.by_type('IfcFurnishingElement')))
print('IfcSpace     :', len(m.by_type('IfcSpace')))
print('Schema       :', m.schema)
"
```

---

<!-- _class: lead bim -->

# 下一步协同

- **Clash check**：书架 vs 顶面线灯 / 排烟 vs 吊顶
- **LOD350 深化**：吧台节点 / 排烟 / 隔油池
- **Family 库**：La Marzocco 咖啡机 · 冷柜 · 操作台需第三方提供 RFA

联系：Studio Copilot BIM Team
