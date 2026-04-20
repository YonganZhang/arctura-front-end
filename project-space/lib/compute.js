// compute.js — 纯函数 · 根据 editable 字段派生 EUI / cost / compliance
// 服务端（Vercel Edge Function）权威实现；前端从 state.derived 读，不重算
// ESM · 可被 api/chat-edit.js 直接 import

// ───────── 基线常量 ─────────

// 各业态默认 HK$/m² 基础成本（简化模型，基于 baseline BOQ 实测值粗估）
export const BASE_COST_PER_M2 = {
  residential: 12000,
  hospitality: 13000,
  workplace: 9000,
  wellness: 13000,
  civic: 7000,
  other: 10000,
};

// 不同地区的成本系数（相对 HK）
export const REGION_COST_FACTOR = {
  HK: 1.0,
  CN: 0.32,     // 大陆成本约 HK 的 30%
  US: 1.08,
  JP: 1.15,
};

// Baseline editable（chat 未改时的默认）
export const BASELINE_EDITABLE = {
  area_m2: 40,
  insulation_mm: 60,
  glazing_uvalue: 2.0,
  lighting_cct: 3000,
  lighting_density_w_m2: 8,
  wwr: 0.25,
  region: "HK",
};

// 各合规地区阈值
export const COMPLIANCE_CODES = {
  HK: { name: "HK BEEO 2021", eui_max: 150, wall_u_max: 1.8, roof_u_max: 0.8, window_u_max: 5.8, lpd_max: 10 },
  CN: { name: "GB 55015-2021", eui_max: 140, wall_u_max: 1.5, roof_u_max: 0.7, window_u_max: 3.0, lpd_max: 9 },
  US: { name: "ASHRAE 90.1-2019", eui_max: 120, wall_u_max: 0.8, roof_u_max: 0.35, window_u_max: 2.4, lpd_max: 11 },
  JP: { name: "省エネ法 2025", eui_max: 100, wall_u_max: 0.6, roof_u_max: 0.3, window_u_max: 2.3, lpd_max: 8 },
};

// ───────── 辅助 ─────────

function num(x, d = 0) {
  const v = Number(x);
  return Number.isFinite(v) ? v : d;
}

function sanitize(e = {}) {
  return {
    area_m2: num(e.area_m2, BASELINE_EDITABLE.area_m2),
    insulation_mm: num(e.insulation_mm, BASELINE_EDITABLE.insulation_mm),
    glazing_uvalue: num(e.glazing_uvalue, BASELINE_EDITABLE.glazing_uvalue),
    lighting_cct: num(e.lighting_cct, BASELINE_EDITABLE.lighting_cct),
    lighting_density_w_m2: num(e.lighting_density_w_m2, BASELINE_EDITABLE.lighting_density_w_m2),
    wwr: num(e.wwr, BASELINE_EDITABLE.wwr),
    region: (e.region && COMPLIANCE_CODES[e.region]) ? e.region : "HK",
  };
}

// ───────── 公式 ─────────

// EUI 增量模型 · 相对 baseline 84 kWh/m²·yr
//   更厚保温 / 更低 U-value / 更低 CCT(warmer) / 更高 WWR / 更高灯密度 → EUI 变化
// 签名方向均符合物理：better envelope → lower EUI
export function recomputeEUI(editable) {
  const e = sanitize(editable);
  const BASELINE = 84;
  const d_insul = -(e.insulation_mm - 60) * 0.30;              // 每多 10mm 保温 → -3 EUI
  const d_glazing = (e.glazing_uvalue - 2.0) * 2.0;             // 每 +1 W/m²K U 值 → +2 EUI
  const d_wwr = (e.wwr - 0.25) * 100 * 0.35;                    // WWR 每 +1% → +0.35 EUI
  const d_cct = (3000 - e.lighting_cct) * 0.015;                // 每暖 100K → +1.5 EUI
  const d_light = (e.lighting_density_w_m2 - 8) * 1.5;          // 灯密度每 +1 W/m² → +1.5 EUI
  const eui = BASELINE + d_insul + d_glazing + d_wwr + d_cct + d_light;
  return Math.max(30, Math.round(eui * 10) / 10);
}

