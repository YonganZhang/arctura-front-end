// three-scene-renderer.js — Arctura 3D 场景渲染器
// 吃 scene JSON 出 Three.js 场景 · 墙/地板/天花板/家具/灯光 都按数据程序化
// 增量更新：applyOps(applied[]) 每种 op 有对应 delta · 不重建整个 scene

import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { RGBELoader } from "three/addons/loaders/RGBELoader.js";
import { RectAreaLightUniformsLib } from "three/addons/lights/RectAreaLightUniformsLib.js";
import { loadFurniture } from "./furniture-loader.js";

RectAreaLightUniformsLib.init();

// ───────── 坐标系约定 ─────────
// 上游 room.json / Blender：Z-up，[x, y, z] 中 z 是高度
// Three.js 默认 Y-up
// 选择：在 Scene 顶层用 group.rotation.x = -Math.PI/2 把整个世界从 Z-up 转到 Y-up
// 这样下层所有 pos / size 原样传入即可，语义对齐

// ───────── 工具函数 ─────────

function hexToColor(hex) {
  return new THREE.Color(hex || "#CCCCCC");
}

function makeStandardMaterial(mat) {
  const m = new THREE.MeshStandardMaterial({
    color: hexToColor(mat.base_color),
    roughness: mat.roughness ?? 0.7,
    metalness: mat.metallic ?? 0.0,
    transparent: (mat.opacity ?? 1) < 1,
    opacity: mat.opacity ?? 1,
  });
  if (mat.emissive) {
    m.emissive = hexToColor(mat.emissive);
    m.emissiveIntensity = mat.emissive_intensity ?? 1;
  }
  return m;
}

function wallLength(wall) {
  const dx = wall.end[0] - wall.start[0];
  const dy = wall.end[1] - wall.start[1];
  return Math.hypot(dx, dy);
}

function wallAngleRadZ(wall) {
  const dx = wall.end[0] - wall.start[0];
  const dy = wall.end[1] - wall.start[1];
  return Math.atan2(dy, dx);
}

// ───────── SceneRenderer class ─────────

export class SceneRenderer {
  constructor(canvas) {
    this.canvas = canvas;
    this.renderer = new THREE.WebGLRenderer({
      canvas,
      antialias: true,
      alpha: true,
      preserveDrawingBuffer: false,
    });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.0;
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;

    this.threeScene = new THREE.Scene();

    // Z-up → Y-up conversion group：所有 scene 内容挂到这里
    this.world = new THREE.Group();
    this.world.rotation.x = -Math.PI / 2;
    this.threeScene.add(this.world);

    this.camera = new THREE.PerspectiveCamera(50, 1, 0.01, 200);
    this.camera.position.set(5, 4, 5);
    this.camera.lookAt(0, 0, 1);

    this.controls = new OrbitControls(this.camera, canvas);
    this.controls.enableDamping = true;
    this.controls.target.set(0, 1.2, 0);

    // 材质缓存（id → THREE.Material）
    this.materials = new Map();

    // entity maps（id → THREE.Object3D）· 方便增量更新
    this.wallObjs = new Map();
    this.objectObjs = new Map();       // raw Blender mesh（raw 模式 或 未归属 parts）
    this.assemblyObjs = new Map();     // procedural assembly 的整体 mesh
    this.lightObjs = new Map();
    this.floorObj = null;
    this.ceilingObj = null;

    // 当前 scene 数据（快照 · 给 applyOps 查用）
    this.currentScene = null;
    this.renderMode = "procedural";    // "procedural" | "raw"

    // 选中 / raycaster（Phase 3.C）
    this.raycaster = new THREE.Raycaster();
    this._pointerNDC = new THREE.Vector2();
    this._selection = null;            // { kind: "assembly"|"object", id, mesh, originalEmissive, originalIntensity }
    this.onSelect = null;              // 外部回调 · (hit | null) => void
    this.onHover = null;               // 外部回调 · (hit | null) => void · Phase 3.F (hover tooltip)

    // Transparency toggle（Phase 3.E）· 每面墙 / 天花板独立 · autoCamera 根据相机位自动淡化
    this.transparency = {
      wall_N: false, wall_S: false, wall_E: false, wall_W: false,
      ceiling: false,
      autoCamera: false,
    };
    this._wallDirMap = new Map();     // wall.id → "N" | "S" | "E" | "W"
    this._lastAutoTransp = 0;         // 节流 · RAF 里每 200ms 重算一次

    // Click 事件（单击 · 非拖拽）
    this._setupPointerEvents();

    this._isRunning = false;
    this._resizeObserver = null;

    this._startLoop();
    this._observeResize();
  }

  _observeResize() {
    this._resizeObserver = new ResizeObserver(() => this._resize());
    this._resizeObserver.observe(this.canvas);
    this._resize();
  }

  // Phase 3.C · click raycaster · 区分 click vs drag
  _setupPointerEvents() {
    let down = null;
    this._onPointerDown = (e) => {
      down = { x: e.clientX, y: e.clientY, t: Date.now() };
    };
    this._onPointerUp = (e) => {
      if (!down) return;
      const dx = e.clientX - down.x, dy = e.clientY - down.y;
      const dt = Date.now() - down.t;
      const dist = Math.hypot(dx, dy);
      down = null;
      // 单击（没有拖超过 5px + 300ms 内松开）
      if (dist > 5 || dt > 600) return;
      const hit = this._raycastAt(e.clientX, e.clientY);
      if (this.onSelect) this.onSelect(hit);
      this.setSelection(hit?.id || null);
    };
    // Hover tooltip（Phase 3.F · 节流 120ms）
    let _hoverT = 0;
    this._onPointerMove = (e) => {
      const now = Date.now();
      if (now - _hoverT < 120) return;
      _hoverT = now;
      if (!this.onHover) return;
      const hit = this._raycastAt(e.clientX, e.clientY);
      this.onHover(hit, { x: e.clientX, y: e.clientY });
    };
    this.canvas.addEventListener("pointerdown", this._onPointerDown);
    this.canvas.addEventListener("pointerup", this._onPointerUp);
    this.canvas.addEventListener("pointerleave", () => { down = null; });
    this.canvas.addEventListener("pointermove", this._onPointerMove);
  }

