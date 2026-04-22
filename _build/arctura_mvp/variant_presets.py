"""3 档套餐共享常量 · 单一真源
修这里 · create_mvp_from_brief + materialize_full_mvp + diff-matrix 自动同步。
修复 2026-04-22 子智能体审查指出的 "三处硬编码" 问题。
"""

VARIANT_PRESETS = [
    {
        "id": "v1-essential",
        "name": "v1",
        "name_zh": "基础方案",
        "price_delta_pct": -25,
        "eui_delta": +5,
        "edit_override": {"insulation_mm": 40, "lighting_density_w_m2": 10},
        "tagline_zh": "核心家具齐全 · 成本优先",
        "annual_maintenance_HKD": 4000,
        "positioning": "预算紧张 · 分校 / 分校区",
    },
    {
        "id": "v2-standard",
        "name": "v2",
        "name_zh": "标准方案",
        "price_delta_pct": 0,
        "eui_delta": 0,
        "edit_override": {},
        "tagline_zh": "标准配置 · 含接待/陈列区 · 品质均衡",
        "annual_maintenance_HKD": 6000,
        "positioning": "主校区标准 · 功能 + 品味均衡（推荐）",
    },
    {
        "id": "v3-premium",
        "name": "v3",
        "name_zh": "高端方案",
        "price_delta_pct": +50,
        "eui_delta": -8,
        "edit_override": {"insulation_mm": 100, "lighting_density_w_m2": 6, "glazing_uvalue": 1.2},
        "tagline_zh": "整面陈列墙 + 软包升级 + 定制灯具",
        "annual_maintenance_HKD": 9000,
        "positioning": "品牌旗舰 · 接待校董 / 外宾",
    },
]


def desc_for(v, project_name):
    return f"{project_name} · {v['tagline_zh']}"


def compute_price(v, base_budget):
    return int(base_budget * (1 + v["price_delta_pct"] / 100))


def compute_eui(v, base_eui):
    return base_eui + v["eui_delta"]
