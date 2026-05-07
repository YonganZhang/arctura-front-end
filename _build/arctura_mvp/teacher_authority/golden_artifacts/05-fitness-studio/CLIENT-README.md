# Lift Studio 精品健身工作室 — 方案文件指南
> 客户/合伙人专用 · 2026-04-15 · Studio Copilot v3

---

## ⏱ 设计统计

| 项 | 值 |
|---|---|
| 设计开始 | 09:33:12 |
| 设计完成 | 09:48:29 |
| 总用时 | **15 分 17 秒** |
| 3D 物体总数 | 90 |
| 平面图实体数 | 82 |
| 方案 PPT 页数 | 9 |
| 5 种导出文件 | DXF + GLB + OBJ + FBX + IFC4 |

---

## 📦 产品内容（13 个文件，共约 5.2 MB）

| 类型 | 文件 | 大小 | 给谁 |
|------|------|------|------|
| 客户决策参考 | brief.json | 2 KB | 客户 / 项目经理 |
| 风格视觉 | moodboard.png | 8 KB | 客户 |
| 3D 渲染 | render.png | 1.6 MB | 客户 |
| 平面图 | floorplan.png/.svg | 20 KB + 13 KB | 客户 / 设计师 |
| 方案 PPT | deck.odp | 1.6 MB | 客户 / 投资人 |
| 施工图 | exports/floorplan.dxf | 66 KB | 施工方 / 建筑师 |
| 3D 网页预览 | exports/05-fitness-studio.glb | 418 KB | 客户 / 营销 |
| 3D 通用 | exports/05-fitness-studio.obj | 432 KB | 3D 设计师 |
| 3D 动画 | exports/05-fitness-studio.fbx | 351 KB | 动画 / Unity 团队 |
| BIM | exports/05-fitness-studio.ifc | 64 KB | BIM 工程师 |
| 源数据 | room.json + deck.lo-cli.json + floorplan.inkscape-cli.json | ~80 KB | 内部修改 |

---

## 🧑‍💼 5 种 Stakeholder 怎么用

### 1️⃣ 客户 / 业主（决策者）
**主要看**: `moodboard.png` → `render.png` → `deck.odp` → `floorplan.png`
**关键决策点**: 颜色方案 / 整体风格 / 是否需要调整功能区
**怎么改**: 直接告诉我们 "把 X 改成 Y"，5-30 分钟内出新版本
**Web 3D 预览**: 把 `exports/05-fitness-studio.glb` 拖到 https://gltf-viewer.donmccurdy.com 即可旋转/缩放查看

### 2️⃣ 投资人 / 合伙人 / 老板
**主要看**: `deck.odp` (完整方案) + `brief.json` (需求) + 本 README 的"设计统计"
**用什么开**: PowerPoint / Keynote / Google Slides / LibreOffice (任意都可)
**核心信息**: 9 页含封面、风格、3D、平面、功能区详情、BOQ、工期、交付、下一步

### 3️⃣ 设计师同事（精修方案）
**源文件**: `room.json` (3D 场景), `floorplan.inkscape-cli.json` (平面图源), `deck.lo-cli.json` (PPT 源)
**软件**: VS Code (编辑 JSON), Inkscape (修 SVG), LibreOffice (修 PPT)
**修改后重出**: 用 cli-anything-* 命令重新跑相关步骤

### 4️⃣ 施工方 / 建筑技师
**主要看**: `exports/floorplan.dxf` (平面施工图基础)
**软件**: AutoCAD / Rhino / QCAD / BricsCAD
**能干**: 直接在 AutoCAD 里加施工标注、节点详图、工程量
**SVG 矢量备份**: `floorplan.svg` 可在 Illustrator / Inkscape 编辑

### 5️⃣ BIM 工程师 / 结构机电
**主要看**: `exports/05-fitness-studio.ifc` (IFC4 BIM 模型 · 93 个 IfcProduct)
**软件**: Revit / ArchiCAD / BlenderBIM (Blender 插件，免费) / Solibri
**能干**: 结构/机电协同、碰撞检测、工程量算量、设备联动
**3D 备份**: `exports/05-fitness-studio.glb / .obj / .fbx` 可导入 SketchUp / Rhino / Max / Maya / Unity

---

## 📄 每个文件的详细说明

### brief.json
**是什么**: 我们整理后的客户需求（结构化 JSON）
**打开**: 任何文本编辑器或浏览器
**改**: 编辑数字（预算/工期）或增减需求条目

### moodboard.png
**是什么**: 整体配色方向 6 色板预览（黑墙 / 镜面银 / 力量黄 / 暖木 / 奶白 / 深红）
**打开**: 双击图片
**改色**: 告诉我们替换哪个颜色

### render.png + room.json
**是什么**: 装修后真实视觉效果（SE 角度看向西北，自由力量区 + 哑铃架 + 淋浴）+ 3D 场景源数据（90 物体）
**打开 (.png)**: 任何看图软件
**换角度/材质**: 描述偏好，重渲染 < 5 分钟

### floorplan.png / .svg
**是什么**: 房间 8 个功能区与家具摆放（俯视图，1:70 比例）
**.png**: 任何看图软件预览
**.svg**: 矢量图，Inkscape (免费) / Illustrator / Figma 编辑

### deck.odp
**是什么**: 9 页完整方案
**打开**: PowerPoint / Keynote / Google Slides / LibreOffice
**改**: 直接在 PPT 软件里改文字

### exports/ 文件夹
- **floorplan.dxf**: 给施工 / 建筑师 (AutoCAD/Rhino) · 82 实体
- **05-fitness-studio.glb**: 给客户 web 预览 (gltf-viewer.donmccurdy.com 拖入) · 90 节点
- **05-fitness-studio.obj**: 给 3D 设计师 (SketchUp/Rhino) · 3292 顶点
- **05-fitness-studio.fbx**: 给动画师 (Maya/Unity)
- **05-fitness-studio.ifc**: 给 BIM 工程师 (Revit/ArchiCAD) · IFC4, 93 Products, 6 Walls

---

## 🎯 常见问题

**Q: 改一次需要多久？**
A: 微调（颜色/数字）<5 分钟；重排平面 ~10 分钟；全方案换风格 ~20 分钟。

**Q: IFC 真能在 Revit 打开吗？**
A: 是。IFC4 ISO 标准，验证过 Revit/ArchiCAD/BlenderBIM 都能打开。

**Q: 这套图能直接施工吗？**
A: DXF + IFC 是行业标准 import 入口，施工方/BIM 团队拿到后可基于此深化做正式施工图。

**Q: 渲染不够 photo-real？**
A: 目前是 EEVEE 实时渲染（< 5 秒）。如需 photo-real，告诉我们，可切 ComfyUI ControlNet 风格化渲染。

**Q: 镜面墙真实吗？**
A: 材质设 metallic=0.95 / roughness=0.05，GLB/FBX/IFC 都保留此材质参数，任何支持 PBR 的引擎可还原。

---

## 🤝 下一步

✅ 已就位：方案 + 5 种格式 + 9 页 PPT
⏭ 等你反馈或确认：
   - 反馈 → 30 分钟内出新版本
   - 确认 → 进入施工图深化阶段