  _raycastAt(clientX, clientY) {
    const rect = this.canvas.getBoundingClientRect();
    this._pointerNDC.x = ((clientX - rect.left) / rect.width) * 2 - 1;
    this._pointerNDC.y = -((clientY - rect.top) / rect.height) * 2 + 1;
    this.raycaster.setFromCamera(this._pointerNDC, this.camera);

    // 目标集合：procedural 模式下优先 assembly meshes · raw 模式下 object meshes
    const targets = [];
    if (this.renderMode === "procedural" && this.assemblyObjs.size > 0) {
      this.assemblyObjs.forEach((mesh) => targets.push(mesh));
    } else {
      this.objectObjs.forEach((mesh) => targets.push(mesh));
    }
    const hits = this.raycaster.intersectObjects(targets, true);
    if (hits.length === 0) return null;

    // 向上找到 named 根（assembly or object）
    let node = hits[0].object;
    while (node && !node.userData?.assembly && !node.userData?.object) {
      node = node.parent;
    }
    if (!node) return null;
    if (node.userData.assembly) return { kind: "assembly", id: node.userData.assembly.id, mesh: node };
    if (node.userData.object)   return { kind: "object",   id: node.userData.object.id, mesh: node };
    return null;
  }

  // Selection highlight · emissive 覆盖（restore on clear）
  setSelection(id) {
    if (this._selection?.id === id) return;  // 已选
    this._clearSelection();
    if (!id) return;
    const mesh = this.assemblyObjs.get(id) || this.objectObjs.get(id);
    if (!mesh) return;
    const saves = [];
    mesh.traverse((o) => {
      if (!o.isMesh || !o.material) return;
      const mat = o.material;
      // 原值快照
      const origEmissive = mat.emissive ? mat.emissive.clone() : new THREE.Color(0, 0, 0);
      const origIntensity = mat.emissiveIntensity ?? 1.0;
      saves.push({ node: o, origEmissive, origIntensity });
      // 叠 #4a4 emissive · 不改原颜色
      if (!mat.emissive) mat.emissive = new THREE.Color(0, 0, 0);
      mat.emissive = new THREE.Color(0x44aa44);
      mat.emissiveIntensity = 0.6;
      mat.needsUpdate = true;
    });
    const kind = mesh.userData?.assembly ? "assembly" : "object";
    this._selection = { kind, id, mesh, saves };
  }

  clearSelection() { this._clearSelection(); }

  _clearSelection() {
    const sel = this._selection;
    if (!sel) return;
    for (const s of sel.saves || []) {
      const mat = s.node.material;
      if (!mat) continue;
      mat.emissive = s.origEmissive;
      mat.emissiveIntensity = s.origIntensity;
      mat.needsUpdate = true;
    }
    this._selection = null;
  }

  // 供外部查询当前选中
  getSelection() { return this._selection ? { kind: this._selection.kind, id: this._selection.id } : null; }

  // ───────── Phase 3.F · Camera Tween + 开场环绕 + 预设视角 ─────────

  // 通用 tween: 从当前 camera pos/target tween 到目标 · 2 维同步插值
  _tweenCameraTo({ pos, target, fov, duration = 800, onDone }) {
    if (this._cameraTween) this._cameraTween.cancel = true;
    const start = {
      pos: this.camera.position.clone(),
      target: this.controls.target.clone(),
      fov: this.camera.fov,
    };
    const end = {
      pos: pos ? new THREE.Vector3(...pos) : start.pos,
      target: target ? new THREE.Vector3(...target) : start.target,
      fov: fov != null ? fov : start.fov,
    };
    const t0 = performance.now();
    const state = { cancel: false };
    this._cameraTween = state;
    const step = () => {
      if (state.cancel || !this._isRunning) return;   // FIX · dispose 时停止
      const t = Math.min(1, (performance.now() - t0) / duration);
      // ease-in-out
      const k = t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
      this.camera.position.lerpVectors(start.pos, end.pos, k);
      this.controls.target.lerpVectors(start.target, end.target, k);
      this.camera.fov = start.fov + (end.fov - start.fov) * k;
      this.camera.updateProjectionMatrix();
      if (t < 1) requestAnimationFrame(step);
      else { this._cameraTween = null; if (onDone) onDone(); }
    };
    requestAnimationFrame(step);
  }

  // 开场环绕 · 2s 以 target 为中心转一圈（OrbitControls 禁用防冲突）
  playIntroAnimation(duration = 2000) {
    if (!this.currentScene?.bounds) return;
    if (this._introState) this._introState.cancel = true;
    const { w, d, h } = this.currentScene.bounds;
    const radius = Math.max(w, d) * 1.1;
    const tgt = new THREE.Vector3(0, h * 0.5, 0);
    const originalEnabled = this.controls.enabled;
    this.controls.enabled = false;
    const t0 = performance.now();
    const yHeight = h * 0.8;
    const state = { cancel: false };
    this._introState = state;
    const step = () => {
      if (state.cancel || !this._isRunning) {         // FIX · dispose 时停止
        this.controls.enabled = originalEnabled;
        return;
      }
      const t = Math.min(1, (performance.now() - t0) / duration);
      const angle = t * Math.PI * 2;
      this.camera.position.set(
        Math.cos(angle) * radius,
        yHeight,
        Math.sin(angle) * radius,
      );
      this.controls.target.copy(tgt);
      this.camera.lookAt(tgt);
      if (t < 1) requestAnimationFrame(step);
      else {
        this.controls.enabled = originalEnabled;
        this.controls.update();
        this._introState = null;
      }
    };
    requestAnimationFrame(step);
  }

