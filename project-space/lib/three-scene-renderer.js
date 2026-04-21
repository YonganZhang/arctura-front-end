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
    this.objectObjs = new Map();
    this.lightObjs = new Map();
    this.floorObj = null;
    this.ceilingObj = null;

    // 当前 scene 数据（快照 · 给 applyOps 查用）
    this.currentScene = null;

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
      this.renderer.render(this.threeScene, this.camera);
      this._rafId = requestAnimationFrame(tick);
    };
    this._rafId = requestAnimationFrame(tick);
  }

  dispose() {
    this._isRunning = false;
    if (this._rafId) cancelAnimationFrame(this._rafId);
    if (this._resizeObserver) this._resizeObserver.disconnect();
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

  // ───────── 构建 ─────────

  async build(scene) {
    this.currentScene = scene;

    // 清空 world
    while (this.world.children.length) this.world.remove(this.world.children[0]);
    this.wallObjs.clear();
    this.objectObjs.clear();
    this.lightObjs.clear();
    this.floorObj = null;
    this.ceilingObj = null;
    this.materials.clear();

    // 环境光 ambient 兜底
    this.threeScene.add(new THREE.AmbientLight(0xffffff, 0.3));

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
    // 建 objects（GLB / primitive）
    for (const o of scene.objects || []) {
      await this._buildObject(o);
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

    this._resize();
  }

  _buildFloor(floor, bounds) {
    const geom = new THREE.BoxGeometry(bounds.w, bounds.d, floor.thickness || 0.02);
    const mesh = new THREE.Mesh(geom, this._getMaterial(floor.material_id));
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
    const mesh = new THREE.Mesh(geom, this._getMaterial(ceiling.material_id));
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

    // 主墙体
    const geom = new THREE.BoxGeometry(length, thickness, height);
    const wallMesh = new THREE.Mesh(geom, this._getMaterial(wall.material_id));
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
    // 如果是 GLB 模型 · 按 default_size 和实际 size 缩放
    if (mesh.userData.glbType) {
      const lib = (await import("./furniture-loader.js")).loadLibrary ? null : null;
      // 简化：按 size 直接 scale · 假设 GLB 是单位尺寸（1×1×1）· Phase E 再统一
      const [w, d, h] = obj.size;
      mesh.scale.set(w, d, h);
    }
    mesh.position.set(obj.pos[0], obj.pos[1], obj.pos[2]);
    if (obj.rotation) {
      mesh.rotation.set(
        THREE.MathUtils.degToRad(obj.rotation[0]),
        THREE.MathUtils.degToRad(obj.rotation[1]),
        THREE.MathUtils.degToRad(obj.rotation[2])
      );
    }
    // Fallback box uses material_id from scene · already colored
    // For GLB models, optionally override material tint via material_id (Phase E)

    mesh.name = obj.id;
    mesh.userData.object = obj;
    this.world.add(mesh);
    this.objectObjs.set(obj.id, mesh);
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
        // 找到新加的（最后一个 matching type）
        const objs = scene.objects || [];
        const added = objs[objs.length - 1];
        if (added) await this._buildObject(added);
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
