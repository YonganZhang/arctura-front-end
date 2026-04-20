// ======= MVP GALLERY =======
const MVP_INDEX_URL = "/data/mvps-index.json";

function complianceBadge(c) {
  if (!c || c === "—") return { cls: "", label: "—", placeholder: true };
  if (/^CONDITIONAL/i.test(c)) return { cls: "warn", label: "REVIEW" };
  return { cls: "", label: "PASS" };
}

function typeLabel(t) {
  if (t === "P1-interior") return "Interior";
  if (t === "P2-architecture") return "Architecture";
  return t || "";
}

function escapeAttr(s) {
  return String(s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function mvpCard(m) {
  const comp = complianceBadge(m.compliance);
  const idNum = (m.slug || "").split("-")[0] || "--";
  const thumb = m.thumb ? `style="background-image:url('${escapeAttr(m.thumb)}')"` : "";
  const area = m.area_m2 ? ` · ${m.area_m2} m²` : "";
  const cost = (m.cost_per_m2 != null && !isNaN(m.cost_per_m2)) ? Math.round(m.cost_per_m2).toLocaleString() : "—";
  const eui = (m.eui != null && !isNaN(m.eui)) ? m.eui : "—";
  const currency = m.currency || "HK$";
  const name = escapeAttr(m.name || m.slug || "Untitled");
  const icon = (m.name || "?").slice(0, 1);
  return `
    <a class="mvp" data-cat="${escapeAttr(m.cat || "")}" data-type="${escapeAttr(m.type || "")}"
       href="/project/${encodeURIComponent(m.slug)}/" aria-label="Open ${name}">
      <div class="mvp-comp ${comp.cls}">${comp.label}</div>
      <div class="mvp-thumb ${m.thumb ? "" : "placeholder"}" data-icon="${escapeAttr(icon)}" ${thumb}></div>
      <div class="mvp-id">MVP-${escapeAttr(idNum)}</div>
      <div class="mvp-name">${name}</div>
      <div class="mvp-type">${escapeAttr(typeLabel(m.type))}${area}</div>
      <div class="mvp-metrics">
        <div class="mvp-metric">
          <div class="mm-label">EUI kWh/m²</div>
          <div class="mm-val">${eui}</div>
        </div>
        <div class="mvp-metric">
          <div class="mm-label">${escapeAttr(currency)} / m²</div>
          <div class="mm-val">${cost}</div>
        </div>
      </div>
    </a>`;
}

function renderMvps(filter = "all") {
  const grid = document.getElementById("mvp-grid");
  if (!grid) return;
  const all = window.MVPS || [];
  const items = filter === "all" ? all : all.filter(m => m.cat === filter);
  if (!items.length) {
    grid.innerHTML = `<div class="mvp-empty" style="grid-column:1/-1;padding:40px;text-align:center;color:var(--ink-mute)">No MVPs in this category yet.</div>`;
    return;
  }
  grid.innerHTML = items.map(mvpCard).join("");
}

async function loadMvpIndex() {
  const grid = document.getElementById("mvp-grid");
  if (grid) {
    grid.innerHTML = `<div style="grid-column:1/-1;padding:40px;text-align:center;color:var(--ink-mute);font-family:var(--f-mono);font-size:12px">Loading MVPs…</div>`;
  }
  try {
    const r = await fetch(MVP_INDEX_URL, { cache: "no-cache" });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    window.MVPS = await r.json();
    renderMvps();
  } catch (err) {
    console.error("[mvp-index] fetch failed:", err);
    if (grid) {
      grid.innerHTML = `<div style="grid-column:1/-1;padding:40px;text-align:center;color:var(--warn)">Failed to load MVP index · ${escapeAttr(String(err.message || err))}</div>`;
    }
  }
}

document.addEventListener("DOMContentLoaded", () => {
  loadMvpIndex();

  function setFilter(filter) {
    document.querySelectorAll(".gal-filter").forEach(b => {
      b.classList.toggle("active", b.dataset.filter === filter);
    });
    document.querySelectorAll(".industry-card").forEach(c => {
      c.classList.toggle("active", c.dataset.filter === filter);
    });
    renderMvps(filter);
  }

  document.querySelectorAll(".gal-filter").forEach(btn => {
    btn.addEventListener("click", () => setFilter(btn.dataset.filter));
  });

  document.querySelectorAll(".industry-card").forEach(card => {
    card.addEventListener("click", (e) => {
      e.preventDefault();
      setFilter(card.dataset.filter);
      // 滚动到 MVP grid
      const grid = document.getElementById("mvp-grid");
      if (grid) grid.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });
});

// ======= TWEAKS =======
function applyTweaks(t) {
  // Accent hue
  if (t.accentHue != null) {
    const h = t.accentHue;
    const r = document.documentElement.style;
    r.setProperty('--accent', `oklch(0.68 0.09 ${h})`);
    r.setProperty('--accent-2', `oklch(0.75 0.09 ${h})`);
    r.setProperty('--accent-dim', `oklch(0.68 0.09 ${h} / 0.14)`);
    r.setProperty('--accent-line', `oklch(0.68 0.09 ${h} / 0.42)`);
    r.setProperty('--accent-ink', `oklch(0.38 0.06 ${h})`);
  }
  // Tagline
  if (t.heroTagline && document.getElementById('hero-title')) {
    const parts = t.heroTagline.split(/\n|\\n/);
    // keep <em> on "compiles" if present
    document.getElementById('hero-title').innerHTML = parts.map(p =>
      p.replace(/\*(.+?)\*/g, '<em>$1</em>').replace(/compiles\.?$/i, m => `<em>${m}</em>`)
    ).join('<br/>');
  }
  if (t.heroSub && document.getElementById('hero-sub')) {
    document.getElementById('hero-sub').textContent = t.heroSub;
  }
  // Density / layout
  if (t.layoutMode) {
    document.body.dataset.density = t.layoutMode;
    if (t.layoutMode === 'compact') {
      document.documentElement.style.setProperty('--maxw', '1200px');
      document.querySelectorAll('section').forEach(s => s.style.padding = '80px 0');
    } else if (t.layoutMode === 'editorial') {
      document.documentElement.style.setProperty('--maxw', '1440px');
      document.querySelectorAll('section').forEach(s => s.style.padding = '160px 0');
    } else {
      document.documentElement.style.removeProperty('--maxw');
      document.querySelectorAll('section').forEach(s => s.style.padding = '');
    }
  }
}

applyTweaks(window.TWEAKS || {});

// Tweaks panel wiring
(function(){
  const panel = document.getElementById('tw-panel');
  const t = window.TWEAKS || {};

  const hueInput = document.getElementById('tw-hue');
  const hueVal = document.getElementById('tw-hue-val');
  hueInput.value = t.accentHue ?? 165;
  hueVal.textContent = hueInput.value;
  hueInput.addEventListener('input', e => {
    const v = +e.target.value;
    hueVal.textContent = v;
    applyTweaks({ accentHue: v });
    persist({ accentHue: v });
  });

  const tagInput = document.getElementById('tw-tagline');
  tagInput.value = (t.heroTagline || '').replace(/\n/g, '\\n');
  tagInput.addEventListener('change', e => {
    applyTweaks({ heroTagline: e.target.value });
    persist({ heroTagline: e.target.value });
  });

  const subInput = document.getElementById('tw-sub');
  subInput.value = t.heroSub || '';
  subInput.addEventListener('change', e => {
    applyTweaks({ heroSub: e.target.value });
    persist({ heroSub: e.target.value });
  });

  document.querySelectorAll('#tw-density .tw-opt').forEach(o => {
    if (o.dataset.val === (t.layoutMode || 'standard')) o.classList.add('active');
    else o.classList.remove('active');
    o.addEventListener('click', () => {
      document.querySelectorAll('#tw-density .tw-opt').forEach(x => x.classList.remove('active'));
      o.classList.add('active');
      applyTweaks({ layoutMode: o.dataset.val });
      persist({ layoutMode: o.dataset.val });
    });
  });

  document.getElementById('tw-close').addEventListener('click', deactivate);

  function activate() { panel.classList.add('open'); }
  function deactivate() { panel.classList.remove('open'); }
  function persist(edits) {
    try { window.parent.postMessage({ type: '__edit_mode_set_keys', edits }, '*'); } catch(e){}
  }

  window.addEventListener('message', (e) => {
    if (!e.data || typeof e.data !== 'object') return;
    if (e.data.type === '__activate_edit_mode') activate();
    if (e.data.type === '__deactivate_edit_mode') deactivate();
  });
  try { window.parent.postMessage({ type: '__edit_mode_available' }, '*'); } catch(e){}
})();


// ============ ANIMATED HERO DEMO ============
(function(){
  const demo = document.getElementById('demo');
  if (!demo) return;

  const BRIEFS = [
    {
      text: "design a 60m² zen tea room in hong kong, budget HK$500K, warm tatami, tea bar for 4",
      project: {
        eui: 88.4, euiItems: [37.1, 21.2, 19.5, 10.6],
        cost: 498, total: 498300,
        boq: [
          { name: "Tatami flooring · 30 m²", qty: "30 m²", val: "62,400" },
          { name: "Oak slat screen · custom", qty: "1 set", val: "84,500" },
          { name: "Tea bar · live-edge elm", qty: "1", val: "118,200" },
          { name: "Lighting · Bega + custom", qty: "24 pc", val: "71,600" },
          { name: "HVAC retrofit + controls", qty: "1 lot", val: "86,400" },
          { name: "Finishes · lime + teak", qty: "lot", val: "48,200" },
          { name: "Joinery · back-of-house", qty: "lot", val: "27,000" },
        ],
        compliance: "PASS",
      },
    },
    {
      text: "boutique hotel lobby, 120m² shenzhen, ASHRAE baseline, 9m ceiling, check-in + lounge",
      project: {
        eui: 112.0, euiItems: [58.2, 24.8, 18.4, 10.6],
        cost: 1704, total: 1704000,
        boq: [
          { name: "Stone cladding · travertine", qty: "180 m²", val: "412,000" },
          { name: "Reception desk · custom", qty: "1", val: "184,000" },
          { name: "Pendant installation", qty: "1 set", val: "248,000" },
          { name: "Lounge seating · 8 pc", qty: "8", val: "296,000" },
          { name: "HVAC · high-volume VRF", qty: "1 lot", val: "318,000" },
          { name: "Acoustic ceiling system", qty: "120 m²", val: "168,000" },
          { name: "Wayfinding + art", qty: "lot", val: "78,000" },
        ],
        compliance: "PASS",
      },
    },
    {
      text: "creative studio for 12 people, tokyo, 180m², warm minimal, natural light first",
      project: {
        eui: 84.2, euiItems: [31.2, 28.1, 19.4, 5.5],
        cost: 1152, total: 1152000,
        boq: [
          { name: "Oak plank floor · 180 m²", qty: "180 m²", val: "342,000" },
          { name: "Linear desk · custom", qty: "12 pos", val: "198,000" },
          { name: "Task chairs · Herman Miller", qty: "12", val: "168,000" },
          { name: "Phone booths × 3", qty: "3", val: "142,000" },
          { name: "Pendant + task lighting", qty: "lot", val: "128,000" },
          { name: "Acoustic panels · wool felt", qty: "80 m²", val: "96,000" },
          { name: "Pantry fit-out", qty: "1", val: "78,000" },
        ],
        compliance: "PASS",
      },
    },
  ];

  const STAGES = [
    { id: "P0", label: "reading brief" },
    { id: "P1", label: "locking scope" },
    { id: "P7", label: "drawing plans" },
    { id: "P8", label: "rendering" },
    { id: "P6", label: "costing + energy" },
    { id: "P11", label: "packaging decks" },
  ];

  // Build stage indicators
  const stagesEl = document.getElementById('demo-stages');
  stagesEl.innerHTML = STAGES.map(s => `<span class="demo-stage-item" data-id="${s.id}">${s.label}</span>`).join('');

  const typedEl = document.getElementById('demo-typed');
  const progressEl = document.getElementById('demo-progress-bar');
  const statusEl = document.getElementById('demo-status');
  const tabs = [...document.querySelectorAll('.demo-tab')];
  const panels = [...document.querySelectorAll('.demo-panel')];
  const planSvg = document.getElementById('demo-plan');
  const kpiEls = [...document.querySelectorAll('.demo-kpi-v[data-count]')];
  const erFills = [...document.querySelectorAll('.er-fill[data-pct]')];
  const erVals = [...document.querySelectorAll('.er-val[data-count]')];
  const erTotal = document.querySelector('.er-total-val[data-count]');
  const boqRowsEl = document.getElementById('demo-boq-rows');
  const boqTotal = document.querySelector('.boq-total-val[data-count]');

  let cancelled = false;
  let briefIdx = 0;

  const sleep = ms => new Promise(r => setTimeout(r, ms));

  function setTab(name) {
    tabs.forEach(t => t.classList.toggle('active', t.dataset.tab === name));
    panels.forEach(p => p.classList.toggle('active', p.dataset.panel === name));
  }

  async function typeText(text) {
    typedEl.textContent = '';
    for (let i = 0; i < text.length; i++) {
      if (cancelled) return;
      typedEl.textContent += text[i];
      await sleep(22 + Math.random() * 28);
    }
  }

  function markStage(id, state) {
    const el = stagesEl.querySelector(`[data-id="${id}"]`);
    if (!el) return;
    el.classList.remove('on', 'done');
    if (state) el.classList.add(state);
  }

  function resetStages() {
    stagesEl.querySelectorAll('.demo-stage-item').forEach(e => e.classList.remove('on', 'done'));
  }

  function animateNumber(el, target, duration = 900, suffix) {
    const prefix = el.dataset.prefix || '';
    const suf = el.dataset.suffix || '';
    const start = performance.now();
    const from = 0;
    function frame(now) {
      const t = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - t, 3);
      const v = from + (target - from) * eased;
      const out = target < 10 ? v.toFixed(1)
                : target < 1000 ? v.toFixed(1)
                : Math.round(v).toLocaleString();
      el.textContent = prefix + out + suf;
      if (t < 1) requestAnimationFrame(frame);
      else el.textContent = prefix + (target < 10 ? target.toFixed(1)
                                     : target < 1000 ? target.toFixed(1)
                                     : Math.round(target).toLocaleString()) + suf;
    }
    requestAnimationFrame(frame);
  }

  function setEnergyFills(items) {
    const total = items.reduce((a,b) => a+b, 0);
    erFills.forEach((el, i) => {
      const pct = items[i] ? (items[i] / total * 100) : 0;
      el.style.setProperty('--pct', pct + '%');
    });
    erVals.forEach((el, i) => {
      el.dataset.count = items[i];
    });
  }

  function buildBoq(items, total) {
    boqRowsEl.innerHTML = items.map(r => `
      <div class="demo-boq-row">
        <span class="boq-name">${r.name}</span>
        <span class="boq-qty">${r.qty}</span>
        <span class="boq-val">${r.val}</span>
      </div>
    `).join('');
    boqTotal.dataset.count = total;
  }

  async function revealBoqRows() {
    const rows = boqRowsEl.querySelectorAll('.demo-boq-row');
    for (const r of rows) {
      if (cancelled) return;
      r.classList.add('on');
      await sleep(90);
    }
  }

  async function runOnce(brief) {
    const p = brief.project;

    // Reset
    cancelled = false;
    resetStages();
    statusEl.classList.remove('done');
    statusEl.innerHTML = '<span class="dot"></span>compiling';
    progressEl.style.width = '0%';
    planSvg.classList.remove('draw');
    kpiEls.forEach(el => el.textContent = '—');
    document.querySelector('.demo-kpi-ok').textContent = '—';
    erFills.forEach(el => el.style.setProperty('--pct', '0%'));
    erVals.forEach(el => el.textContent = '0');
    if (erTotal) erTotal.textContent = '0';
    if (boqTotal) boqTotal.textContent = '0';
    boqRowsEl.innerHTML = '';

    // Configure data
    setEnergyFills(p.euiItems);
    erTotal.dataset.count = p.eui;
    buildBoq(p.boq, p.total);
    kpiEls[0].dataset.count = p.eui;
    kpiEls[1].dataset.count = p.cost;

    setTab('plan');

    // Stage P0 — type brief
    markStage('P0', 'on');
    await typeText(brief.text);
    if (cancelled) return;
    markStage('P0', 'done');
    progressEl.style.width = '16%';
    await sleep(200);

    // Stage P1 — fields
    markStage('P1', 'on');
    progressEl.style.width = '32%';
    await sleep(600);
    markStage('P1', 'done');

    // Stage P7 — plan draw
    markStage('P7', 'on');
    setTab('plan');
    planSvg.classList.add('draw');
    progressEl.style.width = '52%';
    await sleep(1200);
    if (cancelled) return;
    markStage('P7', 'done');

    // Stage P8 — render
    markStage('P8', 'on');
    setTab('render');
    progressEl.style.width = '70%';
    await sleep(1400);
    if (cancelled) return;
    markStage('P8', 'done');

    // Stage P6 — energy + BOQ
    markStage('P6', 'on');
    setTab('energy');
    // animate energy numbers
    erVals.forEach(el => animateNumber(el, +el.dataset.count, 700));
    animateNumber(erTotal, +erTotal.dataset.count, 900);
    // animate kpis
    animateNumber(kpiEls[0], +kpiEls[0].dataset.count, 900);
    progressEl.style.width = '82%';
    await sleep(1400);
    if (cancelled) return;

    setTab('boq');
    animateNumber(kpiEls[1], +kpiEls[1].dataset.count, 900);
    animateNumber(boqTotal, +boqTotal.dataset.count, 1200);
    await revealBoqRows();
    await sleep(800);
    if (cancelled) return;
    markStage('P6', 'done');

    // Stage P11 — done
    markStage('P11', 'on');
    progressEl.style.width = '100%';
    await sleep(500);
    markStage('P11', 'done');

    // Success
    statusEl.classList.add('done');
    statusEl.innerHTML = '<span class="dot"></span>shipped';
    document.querySelector('.demo-kpi-ok').textContent = p.compliance + ' ✓';

    await sleep(3400);
  }

  // Tab click = allow manual override (pauses auto-cycle briefly)
  let userInteracted = 0;
  tabs.forEach(t => t.addEventListener('click', () => {
    setTab(t.dataset.tab);
    userInteracted = Date.now();
  }));

  async function loop() {
    while (true) {
      const brief = BRIEFS[briefIdx % BRIEFS.length];
      await runOnce(brief);
      if (cancelled) return;
      briefIdx++;
    }
  }

  // IntersectionObserver — pause when off screen
  let started = false;
  const io = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting && !started) {
        started = true;
        loop();
      }
    });
  }, { threshold: 0.3 });
  io.observe(demo);
})();