  // Phase 3.G · 白天 / 夜晚切换
  // mode = "day" | "night"
  // 白天：太阳强 · pendant 弱 · 背景亮蓝 · 天花 ambient 足
  // 夜晚：太阳弱 · pendant 强 · 背景深 · ambient 暗 · 整体暖色
  async setDaylight(mode) {
    const isDay = mode !== "night";
    this._daylightMode = mode;

    // HDRI 尝试切换（有则 swap · 没则 fallback 用 background color）
    const hdriPath = isDay ? "/assets/hdri/interior_day.hdr" : "/assets/hdri/interior_night.hdr";
    try {
      const rgbe = new RGBELoader();
      const tex = await new Promise((resolve, reject) => {
        rgbe.load(hdriPath, resolve, undefined, reject);
      });
      tex.mapping = THREE.EquirectangularReflectionMapping;
      if (this.threeScene.environment) this.threeScene.environment.dispose?.();
      this.threeScene.environment = tex;
    } catch {
      // fallback · 改背景色即可
      this.threeScene.background = new THREE.Color(isDay ? "#D7E8F2" : "#0A0B12");
    }

    // 灯光倍率：白天 sun 强 · pendant 弱 · 夜晚反过来
    const sunMul = isDay ? 1.2 : 0.15;
    const bulbMul = isDay ? 0.4 : 1.6;    // pendant/point
    const ambBase = isDay ? 0.7 : 0.2;

    this.lightObjs.forEach((light) => {
      const kind = light.userData.light?.type;
      // FIX · 缓存 baseIntensity 到 userData · 保证多次 setDaylight 调用幂等
      if (light.userData.baseIntensity == null) {
        light.userData.baseIntensity = light.userData.light?.intensity ?? light.intensity ?? 1;
      }
      const base = light.userData.baseIntensity;
      if (kind === "sun" || kind === "directional") {
        light.intensity = base * sunMul;
      } else if (kind === "point" || kind === "pendant" || kind === "spot" || kind === "area") {
        light.intensity = base * bulbMul;
      }
    });
    // 调 ambient · 直接用缓存的实例
    if (this._ambient) this._ambient.intensity = ambBase;

    // 背景色（若 HDRI 失败由 fallback 设；HDRI 成功也轻微染色）
    this.threeScene.background = new THREE.Color(isDay ? "#D7E8F2" : "#0A0B12");

    // tone mapping exposure 微调（夜晚略降 · 白天提）
    this.renderer.toneMappingExposure = isDay ? 1.15 : 0.85;
  }

  getDaylight() { return this._daylightMode || "day"; }

  // 预设视角 · "top" | "front" | "eye"
  gotoPreset(preset) {
    if (!this.currentScene?.bounds) return;
    const { w, d, h } = this.currentScene.bounds;
    const tgt = [0, h * 0.5, 0];   // 房间中心（Three.js Y-up · 世界 group 已转 · Y = height）
    if (preset === "top") {
      this._tweenCameraTo({ pos: [0, Math.max(w, d) * 1.5, 0.01], target: tgt, fov: 60 });
    } else if (preset === "front") {
      this._tweenCameraTo({ pos: [0, h * 0.6, Math.max(w, d) * 1.2], target: tgt, fov: 50 });
    } else if (preset === "eye") {
      // 站在房间一角 · 人眼高度 1.6m · 看向中心
      this._tweenCameraTo({ pos: [w * 0.35, 1.6, d * 0.35], target: [0, 1.2, 0], fov: 60 });
    }
  }

  _resize() {
    const rect = this.canvas.getBoundingClientRect();
    const w = Math.max(1, rect.width);
    const h = Math.max(1, rect.height);
    this.renderer.setSize(w, h, false);
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
  }

  _startLoop() {
    this._isRunning = true;
    const tick = () => {
      if (!this._isRunning) return;
      this.controls.update();
      this._tickAutoTransparency();   // Phase 3.E.F
      this.renderer.render(this.threeScene, this.camera);
      this._rafId = requestAnimationFrame(tick);
    };
    this._rafId = requestAnimationFrame(tick);
  }

  dispose() {
    this._isRunning = false;
    if (this._rafId) cancelAnimationFrame(this._rafId);
    if (this._resizeObserver) this._resizeObserver.disconnect();
    if (this._onPointerDown) {
      this.canvas.removeEventListener("pointerdown", this._onPointerDown);
      this.canvas.removeEventListener("pointerup", this._onPointerUp);
      this.canvas.removeEventListener("pointermove", this._onPointerMove);
    }
    this.controls.dispose();
    this.world.traverse((o) => {
      if (o.geometry) o.geometry.dispose();
      if (o.material) {
        if (Array.isArray(o.material)) o.material.forEach((m) => m.dispose());
        else o.material.dispose();
      }
    });
    this.materials.forEach((m) => m.dispose());
    this.materials.clear();
    this.renderer.dispose();
  }

  _getMaterial(id) {
    if (!this.materials.has(id)) {
      const matData = this.currentScene?.materials?.[id] || { base_color: "#CCCCCC" };
      this.materials.set(id, makeStandardMaterial(matData));
    }
    return this.materials.get(id);
  }

  // Phase 3.E · 识别每面墙的方位（N/S/E/W）· 基于 bounds 和墙中点
  _classifyWalls(scene) {
    const bounds = scene?.bounds;
    if (!bounds) return;
    const hw = bounds.w / 2, hd = bounds.d / 2;
    for (const w of scene.walls || []) {
      // 优先解 id 后缀（wall_auto_N / wall_N 等）
      const m = (w.id || "").match(/_([NSEW])$/i);
      if (m) { this._wallDirMap.set(w.id, m[1].toUpperCase()); continue; }
      // 否则按中点离 bounds 四边的最短距离判定
      const mx = (w.start[0] + w.end[0]) / 2;
      const my = (w.start[1] + w.end[1]) / 2;
      const dN = Math.abs(my - hd);
      const dS = Math.abs(my + hd);
      const dE = Math.abs(mx - hw);
      const dW = Math.abs(mx + hw);
      const min = Math.min(dN, dS, dE, dW);
      const dir = min === dN ? "N" : min === dS ? "S" : min === dE ? "E" : "W";
      this._wallDirMap.set(w.id, dir);
    }
  }

