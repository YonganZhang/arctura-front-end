"""老师权威 SSOT loader · Phase 12.末.G

直接读老师 playbooks/{schemas,defaults,prompts,templates}/ 当 SSOT 用。
所有 LIGHT/FORMAL artifact 都该走这里读权威 · 不再 hardcode 自己的副本。

用户原话:"100% 以我老师的代码为权威 · 直接复制他的来用就行"
不再复制 · 直接 lazy-read · 老师上游升级 → 我们自动同步。
"""
from __future__ import annotations
import functools
import json
from pathlib import Path
from typing import Any, Optional

from ..paths import (
    PLAYBOOKS_SCHEMAS, PLAYBOOKS_DEFAULTS,
    PLAYBOOKS_PROMPTS, PLAYBOOKS_TEMPLATES,
    BIM_CATALOG_JSON,
)


# ───────── schemas/ · 3 真权威 schema ─────────

@functools.lru_cache(maxsize=8)
def load_schema(name: str) -> dict:
    """name ∈ {'brief-interior', 'brief-architecture', 'project'} · 返 jsonschema dict"""
    p = PLAYBOOKS_SCHEMAS / f"{name}.schema.json"
    if not p.exists():
        raise FileNotFoundError(f"老师 schema 缺: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def validate_brief(brief: dict, schema_name: str = "brief-interior") -> list[str]:
    """用老师 schema validate brief · 返错误列表(空 = 通过)"""
    try:
        import jsonschema
    except ImportError:
        return ["jsonschema 未装 · pip install jsonschema"]
    schema = load_schema(schema_name)
    errors = []
    validator = jsonschema.Draft7Validator(schema)
    for err in validator.iter_errors(brief):
        path = " → ".join(str(x) for x in err.absolute_path) or "(root)"
        errors.append(f"{path}: {err.message}")
    return errors


# ───────── defaults/ · 4 SSOT ─────────

@functools.lru_cache(maxsize=4)
def hk_market_defaults() -> dict:
    """HK 市场默认参数 · 9 业态预算/m²(low/mid/high)"""
    return json.loads((PLAYBOOKS_DEFAULTS / "hk_market.json").read_text())


def hk_budget_per_m2(business_type: str, level: str = "mid") -> Optional[int]:
    """业态 → HKD/m² · level ∈ {low,mid,high}"""
    d = hk_market_defaults().get("budget_per_m2_hkd", {})
    item = d.get(business_type) or d.get(business_type.lower())
    return item.get(level) if item else None


@functools.lru_cache(maxsize=1)
def region_code_map() -> dict:
    """统一 region/code/weather mapping(P3→P6→P7→P8)"""
    p = PLAYBOOKS_DEFAULTS / "region-code-map.yaml"
    if not p.exists():
        return {}
    try:
        import yaml
        return yaml.safe_load(p.read_text())
    except ImportError:
        return {"_error": "pyyaml 未装"}


@functools.lru_cache(maxsize=1)
def comparison_cameras() -> dict:
    """A/B/C 对比 cameras 统一配置 · variants_formal 应用"""
    return json.loads((PLAYBOOKS_DEFAULTS / "comparison-cameras.json").read_text())


@functools.lru_cache(maxsize=1)
def site_entourage_catalog() -> dict:
    """44 户外资产 + dimensions/clearance/calibrated · arch-mvp 配景"""
    return json.loads((PLAYBOOKS_DEFAULTS / "site-entourage-catalog.json").read_text())


# ───────── prompts/ · 5 LLM 真模板 ─────────

@functools.lru_cache(maxsize=8)
def llm_prompt(category: str, name: str) -> str:
    """category ∈ {brief-intake, asset-intake} · name ∈ {classify, from-text, turn-based, client-export-guide, vision-extract}"""
    p = PLAYBOOKS_PROMPTS / category / f"{name}.md"
    if not p.exists():
        raise FileNotFoundError(f"老师 prompt 缺: {p}")
    return p.read_text(encoding="utf-8")


# 便捷 alias
def prompt_classify_brief() -> str:
    return llm_prompt("brief-intake", "classify")

def prompt_brief_from_text() -> str:
    return llm_prompt("brief-intake", "from-text")

def prompt_brief_turn_based() -> str:
    return llm_prompt("brief-intake", "turn-based")

def prompt_vision_extract() -> str:
    return llm_prompt("asset-intake", "vision-extract")

def prompt_client_export_guide() -> str:
    return llm_prompt("asset-intake", "client-export-guide")


# ───────── templates/ · _render_script_footer ─────────

@functools.lru_cache(maxsize=1)
def render_script_footer() -> str:
    p = PLAYBOOKS_TEMPLATES / "_render_script_footer.py"
    return p.read_text(encoding="utf-8") if p.exists() else ""


# ───────── assets-furniture · BIM catalog ─────────

@functools.lru_cache(maxsize=1)
def bim_catalog() -> dict:
    """老师 BIM catalog(GLB 资产清单) · mesh-library Path A 必需"""
    if not BIM_CATALOG_JSON.exists():
        return {"_error": f"BIM catalog 缺: {BIM_CATALOG_JSON}"}
    return json.loads(BIM_CATALOG_JSON.read_text())


# ───────── 自检 ─────────

def verify_ssot() -> dict:
    """检查所有 SSOT 是否可读 · 调试用"""
    out = {}
    try:
        out["brief-interior schema"] = bool(load_schema("brief-interior"))
    except Exception as e:
        out["brief-interior schema"] = f"ERR: {e}"
    try:
        out["hk_market"] = f"{len(hk_market_defaults().get('budget_per_m2_hkd', {}))} 业态"
    except Exception as e:
        out["hk_market"] = f"ERR: {e}"
    try:
        out["comparison-cameras"] = f"{len(comparison_cameras())} 配置"
    except Exception as e:
        out["comparison-cameras"] = f"ERR: {e}"
    try:
        out["region-code-map"] = "ok" if region_code_map() else "缺"
    except Exception as e:
        out["region-code-map"] = f"ERR: {e}"
    try:
        out["site-entourage-catalog"] = f"{len(site_entourage_catalog().get('assets', {}))} 资产"
    except Exception as e:
        out["site-entourage-catalog"] = f"ERR: {e}"
    try:
        out["prompt classify"] = f"{len(prompt_classify_brief())} chars"
    except Exception as e:
        out["prompt classify"] = f"ERR: {e}"
    try:
        bc = bim_catalog()
        out["bim_catalog"] = f"{len(bc.get('items', bc.get('assets', [])))} 条" if "_error" not in bc else bc["_error"]
    except Exception as e:
        out["bim_catalog"] = f"ERR: {e}"
    return out


if __name__ == "__main__":
    import json as _j
    print(_j.dumps(verify_ssot(), indent=2, ensure_ascii=False))
