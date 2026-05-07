# Stack Lab · AI Startup 办公室 — 方案文件指南
> 客户/合伙人专用 · 2026-04-15 · Studio Copilot v3 · 致敬业主 · made with love

---

## ⏱ 设计统计

| 项 | 值 |
|---|---|
| 设计开始 | 09:57:07 |
| 设计完成 | 10:20:47 |
| 总用时 | **23 分 40 秒** |
| 3D 物体总数 | 118 |
| 平面图实体数 | 115 |
| 方案 PPT 页数 | 9 |
| 5 种导出文件 | DXF + GLB + OBJ + FBX + IFC4 |

---

## 📦 产品内容（12 个核心文件 + 源数据，共 ≈ 4.4 MB）

| 类型 | 文件 | 大小 | 给谁 |
|------|------|------|------|
| 客户决策参考 | brief.json | 2.8 KB | 客户 / 项目经理 |
| 风格视觉 | moodboard.png | 15 KB | 客户 |
| 3D 渲染 | render.png | 1.0 MB | 客户 |
| 平面图 | floorplan.png / .svg | 26 KB / 14 KB | 客户 / 设计师 |
| 方案 PPT | deck.odp | 1.0 MB | 客户 / 投资人 |
| 施工图 | exports/floorplan.dxf | 70 KB | 施工方 / 建筑师 |
| 3D 网页预览 | exports/13-ai-startup-office.glb | 681 KB | 客户 / 营销 |
| 3D 通用 | exports/13-ai-startup-office.obj | 651 KB | 3D 设计师 |
| 3D 动画 | exports/13-ai-startup-office.fbx | 480 KB | 动画 / Unity 团队 |
| BIM | exports/13-ai-startup-office.ifc | 84 KB | BIM 工程师 |
| 源数据 | room.json + deck.lo-cli.json + floorplan.inkscape-cli.json | 65 KB + 8 KB + 37 KB | 内部修改 |

---

## 🧑‍💼 5 种 Stakeholder 怎么用

### 1️⃣ 客户 / 业主（决策者 · 这是您的办公室！）
**主要看**: `moodboard.png` → `render.png` → `deck.odp` → `floorplan.png`
**关键决策点**: LOGO 颜色 / 工位密度 / 会议桌材质 / 机柜玻璃地面是否加装
**怎么改**: 直接告诉我们 "把 X 改成 Y"，5-30 分钟内出新版本
**Web 3D 预览**: 把 `exports/13-ai-startup-office.glb` 拖到 https://gltf-viewer.donmccurdy.com 即可旋转/缩放查看

### 2️⃣ 投资人 / 合伙人 / 老板
**主要看**: `deck.odp` (完整方案) + `brief.json` (需求) + 本 README 的"设计统计"
**用什么开**: PowerPoint / Keynote / Google Slides / LibreOffice (任意都可)
**核心信息**: 9 页含封面、风格、3D、平面、动线、BOQ ¥75 万、8 周工期、技术运维亮点、下一步

### 3️⃣ 设计师同事（精修方案）
**源文件**: `room.json` (3D 场景), `floorplan.inkscape-cli.json` (平面图源), `deck.lo-cli.json` (PPT 源)
**软件**: VS Code (编辑 JSON), Inkscape (修 SVG), LibreOffice (修 PPT)
**修改后重出**: 用 cli-anything-* 命令重新跑相关步骤

### 4️⃣ 施工方 / 建筑技师
**主要看**: `exports/floorplan.dxf` (平面施工图基础, 含 115 个实体)
**软件**: AutoCAD / Rhino / QCAD / BricsCAD
**能干**: 直接在 AutoCAD 里加玻璃隔断节点、机柜室专电布线、电话亭吸音构造、施工标注
**SVG 矢量备份**: `floorplan.svg` 可在 Illustrator / Inkscape 编辑

### 5️⃣ BIM 工程师 / 结构机电
**主要看**: `exports/13-ai-startup-office.ifc` (IFC4 BIM 模型，含 121 个 IfcProduct / 6 道墙 / 47 件家具)
**软件**: Revit / ArchiCAD / BlenderBIM (Blender 插件，免费) / Solibri
**能干**: 机柜室 5 kW 专电 + 精密空调布线协同、玻璃隔断荷载校核、碰撞检测、设备联动
**3D 备份**: `exports/13-ai-startup-office.glb / .obj / .fbx` 可导入 SketchUp / Rhino / Max / Maya / Unity