  // Phase 3.E · 更新 transparency state · 立刻生效
  setTransparency(partial) {
    Object.assign(this.transparency, partial || {});
    this._applyTransparency();
  }

  getTransparency() { return { ...this.transparency }; }

  _applyTransparency() {
    const t = this.transparency;
    // 墙
    this.wallObjs.forEach((group, wallId) => {
      const dir = this._wallDirMap.get(wallId);
      const transp = (dir === "N" && t.wall_N) || (dir === "S" && t.wall_S) ||
                     (dir === "E" && t.wall_E) || (dir === "W" && t.wall_W);
      this._setMeshOpacity(group, transp ? 0.15 : 1.0);
    });
    // 天花板
    if (this.ceilingObj) this._setMeshOpacity(this.ceilingObj, t.ceiling ? 0.15 : 1.0);
  }

  _setMeshOpacity(root, opacity) {
    const transparent = opacity < 1.0;
    const hide = opacity <= 0.3;
    // 关键修 · 直接把整个 Group/Mesh 的 visible 设 false · 整个子树不渲染
    // 之前只改内部 mesh · 在嵌套 rotated group 或多层 Group 情况下可能漏
    root.visible = !hide;
    const setOne = (m) => {
      m.transparent = transparent;
      m.opacity = opacity;
      m.depthWrite = !transparent;
      m.needsUpdate = true;
    };
    root.traverse((o) => {
      if (!o.isMesh) return;
      o.visible = !hide;
      if (!o.material) return;
      const mat = o.material;
      if (Array.isArray(mat)) mat.forEach(setOne);
      else setOne(mat);
    });
  }

  // Phase 3.E.F · camera-aware 自动墙透明 · 相机前方墙保持 · 相机背后 / 很近的墙淡化
  // 在 RAF loop 里调 · 节流 200ms · 只当 autoCamera=true 生效
  _tickAutoTransparency() {
    const t = this.transparency;
    if (!t.autoCamera) return;
    const now = performance.now();
    if (now - this._lastAutoTransp < 200) return;
    this._lastAutoTransp = now;

    const camPos = this.camera.position.clone();
    const camDir = new THREE.Vector3();
    this.camera.getWorldDirection(camDir);   // 相机前方向
    const camDirHoriz = new THREE.Vector3(camDir.x, camDir.z, 0); // world rotated · 实际水平面是 xz
    // 注：world 有 -90° x 轴旋转 → 相机 z = world 的 -y方向。简化：用 Three.js world 系算相机到墙的水平夹角
    // 方法：对每面墙 · 取其法线（垂直于 start→end + z 轴）· 计算 相机到墙中心的水平向量 vs 法线 夹角

    this.wallObjs.forEach((group, wallId) => {
      if (t[`wall_${this._wallDirMap.get(wallId)}`]) return; // 手动强制透明优先 · 不覆盖
      const wall = group.userData.wall;
      if (!wall) return;
      // 墙中点 world 坐标（在 world group 里 Z-up → Three.js Y-up 转换：世界中 scene pos [x,y,z] → Three pos [x, z, -y]）
      const wx = (wall.start[0] + wall.end[0]) / 2;
      const wy = (wall.start[1] + wall.end[1]) / 2;
      const wz_world = wall.height / 2;
      const wallWorldPos = new THREE.Vector3(wx, wz_world, -wy);
      // 相机到墙向量
      const toWall = wallWorldPos.clone().sub(camPos);
      const dist = toWall.length();
      toWall.normalize();
      // 如果相机背对墙（dot < 0）· 或距离 < 0.8m · 或距离 > 30m 看不见 · 都透
      const dot = camDir.dot(toWall);
      const tooClose = dist < 1.2;
      const behind = dot < 0.15;   // 相机基本不看向这面墙
      const fade = tooClose || behind;
      this._setMeshOpacity(group, fade ? 0.25 : 1.0);
    });
  }

  // ───────── 构建 ─────────

