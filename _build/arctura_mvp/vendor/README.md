# vendor/ · 已 deprecated（Phase 9 · 2026-04-24）

## 为什么空

Phase 9 之前 · 这里 copy 了严老师 `Arctura-Lab/Pipelines` (StartUP-Building) 的 11 脚本 + 3 schema + 3 defaults。

**Phase 9 发现这是错的**：
- 源头就在本机 `Building-CLI-Anything/CLI-Anything/` 和 `Building-CLI-Anything/StartUP-Building/`
- copy 会 drift · 跟源不一致
- 浪费存储 + 难维护

## 新策略（Phase 9+）

**不 copy · 改 sys.path import**：
- 用 `_build/arctura_mvp/paths.py` 的常量（`PLAYBOOKS_SCRIPTS` 等）
- `ensure_playbook_script_subdir_on_path("case-study")` 加 sys.path
- 然后 `import render_templates` 直达源头

**CLI harness 用 pip install**：
- `pip install --user -e Building-CLI-Anything/CLI-Anything/blender/agent-harness`
- 之后 `from cli_anything.blender import ...` 直接可用

## 保留

- `templates/client-readme-template.md` · 在 `_build/arctura_mvp/templates/`（不在本目录）· 因为是需要填空的模板 · 必要 copy
- 本 README · 文档

## 下一步（Phase 9 实装）

删除 `vendor/__init__.py` 后 · 整个 vendor/ 目录可以删除 · 保留本 README 一段时间供参考 · Phase 10 彻底清除。
