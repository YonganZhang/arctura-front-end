// furniture-loader.js — Three.js GLB primitive 加载器
// 扩展接口：只需改 /data/furniture-library.json 加一条 + 丢 GLB 即可；renderer 零改动

import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";

// 内存缓存：每个 type 只加载一次 GLB，之后 clone()
const _glbCache = new Map(); // type → Promise<THREE.Group>
const _loader = new GLTFLoader();

let _library = null; // lazy-loaded from /data/furniture-library.json

export async function loadLibrary() {
  if (_library) return _library;
  try {
    const r = await fetch("/data/furniture-library.json");
    if (!r.ok) throw new Error(`library fetch ${r.status}`);
    _library = await r.json();
  } catch (e) {
    console.warn("[furniture-loader] library load failed, using empty lib:", e);
    _library = { schema_version: "1.0", items: {} };
  }
  return _library;
}

function loadGlb(url) {
  return new Promise((resolve, reject) => {
    _loader.load(
      url,
      (gltf) => resolve(gltf.scene),
      undefined,
      (err) => reject(err)
    );
  });
}

// primitive box fallback · 当 GLB 缺失 / type 未知
function makeFallbackBox(size, color) {
  const [w, d, h] = size;
  const geom = new THREE.BoxGeometry(Math.max(w, 0.05), Math.max(d, 0.05), Math.max(h, 0.05));
  // Three.js: Y 轴高度，但我们的 size 是 [w, d, h]（z 是高）· 保持 box 方向
  // 我们选择统一：object 的 pos[z] = 底部离地 · size[2] = 高 · Three.js 使用 Y-up
  // 在 scene renderer 里转换：swap Y/Z。这里 geometry 按 [w, d, h] 即 x=w, y=d, z=h
  // 但 Three.js 显示 Y-up 需要 rotation。简化：renderer 里统一处理旋转。
  const mat = new THREE.MeshStandardMaterial({
    color: new THREE.Color(color || "#CCCCCC"),
    roughness: 0.7,
    metallic: 0.0,
  });
  const mesh = new THREE.Mesh(geom, mat);
  mesh.castShadow = true;
  mesh.receiveShadow = true;
  mesh.userData.isFallback = true;
  return mesh;
}

// 主入口：type → Three.Object3D（clone）· 缺失时 fallback 到 primitive
// size: [w, d, h] 米 · materials: scene.materials 用来取颜色（fallback 模式用）
export async function loadFurniture(type, size, materials, materialId) {
  const lib = await loadLibrary();
  const entry = lib.items?.[type];

  // 1. 如果 library 有此 type 且有 glb · 加载并缓存
  if (entry?.glb) {
    if (!_glbCache.has(type)) {
      _glbCache.set(type, loadGlb(entry.glb).catch((e) => {
        console.warn(`[furniture-loader] GLB load failed for ${type}:`, e);
        return null; // 标记失败 · 后面走 fallback
      }));
    }
    const master = await _glbCache.get(type);
    if (master) {
      const clone = master.clone(true);
      // clone materials so color override doesn't affect siblings
      clone.traverse((node) => {
        if (node.isMesh && node.material) {
          node.material = node.material.clone();
          node.castShadow = true;
          node.receiveShadow = true;
        }
      });
      // scale to match size
      const defaultSize = entry.default_size || [1, 1, 1];
      clone.userData.glbType = type;
      clone.userData.scaleTarget = size; // renderer 会按 size 缩放
      return clone;
    }
  }

  // 2. Fallback: primitive box colored by material
  const mat = materials?.[materialId] || { base_color: "#CCCCCC" };
  return makeFallbackBox(size, mat.base_color);
}

// 释放缓存（dispose 时调）
export function clearCache() {
  _glbCache.clear();
  _library = null;
}

// 给 prompt 注入用 · 返回可用 type 列表
export async function availableTypes() {
  const lib = await loadLibrary();
  return Object.keys(lib.items || {});
}