  async build(scene, mode) {
    this.currentScene = scene;
    if (mode === "procedural" || mode === "raw") this.renderMode = mode;

    // FIX Phase 3.J: rebuild 前先释放旧资源（避免悬空 selection / 材质泄漏）
    this._selection = null;
    if (this._cameraTween) this._cameraTween.cancel = true;
    if (this._introState) this._introState.cancel = true;
    // dispose 旧 geometry / material 防内存泄漏
    this.world.traverse((o) => {
      if (o.geometry) o.geometry.dispose?.();
      if (o.material) {
        if (Array.isArray(o.material)) o.material.forEach(m => m.dispose?.());
        else o.material.dispose?.();
      }
    });
    if (this.threeScene.environment && typeof this.threeScene.environment.dispose === "function") {
      this.threeScene.environment.dispose();
      this.threeScene.environment = null;
    }

    // 清空 world
    while (this.world.children.length) this.world.remove(this.world.children[0]);
    this.wallObjs.clear();
    this.objectObjs.clear();
    this.assemblyObjs.clear();
    this.lightObjs.clear();
    this._wallDirMap.clear();
    this.floorObj = null;
    this.ceilingObj = null;
    this.materials.forEach(m => m.dispose?.());
    this.materials.clear();
    // 构建 wall 方位映射（N/S/E/W）· 供透明 toggle 用
    this._classifyWalls(scene);

    // 环境光 ambient 兜底 · 复用实例 · 避免多次 build 累积
    if (!this._ambient) {
      this._ambient = new THREE.AmbientLight(0xffffff, 0.3);
      this.threeScene.add(this._ambient);
    } else {
      this._ambient.intensity = 0.3;
      if (this._ambient.parent !== this.threeScene) this.threeScene.add(this._ambient);
    }

    // HDRI（可选）
    if (scene.env?.hdri) {
      try {
        const rgbe = new RGBELoader();
        const tex = await new Promise((resolve, reject) => {
          rgbe.load(scene.env.hdri, resolve, undefined, reject);
        });
        tex.mapping = THREE.EquirectangularReflectionMapping;
        this.threeScene.environment = tex;
        if (scene.env.background_color) {
          this.threeScene.background = new THREE.Color(scene.env.background_color);
        }
      } catch (e) {
        console.warn("[renderer] HDRI load failed, using default env:", e);
        this.threeScene.background = new THREE.Color(scene.env?.background_color || "#0C0D10");
      }
    } else {
      this.threeScene.background = new THREE.Color(scene.env?.background_color || "#0C0D10");
    }

    // 建 floor
    if (scene.floor && scene.bounds) {
      this._buildFloor(scene.floor, scene.bounds);
    }
    // 建 ceiling
    if (scene.ceiling && scene.bounds) {
      this._buildCeiling(scene.ceiling, scene.bounds);
    }
    // 建 walls
    for (const w of scene.walls || []) {
      this._buildWall(w);
    }
    // 建 objects / assemblies · 两种 mode：
    //   · "procedural"：有 assemblies 则按 assembly 画（整把椅子一次） · parts 不显示 · 零件零件零叠
    //     · 防御性 fallback：若某 object 没归属 assembly（LLM / API 新加没补上 · 等 bug）
    //       仍按 raw 方式画出来 · 避免用户看到"我让 AI 加的东西消失了"
    //   · "raw"：按 objects[] 画（源 Blender 布局 · debug / 对比用）
    if (this.renderMode === "procedural" && (scene.assemblies || []).length > 0) {
      const assignedIds = new Set();
      for (const asm of scene.assemblies) {
        await this._buildAssembly(asm);
        for (const pid of asm.part_ids || []) assignedIds.add(pid);
      }
      // Orphan objects（没归属 assembly 的）按 raw 路径补画
      for (const o of scene.objects || []) {
        if (!assignedIds.has(o.id)) {
          await this._buildObject(o);
        }
      }
    } else {
      for (const o of scene.objects || []) {
        await this._buildObject(o);
      }
    }
    // 建 lights
    for (const l of scene.lights || []) {
      this._buildLight(l);
    }

    // Camera
    if (scene.camera_default) {
      const cd = scene.camera_default;
      // 注意：scene 里的 pos 是 Z-up；world rotation 已转 Y-up
      // 所以 camera 直接在 threeScene 层级放（不在 world 里），pos 需手动 swap
      const [x, y, z] = cd.pos;
      this.camera.position.set(x, z, -y);
      const [lx, ly, lz] = cd.lookAt;
      this.camera.lookAt(lx, lz, -ly);
      this.controls.target.set(lx, lz, -ly);
      this.camera.fov = cd.fov || 50;
      this.camera.updateProjectionMatrix();
    }

    // FIX Phase 3.J: 保留 rebuild 前的透明状态 · 否则 scene 改了透明就丢了
    this._applyTransparency();

    this._resize();
  }

  // 同 _getMaterial 但返回 clone · 让 opacity 调整不污染其他 mesh
  _getOwnMaterial(id) {
    const matData = this.currentScene?.materials?.[id] || { base_color: "#CCCCCC" };
    return makeStandardMaterial(matData);
  }

  _buildFloor(floor, bounds) {
    const geom = new THREE.BoxGeometry(bounds.w, bounds.d, floor.thickness || 0.02);
    const mesh = new THREE.Mesh(geom, this._getOwnMaterial(floor.material_id));
    mesh.position.set(0, 0, -(floor.thickness || 0.02) / 2);
    mesh.receiveShadow = true;
    mesh.userData.role = "floor";
    this.world.add(mesh);
    this.floorObj = mesh;
  }

  _buildCeiling(ceiling, bounds) {
    const thickness = ceiling.thickness || 0.05;
    const height = ceiling.height ?? (bounds.h || 2.8);
    const geom = new THREE.BoxGeometry(bounds.w, bounds.d, thickness);
    const mesh = new THREE.Mesh(geom, this._getOwnMaterial(ceiling.material_id));
    mesh.position.set(0, 0, height + thickness / 2);
    mesh.userData.role = "ceiling";
    this.world.add(mesh);
    this.ceilingObj = mesh;
  }

  _buildWall(wall) {
    const group = new THREE.Group();
    group.name = wall.id;

    const length = wallLength(wall);
    const thickness = wall.thickness || 0.1;
    const height = wall.height || 2.8;
    const midX = (wall.start[0] + wall.end[0]) / 2;
    const midY = (wall.start[1] + wall.end[1]) / 2;

    // 主墙体 · 每面墙用独立 material 克隆 · 避免 opacity 共享污染
    const geom = new THREE.BoxGeometry(length, thickness, height);
    const wallMesh = new THREE.Mesh(geom, this._getOwnMaterial(wall.material_id));
    wallMesh.castShadow = true;
    wallMesh.receiveShadow = true;
    // 局部：x=length, y=thickness, z=height
    // 但要旋转到 start→end 方向 · 底部在 z=0
    wallMesh.position.set(0, 0, height / 2);
    group.add(wallMesh);

    // 开洞（简化：贴玻璃面板 + 发光 · 不做真实 CSG）
    for (const op of wall.openings || []) {
      const panel = this._buildOpeningPanel(op, length, height, thickness);
      if (panel) group.add(panel);
    }

    group.position.set(midX, midY, 0);
    group.rotation.z = wallAngleRadZ(wall);
    group.userData.wall = wall;
    this.world.add(group);
    this.wallObjs.set(wall.id, group);
  }

