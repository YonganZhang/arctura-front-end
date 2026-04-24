"""本机权威源路径常量 · Phase 9（2026-04-24）

架构层级：
  公司项目/
  ├── Building-CLI-Anything/                  ← MONOREPO_ROOT
  │   ├── CLI-Anything/                       ← CLI_ANYTHING_ROOT (67 harness)
  │   ├── StartUP-Building/                   ← STARTUP_BUILDING_ROOT (spec + scripts)
  │   │   └── playbooks/
  │   │       ├── scripts/                    ← PLAYBOOKS_SCRIPTS
  │   │       ├── schemas/                    ← PLAYBOOKS_SCHEMAS
  │   │       └── defaults/                   ← PLAYBOOKS_DEFAULTS
  │   └── Arctura-Front-end/                  ← REPO_ROOT（本项目）
  │       └── _build/arctura_mvp/
  └── wiki-methodology/

本模块提供：
  - Arctura 代码里引用严老师资源（scripts / schemas / defaults）统一走本文件
  - 不再 copy 到 vendor/ · 避免 drift
  - `ensure_scripts_path()` 帮 case_study / variants 等 artifact 加 sys.path
"""
from __future__ import annotations
import sys
from pathlib import Path

# 核心路径 · 从 _build/arctura_mvp/paths.py 向上推
_THIS_DIR = Path(__file__).resolve().parent          # _build/arctura_mvp/
REPO_ROOT = _THIS_DIR.parents[1]                     # Arctura-Front-end/
MONOREPO_ROOT = REPO_ROOT.parent                     # Building-CLI-Anything/

# 严老师 权威 monorepo
CLI_ANYTHING_ROOT = MONOREPO_ROOT / "CLI-Anything"
STARTUP_BUILDING_ROOT = MONOREPO_ROOT / "StartUP-Building"

# StartUP-Building/playbooks/ 下的资源
PLAYBOOKS_ROOT = STARTUP_BUILDING_ROOT / "playbooks"
PLAYBOOKS_SCRIPTS = PLAYBOOKS_ROOT / "scripts"
PLAYBOOKS_SCHEMAS = PLAYBOOKS_ROOT / "schemas"
PLAYBOOKS_DEFAULTS = PLAYBOOKS_ROOT / "defaults"

# CLI-Anything agent-harness 入口（pip install -e 后从这里 import）
CLI_HARNESS_ROOTS = {
    "blender": CLI_ANYTHING_ROOT / "blender" / "agent-harness",
    "openstudio": CLI_ANYTHING_ROOT / "openstudio" / "agent-harness",
    "llm-intake": CLI_ANYTHING_ROOT / "llm-intake" / "agent-harness",
    "image-grid": CLI_ANYTHING_ROOT / "image-grid" / "agent-harness",
    "comfyui": CLI_ANYTHING_ROOT / "comfyui" / "agent-harness",
    "libreoffice": CLI_ANYTHING_ROOT / "libreoffice" / "agent-harness",
    "inkscape": CLI_ANYTHING_ROOT / "inkscape" / "agent-harness",
}


# ───────── Helper · artifact 代码加 sys.path 方便 import 严老师脚本 ─────────

def ensure_playbook_scripts_on_path() -> None:
    """把 StartUP-Building/playbooks/scripts/ 加到 sys.path · 幂等"""
    p = str(PLAYBOOKS_SCRIPTS)
    if p not in sys.path:
        sys.path.insert(0, p)


def ensure_playbook_script_subdir_on_path(subdir: str) -> None:
    """把特定子目录加到 sys.path · 如 'case-study' 或 'ab-comparison'"""
    p = str(PLAYBOOKS_SCRIPTS / subdir)
    if p not in sys.path:
        sys.path.insert(0, p)


# ───────── 自检 ─────────

def verify_paths() -> dict:
    """检查关键路径是否存在 · 返 {path_name: bool}"""
    return {
        "REPO_ROOT": REPO_ROOT.exists(),
        "MONOREPO_ROOT": MONOREPO_ROOT.exists(),
        "CLI_ANYTHING_ROOT": CLI_ANYTHING_ROOT.exists(),
        "STARTUP_BUILDING_ROOT": STARTUP_BUILDING_ROOT.exists(),
        "PLAYBOOKS_SCRIPTS": PLAYBOOKS_SCRIPTS.exists(),
        "PLAYBOOKS_SCHEMAS": PLAYBOOKS_SCHEMAS.exists(),
        "PLAYBOOKS_DEFAULTS": PLAYBOOKS_DEFAULTS.exists(),
        **{f"HARNESS_{k}": v.exists() for k, v in CLI_HARNESS_ROOTS.items()},
    }


if __name__ == "__main__":
    import json
    print(json.dumps(verify_paths(), indent=2, ensure_ascii=False))
