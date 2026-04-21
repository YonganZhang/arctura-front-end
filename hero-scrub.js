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

  function draw(frameIdx) {
    const img = imgs[frameIdx];
    if (!img || !img.complete || img.naturalWidth === 0) {
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

  // 自动播 · 从第一帧 → 最后一帧（图纸 → 3D 建筑）· 循环
  // 注：如果方向反了（看起来是从 3D 变成图纸）· 把 DIRECTION 改成 -1
  const DIRECTION = 1;           // +1 = 1→130（图纸→3D）· -1 = 130→1（3D→图纸）
  const START = DIRECTION === -1 ? FRAMES - 1 : 0;
  const END = DIRECTION === -1 ? 0 : FRAMES - 1;

  let currentFrame = START;
  let playing = true;
  let lastTick = 0;
  const frameInterval = 1000 / FPS;

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
