// furniture-loader.js — 家具加载器
// 三级 fallback 策略：
//   1. library[type].glb 存在且加载成功 → GLB mesh
//   2. library[type].builder 存在 → 调 procedural builder 组合 box/cylinder/cone
//   3. 都失败 → 一个 colored box（primitive fallback）
// 扩展接口：只需改 /data/furniture-library.json 加一条 entry · 不必改代码

import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";

const _glbCache = new Map();  // type → Promise<THREE.Group | null>
const _loader = new GLTFLoader();
let _library = null;          // cached from /data/furniture-library.json
let _libraryPromise = null;

// Phase 3.I · PBR 木纹贴图 · 有则用 · 无则静默 fallback（base_color 不变）
const _texLoader = new THREE.TextureLoader();
let _woodAlbedoTex = null, _woodNormalTex = null;
let _woodTexTried = false;
async function tryLoadWoodTextures() {
  if (_woodTexTried) return;
  _woodTexTried = true;
  const tryOne = (url) => new Promise(resolve => {
    _texLoader.load(url, tex => {
      tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
      tex.repeat.set(2, 2);
      resolve(tex);
    }, undefined, () => resolve(null));
  });
  const [albedo, normal] = await Promise.all([
    tryOne("/assets/textures/wood_albedo.jpg"),
    tryOne("/assets/textures/wood_normal.jpg"),
  ]);
  _woodAlbedoTex = albedo; _woodNormalTex = normal;
}
// 判断一个 base_color 是不是"木色"（肉眼看起来是棕 / 橙色系）
function isWoodColor(hex) {
  if (!hex || typeof hex !== "string") return false;
  const m = hex.match(/^#([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$/i);
  if (!m) return false;
  const r = parseInt(m[1], 16), g = parseInt(m[2], 16), b = parseInt(m[3], 16);
  // 棕色族：R > G > B 且 R 在 0.3~0.8 区间
  return r > g && g > b && r >= 80 && r <= 220 && (r - b) > 30;
}

export async function loadLibrary() {
  if (_library) return _library;
  if (_libraryPromise) return _libraryPromise;
  // Phase 3.I · 并发尝试加载 PBR 贴图（失败不阻塞库加载）
  tryLoadWoodTextures();
  _libraryPromise = fetch("/data/furniture-library.json")
    .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`library fetch ${r.status}`))))
    .then((lib) => { _library = lib; return lib; })
    .catch((e) => {
      console.warn("[furniture-loader] library load failed, using empty:", e);
      _library = { schema_version: "1.0", items: {} };
      return _library;
    });
  return _libraryPromise;
}

export async function availableTypes() {
  const lib = await loadLibrary();
  return Object.keys(lib.items || {});
}

function tryLoadGlb(url) {
  return new Promise((resolve) => {
    _loader.load(
      url,
      (gltf) => resolve(gltf.scene),
      undefined,
      (_err) => resolve(null),  // 静默 fallback
    );
  });
}

// ───────── Procedural builders · 每个 type 用 Three.js primitive 组合 ─────────
// 返回一个 Group，里面的 mesh 坐标系：原点在底部中心，+Z 向上，+X 向右，+Y 向前
// 之后 renderer 会按 object.pos / size / rotation 放置 · scale 按 [w, d, h]（占位 size）

const MAT_CACHE = new Map();
function getMat(color, roughness = 0.6, metallic = 0) {
  const key = `${color}|${roughness}|${metallic}`;
  if (!MAT_CACHE.has(key)) {
    const mat = new THREE.MeshStandardMaterial({
      color: new THREE.Color(color),
      roughness,
      metalness: metallic,
    });
    // Phase 3.I · 木色自动叠 normalMap（如 texture 加载成功）
    if (isWoodColor(color) && _woodNormalTex) {
      mat.normalMap = _woodNormalTex;
      mat.normalScale = new THREE.Vector2(0.6, 0.6);
    }
    MAT_CACHE.set(key, mat);
  }
  return MAT_CACHE.get(key).clone();
}

function box(w, d, h, mat) {
  const geom = new THREE.BoxGeometry(Math.max(w, 0.01), Math.max(d, 0.01), Math.max(h, 0.01));
  const m = new THREE.Mesh(geom, mat);
  m.castShadow = true;
  m.receiveShadow = true;
  return m;
}

function cylinder(r, h, mat, segments = 20) {
  const geom = new THREE.CylinderGeometry(r, r, h, segments);
  // 默认 Three.js cylinder 的轴是 Y · 转 Z 轴为轴
  geom.rotateX(Math.PI / 2);
  const m = new THREE.Mesh(geom, mat);
  m.castShadow = true;
  m.receiveShadow = true;
  return m;
}

