"""老师 llm_intake_cli thin runner · brief-intake 真权威入口

老师真 CLI(cli_anything.llm_intake.llm_intake_cli):
  classify   --input "<客户原话>"                                · 室内 vs 建筑
  from-text  --schema <schema> --input "<text>" -o <brief.json>  · 一次性产 brief
  turn-based --schema <schema> -o <brief.json>                   · 多轮对话补全
  validate   --schema <schema> --input <brief.json>              · 校验 brief

我们 brief-chat 应该真接老师 turn_based · 不只读 prompt md。
0 算法 · 0 wrapper 重写 · subprocess 直调。
"""
from __future__ import annotations
import subprocess, sys, time
from pathlib import Path
from typing import Optional

from ..paths import PLAYBOOKS_SCHEMAS

_PY = sys.executable
_CLI_MOD = "cli_anything.llm_intake.llm_intake_cli"


def _run(step: str, args: list, *, input_text: Optional[str] = None,
         timeout: int = 60) -> dict:
    cmd = [_PY, "-m", _CLI_MOD] + args
    t0 = time.time()
    try:
        proc = subprocess.run(
            cmd, input=input_text, capture_output=True, text=True, timeout=timeout,
        )
        return {
            "step": step, "ok": proc.returncode == 0,
            "duration_ms": int((time.time() - t0) * 1000),
            "stdout_tail": (proc.stdout or "")[-1000:],
            "stderr_tail": (proc.stderr or "")[-300:],
        }
    except Exception as e:
        return {"step": step, "ok": False,
                "duration_ms": int((time.time() - t0) * 1000),
                "stderr_tail": str(e)[:300]}


def classify(user_text: str) -> dict:
    """老师 classify · 客户原话 → interior/architecture"""
    return _run("classify", ["classify", "--input", user_text], timeout=30)


def from_text(user_text: str, output_path: Path,
              *, schema: str = "brief-interior") -> dict:
    """从自由文本一次性产 brief.json(老师 from-text 子命令)"""
    schema_path = PLAYBOOKS_SCHEMAS / f"{schema}.schema.json"
    return _run("from_text",
                ["from-text", "--schema", str(schema_path),
                 "--input", user_text, "-o", str(output_path)],
                timeout=120)


def validate_brief_via_cli(brief_path: Path,
                           *, schema: str = "brief-interior") -> dict:
    """用老师 validate 子命令 · jsonschema 校验 brief"""
    schema_path = PLAYBOOKS_SCHEMAS / f"{schema}.schema.json"
    return _run("validate",
                ["validate", "--schema", str(schema_path),
                 "--input", str(brief_path)],
                timeout=15)


def verify_runner() -> dict:
    """检查老师 llm_intake_cli 是否真可调"""
    try:
        proc = subprocess.run([_PY, "-m", _CLI_MOD, "--help"],
                              capture_output=True, text=True, timeout=10)
        return {
            "module_callable": proc.returncode == 0,
            "help_tail": (proc.stdout or proc.stderr or "")[-200:],
        }
    except Exception as e:
        return {"module_callable": False, "error": str(e)[:200]}


if __name__ == "__main__":
    import json
    print(json.dumps(verify_runner(), indent=2, ensure_ascii=False))
