# Vendor · 严老师 Arctura-Lab/Pipelines 的镜像资源

## 来源

- **仓库**：`https://github.com/Arctura-Lab/Pipelines`
- **镜像 commit**：见 `.source-commit` 文件（当前：`1caccd5` · 2026-04-20）
- **本地 clone 位置**：`~/arctura-pipelines/`

## 原则

1. **只读镜像** · 禁手改本目录下文件 · 改 bug 先给严老师提 PR · 这里再同步
2. **升级方式** · 重新 `gh repo clone Arctura-Lab/Pipelines` → 覆盖本目录文件 → 更新 `.source-commit`
3. **drift 检测** · 本地 artifact 如果改过 vendor 文件 · `vendor/_check_drift.py` 对比源应报 diff
4. **vendor/ 只放 LIGHT-compatible 的**（纯 Python stdlib + PIL） · FULL-only（Blender/OpenStudio）不 vendor · 在 _TODO-*.md 指向严老师原仓位置

## 映射表 · 本地路径 ← 严老师源路径 · 用途

### 脚本（Python · 11 个 LIGHT-compatible）

| 本地 | 源路径（playbooks/scripts/）| 用途 | 依赖 |
|---|---|---|---|
| `brief_version.py` | `brief_version.py` | brief.json 版本 backup/list/diff/restore | stdlib |
| `gen_mvp_summary.py` | `gen_mvp_summary.py` | 多 MVP 聚合 markdown 总结 | stdlib |
| `fix_svg_text_zorder.py` | `fix_svg_text_zorder.py` | SVG 文字图层前置（平面图美化） | xml.etree (stdlib) |
| `verify_ifc_enriched.py` | `verify_ifc_enriched.py` | IFC 质检（正则 + 文本） | stdlib |
| `score_variants.py` | `ab-comparison/score_variants.py` | P10 方案加权打分 (40/25/20/15) | stdlib |
| `case_study/extract_metrics.py` | `case-study/extract_metrics.py` | P11 单 MVP 统计抽取（+缩略图） | stdlib + PIL |
| `case_study/aggregate.py` | `case-study/aggregate.py` | P11 多 MVP 聚合到 metrics.json | stdlib |
| `case_study/render_templates.py` | `case-study/render_templates.py` | P11 metrics → portfolio/impact/sales 3 md | stdlib |
| `case_study/populate_narratives.py` | `case-study/populate_narratives.py` | P11 narrative 回写 metrics | stdlib |
| `ai_render/brief_to_prompt.py` | `ai_render/brief_to_prompt.py` | P4 brief → SDXL prompt（设计意图提取） | stdlib |
| `ai_render/prompt_templates.py` | `ai_render/prompt_templates.py` | P4 19 词材质原子库（常量） | — |

### Schemas（JSON Schema · 3 个权威契约）

| 本地 | 源路径（playbooks/schemas/）| 契约 |
|---|---|---|
| `schemas/brief-interior.schema.json` | `brief-interior.schema.json` | P1 室内 brief 输入 |
| `schemas/brief-architecture.schema.json` | `brief-architecture.schema.json` | P2 建筑 brief 输入 |
| `schemas/project.schema.json` | `project.schema.json` | P7 输出 / P6 · P8 · P9 消费 |

### Defaults（单一真源 · 3 个）

| 本地 | 源路径（playbooks/defaults/）| 用途 |
|---|---|---|
| `defaults/region-code-map.yaml` | `region-code-map.yaml` | 地区 ↔ 法规 / BOQ / EPW / 币种 |
| `defaults/hk_market.json` | `hk_market.json` | HK 市场均价库（面积/预算推算）|
| `defaults/comparison-cameras.json` | `comparison-cameras.json` | P10 A/B 统一相机参数（按房间尺寸分档）|

## 不 vendor 的（FULL-only · 不能 LIGHT 跑）

- `scripts/asset-intake/{dxf_extract,vision_extract}.py` · 需 ezdxf / vision API
- `scripts/brief-intake/run_intake.py` · 需 cli_anything.llm_intake harness
- `scripts/ai_render/render_enhance.py` · 需 ComfyUI + GPU
- `scripts/ab-comparison/{run_ab,verify}.py` · 需 OpenStudio whatif + Blender render
- `scripts/case-study/{narrate,run_one,run_all}.py` · 需 Gemini CLI（可 polyfill 但本轮不做）
- `scripts/batch_all_mvps.py` · 需 OpenStudio + Blender

这些脚本在 `_build/arctura_mvp/artifacts/<name>.py` 中作为 skeleton 存在 · `_TODO-<name>.md` 指向本表项。

## 如何验证 vendor 还在跟源同步

```bash
# 对比 vendor/.source-commit 和 ~/arctura-pipelines HEAD
cd ~/arctura-pipelines && git rev-parse HEAD
cat _build/arctura_mvp/vendor/.source-commit

# 对比文件内容（应该 identical）
diff ~/arctura-pipelines/playbooks/scripts/brief_version.py _build/arctura_mvp/vendor/brief_version.py
```

## 风险 + 限制

1. **每次严老师仓升级** · 本 vendor 可能 break · 需人工 re-copy + 跑 pytest
2. **schemas 升级时** · `brief-rules.json` 里的 completeness 计算可能 drift · cross-lang test 保护
3. **本地跟源之间不能双向 diverge** · vendor 是"源的快照" · 不是"源的 fork"
