---
marp: true
theme: studio
paginate: true
size: 16:9
class: designer
header: 'Coffee Lab · 独立精品咖啡店 · v1'
footer: 'Studio Copilot · 2026-04-15 · for 设计师同事'
---

<!-- _class: lead designer -->

# Coffee Lab
## 深化设计交付包 · v1
### 源文件清单 + 材质规格 + 深化要点

---

## 源文件清单

| 文件 | 用途 | 工具 |
|---|---|---|
| `brief.json` | 项目需求锚点 | 任意编辑器 |
| `room.json` | 3D 场景（78 objects · 12 materials） | Blender CLI |
| `floorplan.svg` | 2D 矢量平面 | Inkscape |
| `floorplan.png` | 栅格平面（尺寸标注） | — |
| `moodboard.png` | 配色板 | — |
| `renders/01-08_*.png` | 8 张多角度渲染 | Cycles/Eevee |
| `exports/cafe.glb/obj/fbx/ifc` | 5 种格式 | Blender export |
| `exports/floorplan.dxf` | DXF 施工图 | Inkscape DXF |

---

<!-- _class: split designer -->

![bg right:55%](../moodboard.png)

## 风格关键词 + 配色码
- industrial-wood · japandi-minimal · plant-friendly · warm-but-crafty
- `floor_terrazzo` **#D4CFC2**
- `wood_warm` **#8B6F4E**
- `metal_black` **#2B2B2D**
- `wall_cream` **#EDE8DE**
- `brass_accent` **#B89968**
- `foliage_green` **#3F6B3C**

---

<!-- _class: split designer -->

![bg right:55%](../renders/07_top_ortho.png)

## 俯视彩色渲染
- **78 个 3D 物体** · 12 种材质
- 8 功能分区全部映射
- 可用于客户汇报 / 营销视觉 / 摄影分镜
- 分辨率 1600×1000，150 DPI 出图

---

<!-- _class: split designer -->

![bg right:55%](../floorplan.png)

## 标注式 2D 平面
- 总尺寸 **10.0 × 8.0 m** / 层高 3.5 m
- 临街面 8.0 m（东向）
- 后厨 12 m² 独立带门
- **Inkscape 直接编辑 `.svg`** → `rsvg-convert -d 150` 重出 PNG

---

<!-- _class: split designer -->

![bg right:55%](../renders/01_hero_corner.png)

## 多角度 3D 清单
| # | 视角 | 用途 |
|---|---|---|
| 01 | hero corner | 封面 / 营销 |
| 02 | reception (吧台) | 点单动线 |
| 03 | main zone (散座) | 座位区 |
| 04 | feature (长桌+书架) | 特色视觉 |
| 05 | lounge zone | 休闲氛围 |
| 06 | back corner (后厨/卫生) | 服务动线 |
| 07 | top ortho | 俯视彩色 |
| 08 | birds eye 3d | 鸟瞰 |

---

## Material PBR 参数

```
FloorTerrazzo : base #D4CFC2, roughness 0.60, metallic 0.00
WoodWarm      : base #8B6F4E, roughness 0.50, metallic 0.02
MetalBlack    : base #2B2B2D, roughness 0.35, metallic 0.85
WallCream     : base #EDE8DE, roughness 0.90, metallic 0.00
BrassAccent   : base #B89968, roughness 0.28, metallic 0.90
FoliageGreen  : base #3F6B3C, roughness 0.70, metallic 0.00
GlassClear    : base #DCE3DA, roughness 0.05, transmission 0.92
LeatherTan    : base #A67B5B, roughness 0.55, metallic 0.00
BlackFabric   : base #1F1F22, roughness 0.85, metallic 0.00
CeramicWhite  : base #F2EFE8, roughness 0.40, metallic 0.00
StainlessSteel: base #C8C8CB, roughness 0.30, metallic 0.90
PaperBook     : base #E8DFCB, roughness 0.95, metallic 0.00
```

---

## 关键尺寸

| 元素 | 尺寸 (mm) | 数量 |
|---|---|---|
| L 型吧台 | 3000 × 800 + 2200 × 800, H=1050 | 1 |
| 圆木桌 | Ø900, H=720 | 4 |
| 木椅 | 450 × 480, H=820 | 8 |
| 长木桌 | 4000 × 900, H=750 | 1 |
| 长凳 | 2000 × 350, H=450 | 4 |
| 高脚凳 | Ø380, H=650 | 4 |
| 书架（5 层）| 4000 × 350, H=2400 | 1 |
| 后厨操作台 | 3000 × 700, H=900 | 1 |
| 黄铜吊灯 | Ø250 | 6 |

---

## 照明规划

| 区域 | 类型 | 色温 | 功率 | 数量 |
|---|---|---|---|---|
| 主照明 | 黄铜吊灯（Menu TR Bulb 类）| 2700 K | 8 W × 6 | 6 |
| 吧台后墙 | 嵌入式线性灯 | 3000 K | 18 W/m × 3m | 1 套 |
| 书架内置 | 灯带 | 2700 K | 12 W/m × 4m | 1 套 |
| 后厨 | 平板灯 | 4000 K | 24 W | 3 |
| 卫生间 | 筒灯 | 3000 K | 7 W | 2 |
| 重点展品 | 射灯（后吧/书架）| 3000 K | 5 W | 4 |

---

## 如何修改 · 工作流

```bash
# 1) 改 3D 物体（加/减家具、调位置）
vim room.json
blender -b -P _render_script.py
python _render_multi.py              # 重出 8 张图

# 2) 改平面（墙体/分区）
inkscape floorplan.svg               # GUI 编辑
rsvg-convert -d 150 floorplan.svg -o floorplan.png

# 3) 重出 PPT
vim decks/deck-designer.md
bash <skill>/scripts/build_pptx.sh . # → decks/*.pptx

# 4) 重导 BIM/其他格式
blender -b -P exports/_export_glb_script.py
```

---

<!-- _class: split-1to2 designer -->

![w:100%](../renders/02_reception.png)

## 吧台深化要点
- **L 型 3+2.2 m**，操作台面水磨石 40 mm 厚
- 后吧架 3 层 H=2400，黑铁框 + 胡桃木层板
- 咖啡机位（La Marzocco Linea Mini）预留 220V / 16A 专线
- 净水 + 软水预处理 · 下水 DN50 地漏
- 展示冷柜位：W1200 × D700，独立电源 10A

---

<!-- _class: split-1to2 designer -->

![w:100%](../renders/04_feature_zone.png)

## 书架墙 + 长桌深化
- 书架 **4 m × 5 层 × 350 mm 深**，钢架 + 木板
- 内置灯带 **2700 K 12W/m**，背板防眩乳白色板
- 长桌固定 4 m 不可拆，需提前确定进场路径
- 长凳四条 × 2 m，座面实木，下方藏排插 × 4

---

## 不要写 / 此处省略

- BOQ 报价明细（见 contractor deck）
- ROI / 回收期（见 investor deck）
- 客户决策点（见 client deck）

---

<!-- _class: lead designer -->

# 下一步

> 你来深化哪个区？

- 吧台节点 / 排烟隔油（后厨）/ 书架结构 / 临街立面
- 告诉我 → 源文件打包 + 材质库一并给

联系：Studio Copilot Design Team
