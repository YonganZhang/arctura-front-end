"""老师 P0 Asset Intake 真编排 · 客户给 IFC/DXF/PDF/SVG/PNG/JPG → brief.json

按 playbooks/asset-intake-pipeline.md 真 spec(L1-540):
  Path A · 精确几何重建(IFC + DXF · 精确坐标)
  Path B · 视觉提取(PDF/PNG/JPG → brief 语义级)默认 Claude Code 直接看图
  Path SVG · Claude Code Read XML(零依赖最高精度)

Step 1 格式识别 → Step 1.5 Vision / 1.6 DXF / 1.7 SVG → Step 2 IFC 转换 →
Step 3 audit-ifc → Step 4 enrich-ifc → Step 5 反推 brief → Step 6 路由

我们 thin orchestrator 调老师 asset_intake_runner + blender CLI · 0 算法重写。
"""
from __future__ import annotations
import json, time
from pathlib import Path
from typing import Callable, Optional

from .asset_intake_runner import dxf_extract


def detect_input_kind(input_path: Path) -> str:
    """老师 Step 1 · 格式识别"""
    ext = input_path.suffix.lower()
    if ext == ".ifc":
        return "ifc"
    if ext == ".dxf":
        return "dxf"
    if ext == ".svg":
        return "svg"
    if ext in (".pdf",):
        return "pdf"
    if ext in (".png", ".jpg", ".jpeg", ".webp"):
        return "image"
    return "unknown"


def run_p0_intake(
    input_path: Path,
    output_dir: Path,
    *,
    region_code: str = "HK",
    on_event: Optional[Callable] = None,
) -> dict:
    """老师 P0 6 步真编排 · 自动按文件类型分支"""
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    kind = detect_input_kind(input_path)

    if on_event:
        on_event("p0_intake_start", {
            "input": str(input_path), "output_dir": str(output_dir),
            "kind": kind, "region": region_code,
        })

    if kind == "dxf":
        # Step 1.6 · DXF → brief + IFC(老师 dxf_extract.py)
        result = dxf_extract(input_path, output_dir, code=region_code)
        return {
            "ok": result.get("ok", False),
            "kind": kind, "path": "dxf_extract",
            "duration_ms": int((time.time() - t0) * 1000),
            "output_dir": str(output_dir),
            "stderr_tail": result.get("stderr_tail", ""),
        }

    if kind in ("pdf", "image"):
        # Step 1.5 · Vision Path B · 老师默认 = Claude Code 直接看图(LLM 上层处理)
        # 我们这里只是返"该让 Claude/前端 vision 处理"提示 · 不直接 subprocess
        if on_event:
            on_event("p0_path_b_vision", {
                "input": str(input_path),
                "policy": "Claude Code Read 直接看图(老师默认)· 上层 LLM 处理",
            })
        return {
            "ok": True, "kind": kind, "path": "vision_b_claude_native",
            "duration_ms": int((time.time() - t0) * 1000),
            "next_action": "前端调 LLM Read 图片 → 提取 brief.json",
        }

    if kind == "svg":
        # Step 1.7 · SVG XML 直读(老师推荐 · 最高精度)
        if on_event:
            on_event("p0_path_svg_xml_read", {
                "input": str(input_path),
                "policy": "Claude Code Read XML 提取精确坐标 · 上层 LLM 处理",
            })
        return {
            "ok": True, "kind": "svg", "path": "svg_xml_native",
            "duration_ms": int((time.time() - t0) * 1000),
            "next_action": "前端调 LLM Read SVG XML → 提取 brief + 可选 IFC",
        }

    if kind == "ifc":
        # Step 2 · IFC 已是终态 · 直接进 audit-ifc(可选 enrich)
        return {
            "ok": True, "kind": "ifc", "path": "ifc_passthrough",
            "duration_ms": int((time.time() - t0) * 1000),
            "next_action": "blender model audit-ifc + enrich-ifc(老师 P5 流程)",
        }

    return {"ok": False, "kind": "unknown",
            "error": f"老师 P0 不支持: {input_path.suffix}",
            "duration_ms": int((time.time() - t0) * 1000)}


def verify_runner() -> dict:
    """P0 自检"""
    from .asset_intake_runner import verify_runner as _air
    return {
        "supported_kinds": ["ifc", "dxf", "svg", "pdf", "image"],
        "asset_intake_clis": _air(),
    }


if __name__ == "__main__":
    print(json.dumps(verify_runner(), indent=2, ensure_ascii=False))
