# Teacher Authority Files · 100% 老师代码 · 直接复制 · 不要改

> Phase 12 Codex 第二意见决策(2026-05-07):**用户期望 FORMAL 渲染跟老师真样品视觉相似**
> 实现路径:**直接复制老师文件作 worker 真调用入口** · 不改不包装

## 来源 · 不要在这里编辑 · 改请改老师上游

| 文件 | 老师上游路径 | 用途 |
|---|---|---|
| `marp_deck_scripts/setup_mvp_render.py` | StartUP-Building/.claude/skills/marp-deck/scripts/ | brief.json + _render_script.py → _render_multi.py |
| `marp_deck_scripts/_render_multi_tail.py` | 同上 | 8 视角 cameras + 渲染 tail 模板 |
| `marp_deck_scripts/gen_moodboard.py` | 同上 | brief → moodboard.png |
| `marp_deck_scripts/build_pptx.sh` | 同上 | marp 调用包装 |
| `playbook_scripts/batch_all_mvps.py` | StartUP-Building/playbooks/scripts/ | 跨 MVP 批处理(P7+P8+P6 编排) |
| `playbook_scripts/fix_svg_text_zorder.py` | 同上 | SVG 中文文字层级修复 |
| `playbook_scripts/verify_*.py` | 同上 | 产物验证 |
| `render_scripts/{01,03,05,13,20}-<slug>.py` | StartUP-Building/studio-demo/mvp/<slug>/_render_script.py | 5 个真 MVP scene 几何脚本 · scene_formal 选 template 时参考 |

## 用法

worker 在 scene_formal / moodboard_formal / deck_client_formal 中:
1. 直接 `subprocess.run([python, str(TEACHER_AUTH/marp_deck_scripts/setup_mvp_render.py), ...])`
2. 或读 render_scripts/<slug>.py 作 template · brief.dimensions_m 替换 ROOM_LEN / ROOM_WID / ROOM_HT

## 同步策略

老师上游变了 → 重 `cp -r ` 整目录覆盖 · 不要 merge · 不要改

## 路径 patch

老师代码里 Mac 硬编码 `/Users/kaku/Desktop/...` 通过中央 `_path_patcher.py` monkey-patch 处理(将来加)
