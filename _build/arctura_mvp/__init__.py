"""Arctura MVP 统一包 · Phase 6 实装

核心 API（Python + MCP 共用）：
- create_project(display_name, brief=None, tier=None) -> Project
- chat_brief(slug, user_message) -> {reply, brief_partial, completeness, ready}
- pick_tier(slug, tier, variant_count=1) -> Project
- generate_mvp(slug, dry_run=False) -> {job_id, stream_url}
- get_job_status(job_id) -> JobStatus
- edit_scene(slug, user_message) -> {plan_preview, applied?}
- apply_scene_ops(slug, ops) -> {applied, rejected}
- save_project(slug, commit_message=None) -> {commit_sha, url}
- list_projects(owner="me", limit=20, cursor=None) -> list
- get_project(slug) -> Project

所有函数都：
- 纯 · 无 global 副作用（store 层隔离）
- 支持 dry_run 参数
- 错误不中断 · 累加到 MVPResult.errors
- 支持 on_event hook（SSE / MCP async 预留）
"""
from .types import Project, MVPResult, Job, ArtifactResult, utc_now
from .tiers import (
    TIER_CONFIG, TIER_ALIASES, OPT_ADDONS,
    resolve_tier, pick_engine, all_tier_ids, list_tiers_for_ui,
)
from .state import (
    ProjectState, TRANSITIONS, validate_transition,
    can_edit, can_save, is_terminal,
)

__version__ = "0.1.0"
__all__ = [
    "Project", "MVPResult", "Job", "ArtifactResult", "utc_now",
    "TIER_CONFIG", "TIER_ALIASES", "OPT_ADDONS",
    "resolve_tier", "pick_engine", "all_tier_ids", "list_tiers_for_ui",
    "ProjectState", "TRANSITIONS", "validate_transition",
    "can_edit", "can_save", "is_terminal",
]
