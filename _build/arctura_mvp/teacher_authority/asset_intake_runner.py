"""asset-intake thin runner · P0 客户文件入口(老师 playbooks/scripts/asset-intake/)

老师 2 真 CLI:
  dxf_extract.py <input.dxf> -o <output_dir> [--code HK]   · DXF → brief + IFC
  vision_extract.py(Claude Vision Path B · prompt-driven)

跟 mesh_library_runner / site_entourage_runner 同模式 · 0 算法 · subprocess 直调。
"""
from __future__ import annotations
import subprocess, sys, time
from pathlib import Path

from ..paths import PLAYBOOKS_SCRIPTS

_AI = PLAYBOOKS_SCRIPTS / "asset-intake"
_PY = sys.executable


def _run(step: str, cmd: list, *, timeout: int = 300) -> dict:
    t0 = time.time()
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return {"step": step, "ok": proc.returncode == 0,
                "duration_ms": int((time.time() - t0) * 1000),
                "stdout_tail": (proc.stdout or "")[-300:],
                "stderr_tail": (proc.stderr or "")[-300:]}
    except Exception as e:
        return {"step": step, "ok": False,
                "duration_ms": int((time.time() - t0) * 1000),
                "stderr_tail": str(e)[:300]}


def dxf_extract(input_dxf: Path, output_dir: Path, *, code: str = "HK") -> dict:
    """P0 · DXF → brief.json + IFC(老师真 CLI)"""
    output_dir.mkdir(parents=True, exist_ok=True)
    return _run("dxf_extract",
                [_PY, str(_AI / "dxf_extract.py"), str(input_dxf),
                 "-o", str(output_dir), "--code", code],
                timeout=180)


def vision_extract_prompt() -> str:
    """老师 Path B vision 提取 prompt(Claude Vision · 用户给前端调 LLM)"""
    p = _AI / "vision_extract.py"
    if not p.exists():
        return ""
    # vision_extract 不是 CLI · 是 prompt 模板代码 · 我们读它的 PROMPT 常量
    text = p.read_text(encoding="utf-8")
    # 简单提取(老师可能定义 PROMPT 常量)
    return text


def verify_runner() -> dict:
    return {
        "dxf_extract":     (_AI / "dxf_extract.py").exists(),
        "vision_extract":  (_AI / "vision_extract.py").exists(),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(verify_runner(), indent=2, ensure_ascii=False))
