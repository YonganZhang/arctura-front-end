# Arctura-Front-end

> 对应 GitHub 私有仓 `Arctura-Lab/Front-end` · 2026-04-20 通过 Telegram zip 传输（仓 private 没直接 clone）
>
> **不同于 `StartUP-Building/.claude/skills/client-portal/`** —— 这里是**对外官网 + Project Space 演示前端**（marketing + demo），client-portal skill 是**按 MVP 动态生成 portal.html 的 agent 工具**。

## 来源

- zip 原件：`/root/telegrambot/exchange_files/2026-04-20/13-46-20_Arctura-Front.zip`（9.5 MB · 33 文件）
- 上传时间：老师 2026-04-19 17:45（zip mtime）

## 内容

| 文件/目录 | 大小 | 用途 |
|---|---|---|
| `Arctura Labs.html` | 60 KB | 官网主页（当前版 · hero: "Design that compiles"）|
| `Arctura Labs v1.html` | 64 KB | 官网 v1 版（归档/对比）|
| `Project Space.html` | 14 KB | 项目空间入口 |
| `app.js` | 27 KB | 官网主页 JS |
| `styles.css` | 66 KB | 官网样式 |
| `mvps-data.js` | 3.5 KB | 官网展示用 MVP 数据 |
| `project-space/app.jsx` | 40 KB | Project Space 的 React app（zen-tea demo）|
| `project-space/data.js` | 11 KB | zen-tea 项目数据（zones / furniture / pricing）|
| `project-space/styles.css` | 37 KB | Project Space 样式 |
| `assets/zen-tea/` | 4 PNG + 1 SVG | 禅意茶室 demo 素材（hero / render-03/04/08 / floorplan）|
| `assets/intake-*.png` | 3 PNG | 客户 intake 示意图（floorplan / moodboard / site-photo）|
| `screenshots/` | 5 PNG | homepage hero 设计截图 |
| `debug/intake*.png` | 2 PNG | 设计调试截图 |
| `uploads/QUICK-START.md` | 20 KB | 前端上传演示样本（pipeline 全景图 + 快速用法）|
| `uploads/internal-handbook.md` | 38 KB | 前端上传演示样本（**4-18 v2 历史快照**，不是权威版；权威在 `StartUP-Building/deliverables/internal-handbook/internal-handbook-v4.md`）|
| `uploads/pasted-*.png` | 4 PNG | 用户上传示例图 |

## 产品定位

- **对外官网**（Arctura Labs.html）：marketing 主页，宣讲"Design that compiles"产品理念
- **Project Space**（Project Space.html + `project-space/`）：给客户看的 **demo 交互页**，以 zen-tea 茶室为样本展示"设计管线产出 → 可浏览交付"
- 与 `client-portal` skill 的关系：**客户拿到的 portal.html 走 skill 动态生成**，这份 Front-end repo 是 **产品门面 + 标准演示**

## 本地静态预览

```bash
cd Building-CLI-Anything/Arctura-Front-end/
$PY -m http.server 8880    # 然后浏览器开 localhost:8880
```

## 跟 client-portal skill 的功能边界

| 维度 | Arctura-Front-end（本目录） | `client-portal` skill |
|---|---|---|
| 角色 | 产品门面 + demo | 工具（agent 调用）|
| 输入 | 固定 zen-tea 数据 | 任意 MVP 目录 |
| 产出 | 静态官网 3 页 | `<MVP>/portal.html` + `_server.py` |
| 调用方 | 访客浏览器 | 客户拿到项目产出后点"生成门户" |
| 仓库 | `Arctura-Lab/Front-end` | `Arctura-Lab/Pipelines` 里的 `.claude/skills/client-portal/` |

## 上游版本

当前 zip = `Arctura-Lab/Front-end` 某个 commit 的 working tree 导出。老师后续推送需要新 zip 或授权 clone 权限。

## TODO

- [ ] 老师授权 clone 后从 zip 路径切换到 `git clone Arctura-Lab/Front-end`
- [ ] 补 `Arctura-Front-end` 的变更历史到 wiki `top/findings/` 如果涉及 pipeline 设计
