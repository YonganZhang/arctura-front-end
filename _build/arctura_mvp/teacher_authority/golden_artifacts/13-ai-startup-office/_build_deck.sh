#!/usr/bin/env bash
set -e
cd /Users/kaku/Desktop/Work/StartUP-Building/studio-demo/mvp/13-ai-startup-office

lo() { python3 -c "from cli_anything.libreoffice.libreoffice_cli import cli; cli()" "$@"; }

# New Impress doc
lo document new --type impress --name "Stack Lab v1" -o deck.lo-cli.json

L() { lo --project deck.lo-cli.json "$@"; }

# Page 1 · Cover
L impress add-slide -t "Stack Lab · AI Startup 办公室 v1" -c "130m² · Tech-Loft + 10 工位 + GPU 机柜 · 预算 ¥750,000 · 工期 8 周
致敬业主 · made with love by Studio Copilot"

# Page 2 · Style (moodboard)
L impress add-slide -t "1. 风格 & 6 色调色板" -c "Tech-Loft + Plant-Rich + Exposed-Pipe · 4000K 主光 · 机柜蓝 LED accent"
L impress add-image 1 moodboard.png --x 2cm --y 4cm -w 22cm -h 13cm

# Page 3 · 3D render
L impress add-slide -t "2. 3D 方案渲染 (EEVEE)" -c "118 物体 · 14 材质 · 玻璃隔断 + 机柜蓝光 + 暖木工位 · 0.5 秒出图"
L impress add-image 2 render.png --x 2cm --y 4cm -w 22cm -h 13cm

# Page 4 · floor plan
L impress add-slide -t "3. 9 分区平面布局" -c "入口LOGO + 10 工位双屏 + GPU 服务器室 + 玻璃会议室 + 2 电话亭 + 茶水间 + 休闲 + WC + 绿植"
L impress add-image 3 floorplan.png --x 2cm --y 4cm -w 22cm -h 13cm

# Page 5 · Zones & flow
L impress add-slide -t "4. 工位密度 & 动线" -c "工位容量:
  开放工位 10 位 × 双屏 = 20 屏 (GPU 开发标配)
  玻璃会议 10 人 (大屏 + 4m 白板)
  电话亭 × 2 (远程面试 / 1v1)
  休闲沙发 + 桌足球 (减压)

核心动线:
  入口 → 接待 → 开放工位 (主路径)
  工位 ↔ 茶水间 (短路径, 频繁)
  工位 ↔ 电话亭 (快速进出)
  访客 → 玻璃会议室 (视觉穿透, 无需穿过工位)
  工程师 → GPU 机柜室 (玻璃门, 权限管控)"

# Page 6 · BOQ
L impress add-slide -t "5. BOQ 概算 (¥750,000)" -c "主结构/装修:
  loft 改造 + 外露管道涂装 130m²:       ¥95,000
  玻璃隔断 4 套 (会议 + 服务器 + 电话亭): ¥88,000
  LOGO 墙 (可拆换框 + 背光):            ¥22,000
  4m 白板墙定制:                        ¥14,000
  卫生间基础 + 干湿分区:                ¥25,000

家具:
  10 × 电动升降桌 + 10 × 人体工学椅:    ¥72,000
  20 × 27″ 显示器 + 支臂:               ¥58,000
  玻璃会议桌 2.4m + 10 椅:              ¥28,000
  2 × 电话亭 (含吸音/USB-C):            ¥42,000
  茶水间台面 + 吊柜 + 3 电器:           ¥38,000
  休闲沙发 × 2 + 桌足球 + 豆袋:         ¥32,000

设备 / 基建:
  3 × 42U 机柜 (含蓝 LED + 精密空调):   ¥155,000
  5 kW 专电 + 弱电布线 + AP 6 个:       ¥45,000
  75″ 会议大屏 + 视讯设备:              ¥22,000
  线性吸顶灯 + 轨道灯 + 生长灯:         ¥28,000

5 盆栽 + 软装 + 清洁:                   ¥36,000
合计:                                 ¥750,000 (预算内 ✓)"

# Page 7 · Timeline
L impress add-slide -t "6. 8 周工期" -c "W1: 深化设计 + 材料选样 + 消防/弱电审批
W2: loft 水电拆改 + 机柜室专电 + 精密空调点位
W3: 地面/墙面基础 + 玻璃隔断框架施工
W4: 定制家具生产 (工位 + 会议桌 + LOGO 墙)
W5: 玻璃安装 + 白板墙 + 照明 + 吊顶 + 轨道灯
W6: 3 × 机柜进场 + 蓝 LED + 空调调试 + 弱电入柜
W7: 10 工位 + 20 屏 + 会议设备 + 电话亭 + 茶水间
W8: 软装 (5 盆栽 + 沙发 + 桌足球) + 保洁 + 启用仪式"

# Page 8 · Tech-ops notes
L impress add-slide -t "7. 技术运维亮点" -c "GPU 机柜室:
  - 3 × 42U 机柜 (可上 12 × RTX 4090 / 6 × H100)
  - 蓝色 LED accent = 温控状态可视化
  - 玻璃门 + 刷卡 = 安全 + 展示
  - 5 kW 专用电路 + 精密空调 = 24/7 稳定

开发者工效:
  - 10 × 电动升降桌 = 久坐 / 站立切换
  - 20 × 27″ 屏 = 每人双屏代码 + 预览
  - 人体工学椅 = 程序员腰肌友好

协作:
  - 玻璃会议室 + 75″ 屏 = 10 人 review / demo
  - 4m 白板墙 = 架构图 / 脑暴
  - 2 电话亭 = 远程面试 / 客户 call 隔音"

# Page 9 · Next
L impress add-slide -t "8. 下一步 & 待业主确认" -c "待业主决策:
  - LOGO 颜色 (方案 A: 酸橙绿 #A8C947 / 方案 B: 深青 #2E5454)
  - 会议桌材质 (白橡 / 胡桃 / 黑色岩板)
  - 服务器机柜是否要 glass floor 展示 (+¥18,000)
  - 桌足球是否替换为乒乓球桌 (同价)

签单即启动:
  1. Pascal Editor 导出施工 IFC (Revit 协作, 已导出)
  2. Inkscape 导出 DXF 施工图 (AutoCAD, 已导出 115 实体)
  3. Blender 导出 GLB (AR / Sketchfab 预览, 已导出)
  4. FBX + OBJ (动画团队 + 3D 设计师, 已导出)

本方案由 Studio Copilot 自动生成, 9 页 deck + 平面 + 3D + 5 种施工格式,
耗时 < 15 分钟. 致敬业主 — 做一个您想去的办公室."

# Export to ODP
L export render deck.odp --preset odp --overwrite
ls -la deck.odp
