// hero-scrub.js — 滚动驱动 hero canvas 动画
// 130 帧 WebP 序列 · scroll 位置映射到 frame index · drawImage 到 canvas
(function () {
  const FRAMES = 130;
  const FRAME_URL = (i) => `/assets/hero/cleanspace-seq/${String(i).padStart(3, "0")}.webp`;

  const canvas = document.getElementById("hero-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const bar = document.getElementById("hero-3d-bar");
  const hero = document.querySelector(".hero");
  if (!hero) return;

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
      // 不断触发 onScroll · 帮助首屏加载完逐步能绘到当前帧
      if (loadedCount % 10 === 0 || loadedCount === FRAMES) onScroll();
    };
    img.src = FRAME_URL(i + 1);
    imgs[i] = img;
  }

  // 滚动进度 0..1 · 以 hero 整体经过视口为参考
  //   hero 顶部 在 viewport 顶部 = 0
  //   hero 底部 离开 viewport 顶部 = 1
  function progress() {
    const rect = hero.getBoundingClientRect();
    const total = Math.max(1, rect.height);
    const y = -rect.top; // 滚过多少 hero
    return Math.max(0, Math.min(1, y / total));
  }

  function draw(frameIdx) {
    const img = imgs[frameIdx];
    if (!img || !img.complete || img.naturalWidth === 0) {
      // 未加载好 · 找最近的已加载的帧
      let nearest = -1, delta = Infinity;
      for (let i = 0; i < FRAMES; i++) {
        if (imgs[i]?.complete && imgs[i].naturalWidth > 0) {
          const d = Math.abs(i - frameIdx);
          if (d < delta) { delta = d; nearest = i; }
        }
      }
      if (nearest < 0) return;
      ctx.drawImage(imgs[nearest], 0, 0, canvas.width, canvas.height);
    } else {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
    }
  }

  let rafId = null;
  let currentFrame = -1;
  function onScroll() {
    if (rafId) return;
    rafId = requestAnimationFrame(() => {
      rafId = null;
      const p = progress();
      const frame = Math.round(p * (FRAMES - 1));
      if (frame !== currentFrame) {
        currentFrame = frame;
        draw(frame);
        if (bar) bar.style.width = (p * 100).toFixed(1) + "%";
      }
    });
  }

  window.addEventListener("scroll", onScroll, { passive: true });
  window.addEventListener("resize", onScroll, { passive: true });
  document.addEventListener("DOMContentLoaded", onScroll);
  // 初始绘制
  onScroll();
})();
