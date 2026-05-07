"""老师 change-impact-matrix 真权威表 parser

老师 playbooks/change-impact-matrix.md 是真权威速查:客户改需求 → 重跑哪些 pipeline。
我们 chat-edit / scene-ops 应该真用此表 · 不自己 hardcode。
0 算法重写 · 解析老师 markdown 表 → 给上层用。
"""
from __future__ import annotations
import functools
import re
from pathlib import Path
from typing import Optional

from ..paths import PLAYBOOKS_ROOT


_MATRIX_MD = PLAYBOOKS_ROOT / "change-impact-matrix.md"

# P1 表头 pipeline 列(从老师 markdown 表头解析)
_P1_PIPELINES = [
    "P0_intake", "P3_brief", "P1_3d", "P5_asset", "render", "floorplan",
    "ifc_export", "P7_energy", "P8_compliance", "P6_boq",
    "P4_ai_render", "P10_variants", "P11_case_study",
]

# P2 简化列
_P2_PIPELINES = [
    "P2_modeling", "render", "elev_section", "ifc_export",
    "P7_energy", "P8_compliance", "P6_boq", "P11_case_study",
]


def _parse_row(line: str) -> Optional[dict]:
    """parse 老师表行 · 返 {category, example, brief_field, pipelines: [...], duration}"""
    cells = [c.strip() for c in line.split("|")[1:-1]]
    if len(cells) < 5:
        return None
    cat = re.sub(r"\*\*", "", cells[0]).strip()
    if not cat or cat in ("变更类别",) or "----" in cat:
        return None
    return {
        "category": cat,
        "example": cells[1],
        "brief_field": cells[2],
        "raw_cells": cells,
        "duration": cells[-1],
    }


@functools.lru_cache(maxsize=2)
def parse_matrix(profile: str = "P1") -> list[dict]:
    """parse 老师 markdown 表 · 返按 profile 的 row 列表 · 每 row 含 pipelines 重跑标记"""
    if not _MATRIX_MD.exists():
        return []
    text = _MATRIX_MD.read_text(encoding="utf-8")

    if profile == "P1":
        section_re = r"## Impact Matrix — 室内设计 \(P1\)(.*?)## Impact Matrix — 建筑设计"
        pipelines = _P1_PIPELINES
    elif profile == "P2":
        section_re = r"## Impact Matrix — 建筑设计 \(P2\)(.*?)## 依赖链速查"
        pipelines = _P2_PIPELINES
    else:
        return []

    m = re.search(section_re, text, re.S)
    if not m:
        return []
    section = m.group(1)

    rows = []
    for line in section.splitlines():
        if not line.startswith("|") or ":-" in line or "变更类别" in line:
            continue
        row = _parse_row(line)
        if not row:
            continue
        # 抽 pipeline 标记列(去掉前 3 列 + 最后 1 列耗时)
        cells = row["raw_cells"]
        marks = cells[3:-1]
        if len(marks) >= len(pipelines):
            marks = marks[:len(pipelines)]
        else:
            marks = marks + ["—"] * (len(pipelines) - len(marks))
        row["pipelines"] = {p: _classify_mark(marks[i]) for i, p in enumerate(pipelines)}
        rows.append(row)
    return rows


def _classify_mark(mark: str) -> str:
    """老师标记 → 标准 enum"""
    mark = mark.strip()
    if "✅" in mark:
        return "rerun"
    elif "按需" in mark:
        return "on_demand"
    elif "—" in mark or not mark:
        return "skip"
    elif "改坐标" in mark or "改对象" in mark:
        return "rerun"  # 老师写"改坐标" = 还是要改 3D 模型
    else:
        return "rerun"  # 默认保守


def pipelines_to_rerun(category: str, *, profile: str = "P1") -> dict:
    """给定客户改类(中文 category)· 返 {must_rerun: [...], on_demand: [...], skip: [...], duration}

    上层 chat-edit / scene-ops 用此函数智能决定重跑范围。
    """
    rows = parse_matrix(profile)
    for row in rows:
        if category in row["category"] or row["category"] in category:
            must_rerun = [p for p, v in row["pipelines"].items() if v == "rerun"]
            on_demand = [p for p, v in row["pipelines"].items() if v == "on_demand"]
            skip = [p for p, v in row["pipelines"].items() if v == "skip"]
            return {
                "category": row["category"],
                "example": row["example"],
                "duration": row["duration"],
                "must_rerun": must_rerun,
                "on_demand": on_demand,
                "skip": skip,
            }
    return {"_error": f"未知 category: {category}", "_known": [r["category"] for r in rows]}


def all_categories(profile: str = "P1") -> list[str]:
    """老师真权威所有变更类别清单 · UI 给用户选时用"""
    return [r["category"] for r in parse_matrix(profile)]


def verify() -> dict:
    return {
        "matrix_exists": _MATRIX_MD.exists(),
        "P1_rows": len(parse_matrix("P1")),
        "P2_rows": len(parse_matrix("P2")),
        "P1_categories": all_categories("P1"),
        "P2_categories": all_categories("P2"),
    }


if __name__ == "__main__":
    import json
    info = verify()
    print(json.dumps(info, indent=2, ensure_ascii=False))
    print()
    # 演示:客户说"换橡木地板" → 决定重跑范围
    r = pipelines_to_rerun("材质/颜色")
    print("演示:客户说'换橡木地板' →")
    print(json.dumps(r, indent=2, ensure_ascii=False))