/* ========== EDIT STAGE — auto-cycling demo ========== */
(function initEditStage() {
  const stage = document.getElementById("edit-stage");
  if (!stage) return;

  // Timeline state
  const state = {
    warm: 0,     // 0..1
    tatami: 0,   // 0..1
    lamp: 0,     // 0..1
    sofaX: 70,   // x translate
    sofaY: 190,
    ghost: 0,
    cursorVis: 0,
    cursorX: 120,
    cursorY: 210,
    cursorRing: 0,
  };

  const SOFA_START = { x: 70, y: 190 };
  const SOFA_END = { x: 205, y: 80 }; // moves up and right, next to a chair

  // Accessors
  const $ = (s, root = stage) => root.querySelector(s);
  const $$ = (s, root = stage) => [...root.querySelectorAll(s)];

  const layer = (name) => $(`[data-layer="${name}"]`);

  function setMode(mode) {
    stage.setAttribute("data-mode", mode);
    $$(".edit-pill").forEach(p => p.classList.toggle("active", p.dataset.mode === mode));
    $$(".edit-mode-panel").forEach(p => p.classList.toggle("active", p.dataset.panel === mode));
  }

  function setStatus(txt) { $("[data-edit-status]").textContent = txt; }
  function setTranscript(txt) { $("[data-edit-transcript]").textContent = txt || "—"; }
  function setProgress(pct) { $("[data-edit-progress]").style.width = pct + "%"; }
  function setCounter(n) { $("[data-edit-counter]").textContent = n; }
  function setCommit(txt, committed) {
    $("[data-commit-txt]").textContent = txt;
    $("[data-edit-commit]").classList.toggle("committed", !!committed);
  }

  function applyState() {
    if (layer("warm")) layer("warm").setAttribute("opacity", state.warm);
    if (layer("tatami")) layer("tatami").setAttribute("opacity", state.tatami);
    if (layer("lamp")) layer("lamp").setAttribute("opacity", state.lamp);
    if (layer("ghost")) layer("ghost").setAttribute("opacity", state.ghost);
    const sofa = layer("sofa");
    if (sofa) sofa.setAttribute("transform", `translate(${state.sofaX} ${state.sofaY})`);
    const cursor = layer("cursor");
    if (cursor) {
      cursor.setAttribute("opacity", state.cursorVis);
      cursor.setAttribute("transform", `translate(${state.cursorX} ${state.cursorY})`);
    }
    const ring = layer("cursor-ring");
    if (ring) {
      ring.setAttribute("r", state.cursorRing * 18);
      ring.setAttribute("opacity", state.cursorRing > 0 ? (1 - state.cursorRing) * 0.9 : 0);
    }
  }

  function resetAllState() {
    state.warm = 0;
    state.tatami = 0;
    state.lamp = 0;
    state.sofaX = SOFA_START.x;
    state.sofaY = SOFA_START.y;
    state.ghost = 0;
    state.cursorVis = 0;
    state.cursorRing = 0;
    applyState();
  }

  const sleep = (ms) => new Promise(r => setTimeout(r, ms));

  async function typeInto(el, txt, perChar = 35) {
    el.textContent = "";
    for (const ch of txt) {
      el.textContent += ch;
      await sleep(perChar);
    }
  }

  // ============ VOICE CYCLE (~6s) ============
  async function voiceCycle() {
    setMode("voice");
    setCounter(1);
    setStatus("listening…");
    setCommit("editing · voice", false);
    setTranscript("");
    await sleep(400);

    // transcript types in
    const transcript = $("[data-edit-transcript]");
    await typeInto(transcript, "make the lighting warmer and add a floor lamp");

    setStatus("applying…");
    await sleep(250);

    // warm tint fades in + lamp appears
    state.warm = 0.8;
    state.lamp = 1;
    applyState();

    await sleep(900);
    setCommit("updated · 1.1s", true);
    setStatus("committed");
    await sleep(1600);
  }

  // ============ TEXT CYCLE (~6s) ============
  async function textCycle() {
    setMode("text");
    setCounter(2);
    setStatus("ready");
    setCommit("editing · text", false);
    setTranscript("");
    const typedEl = $("[data-edit-typed]");
    typedEl.textContent = "";
    await sleep(400);

    // typing animation
    await typeInto(typedEl, "replace the carpet with tatami", 32);
    await sleep(250);

    // transcript mirror
    setTranscript("swap floor material · carpet → tatami");
    setStatus("applying…");
    await sleep(350);

    state.tatami = 1;
    applyState();

    await sleep(1000);
    setCommit("updated · 0.9s", true);
    setStatus("committed");
    await sleep(1600);
  }

  // ============ TOUCH CYCLE (~7s) ============
  async function touchCycle() {
    setMode("touch");
    setCounter(3);
    setStatus("idle");
    setCommit("editing · drag", false);
    setTranscript("");

    $("[data-touch-target]").textContent = "sofa · 1";
    $("[data-touch-from]").textContent = `${SOFA_START.x}, ${SOFA_START.y}`;
    $("[data-touch-to]").textContent = "—";
    await sleep(400);

    // cursor appears near sofa
    state.cursorVis = 1;
    state.cursorX = SOFA_START.x + 35;
    state.cursorY = SOFA_START.y + 14;
    applyState();
    setStatus("cursor");
    await sleep(700);

    // "grab" — ring pulse
    state.cursorRing = 0.01;
    applyState();
    await sleep(40);
    state.cursorRing = 1;
    applyState();
    state.ghost = 1;
    setStatus("dragging");
    setTranscript("grab sofa · translate · snap to alignment");
    await sleep(500);
    state.cursorRing = 0;
    applyState();

    // animate sofa and cursor together to end position
    const steps = 20;
    for (let i = 1; i <= steps; i++) {
      const t = i / steps;
      // ease out
      const e = 1 - Math.pow(1 - t, 3);
      state.sofaX = SOFA_START.x + (SOFA_END.x - SOFA_START.x) * e;
      state.sofaY = SOFA_START.y + (SOFA_END.y - SOFA_START.y) * e;
      state.cursorX = (SOFA_START.x + 35) + ((SOFA_END.x + 35) - (SOFA_START.x + 35)) * e;
      state.cursorY = (SOFA_START.y + 14) + ((SOFA_END.y + 14) - (SOFA_START.y + 14)) * e;
      $("[data-touch-to]").textContent = `${Math.round(state.sofaX)}, ${Math.round(state.sofaY)}`;
      applyState();
      await sleep(55);
    }

    // release
    state.cursorRing = 0.01;
    applyState();
    await sleep(40);
    state.cursorRing = 1;
    applyState();
    await sleep(300);
    state.ghost = 0;
    state.cursorVis = 0;
    state.cursorRing = 0;
    applyState();

    setCommit("updated · 0.6s", true);
    setStatus("committed");
    await sleep(1600);
  }

  // ============ RESET / LOOP ============
  async function loop() {
    while (true) {
      resetAllState();
      setCounter(1); setProgress(0);
      await sleep(300);

      // Voice
      setProgress(5);
      await voiceCycle();
      setProgress(33);

      // Text (state accumulates)
      await textCycle();
      setProgress(66);

      // Touch
      await touchCycle();
      setProgress(100);

      // Hold the final state briefly so viewers appreciate the cumulative edit
      setStatus("all edits applied");
      setTranscript("three edits, three modalities, one consistent package");
      await sleep(2200);
      setProgress(0);
    }
  }

  // Pause when off screen
  let started = false;
  const io = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting && !started) {
        started = true;
        loop();
      }
    });
  }, { threshold: 0.25 });
  io.observe(stage);

  // Initialize visual state
  setMode("voice");
  resetAllState();
  setCommit("ready", false);
})();