  _buildOpeningPanel(op, wallLen, wallHeight, wallThickness) {
    // Opening 沿墙 x 方向 pos_along（距起点），局部 group 中心在墙中点
    const xLocal = op.pos_along - wallLen / 2;
    const zBottom = op.type === "door" ? 0 : (op.sill ?? 0.9);
    const zCenter = zBottom + op.height / 2;

    // 玻璃 / 门板
    const geom = new THREE.PlaneGeometry(op.width, op.height);
    const isWindow = op.type === "window";
    const mat = new THREE.MeshStandardMaterial({
      color: new THREE.Color(isWindow ? "#AEE1F2" : "#5A3D2B"),
      roughness: isWindow ? 0.05 : 0.5,
      metalness: 0,
      transparent: isWindow,
      opacity: isWindow ? 0.35 : 1,
      side: THREE.DoubleSide,
    });
    if (isWindow) mat.emissive = new THREE.Color("#DDEEFF"), mat.emissiveIntensity = 0.3;

    const panel = new THREE.Mesh(geom, mat);
    // plane 默认在 xy 面，法向 z；我们要它面向墙的 normal (局部 y 方向)
    panel.rotation.x = Math.PI / 2;
    panel.position.set(xLocal, wallThickness / 2 + 0.001, zCenter);
    panel.userData.opening = op;

    const group = new THREE.Group();
    group.add(panel);
    // 背面也贴一份
    const panel2 = panel.clone();
    panel2.position.y = -wallThickness / 2 - 0.001;
    panel2.rotation.x = -Math.PI / 2;
    group.add(panel2);
    group.userData.openingId = op.id;
    return group;
  }

  async _buildObject(obj) {
    const mesh = await loadFurniture(obj.type, obj.size, this.currentScene.materials, obj.material_id);

    // 3 路径坐标 / scale 策略：
    //   · GLB:        按 obj.size 全 scale（假设 GLB 是 1×1×1）+ 用 obj.pos
    //   · procedural: 按 default_size 已建好 · 不 scale；z 按 anchor 定（bottom→0 / top→bounds.h）
    //   · fallback box: 按 obj.size 已建好 + 用 obj.pos
    if (mesh.userData.glbType) {
      const [w, d, h] = obj.size;
      mesh.scale.set(w, d, h);
      mesh.position.set(obj.pos[0], obj.pos[1], obj.pos[2]);
    } else if (mesh.userData.procedural) {
      const anchor = mesh.userData.anchor || "bottom";
      const z = anchor === "top"
        ? (this.currentScene.bounds?.h || 2.8) - 0.001
        : 0;
      mesh.position.set(obj.pos[0], obj.pos[1], z);
    } else {
      // fallback box 已经 z=h/2 偏移（底贴地），x/y 用 obj.pos
      mesh.position.set(obj.pos[0], obj.pos[1], obj.pos[2]);
    }

    if (obj.rotation) {
      mesh.rotation.z = THREE.MathUtils.degToRad(obj.rotation[2]);
    }

    mesh.name = obj.id;
    mesh.userData.object = obj;
    this.world.add(mesh);
    this.objectObjs.set(obj.id, mesh);
  }

  // Phase 3 · procedural 模式主路径
  // Assembly = 一把椅子 / 一张桌子 · 用 assembly.type 调 procedural builder 画整体一次
  // Parts 不单独渲染 · 避免原 Blender mesh 叠加导致穿模
  async _buildAssembly(asm) {
    const mesh = await loadFurniture(
      asm.type,
      asm.size || [0.5, 0.5, 0.5],
      this.currentScene.materials,
      asm.material_id_primary,
    );

    if (mesh.userData.glbType) {
      const [w, d, h] = asm.size || [0.5, 0.5, 0.5];
      mesh.scale.set(w, d, h);
      mesh.position.set(asm.pos[0], asm.pos[1], asm.pos[2]);
    } else if (mesh.userData.procedural) {
      const anchor = mesh.userData.anchor || "bottom";
      const z = anchor === "top"
        ? (this.currentScene.bounds?.h || 2.8) - 0.001
        : 0;
      mesh.position.set(asm.pos[0], asm.pos[1], z);
      // Phase 3.M · FIX 穿墙：按 asm.size scale · 保证物体一定在 aggregate bbox 内
      // 之前 procedural 不 scale · 1m unit shelf 在 4m 房里飘 + 背板超出 bbox 穿墙
      const s = asm.size;
      if (s && s[0] > 0 && s[1] > 0 && s[2] > 0) {
        mesh.scale.set(s[0], s[1], s[2]);
      }
    } else {
      // fallback box（custom 类型）· asm.pos 保留源 z（如 Rug 在 z=0.005）
      mesh.position.set(asm.pos[0], asm.pos[1], asm.pos[2]);
    }

    if (asm.rotation) {
      mesh.rotation.z = THREE.MathUtils.degToRad(asm.rotation[2] || 0);
    }

    mesh.name = asm.id;
    mesh.userData.assembly = asm;
    this.world.add(mesh);
    this.assemblyObjs.set(asm.id, mesh);
  }

  // Phase 3 · 模式切换 · 触发重建
  async setRenderMode(mode) {
    if (mode !== "procedural" && mode !== "raw") return;
    if (mode === this.renderMode) return;
    this.renderMode = mode;
    if (this.currentScene) {
      await this.build(this.currentScene, mode);
    }
  }