// 成本模型 · area × base_per_m2 × region × (premium factors)
// BOQ 展示的 6 个分档：direct subtotal · MEP(25%) · prelim(12%) · contingency(10%) · grand total
export function recomputeCost(editable, cat = "other") {
  const e = sanitize(editable);
  const base_per_m2 = BASE_COST_PER_M2[cat] || BASE_COST_PER_M2.other;
  const region_fac = REGION_COST_FACTOR[e.region] || 1.0;
  const insul_fac = 1 + (e.insulation_mm - 60) / 300;             // +1% 每 3mm
  const glazing_fac = 1 - (e.glazing_uvalue - 2.0) * 0.05;        // U 每降 1 → +5%
  const light_fac = 1 + (e.lighting_density_w_m2 - 8) * 0.004;    // 灯密度每 +1W → +0.4%
  const per_m2 = Math.max(500, base_per_m2 * region_fac * insul_fac * glazing_fac * light_fac);
  const total = per_m2 * e.area_m2;
  // BOQ 细项拆解：直接工程量 / MEP 25% / 前期 12% / 应急 10%（合计 1.47 系数）
  // 所以 direct_subtotal = total / 1.47
  const direct = total / 1.47;
  const mep = direct * 0.25;
  const prelim = direct * 0.12;
  const cont = direct * 0.10;
  const fmt = (n) => Math.round(n).toLocaleString();
  const currency = { HK: "HK$", CN: "¥", US: "US$", JP: "¥" }[e.region] || "HK$";
  return {
    currency,
    per_m2: Math.round(per_m2),
    total: Math.round(total),
    // 供 BOQ 表展示（字符串形式，带千分位）
    subtotal: fmt(direct),
    mep: fmt(mep),
    prelim: fmt(prelim),
    cont: fmt(cont),
    total_fmt: fmt(total),
    breakdown: {
      base: Math.round(base_per_m2 * region_fac * e.area_m2),
      insul_premium: Math.round((insul_fac - 1) * base_per_m2 * region_fac * e.area_m2),
      glazing_premium: Math.round((glazing_fac - 1) * base_per_m2 * region_fac * e.area_m2),
      light_premium: Math.round((light_fac - 1) * base_per_m2 * region_fac * e.area_m2),
    },
  };
}

// U-value 粗算 · 基于 XPS λ=0.035 W/mK 简化热阻模型
// U = 1 / R_total · R_total = 1/h_in + d/λ + 1/h_out + R_other
function computeWallU(insulation_mm) {
  const R_air_in = 1 / 8;
  const R_insul = (insulation_mm / 1000) / 0.035;
  const R_brick = 0.2 / 0.72;         // 200mm 砖墙
  const R_air_out = 1 / 25;
  return 1 / (R_air_in + R_insul + R_brick + R_air_out);
}

function computeRoofU(insulation_mm) {
  const R_air_in = 1 / 10;
  const R_insul = (insulation_mm / 1000) / 0.035;
  const R_slab = 0.12 / 2.3;          // RC 板 120mm
  const R_air_out = 1 / 25;
  return 1 / (R_air_in + R_insul + R_slab + R_air_out);
}

