"""Phase 9.4 · materializer.py 单测 · 喂真 smoke MVP 目录 · 验证输出 schema + 关键字段非空"""
from __future__ import annotations
from pathlib import Path
import pytest

from _build.arctura_mvp.materializer import (
    build_fe_payload,
    parse_boq_md,
    parse_compliance_md,
    list_renders,
    list_fe_renders,
    categorize_mvp,
    default_editable,
)


REPO_ROOT = Path(__file__).resolve().parents[3]  # Arctura-Front-end/
SB_ROOT = REPO_ROOT.parent / "StartUP-Building"
SMOKE_SLUG = "smoke-ep-202886"   # Phase 9.3 产的 smoke MVP（hotel lobby · full 档）
SMOKE_DIR = SB_ROOT / "studio-demo" / "mvp" / SMOKE_SLUG


pytestmark = pytest.mark.skipif(
    not SMOKE_DIR.is_dir(),
    reason=f"smoke MVP {SMOKE_SLUG} 不存在 · 跑 E2E 生成 or update SMOKE_SLUG",
)


def test_build_fe_payload_schema():
    """payload 必须有前端 app.jsx 消费的 top-level key"""
    payload = build_fe_payload(SMOKE_DIR, SMOKE_SLUG, REPO_ROOT, mvp_type="P1-interior", agg={})
    required_keys = {
        "slug", "cat", "type", "complete", "project",
        "renders", "floorplan", "moodboard", "hero_img",
        "zones", "pricing", "energy", "compliance",
        "variants", "decks", "downloads", "editable", "derived",
    }
    missing = required_keys - set(payload.keys())
    assert not missing, f"payload 缺 key: {missing}"


def test_build_fe_payload_real_data():
    """Phase 9.3 smoke · 关键字段非占位"""
    payload = build_fe_payload(SMOKE_DIR, SMOKE_SLUG, REPO_ROOT, mvp_type="P1-interior", agg={})
    # renders 真有（磁盘 + fe_root assets）
    assert len(payload["renders"]) >= 6, f"renders={len(payload['renders'])} < 6"
    # decks PPT/PDF 至少 1 个
    assert len(payload["decks"]) >= 1, f"decks={len(payload['decks'])}"
    # downloads (bundle + exports + energy csv + client-readme)
    assert len(payload["downloads"]) >= 3, f"downloads={len(payload['downloads'])}"
    # energy.eui 真数字 · 不是 45 占位
    eui = payload["energy"]["eui"]
    assert eui and eui != 45, f"energy.eui={eui} 疑似占位"
    # compliance checks
    checks = payload["compliance"]["HK"]["checks"]
    assert len(checks) >= 5, f"compliance checks={len(checks)}"
    # pricing rows
    rows = payload["pricing"]["HK"]["rows"]
    assert len(rows) >= 3, f"pricing rows={len(rows)}"


def test_parse_boq_md_basic():
    md = """# BOQ

| 分类 | 说明 | 子项 | 数量 | 金额 |
|---|---|---|---|---|
| 地面 | 实木地板 | 40m² | 40 | 24,000 |
| 墙面 | 乳胶漆 | 120m² | 120 | 6,000 |
"""
    rows, total, currency = parse_boq_md(md)
    assert len(rows) == 2
    assert total == 30000
    assert currency == "HK$"


def test_parse_compliance_md_basic():
    md = """# Compliance

| Check | Value | Limit | Unit | Status | Note |
|---|---|---|---|---|---|
| LPD | 8 | 10 | W/m² | ✅ | pass |
| EUI | 46 | 150 | kWh/m²·yr | ⚠️ | advisory |
"""
    checks = parse_compliance_md(md)
    assert len(checks) == 2
    assert checks[0]["status"] == "pass"
    assert checks[1]["status"] == "advisory"


def test_categorize_mvp_wellness():
    assert categorize_mvp({"slug": "05-fitness-studio"}) == "wellness"
    assert categorize_mvp({"slug": "10-dental-clinic"}) == "wellness"


def test_categorize_mvp_hospitality():
    assert categorize_mvp({"slug": "14-central-japanese-coffee-bakery"}) == "hospitality"


def test_default_editable():
    e = default_editable("workplace", 50)
    assert e["area_m2"] == 50
    assert e["lighting_density_w_m2"] == 9
    assert e["region"] == "HK"


def test_list_fe_renders_empty_ok():
    """fe_root 下没 renders 目录时 · 返空 list 不抛"""
    result = list_fe_renders(REPO_ROOT, "slug-that-doesnt-exist-1a2b3c")
    assert result == []
