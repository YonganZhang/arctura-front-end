"""公共类型 · dataclass 版（纯函数 / MCP 友好）"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Optional, Literal
from datetime import datetime

from .state import ProjectState
from .tiers import TierId, RenderEngine


@dataclass
class Project:
    slug: str
    state: ProjectState
    version: int = 0
    visibility: Literal["private", "unlisted", "public"] = "private"
    owner: Optional[str] = None                # anon session id
    display_name: str = ""
    brief: Optional[dict] = None
    brief_schema_version: str = "v1"
    tier: Optional[TierId] = None
    variant_count: int = 1
    render_engine: Optional[RenderEngine] = None
    scene: Optional[dict] = None
    scene_schema_version: str = "v1"
    artifacts: dict = field(default_factory=lambda: {
        "produced": [], "skipped": [], "errors": [],
        "partial": False, "timing_ms": {}, "urls": {},
    })
    pending_count: int = 0
    last_save_ref: Optional[str] = None       # git commit SHA
    created_at: str = ""
    updated_at: str = ""
    _pii_fields: list[str] = field(default_factory=list)


@dataclass
class ArtifactResult:
    name: str
    status: Literal["done", "skipped", "error"]
    timing_ms: int
    output_path: Optional[str] = None
    error: Optional[dict] = None              # {exception, trace_tail}
    reason: Optional[str] = None              # for skipped


@dataclass
class MVPResult:
    slug: str
    tier: str
    variant_count: int
    render_engine: str
    produced: list[str] = field(default_factory=list)
    skipped: list[dict] = field(default_factory=list)
    errors: list[dict] = field(default_factory=list)
    partial: bool = False
    urls: dict = field(default_factory=dict)
    timing_ms: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Job:
    id: str
    slug: str
    tier: str
    variant_count: int
    render_engine: str
    status: Literal["queued", "running", "done", "cancelled", "error"] = "queued"
    events: list[dict] = field(default_factory=list)   # SSE event log
    created_at: str = ""
    started_at: Optional[str] = None
    finished_at: Optional[str] = None


def utc_now() -> str:
    # Python 3.12+ deprecates datetime.utcnow() · 用 timezone-aware
    from datetime import timezone
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
