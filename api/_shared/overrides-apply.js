// JS apply_overrides_to_scene · Python `_build/arctura_mvp/derive/overrides.py` 对称实现
//
// 用途：前端可在浏览器内对 base scene 应用 overrides 做即时预览（不必等 derive worker 跑）；
//       校验 overrides schema 合法性。
//
// 跨语言 case 锁定：_tests/unit/overrides-apply.test.mjs + _build/arctura_mvp/tests/test_derive.py

export const OVERRIDES_SCHEMA_VERSION = "v1";
export const NAMESPACES = ["layout", "structural", "appearance", "lighting", "tombstones"];

function isObj(x) { return x && typeof x === "object" && !Array.isArray(x); }
function isArr(x) { return Array.isArray(x); }
function deepClone(x) { return JSON.parse(JSON.stringify(x)); }

export function applyOverridesToScene(baseScene, overrides) {
  if (!isObj(overrides) || Object.keys(overrides).length === 0) {
    return deepClone(baseScene);
  }
  const scene = deepClone(baseScene);

  // 1. tombstones 删除
  const tomb = overrides.tombstones || {};
  if (isObj(tomb)) {
    const objIds = new Set(tomb.objects || []);
    const asmIds = new Set(tomb.assemblies || []);
    const lightIds = new Set(tomb.lights || []);
    if (objIds.size) {
      scene.objects = (scene.objects || []).filter(o => !objIds.has(o.id));
      for (const a of (scene.assemblies || [])) {
        a.part_ids = (a.part_ids || []).filter(p => !objIds.has(p));
      }
    }
    if (asmIds.size) {
      scene.assemblies = (scene.assemblies || []).filter(a => !asmIds.has(a.id));
    }
    if (lightIds.size) {
      scene.lights = (scene.lights || []).filter(l => !lightIds.has(l.id));
    }
  }

  // 2. appearance
  const app = overrides.appearance || {};
  if (isObj(app)) {
    if (isObj(app.materials_added)) {
      scene.materials = scene.materials || {};
      for (const [mid, def] of Object.entries(app.materials_added)) {
        if (isObj(def)) scene.materials[mid] = { ...def };
      }
    }
    for (const k of ["floor", "ceiling"]) {
      if (isObj(app[k]) && app[k].material_id) {
        scene[k] = scene[k] || {};
        scene[k].material_id = app[k].material_id;
      }
    }
    if (isObj(app.walls)) {
      const wmap = Object.fromEntries((scene.walls || []).map(w => [w.id, w]));
      for (const [wid, ch] of Object.entries(app.walls)) {
        if (wmap[wid] && ch.material_id) wmap[wid].material_id = ch.material_id;
      }
    }
    if (isObj(app.assemblies)) {
      const amap = Object.fromEntries((scene.assemblies || []).map(a => [a.id, a]));
      for (const [aid, ch] of Object.entries(app.assemblies)) {
        if (amap[aid] && ch.material_id) amap[aid].material_id_primary = ch.material_id;
      }
    }
    if (isObj(app.objects)) {
      const omap = Object.fromEntries((scene.objects || []).map(o => [o.id, o]));
      for (const [oid, ch] of Object.entries(app.objects)) {
        if (omap[oid] && ch.material_id) omap[oid].material_id = ch.material_id;
      }
    }
  }

  // 3. layout
  const layout = overrides.layout || {};
  if (isObj(layout)) {
    const omap = Object.fromEntries((scene.objects || []).map(o => [o.id, o]));
    const amap = Object.fromEntries((scene.assemblies || []).map(a => [a.id, a]));
    for (const [, ch] of Object.entries(layout)) {
      if (!isObj(ch)) continue;
      const target = ch.target;
      const tid = ch.target_id;
      if (target === "added" && ch.payload) {
        // add_object · 完整 payload
        scene.objects = scene.objects || [];
        scene.objects.push({ ...ch.payload });
        continue;
      }
      if (!tid) continue;
      const bag = target === "object" ? omap : amap;
      const item = bag[tid];
      if (!item) continue;   // orphan
      if (isArr(ch.pos)) item.pos = [...ch.pos];
      if (isArr(ch.rotation)) item.rotation = [...ch.rotation];
      if (isArr(ch.size)) item.size = [...ch.size];
    }
  }

  // 4. structural
  const stru = overrides.structural || {};
  if (isObj(stru)) {
    const wallChanges = stru.walls || [];
    if (isArr(wallChanges)) {
      const wmap = Object.fromEntries((scene.walls || []).map(w => [w.id, w]));
      for (const ch of wallChanges) {
        if (!isObj(ch)) continue;
        const w = wmap[ch.id];
        if (!w) continue;
        for (const k of ["start", "end", "height", "thickness"]) {
          if (k in ch) w[k] = ch[k];
        }
      }
    }
    const openingChanges = stru.openings || [];
    if (isArr(openingChanges)) {
      scene.openings = scene.openings || [];
      for (const ch of openingChanges) {
        if (!isObj(ch)) continue;
        if (ch._op === "add") {
          const { _op, ...payload } = ch;
          if (payload.id) scene.openings.push(payload);
        } else if (ch._op === "remove") {
          scene.openings = scene.openings.filter(o => o.id !== ch.id);
        }
      }
    }
  }

  // 5. lighting
  const lighting = overrides.lighting || {};
  if (isObj(lighting)) {
    if (isArr(lighting._added)) {
      scene.lights = scene.lights || [];
      for (const e of lighting._added) {
        if (isObj(e) && e.id) scene.lights.push({ ...e });
      }
    }
    const lmap = Object.fromEntries((scene.lights || []).map(l => [l.id, l]));
    for (const [lid, ch] of Object.entries(lighting)) {
      if (lid === "_added") continue;
      if (!isObj(ch)) continue;
      const target = lmap[lid];
      if (!target) continue;
      if (ch._op === "remove") {
        scene.lights = scene.lights.filter(l => l.id !== lid);
        continue;
      }
      for (const k of ["pos", "dir", "color", "power", "intensity", "size", "size_y", "shape", "cct"]) {
        if (k in ch) target[k] = ch[k];
      }
      if ("intensity_scale" in ch) {
        const cur = target.intensity || 1.0;
        target.intensity = Math.round(cur * Number(ch.intensity_scale) * 1000) / 1000;
      }
    }
  }

  return scene;
}

export function validateOverrides(overrides) {
  const errors = [];
  if (!isObj(overrides)) return ["overrides must be object"];
  for (const ns of Object.keys(overrides)) {
    if (!NAMESPACES.includes(ns)) {
      errors.push(`unknown namespace: ${ns} · allowed: ${NAMESPACES.join(",")}`);
    }
  }
  if (isObj(overrides.layout)) {
    for (const [oid, ch] of Object.entries(overrides.layout)) {
      if (!isObj(ch)) {
        errors.push(`layout.${oid} not object`);
        continue;
      }
      // target=added 不需要 target_id
      if (ch.target !== "added" && !ch.target_id) {
        errors.push(`layout.${oid} missing target_id`);
      }
    }
  }
  return errors;
}