function cone(rBottom, rTop, h, mat, segments = 20) {
  const geom = new THREE.CylinderGeometry(rTop, rBottom, h, segments);
  geom.rotateX(Math.PI / 2);
  const m = new THREE.Mesh(geom, mat);
  m.castShadow = true;
  m.receiveShadow = true;
  return m;
}

const BUILDERS = {
  // 默认 size [w, d, h]；内部坐标：底面在 z=0，中心在 x=0, y=0
  chair_standard(color) {
    // 总高 0.9m: 座位高 0.45 · 靠背到 0.85
    const g = new THREE.Group();
    const legMat = getMat("#3A3A3A", 0.7, 0.3);
    const seatMat = getMat(color, 0.6);
    // 四条腿
    const legH = 0.45, legW = 0.04;
    [[-0.2, -0.2], [0.2, -0.2], [-0.2, 0.2], [0.2, 0.2]].forEach(([x, y]) => {
      const l = box(legW, legW, legH, legMat);
      l.position.set(x, y, legH / 2);
      g.add(l);
    });
    // 座位板
    const seat = box(0.48, 0.48, 0.04, seatMat);
    seat.position.set(0, 0, legH + 0.02);
    g.add(seat);
    // 靠背
    const back = box(0.48, 0.04, 0.4, seatMat);
    back.position.set(0, -0.22, legH + 0.25);
    g.add(back);
    return g;
  },

  chair_lounge(color) {
    const g = new THREE.Group();
    const mat = getMat(color, 0.7);
    // 座位 + 靠背 + 扶手（方形简化）
    const seat = box(0.8, 0.8, 0.4, mat);
    seat.position.set(0, 0, 0.2);
    g.add(seat);
    const back = box(0.8, 0.1, 0.5, mat);
    back.position.set(0, -0.35, 0.55);
    g.add(back);
    // 两侧扶手
    [-0.35, 0.35].forEach(x => {
      const arm = box(0.1, 0.6, 0.35, mat);
      arm.position.set(x, 0, 0.475);
      g.add(arm);
    });
    return g;
  },

  sofa(color) {
    // 通用 sofa builder · 根据 scale 自动适配 2-seat / 3-seat
    const g = new THREE.Group();
    const mat = getMat(color, 0.85);
    // 以 1×1×1 为单位 · renderer 会 scale 到 default_size (e.g. 1.6×0.9×0.85)
    const seat = box(1.0, 1.0, 0.45, mat);
    seat.position.set(0, 0, 0.225);
    g.add(seat);
    const back = box(1.0, 0.15, 0.55, mat);
    back.position.set(0, -0.4, 0.575);
    g.add(back);
    // 扶手
    [-0.45, 0.45].forEach(x => {
      const arm = box(0.1, 0.85, 0.5, mat);
      arm.position.set(x, 0, 0.475);
      g.add(arm);
    });
    return g;
  },

  desk(color) {
    const g = new THREE.Group();
    const wood = getMat(color, 0.5);
    const leg = getMat("#3A3A3A", 0.4, 0.5);
    // 桌面（默认 size 1×1×1，底到顶高 1 · 桌面在 top · 单位 scale）
    const top = box(1.0, 1.0, 0.04, wood);
    top.position.set(0, 0, 0.98);
    g.add(top);
    // 两侧抽屉侧板
    [[-0.48, 0], [0.48, 0]].forEach(([x, y]) => {
      const l = box(0.04, 1.0, 0.95, leg);
      l.position.set(x, y, 0.475);
      g.add(l);
    });
    return g;
  },

  table(color) {
    const g = new THREE.Group();
    const wood = getMat(color, 0.5);
    const top = box(1.0, 1.0, 0.04, wood);
    top.position.set(0, 0, 0.98);
    g.add(top);
    // 4 条腿
    [[-0.45, -0.45], [0.45, -0.45], [-0.45, 0.45], [0.45, 0.45]].forEach(([x, y]) => {
      const l = box(0.05, 0.05, 0.94, wood);
      l.position.set(x, y, 0.47);
      g.add(l);
    });
    return g;
  },

  bed(color) {
    const g = new THREE.Group();
    const fabric = getMat(color, 0.9);
    const wood = getMat("#5A3E2B", 0.4);
    // 床垫
    const mattress = box(1.0, 1.0, 0.4, fabric);
    mattress.position.set(0, 0, 0.25);
    g.add(mattress);
    // 床头板
    const headboard = box(1.0, 0.08, 0.6, wood);
    headboard.position.set(0, 0.5, 0.3);
    g.add(headboard);
    return g;
  },

  shelf(color) {
    const g = new THREE.Group();
    const wood = getMat(color, 0.55);
    // 两侧板
    [[-0.48, 0], [0.48, 0]].forEach(([x, y]) => {
      const side = box(0.04, 1.0, 1.0, wood);
      side.position.set(x, y, 0.5);
      g.add(side);
    });
    // 背板
    const back = box(1.0, 0.02, 1.0, wood);
    back.position.set(0, 0.48, 0.5);
    g.add(back);
    // 5 层搁板
    for (let i = 0; i < 5; i++) {
      const shelf = box(0.95, 0.95, 0.03, wood);
      shelf.position.set(0, 0, 0.1 + i * 0.22);
      g.add(shelf);
    }
    return g;
  },

  closet(color) {
    const g = new THREE.Group();
    const wood = getMat(color, 0.4);
    // 整体箱体
    const body = box(1.0, 1.0, 1.0, wood);
    body.position.set(0, 0, 0.5);
    g.add(body);
    // 门缝（竖线 · 两扇门）· 稍深的面板做门把手
    const handleMat = getMat("#D4AF37", 0.3, 0.8);
    [-0.1, 0.1].forEach(x => {
      const h = box(0.02, 0.03, 0.1, handleMat);
      h.position.set(x, -0.51, 0.5);
      g.add(h);
    });
    return g;
  },

  lamp_floor(color) {
    const g = new THREE.Group();
    const poleMat = getMat(color, 0.3, 0.6);
    const shadeMat = getMat("#F4E4B6", 0.8);
    shadeMat.emissive = new THREE.Color("#FFD98A");
    shadeMat.emissiveIntensity = 0.4;
    // Base
    const base = cylinder(0.15, 0.03, poleMat);
    base.position.set(0, 0, 0.015);
    g.add(base);
    // Pole
    const pole = cylinder(0.015, 0.85, poleMat);
    pole.position.set(0, 0, 0.45);
    g.add(pole);
    // Shade
    const shade = cone(0.18, 0.1, 0.15, shadeMat);
    shade.position.set(0, 0, 0.95);
    g.add(shade);
    return g;
  },

  lamp_pendant(color) {
    const g = new THREE.Group();
    const wireMat = getMat("#2A2A2A", 0.3, 0.6);
    const shadeMat = getMat(color, 0.5);
    shadeMat.emissive = new THREE.Color("#FFD98A");
    shadeMat.emissiveIntensity = 0.5;
    // 细线（悬挂）· 假设从顶吊下 30cm
    const wire = cylinder(0.008, 0.3, wireMat);
    wire.position.set(0, 0, 0.85);
    g.add(wire);
    // Cone shade（开口向下）
    const shade = cone(0.2, 0.1, 0.3, shadeMat);
    shade.position.set(0, 0, 0.5);
    g.add(shade);
    return g;
  },
};

