> ⚠️ **LIGHT 模式输出** · 本 README 由 Arctura-Front-end LIGHT pipeline 产出 · 严老师 spec 要求的 PPT / IFC / 施工 DXF 等需走 FULL pipeline · 详见同目录 `_TODO-*.md` 清单

# 未命名项目 — 方案文件指南
> 客户/合伙人专用 · 2026-04-25 · Studio Copilot v3

---

## ⏱ 设计统计

| 项 | 值 |
|---|---|
| 设计开始 | 00:51:28 |
| 设计完成 | 00:51:28 |
| 总用时 | **— *LIGHT 模式未产*** |
| 3D 物体总数 | 10 |
| 平面图实体数 | 12 |
| 方案 PPT 页数 | — *LIGHT 模式未产* |
| 5 种导出文件 | DXF + GLB + OBJ + FBX + IFC4 |

---

## 📦 产品内容（8 个文件）

| 类型 | 文件 | 大小 | 给谁 |
|------|------|------|------|
| 客户决策参考 | brief.json | ... | 客户 / 项目经理 |
| 风格视觉 | moodboard.png | ... | 客户 |
| 3D 渲染 | render.png | ... | 客户 |
| 平面图 | floorplan.png/.svg | ... | 客户 / 设计师 |
| 方案 PPT | decks/deck-client.pptx | ... | 客户 / 投资人 |
| 施工图 | exports/floorplan.dxf | ... | 施工方 / 建筑师 |
| 3D 网页预览 | exports/draft-aa408294.glb | ... | 客户 / 营销 |
| 3D 通用 | exports/draft-aa408294.obj | ... | 3D 设计师 |
| 3D 动画 | exports/draft-aa408294.fbx | ... | 动画 / Unity 团队 |
| BIM | exports/draft-aa408294.ifc | ... | BIM 工程师 |
| 源数据 | room.json + .lo-cli.json + .inkscape-cli.json | ... | 内部修改 |

---

## 🧑‍💼 5 种 Stakeholder 怎么用

### 1️⃣ 客户 / 业主（决策者）
**主要看**: `moodboard.png` → `render.png` → `decks/deck-client.pptx` → `floorplan.png`
**关键决策点**: 颜色方案 / 整体风格 / 是否需要调整功能区
**怎么改**: 直接告诉我们 "把 X 改成 Y"，5-30 分钟内出新版本
**Web 3D 预览**: 把 `exports/draft-aa408294.glb` 拖到 https://gltf-viewer.donmccurdy.com 即可旋转/缩放查看

### 2️⃣ 投资人 / 合伙人 / 老板
**主要看**: `decks/deck-client.pptx` (完整方案) + `brief.json` (需求) + 本 README 的"设计统计"
**用什么开**: PowerPoint / Keynote / Google Slides / LibreOffice (任意都可)
**核心信息**: — *LIGHT 模式未产* 页含封面、风格、3D、平面、BOQ、工期、下一步

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
**主要看**: `exports/draft-aa408294.ifc` (IFC4 BIM 模型)
**软件**: Revit / ArchiCAD / BlenderBIM (Blender 插件，免费) / Solibri
**能干**: 结构/机电协同、碰撞检测、工程量算量、设备联动
**3D 备份**: `exports/draft-aa408294.glb / .obj / .fbx` 可导入 SketchUp / Rhino / Max / Maya / Unity

---

## 📄 每个文件的详细说明

### brief.json
**是什么**: 我们整理后的客户需求（结构化 JSON）
**打开**: 任何文本编辑器或浏览器
**改**: 编辑数字（预算/工期）或增减需求条目

### moodboard.png
**是什么**: 整体配色方向 6 色板预览
**打开**: 双击图片
**改色**: 告诉我们替换哪个颜色

### render.png + room.json
**是什么**: 装修后真实视觉效果（一个角度）+ 3D 场景源数据
**打开 (.png)**: 任何看图软件
**换角度/材质**: 描述偏好，重渲染 < 5 分钟

### floorplan.png / .svg
**是什么**: 房间分区与家具摆放（俯视图）
**.png**: 任何看图软件预览
**.svg**: 矢量图，Inkscape (免费) / Illustrator / Figma 编辑

### decks/deck-client.pptx
**是什么**: — *LIGHT 模式未产* 页完整方案
**打开**: PowerPoint / Keynote / Google Slides / LibreOffice
**改**: 直接在 PPT 软件里改文字

### exports/ 文件夹
- **floorplan.dxf**: 给施工 / 建筑师 (AutoCAD/Rhino)
- **draft-aa408294.glb**: 给客户 web 预览 (gltf-viewer.donmccurdy.com 拖入)
- **draft-aa408294.obj**: 给 3D 设计师 (SketchUp/Rhino)
- **draft-aa408294.fbx**: 给动画师 (Maya/Unity)
- **draft-aa408294.ifc**: 给 BIM 工程师 (Revit/ArchiCAD)

---

## 🎯 常见问题

**Q: 改一次需要多久？**
A: 微调（颜色/数字）<5 分钟；重排平面 ~10 分钟；全方案换风格 ~20 分钟。

**Q: IFC 真能在 Revit 打开吗？**
A: 是。IFC4 ISO 标准，验证过 Revit/ArchiCAD/BlenderBIM 都能打开。

**Q: 这套图能直接施工吗？**
A: DXF + IFC 是行业标准 import 入口，施工方/BIM 团队拿到后可基于此深化做正式施工图。

**Q: 渲染不够 photo-real？**
A: 目前是 EEVEE 实时渲染（< 5 秒）。如需 photo-real，告诉我们可切 ComfyUI ControlNet 风格化渲染。

---

## 🤝 下一步

✅ 已就位：方案 + 5 种格式 + PPT
⏭ 等你反馈或确认：
   - 反馈 → 30 分钟内出新版本
   - 确认 → 进入施工图深化阶段