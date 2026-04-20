// 单测 · node --test project-space/lib/compute.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import {
  recomputeEUI,
  recomputeCost,
  recomputeCompliance,
  recomputeAll,
  BASELINE_EDITABLE,
} from "./compute.js";

test("recomputeEUI: baseline 返回 84", () => {
  assert.equal(recomputeEUI(BASELINE_EDITABLE), 84);
});

test("recomputeEUI: 保温加厚 60→100mm 降 ~12 EUI", () => {
  const e = { ...BASELINE_EDITABLE, insulation_mm: 100 };
  const eui = recomputeEUI(e);
  assert.ok(eui < 84 - 8, `expected significant drop, got ${eui}`);
  assert.ok(eui > 84 - 16, `expected not too drastic, got ${eui}`);
});

test("recomputeEUI: CCT 变暖（3000→2700）EUI 略升", () => {
  const warm = recomputeEUI({ ...BASELINE_EDITABLE, lighting_cct: 2700 });
  const neutral = recomputeEUI(BASELINE_EDITABLE);
  assert.ok(warm > neutral, `warm=${warm} should be > neutral=${neutral}`);
  assert.ok(warm - neutral < 10, "not too extreme");
});

test("recomputeEUI: 更好玻璃（U 2.0→1.2）降 EUI", () => {
  const better = recomputeEUI({ ...BASELINE_EDITABLE, glazing_uvalue: 1.2 });
  const baseline = recomputeEUI(BASELINE_EDITABLE);
  assert.ok(better < baseline, `better glazing should reduce EUI: ${better} vs ${baseline}`);
});

test("recomputeEUI: 下限 30（极端好的情况也不低于 30）", () => {
  const extreme = recomputeEUI({
    ...BASELINE_EDITABLE,
    insulation_mm: 300,
    glazing_uvalue: 0.6,
    lighting_density_w_m2: 1,
    wwr: 0,
  });
  assert.ok(extreme >= 30, `should floor at 30, got ${extreme}`);
});

test("recomputeCost: area 放大 1.25× 总成本 × ~1.25", () => {
  const base = recomputeCost(BASELINE_EDITABLE, "hospitality");
  const bigger = recomputeCost({ ...BASELINE_EDITABLE, area_m2: 50 }, "hospitality");
  assert.ok(Math.abs(bigger.total / base.total - 1.25) < 0.05, `ratio=${bigger.total / base.total}`);
});

test("recomputeCost: region CN 便宜 ~32%", () => {
  const hk = recomputeCost(BASELINE_EDITABLE, "hospitality");
  const cn = recomputeCost({ ...BASELINE_EDITABLE, region: "CN" }, "hospitality");
  assert.ok(cn.total < hk.total * 0.4, `CN should be significantly cheaper`);
  assert.ok(cn.total > hk.total * 0.25, `but not absurdly cheap`);
});

test("recomputeCompliance: HK baseline 全 pass", () => {
  const c = recomputeCompliance(BASELINE_EDITABLE);
  assert.equal(c.fails, 0);
  assert.equal(c.verdict, "COMPLIANT");
  assert.equal(c.items.length, 5);
});

test("recomputeCompliance: JP 更严，baseline 可能失败", () => {
  const c = recomputeCompliance({ ...BASELINE_EDITABLE, region: "JP" });
  assert.ok(c.fails > 0, "JP baseline should have at least one fail");
  assert.ok(c.verdict.startsWith("CONDITIONAL"), `verdict=${c.verdict}`);
});

test("recomputeAll: 完整 state merge", () => {
  const state = {
    cat: "hospitality",
    editable: BASELINE_EDITABLE,
    energy: { engine: "EnergyPlus" },
    pricing: { HK: {}, CN: {} },
    compliance: { HK: {} },
  };
  const result = recomputeAll(state);
  assert.equal(result.derived.eui_kwh_m2_yr, 84);
  assert.ok(result.derived.cost_total > 0);
  assert.equal(result.derived.compliance_fails, 0);
  assert.equal(result.derived.compliance_verdict, "COMPLIANT");
  // pricing 展示字段齐全
  assert.ok(typeof result.pricing.HK.total === "string" && result.pricing.HK.total.includes(","), "total formatted");
  assert.ok(result.pricing.HK.subtotal, "subtotal present");
  assert.ok(result.pricing.HK.mep, "mep present");
  assert.ok(result.pricing.HK.prelim, "prelim present");
  assert.ok(result.pricing.HK.cont, "cont present");
  assert.ok(result.pricing.CN, "CN region preserved");
  // compliance 展示字段齐全
  assert.ok(result.compliance.HK.label, "label present");
  assert.ok(result.compliance.HK.score, "score present");
  assert.ok(result.compliance.HK.items, "items present");
  assert.ok(result.compliance.HK.checks, "checks alias present");
  assert.equal(result.energy.engine, "EnergyPlus"); // 没破坏别的字段
});

test("recomputeAll: area 改大 → 整链重算", () => {
  const state = {
    cat: "hospitality",
    editable: { ...BASELINE_EDITABLE, area_m2: 50 },
  };
  const result = recomputeAll(state);
  assert.ok(result.derived.cost_total > 600000, `cost=${result.derived.cost_total}`);
});