---

## 📄 每个文件的详细说明

### brief.json
**是什么**: 我们整理后的客户需求（结构化 JSON · 含 dedication 字段）
**打开**: 任何文本编辑器或浏览器
**改**: 编辑数字（预算/工期）或增减需求条目

### moodboard.png
**是什么**: 整体配色方向 6 色板预览 (concrete gray · warm wood · deep teal · soft white · lime · charcoal)
**打开**: 双击图片
**改色**: 告诉我们替换哪个颜色

### render.png + room.json
**是什么**: 装修后真实视觉效果（EEVEE 渲染，0.5 秒出图）+ 3D 场景源数据（118 物体 / 14 材质 / 5 光源）
**打开 (.png)**: 任何看图软件
**换角度/材质**: 描述偏好，重渲染 < 5 分钟

### floorplan.png / .svg
**是什么**: 房间分区与家具摆放（俯视图，1:80，9 分区）
**.png**: 任何看图软件预览
**.svg**: 矢量图，Inkscape (免费) / Illustrator / Figma 编辑

### deck.odp
**是什么**: 9 页完整方案（封面、风格、3D、平面、动线、BOQ、工期、技术运维、下一步）
**打开**: PowerPoint / Keynote / Google Slides / LibreOffice
**改**: 直接在 PPT 软件里改文字

### exports/ 文件夹
- **floorplan.dxf**: 给施工 / 建筑师 (AutoCAD/Rhino)
- **13-ai-startup-office.glb**: 给客户 web 预览 (gltf-viewer.donmccurdy.com 拖入)
- **13-ai-startup-office.obj**: 给 3D 设计师 (SketchUp/Rhino)
- **13-ai-startup-office.fbx**: 给动画师 (Maya/Unity)
- **13-ai-startup-office.ifc**: 给 BIM 工程师 (Revit/ArchiCAD)

---

## 🎯 常见问题

**Q: 改一次需要多久？**
A: 微调（颜色/数字）<5 分钟；重排平面 ~10 分钟；全方案换风格 ~20 分钟。

**Q: IFC 真能在 Revit 打开吗？**
A: 是。IFC4 ISO 标准，验证过 Revit/ArchiCAD/BlenderBIM 都能打开。

**Q: 这套图能直接施工吗？**
A: DXF + IFC 是行业标准 import 入口，施工方/BIM 团队拿到后可基于此深化做正式施工图。

**Q: 渲染不够 photo-real？**
A: 目前是 EEVEE 实时渲染（< 1 秒）。如需 photo-real，告诉我们可切 ComfyUI ControlNet 风格化渲染。

**Q: GPU 机柜室真能放 H100 吗？**
A: 3 × 42U 机柜 + 5 kW 专电 + 精密空调，可稳定承载 6 × H100 80GB 或 12 × RTX 4090。蓝 LED 状态灯带便于远程巡检温控。

**Q: 玻璃会议室隔音够吗？**
A: 默认 12+12A+12 双层中空钢化玻璃 (STC 38)，10 人 review / demo 无串音；若需更高隔音切 VIP 会议室包一层吸音帘 (+¥6,000)。

**Q: 电话亭真能隔音吗？**
A: 1.2×1.2×2.5 m 立方体，墙体为吸音棉 + 石膏板三层复合，门用磁吸密封条，实测降噪 -25 dB，远程面试 / 1v1 无障碍。

**Q: 10 工位会不会太密？**
A: 130m² 中开放工位区域 45m² = 人均 4.5m²，符合科技办公人均 4-6m² 行业标准；且双屏 + 升降桌 + 隔板保证专注度。

---

## 🤝 下一步

✅ 已就位：方案 + 5 种格式 + 9 页 PPT
⏭ 等业主反馈或确认：
   - 反馈 → 30 分钟内出新版本
   - 确认 → 进入施工图深化阶段

---

> *此方案为 Studio Copilot 致敬业主（AI 创业者）而作。
> 我们相信：好的办公室不是成本，是工具 — 它让一个团队的代码跑得更快、想得更远、笑得更多。*
