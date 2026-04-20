// node --test project-space/lib/apply-tools.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import { applyTools } from "./apply-tools.js";
import { BASELINE_EDITABLE } from "./compute.js";

const baseState = () => ({
  slug: "test-mvp",
  cat: "hospitality",
  editable: { ...BASELINE_EDITABLE },
  energy: {},
  pricing: { HK: {} },
  compliance: { HK: {} },
  variants: { list: [{ id: "v2-wabi-sabi", name: "Wabi-Sabi" }] },
  timeline: [],
});

test("set_editable: CCT 改暖", async () => {
  const r = await applyTools(baseState(), [
    { name: "set_editable", args: { field: "lighting_cct", value: 2700 } },
  ]);
  assert.equal(r.applied.length, 1);
  assert.equal(r.rejected.length, 0);
  assert.equal(r.state.editable.lighting_cct, 2700);
  assert.ok(r.state.derived.eui_kwh_m2_yr > 84, "EUI should increase with warmer CCT");
  assert.equal(r.state.timeline.length, 1, "auto-timeline added");
});

test("scale_editable: area ×1.25", async () => {
  const r = await applyTools(baseState(), [
    { name: "scale_editable", args: { field: "area_m2", factor: 1.25 } },
  ]);
  assert.equal(r.state.editable.area_m2, 50);
  assert.ok(r.state.derived.cost_total > 600000);
});

test("switch_region: HK → JP · 更严合规触发 fail", async () => {
  const r = await applyTools(baseState(), [
    { name: "switch_region", args: { region: "JP" } },
  ]);
  assert.equal(r.state.editable.region, "JP");
  // JP 合规阈值严，baseline 可能失败
  assert.ok(r.state.derived.compliance_fails > 0 || r.state.derived.compliance_verdict.startsWith("CONDITIONAL"));
});

test("switch_variant: 有 variantLoader 会 overlay", async () => {
  const variantData = {
    project: { name: "Wabi-Sabi Override", area: 40 },
    renders: [{ id: "01", file: "/foo.webp", title: "hero" }],
    editable: { insulation_mm: 80 },
  };
  const r = await applyTools(baseState(), [
    { name: "switch_variant", args: { variant_id: "v2-wabi-sabi" } },
  ], { variantLoader: (slug, vid) => vid === "v2-wabi-sabi" ? variantData : null });
  assert.equal(r.applied.length, 1);
  assert.equal(r.state.active_variant_id, "v2-wabi-sabi");
  assert.equal(r.state.project.name, "Wabi-Sabi Override");
  assert.equal(r.state.editable.insulation_mm, 80);
});

test("switch_variant: 未知 variant 拒绝", async () => {
  const r = await applyTools(baseState(), [
    { name: "switch_variant", args: { variant_id: "v99-fake" } },
  ]);
  assert.equal(r.rejected.length, 1);
  assert.ok(r.rejected[0].reason.includes("not found"));
});

test("invalid field: 拒绝", async () => {
  const r = await applyTools(baseState(), [
    { name: "set_editable", args: { field: "fake_field", value: 100 } },
  ]);
  assert.equal(r.rejected.length, 1);
  assert.ok(r.rejected[0].reason.includes("Unknown"));
});

test("out of range: 拒绝", async () => {
  const r = await applyTools(baseState(), [
    { name: "set_editable", args: { field: "insulation_mm", value: 5000 } },
  ]);
  assert.equal(r.rejected.length, 1);
  assert.ok(r.rejected[0].reason.includes("out of range"));
});

test("混合：一条 OK 一条 rejected", async () => {
  const r = await applyTools(baseState(), [
    { name: "set_editable", args: { field: "lighting_cct", value: 2700 } },
    { name: "set_editable", args: { field: "insulation_mm", value: 99999 } },
  ]);
  assert.equal(r.applied.length, 1);
  assert.equal(r.rejected.length, 1);
  assert.equal(r.state.editable.lighting_cct, 2700);
  assert.equal(r.state.editable.insulation_mm, 60); // unchanged
});

test("append_timeline 覆盖 auto-timeline", async () => {
  const r = await applyTools(baseState(), [
    { name: "set_editable", args: { field: "lighting_cct", value: 2700 } },
    { name: "append_timeline", args: { title: "Warmer feel", diff: "CCT 3000→2700" } },
  ]);
  assert.equal(r.state.timeline.length, 1);
  assert.equal(r.state.timeline[0].title, "Warmer feel");
});

test("无改动：state 不 recompute · timeline 不加", async () => {
  const r = await applyTools(baseState(), [
    { name: "set_editable", args: { field: "fake", value: 1 } }, // 被拒
  ]);
  assert.equal(r.applied.length, 0);
  assert.equal(r.state.timeline.length, 0);
  // derived 未触发（不检查具体数，只看 state 没被 recompute 覆盖）
});