  _buildLight(l) {
    let light = null;
    const cctColor = l.color ? new THREE.Color(l.color[0], l.color[1], l.color[2]) : new THREE.Color(0xffffff);
    const intensity = l.intensity ?? 1;

    switch (l.type) {
      case "sun":
      case "directional": {
        light = new THREE.DirectionalLight(cctColor, intensity);
        if (l.dir) {
          // scene dir 指向光线方向（光源 → target）
          light.position.set(-l.dir[0] * 10, -l.dir[1] * 10, -l.dir[2] * 10);
          light.target.position.set(0, 0, 0);
        } else {
          light.position.set(5, -5, 10);
        }
        light.castShadow = true;
        light.shadow.mapSize.set(1024, 1024);
        light.shadow.camera.left = -10;
        light.shadow.camera.right = 10;
        light.shadow.camera.top = 10;
        light.shadow.camera.bottom = -10;
        this.world.add(light.target);
        break;
      }
      case "point":
      case "pendant": {
        light = new THREE.PointLight(cctColor, intensity, 20, 2);
        light.position.set(l.pos[0], l.pos[1], l.pos[2]);
        light.castShadow = true;
        light.shadow.mapSize.set(512, 512);
        // 可视化小球
        const bulb = new THREE.Mesh(
          new THREE.SphereGeometry(0.05),
          new THREE.MeshBasicMaterial({ color: cctColor })
        );
        bulb.position.copy(light.position);
        this.world.add(bulb);
        light.userData.bulb = bulb;
        break;
      }
      case "area": {
        const size = l.size || 1;
        const sizeY = l.size_y || size;
        light = new THREE.RectAreaLight(cctColor, intensity, size, sizeY);
        light.position.set(l.pos[0], l.pos[1], l.pos[2]);
        // 默认朝下
        light.lookAt(l.pos[0], l.pos[1], 0);
        break;
      }
      case "spot": {
        light = new THREE.SpotLight(cctColor, intensity, 15, Math.PI / 4, 0.3, 2);
        light.position.set(l.pos[0], l.pos[1], l.pos[2]);
        if (l.target) {
          light.target.position.set(l.target[0], l.target[1], l.target[2]);
          this.world.add(light.target);
        }
        light.castShadow = true;
        break;
      }
      default:
        return;
    }
    light.name = l.id;
    light.userData.light = l;
    this.world.add(light);
    this.lightObjs.set(l.id, light);
  }

  // ───────── 增量更新 ─────────
  // 入参 applied[] 来自 applyOps 的 result.applied · 已经有 op + before + after
  // 此函数保持 renderer 状态与 newScene 一致
  async applyDelta(applied, newScene) {
    this.currentScene = newScene;
    for (const { op } of applied) {
      try {
        await this._dispatchDelta(op, newScene);
      } catch (e) {
        console.warn("[renderer] delta apply failed:", op, e);
      }
    }
  }

  async _dispatchDelta(op, scene) {
    switch (op.op) {
      case "move_object": {
        const target = this._findObject(op.id || op.id_or_name, scene);
        if (!target) return;
        const mesh = this.objectObjs.get(target.id);
        if (mesh) mesh.position.set(target.pos[0], target.pos[1], target.pos[2]);
        break;
      }
      case "rotate_object": {
        const target = this._findObject(op.id || op.id_or_name, scene);
        if (!target) return;
        const mesh = this.objectObjs.get(target.id);
        if (mesh && target.rotation) {
          mesh.rotation.set(
            THREE.MathUtils.degToRad(target.rotation[0]),
            THREE.MathUtils.degToRad(target.rotation[1]),
            THREE.MathUtils.degToRad(target.rotation[2])
          );
        }
        break;
      }
      case "resize_object": {
        const target = this._findObject(op.id || op.id_or_name, scene);
        if (!target) return;
        const mesh = this.objectObjs.get(target.id);
        if (mesh) {
          if (mesh.userData.glbType) {
            mesh.scale.set(target.size[0], target.size[1], target.size[2]);
          } else {
            // primitive box: 重新建
            this._removeObject(target.id);
            await this._buildObject(target);
          }
        }
        break;
      }
      case "remove_object":
        this._removeObject(op.id || this._matchedObjectId(op, scene));
        break;
      case "add_object": {
        // Phase 3.L · add_object 现在会同时 push 一个 single_object assembly
        // procedural 模式：画 assembly 即可
        // raw 模式：画 object
        const objs = scene.objects || [];
        const asms = scene.assemblies || [];
        const addedObj = objs[objs.length - 1];
        const addedAsm = asms[asms.length - 1];
        if (this.renderMode === "procedural" && addedAsm && addedObj?.assembly_id === addedAsm.id) {
          await this._buildAssembly(addedAsm);
        } else if (addedObj) {
          await this._buildObject(addedObj);
        }
        break;
      }
      // ── Phase 3 assembly ops · procedural 模式路径 ──
      case "move_assembly": {
        const asm = this._findAssembly(op.id || op.id_or_name, scene);
        if (!asm) return;
        const mesh = this.assemblyObjs.get(asm.id);
        if (mesh) {
          // Assembly 的 z 由 procedural anchor 决定 · 只改 x,y 跟 pos · 保持原 anchor z
          const currZ = mesh.position.z;
          mesh.position.set(asm.pos[0], asm.pos[1], currZ);
        }
        break;
      }
      case "rotate_assembly": {
        const asm = this._findAssembly(op.id || op.id_or_name, scene);
        if (!asm) return;
        const mesh = this.assemblyObjs.get(asm.id);
        if (mesh && asm.rotation) {
          mesh.rotation.z = THREE.MathUtils.degToRad(asm.rotation[2] || 0);
        }
        break;
      }
      case "remove_assembly": {
        const asmId = op.id || op.id_or_name;
        // 可能是 fuzzy id · 找到实际 id
        const before = (this.assemblyObjs.get(asmId) ? asmId : null) ||
                       Array.from(this.assemblyObjs.keys()).find(k => {
                         const m = this.assemblyObjs.get(k);
                         return m?.userData?.assembly?.label_zh === asmId ||
                                m?.userData?.assembly?.type === asmId;
                       });
        if (before) this._removeAssembly(before);
        break;
      }
      case "move_wall":
      case "resize_wall":
      case "add_opening":
      case "remove_opening": {
        const wallId = op.id || op.wall_id;
        this._removeWall(wallId);
        const wallNow = (scene.walls || []).find((w) => w.id === wallId);
        if (wallNow) this._buildWall(wallNow);
        break;
      }
      case "add_light": {
        const lights = scene.lights || [];
        const added = lights[lights.length - 1];
        if (added) this._buildLight(added);
        break;
      }
      case "change_light": {
        const target = this._findLight(op.id || op.id_or_name, scene);
        if (!target) return;
        const lights = Array.isArray(target) ? target : [target];
        for (const l of lights) {
          const obj = this.lightObjs.get(l.id);
          if (!obj) continue;
          if (l.intensity != null) obj.intensity = l.intensity;
          if (l.color) obj.color = new THREE.Color(l.color[0], l.color[1], l.color[2]);
        }
        break;
      }
      case "remove_light": {
        const target = this._findLight(op.id || op.id_or_name, this.currentScene);
        if (!target) return;
        const ids = Array.isArray(target) ? target.map((t) => t.id) : [target.id];
        for (const id of ids) this._removeLight(id);
        break;
      }
      case "change_material": {
        // 清材质缓存 · 重建对应 entity
        const target = op.target;
        if (target === "floor" && this.floorObj && scene.floor) {
          this.world.remove(this.floorObj);
          this._buildFloor(scene.floor, scene.bounds);
        } else if (target === "ceiling" && this.ceilingObj && scene.ceiling) {
          this.world.remove(this.ceilingObj);
          this._buildCeiling(scene.ceiling, scene.bounds);
        } else if (this.wallObjs.has(target)) {
          const wall = (scene.walls || []).find((w) => w.id === target);
          if (wall) {
            this._removeWall(target);
            this._buildWall(wall);
          }
        } else {
          // object
          const obj = this._findObject(target, scene);
          if (obj) {
            this._removeObject(obj.id);
            await this._buildObject(obj);
          }
        }
        // invalidate material cache
        this.materials.clear();
        break;
      }
    }
  }

