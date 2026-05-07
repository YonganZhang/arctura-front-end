"""老师 change-impact-matrix 接 chat-edit · 智能重跑

按 change_impact.py(老师真权威 markdown 表 parser):
  客户改"材质/颜色" → 重跑 render + boq + case-study(3 个 ~1min)
  客户改"房间尺寸" → 重跑 7+ 个(~5min · 全 pipeline)
  客户改"合规标准" → 仅 P8(~30s)

我们 chat-edit 收到 op 后 · 调此 helper 决定重跑哪些 artifact · 替代一刀切。
"""
from __future__ import annotations
from typing import Optional

from .change_impact import pipelines_to_rerun, all_categories


# 老师 pipeline_name → 我们 artifact_name 映射(把 pipeline 名映到 artifact)
_PIPELINE_TO_ARTIFACT = {
    "P1_3d": "scene",
    "P5_asset": "scene",  # Path A asset 也是 scene
    "render": "renders",
    "floorplan": "floorplan",
    "ifc_export": "exports",
    "P7_energy": "energy_report",
    "P8_compliance": "energy_report",  # compliance 在 energy_report 内
    "P6_boq": "energy_report",
    "P4_ai_render": "ai_renders",
    "P10_variants": "variants",
    "P11_case_study": "case_study",
    "P3_brief": None,  # brief 不重跑 artifact · chat-edit 直接改
    "P0_intake": None,
}


def smart_rerun_for_op(op_category: str, *, profile: str = "P1") -> dict:
    """给定客户 op 类(老师 15 类之一)· 返我们应重跑的 artifact 清单

    返:{
      'category', 'must_artifacts', 'on_demand_artifacts', 'skip_artifacts',
      'duration_estimate', 'pipelines'
    }
    """
    r = pipelines_to_rerun(op_category, profile=profile)
    if "_error" in r:
        return r

    def _to_artifacts(pipeline_list: list) -> list:
        out = set()
        for p in pipeline_list:
            a = _PIPELINE_TO_ARTIFACT.get(p)
            if a:
                out.add(a)
        return sorted(out)

    return {
        "category": r["category"],
        "duration_estimate": r["duration"],
        "must_artifacts": _to_artifacts(r["must_rerun"]),
        "on_demand_artifacts": _to_artifacts(r["on_demand"]),
        "skip_artifacts": _to_artifacts(r["skip"]),
        "raw_pipelines": {
            "must": r["must_rerun"],
            "on_demand": r["on_demand"],
            "skip": r["skip"],
        },
    }


def detect_change_category(op: dict) -> Optional[str]:
    """从 chat-edit op 推断变更类(返 15 类之一或 None)

    op 例:{"type": "set_palette", "value": ["#fff", ...]}
       → "材质/颜色"
       op:{"type": "move_furniture", "id": "...", "to": [x,y]}
       → "家具位置"
    """
    op_type = (op.get("type") or "").lower()
    # 老师 15 类映射(基于 op 名)
    mapping = {
        "set_palette": "材质/颜色",
        "set_material": "材质/颜色",
        "set_color": "材质/颜色",
        "move_furniture": "家具位置",
        "rotate_furniture": "家具位置",
        "add_furniture": "家具增删",
        "remove_furniture": "家具增删",
        "set_lighting": "灯光氛围",
        "set_zone_area": "功能区调整",
        "set_room_dims": "房间尺寸",
        "set_area_sqm": "房间尺寸",
        "set_style_keywords": "风格大改",
        "set_render_path": "换渲染风格",
        "set_hvac": "HVAC/设备",
        "set_envelope": "围护结构",
        "set_compliance_code": "合规标准",
        "set_region": "报价地区",
        "upload_file": "新文件",
        "set_brief_text": "只改描述",
        "request_variants": "要第 2/3 方案",
    }
    return mapping.get(op_type)


def smart_rerun_for_chat_edit(op: dict, *, profile: str = "P1") -> dict:
    """完整 chat-edit smart rerun · op → 老师权威重跑范围"""
    category = detect_change_category(op)
    if not category:
        return {
            "_warning": f"op type '{op.get('type')}' 不在老师 15 类 · 默认全重跑",
            "must_artifacts": ["scene", "renders", "floorplan",
                               "energy_report", "case_study"],  # 保守默认
            "category": None,
        }
    return smart_rerun_for_op(category, profile=profile)


def get_all_categories() -> list[str]:
    """老师真权威 15 客户改类(给 UI 用)"""
    return all_categories("P1")
