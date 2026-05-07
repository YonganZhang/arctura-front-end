"""verify_mvp_exports thin runner · 老师 gate · 全案 done 前必跑

老师真 CLI(playbooks/scripts/verify_mvp_exports.py):
  $PY verify_mvp_exports.py <mvp-dir> [--tier concept|delivery|quote|full|selection]
退出码:0 = 通过 / 1 = 有 required 项缺失

老师 CLAUDE.md L521-560 关键产物必含:
  - brief.json / moodboard.png / room.json (or building.json)
  - renders ≥6 (Path A 6 张 / Path B 8 张 · 至少 01_hero_corner.png)
  - floorplan.svg + .png(必须手画 · floorplan_pro 仅 mockup)
  - exports 5 格式: GLB + OBJ + FBX + IFC raw + IFC enriched
  - decks/deck-client.{md,pptx,pdf}
  - CLIENT-README.md
  - energy/{project.json, compliance-*.md, boq-*.md, .csv}
  - case-study/ 7+ 文件: portfolio.md + impact.md + sales.md + metrics.json +
                         narrative-{portfolio,impact,sales}.txt + thumbs/
"""
from __future__ import annotations
import subprocess, sys, time
from pathlib import Path

from ..paths import PLAYBOOKS_SCRIPTS

_VERIFY = PLAYBOOKS_SCRIPTS / "verify_mvp_exports.py"
_PY = sys.executable


def verify_mvp(mvp_dir: Path, *, tier: str = "full") -> dict:
    """跑老师 verify_mvp_exports.py · 返 {ok, returncode, stdout, missing}"""
    t0 = time.time()
    if not _VERIFY.exists():
        return {"ok": False, "error": f"老师 verify_mvp_exports.py 缺: {_VERIFY}"}
    try:
        proc = subprocess.run(
            [_PY, str(_VERIFY), str(mvp_dir), "--tier", tier],
            capture_output=True, text=True, timeout=30,
        )
        # 解析 stdout 找 missing / 通过 项
        lines = (proc.stdout or "").splitlines()
        missing = [l.strip() for l in lines if "missing" in l.lower() or "✗" in l or "🔴" in l]
        return {
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "tier": tier,
            "duration_ms": int((time.time() - t0) * 1000),
            "missing_summary": missing[:20],
            "stdout_tail": (proc.stdout or "")[-1000:],
            "stderr_tail": (proc.stderr or "")[-300:],
        }
    except Exception as e:
        return {"ok": False, "error": str(e)[:300]}


def verify_runner() -> dict:
    return {"verify_mvp_exports.py": _VERIFY.exists()}


if __name__ == "__main__":
    import json
    print(json.dumps(verify_runner(), indent=2))