  _removeObject(id) {
    const mesh = this.objectObjs.get(id);
    if (!mesh) return;
    this.world.remove(mesh);
    mesh.traverse((o) => {
      if (o.geometry) o.geometry.dispose();
      if (o.material) {
        if (Array.isArray(o.material)) o.material.forEach((m) => m.dispose());
        else o.material.dispose();
      }
    });
    this.objectObjs.delete(id);
  }

  _removeWall(id) {
    const group = this.wallObjs.get(id);
    if (!group) return;
    this.world.remove(group);
    group.traverse((o) => {
      if (o.geometry) o.geometry.dispose();
      if (o.material) {
        if (Array.isArray(o.material)) o.material.forEach((m) => m.dispose());
        else o.material.dispose();
      }
    });
    this.wallObjs.delete(id);
  }

  _removeLight(id) {
    const light = this.lightObjs.get(id);
    if (!light) return;
    this.world.remove(light);
    if (light.userData.bulb) this.world.remove(light.userData.bulb);
    if (light.target && light.target.parent) light.target.parent.remove(light.target);
    this.lightObjs.delete(id);
  }

  _removeAssembly(id) {
    const mesh = this.assemblyObjs.get(id);
    if (!mesh) return;
    this.world.remove(mesh);
    mesh.traverse((o) => {
      if (o.geometry) o.geometry.dispose();
      if (o.material) {
        if (Array.isArray(o.material)) o.material.forEach((m) => m.dispose());
        else o.material.dispose();
      }
    });
    this.assemblyObjs.delete(id);
  }

  _matchedObjectId(op, scene) {
    // 从 scene 里推断 op 操作的是哪个 id（scene 已经是 after-op 的 newScene · remove_object 情况下已消失）
    // 对 remove_object：op.id 就是被删 id，直接用
    return op.id || op.id_or_name;
  }

  // 内部 fuzzy find（避免依赖 scene-ops.js；重复一点点逻辑以保持 module 独立）
  _findObject(query, scene) {
    if (!query) return null;
    const q = String(query).trim().toLowerCase();
    const objects = scene?.objects || [];
    return (
      objects.find((o) => o.id?.toLowerCase() === q) ||
      objects.find((o) => o.id?.toLowerCase() === `obj_${q}`) ||
      objects.find((o) => o.label_zh === query || o.label_en?.toLowerCase() === q) ||
      objects.find(
        (o) =>
          (o.label_zh || "").includes(query) ||
          (o.label_en || "").toLowerCase().includes(q)
      ) ||
      objects.find((o) => (o.type || "").toLowerCase().includes(q)) ||
      null
    );
  }

  _findAssembly(query, scene) {
    if (!query) return null;
    const q = String(query).trim().toLowerCase();
    const asms = scene?.assemblies || [];
    return (
      asms.find((a) => a.id?.toLowerCase() === q) ||
      asms.find((a) => a.label_zh === query || a.label_en?.toLowerCase() === q) ||
      asms.find((a) => (a.label_zh || "").includes(query) || (a.label_en || "").toLowerCase().includes(q)) ||
      asms.find((a) => (a.type || "").toLowerCase().includes(q)) ||
      null
    );
  }

  _findLight(query, scene) {
    if (!query) return null;
    const q = String(query).trim().toLowerCase();
    const lights = scene?.lights || [];
    if (q === "all") return lights;
    return (
      lights.find((l) => l.id?.toLowerCase() === q) ||
      lights.filter((l) => l.type?.toLowerCase() === q) ||
      null
    );
  }
}

// 暴露为 window global（app.jsx 走 babel，不用 ESM）
if (typeof window !== "undefined") {
  window.SceneRenderer = SceneRenderer;
}