/* ============ INTAKE TERMINAL DRIVER ============ */
(function intakeDriver() {
  const term = document.getElementById('intake-term');
  if (!term) return;

  const INPUTS = [
    {
      id: 'sentence',
      typed: '> "改成像茶室的样子, 4 个人坐得下"',
      stages: ['detect', 'parse', 'extract', 'normalise', 'commit'],
      formats: 'text · voice · 中 · en',
      route: 'path a — nl parser',
    },
    {
      id: 'photo',
      typed: '> IMG_8421.heic  (4032×3024)  upload',
      stages: ['detect', 'parse', 'extract', 'normalise', 'commit'],
      formats: '.jpg · .png · .heic',
      route: 'path b — vision + depth',
    },
    {
      id: 'moodboard',
      typed: '> 6 reference images  +  pinterest/studio-kin-tea',
      stages: ['detect', 'parse', 'extract', 'normalise', 'commit'],
      formats: 'images · figma · url',
      route: 'path b — vision + palette',
    },
    {
      id: 'pdf',
      typed: '> landlord-plan-L1.pdf  (2.1 mb, vector)',
      stages: ['detect', 'parse', 'extract', 'normalise', 'commit'],
      formats: '.pdf · .dwg · .dxf',
      route: 'path c — ocr + geometry',
    },
    {
      id: 'model',
      typed: '> studio-kin-tea.ifc  (12 spaces, 284 elements)',
      stages: ['detect', 'parse', 'extract', 'normalise', 'commit'],
      formats: '.ifc · .glb · .obj · .fbx',
      route: 'path d — ifc audit',
    },
    {
      id: 'json',
      typed: '> POST /intake  brief.json  (structured)',
      stages: ['detect', 'parse', 'extract', 'normalise', 'commit'],
      formats: '.json · api',
      route: 'path e — direct ingest',
    },
  ];

  const STAGE_LABELS = {
    detect: 'detecting format',
    parse: 'parsing',
    extract: 'extracting signals',
    normalise: 'normalising',
    commit: '→ brief.json',
  };

  const tabs = [...term.querySelectorAll('.intake-tab')];
  const panels = [...term.querySelectorAll('.intake-panel')];
  const stagesRow = term.querySelector('#intake-stages');
  const stageItems = [...stagesRow.querySelectorAll('.intake-stage-item')];
  const typedEl = term.querySelector('#intake-typed');
  const statusEl = term.querySelector('#intake-status');
  const statusTxt = term.querySelector('[data-intake-status]');
  const formatsEl = term.querySelector('[data-intake-formats]');
  const routeEl = term.querySelector('[data-intake-route]');

  let cancelled = false;
  const sleep = ms => new Promise(r => setTimeout(r, ms));

  function setActive(id) {
    term.setAttribute('data-active', id);
    tabs.forEach(t => t.classList.toggle('active', t.dataset.tab === id));
    panels.forEach(p => p.classList.toggle('active', p.dataset.panel === id));
  }

  function setStatus(txt, done=false) {
    statusTxt.textContent = txt;
    statusEl.classList.toggle('done', done);
  }

  function resetStages() {
    stageItems.forEach(i => i.classList.remove('on', 'done'));
  }

  async function typeText(text) {
    typedEl.textContent = '';
    for (let i = 0; i < text.length; i++) {
      if (cancelled) return;
      typedEl.textContent += text[i];
      // variable speed
      const ch = text[i];
      await sleep(ch === ' ' ? 18 : 22 + Math.random() * 18);
    }
  }

  async function runOne(input) {
    if (cancelled) return;
    setActive(input.id);
    setStatus('receiving', false);
    resetStages();

    // let panel fade in briefly
    await sleep(220);

    // Type the prompt
    await typeText(input.typed);
    if (cancelled) return;
    await sleep(240);

    // Update footer meta mid-processing
    formatsEl.textContent = input.formats;
    routeEl.textContent = input.route;

    // Run through stages
    for (let i = 0; i < input.stages.length; i++) {
      if (cancelled) return;
      const stageId = input.stages[i];
      const item = stageItems.find(x => x.dataset.id === stageId);
      if (item) {
        // clear prev on
        stageItems.forEach(s => s.classList.remove('on'));
        item.classList.add('on');
      }
      setStatus(STAGE_LABELS[stageId] || stageId, false);
      await sleep(520);
      if (item) {
        item.classList.remove('on');
        item.classList.add('done');
      }
    }

    if (cancelled) return;
    setStatus('committed', true);
    await sleep(1600);
  }

  async function loop() {
    let idx = 0;
    while (!cancelled) {
      await runOne(INPUTS[idx]);
      idx = (idx + 1) % INPUTS.length;
    }
  }

  // Click to jump
  tabs.forEach(t => {
    t.addEventListener('click', () => {
      const idx = INPUTS.findIndex(i => i.id === t.dataset.tab);
      if (idx < 0) return;
      cancelled = true;
      setTimeout(() => {
        cancelled = false;
        (async () => {
          let i = idx;
          while (!cancelled) {
            await runOne(INPUTS[i]);
            i = (i + 1) % INPUTS.length;
          }
        })();
      }, 50);
    });
  });

  // Gate by visibility
  let started = false;
  const io = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting && !started) {
        started = true;
        loop();
      }
    });
  }, { threshold: 0.2 });
  io.observe(term);
})();