export function recomputeCompliance(editable) {
  const e = sanitize(editable);
  const code = COMPLIANCE_CODES[e.region] || COMPLIANCE_CODES.HK;
  const eui = recomputeEUI(e);
  const wall_u = computeWallU(e.insulation_mm);
  const roof_u = computeRoofU(e.insulation_mm);
  const window_u = e.glazing_uvalue;
  const lpd = e.lighting_density_w_m2;

  const items = [
    { check: "Energy Use Intensity (EUI)", value: eui, limit: code.eui_max, unit: "kWh/m²·yr",
      status: eui <= code.eui_max ? "pass" : "fail",
      note: `${Math.round(eui / code.eui_max * 100)}% of limit` },
    { check: "Exterior Wall U-value", value: Math.round(wall_u * 1000) / 1000, limit: code.wall_u_max, unit: "W/m²K",
      status: wall_u <= code.wall_u_max ? "pass" : "fail",
      note: "" },
    { check: "Roof U-value", value: Math.round(roof_u * 1000) / 1000, limit: code.roof_u_max, unit: "W/m²K",
      status: roof_u <= code.roof_u_max ? "pass" : "fail",
      note: "" },
    { check: "Window U-value", value: Math.round(window_u * 100) / 100, limit: code.window_u_max, unit: "W/m²K",
      status: window_u <= code.window_u_max ? "pass" : "fail",
      note: "" },
    { check: "Lighting Power Density", value: Math.round(lpd * 10) / 10, limit: code.lpd_max, unit: "W/m²",
      status: lpd <= code.lpd_max ? "pass" : "fail",
      note: "" },
  ];
  const fails = items.filter(i => i.status === "fail").length;
  const passes = items.filter(i => i.status === "pass").length;
  const verdict = fails === 0 ? "COMPLIANT" : `CONDITIONAL — ${fails} item${fails > 1 ? "s" : ""} need remediation`;
  const label = { HK: "HK · BEEO 2021", CN: "CN · GB 55015-2021", US: "US · ASHRAE 90.1-2019", JP: "JP · 省エネ法 2025" }[e.region] || code.name;
  return {
    region: e.region,
    code_name: code.name,
    label,
    items,
    checks: items,   // alias · 兼容组件读 C.checks
    verdict,
    fails,
    score: `${passes}/${items.length} passed`,
  };
}

// 一体化：根据 state.editable 刷新 derived / energy / pricing / compliance
export function recomputeAll(state) {
  const cat = state.cat || "other";
  const e = sanitize(state.editable);
  const eui = recomputeEUI(e);
  const cost = recomputeCost(e, cat);
  const comp = recomputeCompliance(e);
  const co2_t = Math.round(eui * e.area_m2 * 0.59 / 1000 * 100) / 100;
  const annual = Math.round(eui * e.area_m2);

  // Merge 不破坏别的 region 数据
  const pricing = { ...(state.pricing || {}) };
  pricing[e.region] = {
    ...(pricing[e.region] || {}),
    label: { HK: "Hong Kong", CN: "Mainland China", US: "United States", JP: "Japan" }[e.region] || e.region,
    currency: cost.currency,
    perM2: cost.per_m2,
    total: cost.total_fmt,            // 带千分位 "540,392"
    totalNumber: cost.total,           // 原始数字
    subtotal: cost.subtotal,
    mep: cost.mep,
    prelim: cost.prelim,
    cont: cost.cont,
    breakdown: cost.breakdown,
    rows: (pricing[e.region] || {}).rows || [],  // 保留 base rows（chat 不改 rows）
  };

  const compliance = { ...(state.compliance || {}) };
  compliance[e.region] = {
    ...(compliance[e.region] || {}),
    code: comp.code_name,
    label: comp.label,
    score: comp.score,
    checks: comp.items,
    items: comp.items,                // alias 兼容两种字段名
    verdict: comp.verdict,
  };

  return {
    ...state,
    editable: e,
    energy: { ...(state.energy || {}), eui, annual, limit: 150 },
    pricing,
    compliance,
    derived: {
      eui_kwh_m2_yr: eui,
      cost_total: cost.total,
      cost_per_m2: cost.per_m2,
      co2_t_per_yr: co2_t,
      compliance_fails: comp.fails,
      compliance_verdict: comp.verdict,
    },
  };
}
