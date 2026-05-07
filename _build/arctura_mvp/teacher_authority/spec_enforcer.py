"""老师 spec_lock 真 enforce 进 worker/api · 不只锁定 · 真用

按 spec_lock.py 不变量:
  - REQUIRED_ARTIFACTS_FULL_TIER · 21 必含 · enforce 全案 done 前必查
  - REQUIRED_CASE_STUDY_FILES · 7+ 必含
  - STAKEHOLDER_HERO_IMAGE · 8 真映射 · enforce deck 时按 stakeholder 选 hero
  - RENDER_PATH_SPEC · Path A=6 / B=8 · enforce render count
  - COMPLIANCE_CODES · 5 法规 · enforce P8
  - EUI_IS_ADVISORY=True · enforce P8 不当硬指标

0 算法重写 · 仅 gate · 配 spec_lock 数据驱动。
"""
from __future__ import annotations
from pathlib import Path
from typing import Optional

from . import spec_lock


class SpecLockViolation(Exception):
    """spec 违反 · 阻断 worker 流程"""
    pass


def enforce_full_tier_completeness(mvp_dir: Path, *, raise_on_fail: bool = False) -> dict:
    """worker 全案 done 前必跑 · 不通过 raise 或返 missing"""
    r = spec_lock.is_full_tier_complete(Path(mvp_dir))
    if not r["ok"] and raise_on_fail:
        raise SpecLockViolation(
            f"全案不完整 · missing {len(r['missing'])} 项: {r['missing'][:5]}"
        )
    return r


def enforce_render_count(mvp_dir: Path, render_path: str, *,
                         raise_on_fail: bool = False) -> dict:
    """Path A 必 6 张 / Path B 必 8 张 · 老师 spec 不变量"""
    expected = spec_lock.expected_render_count(render_path)
    renders = sorted((Path(mvp_dir) / "renders").glob("*.png"))
    actual = len(renders)
    ok = actual >= expected
    result = {"ok": ok, "expected": expected, "actual": actual,
              "render_path": render_path}
    if not ok and raise_on_fail:
        raise SpecLockViolation(
            f"render path={render_path} 应 ≥{expected} 张 · 实 {actual}"
        )
    return result


def enforce_stakeholder_hero(stakeholder: str) -> str:
    """8 stakeholder · 老师真 hero image 路径(deck 生成时按 stakeholder 选)"""
    return spec_lock.get_stakeholder_hero(stakeholder)


def enforce_compliance_code(code: str, *, raise_on_fail: bool = False) -> dict:
    """老师 P8 · 5 法规之一 · EUI 全 advisory"""
    valid = code in spec_lock.COMPLIANCE_CODES
    if not valid and raise_on_fail:
        raise SpecLockViolation(
            f"compliance code={code} 不在老师 5 法规: {spec_lock.COMPLIANCE_CODES}"
        )
    return {"ok": valid, "code": code, "is_advisory": spec_lock.EUI_IS_ADVISORY,
            "valid_codes": spec_lock.COMPLIANCE_CODES}


def enforce_case_study_files(mvp_dir: Path, *, raise_on_fail: bool = False) -> dict:
    """老师 case-study/ 必 7+ 文件(portfolio/impact/sales md + metrics.json + 3 narrative + thumbs)"""
    cs = Path(mvp_dir) / "case-study"
    if not cs.exists():
        if raise_on_fail:
            raise SpecLockViolation(f"case-study/ 不存在: {cs}")
        return {"ok": False, "missing": spec_lock.REQUIRED_CASE_STUDY_FILES}
    missing = [f for f in spec_lock.REQUIRED_CASE_STUDY_FILES
               if not (cs / f).exists()]
    ok = not missing
    if not ok and raise_on_fail:
        raise SpecLockViolation(f"case-study 缺: {missing}")
    return {"ok": ok, "missing": missing}


def enforce_change_category(category: str, *,
                            raise_on_fail: bool = False) -> dict:
    """老师 change-impact-matrix 15 类 · UI/chat-edit 选时校验"""
    valid = category in spec_lock.CLIENT_CHANGE_CATEGORIES
    if not valid and raise_on_fail:
        raise SpecLockViolation(
            f"change category={category} 不在老师 15 类: {spec_lock.CLIENT_CHANGE_CATEGORIES}"
        )
    return {"ok": valid, "category": category,
            "valid_categories": spec_lock.CLIENT_CHANGE_CATEGORIES}


def all_enforcers_summary(mvp_dir: Path) -> dict:
    """worker 全案 done 前一锅过 · 返完整 enforce 结果"""
    return {
        "full_tier_completeness": enforce_full_tier_completeness(mvp_dir),
        "case_study_files": enforce_case_study_files(mvp_dir),
        "tier_spec": spec_lock.TIER_SPEC,
        "compliance_codes": spec_lock.COMPLIANCE_CODES,
        "eui_is_advisory": spec_lock.EUI_IS_ADVISORY,
    }
