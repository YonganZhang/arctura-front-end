// hero-scrub.js — 自动播放 canvas 动画（130 帧循环 · 不再依赖 scroll）
(function () {
  const FRAMES = 130;
  const FPS = 28;               // 约 4.6 秒一次循环
  const FRAME_URL = (i) => `/assets/hero/cleanspace-seq/${String(i).padStart(3, "0")}.webp`;

  const canvas = document.getElementById("hero-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const bar = document.getElementById("hero-3d-bar");
  const section = document.querySelector(".section-scroll-3d");
  if (!section) return;

  // 播放方向 · DIRECTION -1 = 130→1（图纸→3D 建筑）
  const DIRECTION = -1;
  const START = DIRECTION === -1 ? FRAMES - 1 : 0;
  let currentFrame = START;
  let playing = true;
  let lastTick = 0;
  const frameInterval = 1000 / FPS;

  // 预加载 · 所有 130 帧并行 · img cache
  // 注：onload 必须在 src 之前设 · 否则缓存的图会错过 onload 触发
  const imgs = new Array(FRAMES);
  let loadedCount = 0;
  let firstReady = false;
  for (let i = 0; i < FRAMES; i++) {
    const img = new Image();
    img.onload = () => {
      loadedCount++;
      if (i === 0 && !firstReady) {
        firstReady = true;
        draw(0);
      }
      // 首帧加载后立刻画一次
      if (loadedCount === 1 || loadedCount % 10 === 0 || loadedCount === FRAMES) {
        draw(currentFrame);
      }
    };
    img.src = FRAME_URL(i + 1);
    imgs[i] = img;
  }

  // 窗口 resize 后 · canvas intrinsic 尺寸与布局对齐 · 保证 drawImage 铺满
  function syncCanvasSize() {
    const rect = canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    const w = Math.max(1, Math.floor(rect.width * dpr));
    const h = Math.max(1, Math.floor(rect.height * dpr));
    if (canvas.width !== w || canvas.height !== h) {
      canvas.width = w;
      canvas.height = h;
    }
  }

  // 手动 cover-style 绘制 · 模仿 CSS object-fit: cover · 但对 canvas 生效
  // 把 1920×1920 源图按"占满容器 + 裁切多余"规则画满 canvas
  function drawCover(img) {
    const cw = canvas.width, ch = canvas.height;
    if (!cw || !ch || !img.naturalWidth) return;
    const sw = img.naturalWidth, sh = img.naturalHeight;
    const sAspect = sw / sh;
    const cAspect = cw / ch;
    let sx, sy, sWidth, sHeight;
    if (sAspect > cAspect) {
      // 源图更宽 · 左右裁切
      sHeight = sh;
      sWidth = sh * cAspect;
      sx = (sw - sWidth) / 2;
      sy = 0;
    } else {
      // 源图更高（或相等）· 上下裁切 · 源是 1:1 · 容器 16:9 → 裁上下
      sWidth = sw;
      sHeight = sw / cAspect;
      sx = 0;
      sy = (sh - sHeight) / 2;
    }
    ctx.clearRect(0, 0, cw, ch);
    ctx.drawImage(img, sx, sy, sWidth, sHeight, 0, 0, cw, ch);
  }

  function draw(frameIdx) {
    const img = imgs[frameIdx];
    let target = img;
    if (!target || !target.complete || target.naturalWidth === 0) {
      let nearest = -1, delta = Infinity;
      for (let i = 0; i < FRAMES; i++) {
        if (imgs[i]?.complete && imgs[i].naturalWidth > 0) {
          const d = Math.abs(i - frameIdx);
          if (d < delta) { delta = d; nearest = i; }
        }
      }
      if (nearest < 0) return;
      target = imgs[nearest];
    }
    drawCover(target);
  }

  // 初次 + resize 时同步 canvas size
  syncCanvasSize();
  window.addEventListener("resize", () => {
    syncCanvasSize();
    draw(currentFrame >= 0 ? currentFrame : 0);
  }, { passive: true });

  // （DIRECTION / currentFrame / playing 等已在顶部声明）
  function tick(now) {
    if (!playing) { requestAnimationFrame(tick); return; }
    if (now - lastTick >= frameInterval) {
      lastTick = now;
      draw(currentFrame);
      if (bar) {
        // 进度条：按播放方向计算 0→100%
        const p = DIRECTION === -1 ? (FRAMES - 1 - currentFrame) / (FRAMES - 1) : currentFrame / (FRAMES - 1);
        bar.style.width = (p * 100).toFixed(1) + "%";
      }
      currentFrame += DIRECTION;
      // 循环重置
      if (DIRECTION === -1 && currentFrame < 0) currentFrame = FRAMES - 1;
      if (DIRECTION === 1 && currentFrame >= FRAMES) currentFrame = 0;
    }
    requestAnimationFrame(tick);
  }

  // 在视口外暂停 · 省 CPU
  if ("IntersectionObserver" in window) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach(e => { playing = e.isIntersecting; });
    }, { threshold: 0.01 });
    io.observe(section);
  }

  requestAnimationFrame(tick);
})();