function makeBasicBox(size, color) {
  const [w, d, h] = size;
  const mat = getMat(color || "#CCCCCC");
  const mesh = box(w, d, h, mat);
  mesh.position.z = h / 2;  // 底贴地
  mesh.userData.isFallback = true;
  return mesh;
}

// ───────── 主入口 ─────────

export async function loadFurniture(type, size, materials, materialId) {
  const lib = await loadLibrary();
  const entry = lib.items?.[type];

  // 1. GLB 优先
  if (entry?.glb) {
    if (!_glbCache.has(type)) {
      _glbCache.set(type, tryLoadGlb(entry.glb));
    }
    const master = await _glbCache.get(type);
    if (master) {
      const cloneG = master.clone(true);
      cloneG.traverse((node) => {
        if (node.isMesh && node.material) {
          node.material = node.material.clone();
          node.castShadow = true;
          node.receiveShadow = true;
        }
      });
      cloneG.userData.glbType = type;
      return cloneG;
    }
  }

  // 2. Procedural builder
  if (entry?.builder && BUILDERS[entry.builder]) {
    const matData = materials?.[materialId];
    const color = matData?.base_color || entry.default_color || "#CCCCCC";
    const g = BUILDERS[entry.builder](color);
    g.userData.builder = entry.builder;
    g.userData.procedural = true;
    g.userData.anchor = entry.anchor || "bottom";
    g.userData.defaultSize = entry.default_size;
    return g;
  }

  // 3. Fallback: primitive box
  const matData = materials?.[materialId];
  const color = matData?.base_color || entry?.default_color || "#CCCCCC";
  return makeBasicBox(size, color);
}

export function clearCache() {
  _glbCache.clear();
  MAT_CACHE.clear();
  _library = null;
  _libraryPromise = null;
}
