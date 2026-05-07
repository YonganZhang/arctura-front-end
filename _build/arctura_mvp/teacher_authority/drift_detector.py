"""老师 git revision drift 监控 · 100% 接入度的最后保障

老师每周升级 33 spec(平均 1.4 个/天)· 我们 thin runner / spec_lock 跟头部追。
每次 worker 启动跑一次 detect_drift() · 看老师上游有没新 commit / spec 变化 ·
有则告警 · 提示我们 review。

不阻断生产 · 仅 advisory。
"""
from __future__ import annotations
import json, subprocess, time
from pathlib import Path
from typing import Optional

from ..paths import STARTUP_BUILDING_ROOT


_DRIFT_CACHE = Path("/tmp/arctura_teacher_drift_cache.json")


def _git_head_rev() -> Optional[str]:
    """老师本机 mirror 的 HEAD commit"""
    if not (STARTUP_BUILDING_ROOT / ".git").exists():
        return None
    try:
        proc = subprocess.run(
            ["git", "-C", str(STARTUP_BUILDING_ROOT), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=5,
        )
        return proc.stdout.strip() if proc.returncode == 0 else None
    except Exception:
        return None


def _git_recent_commits(n: int = 10) -> list[dict]:
    """最近 N commit(老师 spec 变更追踪)"""
    if not (STARTUP_BUILDING_ROOT / ".git").exists():
        return []
    try:
        proc = subprocess.run(
            ["git", "-C", str(STARTUP_BUILDING_ROOT), "log",
             f"-n{n}", "--format=%h|%ad|%s", "--date=short"],
            capture_output=True, text=True, timeout=10,
        )
        if proc.returncode != 0:
            return []
        out = []
        for line in proc.stdout.splitlines():
            parts = line.split("|", 2)
            if len(parts) == 3:
                out.append({"sha": parts[0], "date": parts[1], "subject": parts[2]})
        return out
    except Exception:
        return []


def _list_zhiling_specs() -> list[str]:
    """33 Zhiling docx · 老师方法论日志(每个 spec 是一次 task)"""
    z = STARTUP_BUILDING_ROOT / "Zhiling" / "docx"
    if not z.exists():
        return []
    return sorted([p.name for p in z.glob("*.md")])


def detect_drift() -> dict:
    """对比上次 cache · 检测老师上游 drift

    返:{
      'has_drift': bool,
      'current_head': str,
      'last_head': str | None,
      'new_commits_count': int,
      'recent_commits': [...10],
      'zhiling_specs_count': int,
      'last_check_at': iso_str,
    }
    """
    current_head = _git_head_rev()
    cache = {}
    if _DRIFT_CACHE.exists():
        try:
            cache = json.loads(_DRIFT_CACHE.read_text())
        except Exception:
            cache = {}
    last_head = cache.get("last_head")
    has_drift = (current_head is not None and current_head != last_head)
    recent = _git_recent_commits(10)
    new_count = 0
    if has_drift and last_head:
        for c in recent:
            if c["sha"] == last_head[:7] or c["sha"] in last_head:
                break
            new_count += 1

    result = {
        "has_drift": has_drift,
        "current_head": current_head,
        "last_head": last_head,
        "new_commits_count": new_count,
        "recent_commits": recent,
        "zhiling_specs_count": len(_list_zhiling_specs()),
        "last_check_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    return result


def update_drift_cache(*, current_head: Optional[str] = None) -> bool:
    """worker review 老师变更后调此 · 更新 cache 防止重复告警"""
    if current_head is None:
        current_head = _git_head_rev()
    if not current_head:
        return False
    try:
        _DRIFT_CACHE.write_text(json.dumps({
            "last_head": current_head,
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }))
        return True
    except Exception:
        return False


def verify() -> dict:
    return {
        "git_available": _git_head_rev() is not None,
        "current_head": _git_head_rev(),
        "zhiling_specs_count": len(_list_zhiling_specs()),
        "drift_cache": str(_DRIFT_CACHE),
    }


if __name__ == "__main__":
    print(json.dumps(detect_drift(), indent=2, ensure_ascii=False))
