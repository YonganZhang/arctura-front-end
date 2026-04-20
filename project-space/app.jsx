/* global React, ReactDOM, ZEN_DATA */
const { useState, useRef, useEffect, useMemo, useReducer, useContext, createContext } = React;

// D 是 live-proxy 到 window.ZEN_DATA · 读取当前 state
// 运行时被 ProjectProvider 通过 stateHolder 接管（chat-edit 后切换数据）
const stateHolder = { current: null };
const D = new Proxy({}, {
  get: (_, prop) => (stateHolder.current || window.ZEN_DATA || {})[prop],
  has: (_, prop) => prop in (stateHolder.current || window.ZEN_DATA || {}),
  ownKeys: () => Object.keys(stateHolder.current || window.ZEN_DATA || {}),
  getOwnPropertyDescriptor: (_, prop) => {
    const v = (stateHolder.current || window.ZEN_DATA || {})[prop];
    return v !== undefined ? { enumerable: true, configurable: true, value: v } : undefined;
  },
});

// ───────── Project State Context · chat-edit 驱动的状态层 ─────────

// reducer manages { current, original, history }
//   SET_ORIGINAL  初始化 base · 从 JSON 加载后调
//   APPLY_EDIT    chat 返回 newState → 推 history 顶 · 切 current
//   REWIND(idx)   Undo 到 history[idx]
//   RESET         current = original · 清 history
function projectReducer(state, action) {
  switch (action.type) {
    case "SET_ORIGINAL": {
      // 在 data 上钉 _baseline_* · 后续 compute 引用
      const data = {
        ...action.data,
        _baseline_editable: { ...(action.data.editable || {}) },
        _baseline_eui: action.data.energy?.eui ?? action.data.derived?.eui_kwh_m2_yr,
        _baseline_cost_per_m2: action.data.pricing?.HK?.perM2 ?? action.data.derived?.cost_per_m2,
      };
      return { current: data, original: data, history: [] };
    }
    case "APPLY_EDIT": {
      if (!action.newState) return state;
      return {
        ...state,
        current: action.newState,
        history: [...state.history, state.current].slice(-20),
      };
    }
    case "REWIND": {
      const i = Math.max(0, Math.min(action.index, state.history.length - 1));
      const target = state.history[i];
      return { ...state, current: target, history: state.history.slice(0, i) };
    }
    case "RESET": {
      // Reset 回 original · 清除 active_variant_id（若有）· 清 history
      const fresh = { ...state.original };
      if ("active_variant_id" in fresh) delete fresh.active_variant_id;
      return { ...state, current: fresh, history: [] };
    }
    default:
      return state;
  }
}

const ProjectCtx = createContext({ current: null, dispatch: () => {}, history: [], canUndo: false, canReset: false });

// 组件调这个钩子就自动订阅 state 变化（触发 re-render）+ 获得 dispatch
function useProject() {
  return useContext(ProjectCtx);
}

// URL slug 解析：?mvp=<slug> 或 /project/<slug>/ 或 /project/
// /project 默认进 20-zen-tea-room（有 3 个真 variants · 能完整演示 chat / 3D / variant 切换）
function getSlugFromUrl() {
  const q = new URLSearchParams(location.search).get("mvp");
  if (q) return q;
  const parts = location.pathname.split("/").filter(Boolean);
  // /project/index.html 时 parts[1]="index.html" · 不是真 slug
  if (parts[0] === "project" && parts[1] && parts[1] !== "index.html") {
    return parts[1];
  }
  return "20-zen-tea-room"; // 默认 slug · 不用 data.js 老 demo
}

// 缓存默认 data.js 的初始 ZEN_DATA · 不被后续 state 同步覆盖
const DEFAULT_ZEN_DATA = window.ZEN_DATA;

async function loadMvpData(slug) {
  if (!slug) {
    // 用 data.js 默认 zen-tea · 走 DEFAULT_ZEN_DATA 避免被 state effect 覆盖
    if (!DEFAULT_ZEN_DATA) {
      throw new Error("默认 zen-tea 数据未加载（data.js 可能加载失败）");
    }
    return DEFAULT_ZEN_DATA;
  }
  const r = await fetch(`/data/mvps/${slug}.json`);
  if (!r.ok) throw new Error(`MVP "${slug}" 不存在 (HTTP ${r.status})`);
  return await r.json();
}

// Robust image: defers src until after mount (lets the sandbox path rewriter
// register), retries once on error with a cache-buster.
function Img({ src, alt, ...rest }) {
  const [resolved, setResolved] = useState(null);
  const [tries, setTries] = useState(0);
  useEffect(() => {
    // defer by a frame so service-worker / path rewriter is definitely alive
    const raf = requestAnimationFrame(() => setResolved(src));
    return () => cancelAnimationFrame(raf);
  }, [src]);
  const onError = () => {
    if (tries < 2) {
      setTries(t => t + 1);
      setResolved(src + (src.includes("?") ? "&" : "?") + "r=" + (tries + 1));
    }
  };
  if (!resolved) return <span {...rest} style={{ ...(rest.style || {}), background: "var(--bg-2)" }} />;
  return <img src={resolved} alt={alt} onError={onError} {...rest} />;
}

// ───────── Toast ─────────
function showToast(text) {
  const t = document.createElement("div");
  t.textContent = text;
  Object.assign(t.style, {
    position: "fixed", bottom: "24px", left: "50%", transform: "translateX(-50%)",
    background: "rgba(20,20,20,0.94)", color: "#fff", padding: "10px 18px",
    borderRadius: "6px", fontSize: "13px", fontFamily: "var(--f-sans)",
    zIndex: 9999, boxShadow: "0 4px 20px rgba(0,0,0,0.3)", opacity: "0",
    transition: "opacity 0.2s ease"
  });
  document.body.appendChild(t);
  requestAnimationFrame(() => { t.style.opacity = "1"; });
  setTimeout(() => { t.style.opacity = "0"; setTimeout(() => t.remove(), 200); }, 2400);
}

async function handleShare() {
  const url = window.location.href;
  try {
    await navigator.clipboard.writeText(url);
    showToast("✓ 链接已复制到剪贴板");
  } catch (e) {
    showToast("复制失败 · URL: " + url);
  }
}

// ───────── Topbar ─────────
function Topbar() {
  useProject();
  return (
    <header className="topbar">
      <div className="tb-logo">
        <span className="logo-mark" />
        <span>Arctura</span>
        <span className="labs">Labs</span>
      </div>
      <div className="tb-crumb">
        <a href="/" style={{color: "inherit", textDecoration: "none"}}>My Projects</a>
        <span className="slash">/</span>
        <b>{D.project?.name || "Untitled"}</b>
        {D.project?.zh && <>
          <span className="slash">·</span>
          <span>{D.project.zh}</span>
        </>}
        {D.project?.style && <>
          <span className="slash">·</span>
          <span>{String(D.project.style).split(",")[0].trim()}</span>
        </>}
        <span className="project-badge">{D.complete === false ? "Draft" : "Live"}</span>
      </div>
      <div className="tb-right">
        <span className="tb-status">
          {D.project?.area ? `${D.project.area} m² · ${D.project.location || "HK"}` : "Pipeline synced"}
        </span>
        <button className="tb-btn" onClick={handleShare}>Share</button>
        <a className="tb-btn primary"
           href={D.slug && D.slug !== "zen-tea" ? "#" : "/assets/zen-tea/bundle.zip"}
           download={`${D.slug || "zen-tea-room"}-bundle.zip`}
           onClick={e => {
             if (D.slug && D.slug !== "zen-tea") {
               e.preventDefault();
               showToast("当前 MVP 暂无打包 zip · zen-tea demo 可下");
             }
           }}
           style={{textDecoration: "none", display: "inline-flex", alignItems: "center"}}>
          Download all
        </a>
      </div>
    </header>
  );
}

// ───────── Sidebar ─────────
function Sidebar({ active, setActive }) {
  useProject();
  const proj = D.project || {};
  const renders = D.renders || [];
  const zones = D.zones || [];
  const variants = D.variants?.list || [];
  const pricing = D.pricing || {};
  const rows = (pricing[D.editable?.region || "HK"] || pricing.HK || {}).rows || [];
  const eui = D.derived?.eui_kwh_m2_yr ?? D.energy?.eui ?? "—";
  const complianceCount = ((D.compliance?.HK?.items || D.compliance?.HK?.checks) || []).length;
  const variantActiveId = D.active_variant_id;
  const items = [
    { id:"overview", label:"Overview", count:"—" },
    { id:"renders", label:"Renders", count: renders.length || "—" },
    { id:"floorplan", label:"Floorplan", count: zones.length || "—" },
    { id:"3d", label:"3D Viewer", count: D.model_glb ? "GLB" : "—" },
    { id:"boq", label:"BOQ · Pricing", count: rows.length || "—" },
    { id:"energy", label:"Energy", count: eui !== "—" ? `EUI ${eui}` : "—" },
    { id:"compliance", label:"Compliance", count: complianceCount || "—" },
    { id:"whatif", label:"What-If", count:"5" },
    { id:"variants", label: variants.length ? `A / B / C` : "Variants", count: variants.length || "—" },
    { id:"decks", label:"Decks", count:(D.decks || []).length || "—" },
    { id:"timeline", label:"Timeline", count: (D.timeline || []).length || "—" },
    { id:"files", label:"Files", count: (D.downloads || []).length || "—" },
  ];
  const projName = proj.name || D.slug || "Project";
  const projZh = proj.zh || "";
  const projMeta = [
    proj.area ? `${proj.area} m²` : null,
    proj.location || null,
    variantActiveId || "v1",
  ].filter(Boolean).join(" · ");
  return (
    <aside className="sidebar">
      <div className="sb-project">
        <div className="sb-proj-name">{projName}</div>
        {projZh && <div className="sb-proj-zh">{projZh}</div>}
        <div className="sb-proj-meta">{projMeta}</div>
      </div>
      <div className="sb-section">
        <div className="sb-label">Artifacts</div>
        {items.map(it => (
          <div key={it.id}
               data-tab={it.id}
               className={"sb-item " + (active===it.id ? "active" : "")}
               onClick={() => setActive(it.id)}>
            <span>{it.label}</span>
            <span className="sb-count">{it.count}</span>
          </div>
        ))}
      </div>
      <div className="sb-section">
        <div className="sb-label">Revisions</div>
        <div className="sb-item"><span>v1 · new-chinese</span><span className="sb-count">now</span></div>
        <div className="sb-item"><span style={{color:"var(--text-4)"}}>v0 · brief only</span><span className="sb-count">1d</span></div>
      </div>
    </aside>
  );
}

// ───────── Overview ─────────
function Overview({ setActive }) {
  useProject();
  const renders = D.renders || [];
  const [thumb, setThumb] = useState(0);
  const safeIdx = Math.min(thumb, Math.max(0, renders.length - 1));
  const current = renders[safeIdx];
  // 动态字段
  const proj = D.project || {};
  const der = D.derived || {};
  const zones = D.zones || [];
  const compliance = D.compliance || {};
  const region = D.editable?.region || "HK";
  const C = compliance[region] || {};
  const fmtInt = (n) => n != null ? Number(n).toLocaleString() : "—";
  const titleEn = proj.name || D.slug || "Untitled";
  const subParts = [
    proj.zh,
    proj.style ? (typeof proj.style === "string" ? proj.style.split(",")[0].trim() : "") : "",
    proj.area ? `${proj.area} m²` : "",
    proj.location || "",
  ].filter(Boolean);
  const eui = der.eui_kwh_m2_yr ?? D.energy?.eui ?? "—";
  const euiLimit = D.energy?.limit || 150;
  const costTotal = der.cost_total || (D.pricing || {})[region]?.totalNumber;
  const costPerM2 = der.cost_per_m2 || (D.pricing || {})[region]?.perM2;
  const verdict = der.compliance_verdict || C.verdict || "—";
  const verdictClass = verdict === "COMPLIANT" ? "ok" : /CONDITIONAL|REVIEW|ADVISORY/i.test(verdict) ? "warn" : verdict === "—" ? "ok" : "warn";
  return (
    <section>
      <div className="view-head">
        <div>
          <h1 className="view-title">{titleEn}</h1>
          <div className="view-sub">{subParts.join(" · ")}</div>
        </div>
      </div>

      <div className="ov-grid-3">
        <div className="card">
          <div className="card-head"><span className="card-lbl">Total Cost</span><span className="card-tag ok">{region}</span></div>
          <div className="card-value">{(D.pricing||{})[region]?.currency || "HK$"}{costTotal != null ? (costTotal >= 1000 ? `${Math.round(costTotal/1000)}` : `${costTotal}`) : "—"}<small>{costTotal >= 1000 ? "k" : ""}</small></div>
          <div className="card-sub">{costPerM2 ? `${fmtInt(costPerM2)} / m²` : "—"}</div>
          <div className="card-footer"><span>BOQ · {((D.pricing||{})[region]?.rows || []).length} items</span><span onClick={()=>setActive("boq")} style={{cursor:"pointer",color:"var(--accent)"}}>View →</span></div>
        </div>
        <div className="card">
          <div className="card-head"><span className="card-lbl">Energy (EUI)</span><span className={"card-tag " + (Number(eui) <= euiLimit ? "ok" : "warn")}>{Number(eui) <= euiLimit ? "Pass" : "Review"}</span></div>
          <div className="card-value">{eui}<small>kWh/m²·yr</small></div>
          <div className="card-sub">{eui !== "—" && Number(eui) < euiLimit ? `${Math.round((1 - eui/euiLimit)*100)}% below limit ${euiLimit}` : `Limit ${euiLimit} kWh/m²·yr`}</div>
          <div className="card-footer"><span>{D.energy?.engine || "EnergyPlus"}</span><span onClick={()=>setActive("energy")} style={{cursor:"pointer",color:"var(--accent)"}}>View →</span></div>
        </div>
        <div className="card">
          <div className="card-head"><span className="card-lbl">Compliance</span><span className={"card-tag " + verdictClass}>{region}</span></div>
          <div className="card-value">{C.score || verdict}</div>
          <div className="card-sub">{verdict.length > 50 ? verdict.slice(0, 50) + "…" : verdict}</div>
          <div className="card-footer"><span>{C.label || C.code || region}</span><span onClick={()=>setActive("compliance")} style={{cursor:"pointer",color:"var(--accent)"}}>View →</span></div>
        </div>
      </div>

      {current ? (
        <div className="render-feature">
          <div className="render-main" onClick={()=>setActive("renders")}>
            <Img src={current.file} alt={current.title} />
            <div className="render-overlay">
              <div className="render-tag">{current.tag} · click to expand gallery</div>
              <div className="render-title">{current.title}</div>
            </div>
          </div>
          <div className="render-thumbs">
            {renders.map((r, i) => (
              <div key={i} className={"render-thumb " + (safeIdx===i ? "active":"")} onClick={()=>setThumb(i)}>
                <Img src={r.file} alt={r.title} />
                <div className="render-thumb-lbl">{r.tag}</div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div style={{padding:40, background:"var(--bg-1)", border:"1px dashed var(--line)", borderRadius:6, textAlign:"center", color:"var(--text-3)"}}>
          此 MVP 暂无渲染图 · Chat 仍可改数据
        </div>
      )}

      <div className="ov-grid">
        <div className="card" style={{cursor:"pointer"}} onClick={()=>setActive("floorplan")}>
          <div className="card-head"><span className="card-lbl">Floorplan</span><span className="card-tag ok">{zones.length} zone{zones.length !== 1 ? "s" : ""}</span></div>
          <div style={{fontFamily:"var(--f-display)",fontSize:22,fontWeight:400,letterSpacing:"-0.01em"}}>{zones.length ? "Interactive · drag furniture" : "No zone data"}</div>
          <div className="card-sub">{zones.length ? "Hover any zone for details." : "This MVP has no interactive floorplan layout."}</div>
          <div className="card-footer"><span>{zones.slice(0,3).map(z=>z.name).filter(Boolean).join(" · ") || "—"}</span><span>Open →</span></div>
        </div>
        <div className="card" style={{cursor:"pointer"}} onClick={()=>setActive("3d")}>
          <div className="card-head"><span className="card-lbl">3D Viewer</span><span className={"card-tag " + (D.model_glb ? "ok" : "warn")}>{D.model_glb ? "GLB ready" : "images only"}</span></div>
          <div style={{fontFamily:"var(--f-display)",fontSize:22,fontWeight:400,letterSpacing:"-0.01em"}}>{D.model_glb ? "Rotate · zoom · pan" : "Multi-angle renders"}</div>
          <div className="card-sub">{D.model_glb ? "Real Blender-exported BIM geometry. Drag to orbit." : "Pre-rendered views only for this MVP."}</div>
          <div className="card-footer"><span>{D.model_glb ? "GLB · " + Math.round((D.model_glb || "").length/10) + " loaded" : renders.length + " views"}</span><span>Open →</span></div>
        </div>
      </div>
    </section>
  );
}

// ───────── Floorplan (drag-able + hover info) ─────────
function Floorplan() {
  useProject();
  const wrapRef = useRef(null);
  const [hovered, setHovered] = useState((D.zones || [])[0]);
  const [furn, setFurn] = useState(D.furniture || []);
  const dragRef = useRef({ active:null, dx:0, dy:0 });

  const startDrag = (e, id) => {
    const wrap = wrapRef.current.getBoundingClientRect();
    const item = furn.find(f=>f.id===id);
    dragRef.current = {
      active: id,
      dx: e.clientX - (wrap.left + (item.x/100)*wrap.width),
      dy: e.clientY - (wrap.top + (item.y/100)*wrap.height)
    };
    const move = (ev) => {
      const r = wrapRef.current.getBoundingClientRect();
      const nx = ((ev.clientX - dragRef.current.dx - r.left) / r.width) * 100;
      const ny = ((ev.clientY - dragRef.current.dy - r.top) / r.height) * 100;
      setFurn(fs => fs.map(f => f.id===id ? {...f, x: Math.max(2, Math.min(96-f.w, nx)), y: Math.max(2, Math.min(96-f.h, ny))} : f));
    };
    const up = () => {
      dragRef.current.active = null;
      window.removeEventListener("mousemove", move);
      window.removeEventListener("mouseup", up);
    };
    window.addEventListener("mousemove", move);
    window.addEventListener("mouseup", up);
  };

  const zones = D.zones || [];
  const floorplanImg = D.floorplan;
  const area = D.project?.area || D.editable?.area_m2 || 40;
  // 如果 zone 数据变了（比如切了 variant），确保 hovered 仍有效
  const safeHover = (hovered && zones.find(z => z.id === hovered.id)) || zones[0] || {};

  // 无 zones 且无平面图 · 空态
  if (zones.length === 0 && !floorplanImg) {
    return (
      <section>
        <div className="view-head">
          <div>
            <h1 className="view-title">Floorplan</h1>
            <div className="view-sub">此 MVP 暂无交互平面图数据</div>
          </div>
        </div>
        <div style={{padding:60, background:"var(--bg-1)", border:"1px dashed var(--line)", borderRadius:6, textAlign:"center", color:"var(--text-3)"}}>
          Pipeline 未产出 zone 分区数据 · 3D Viewer 或 Renders tab 可看空间布局
        </div>
      </section>
    );
  }

  // 有平面图 WebP 但无 zone 交互 · 显示静态图
  if (zones.length === 0 && floorplanImg) {
    return (
      <section>
        <div className="view-head">
          <div>
            <h1 className="view-title">Floorplan</h1>
            <div className="view-sub">平面图 · {area} m² · 静态渲染（无交互分区）</div>
          </div>
        </div>
        <div style={{background:"var(--bg-1)", border:"1px solid var(--line)", borderRadius:6, padding:20, display:"flex", justifyContent:"center"}}>
          <Img src={floorplanImg} alt="floorplan" style={{maxWidth:"100%", maxHeight:"600px"}} />
        </div>
      </section>
    );
  }

  return (
    <section>
      <div className="view-head">
        <div>
          <h1 className="view-title">Floorplan</h1>
          <div className="view-sub">平面图 · {zones.length} zone{zones.length !== 1 ? "s" : ""} · {area} m² · hover + drag</div>
        </div>
      </div>
      <div className="fp-wrap" ref={wrapRef}>
        <div className="fp-canvas">
          {zones.map(z => (
            <div key={z.id}
                 className={"fp-zone " + (safeHover.id===z.id ? "hover":"")}
                 style={{ left:z.x+"%", top:z.y+"%", width:z.w+"%", height:z.h+"%" }}
                 onMouseEnter={()=>setHovered(z)}>
              <div className="fp-zone-name">{z.name}</div>
              <div className="fp-zone-meta">{z.zh} · {z.area} m²</div>
            </div>
          ))}
          {furn.map(f => (
            <div key={f.id}
                 className={"fp-furn " + (dragRef.current.active===f.id ? "dragging":"")}
                 style={{ left:f.x+"%", top:f.y+"%", width:f.w+"%", height:f.h+"%", background:f.color, borderRadius: f.id.startsWith("chair") ? "50%" : 2 }}
                 onMouseDown={(e)=>startDrag(e, f.id)}
                 title={f.label} />
          ))}
        </div>
        <div className="fp-info-panel">
          <div className="fp-info-name">{safeHover.name}</div>
          <div className="fp-info-zh">{safeHover.zh}</div>
          <div className="fp-info-row"><span>Area</span><b>{safeHover.area} m²</b></div>
          <div className="fp-info-row"><span>Share</span><b>{safeHover.area ? Math.round(safeHover.area/area*100) : 0}%</b></div>
          <div style={{marginTop:10,fontSize:11,fontFamily:"var(--f-sans)",color:"var(--text-2)",lineHeight:1.5}}>{safeHover.notes}</div>
        </div>
        <div className="fp-hint">Drag chairs · table to try layouts</div>
      </div>
    </section>
  );
}

// ───────── 3D Viewer · 真 3D 模型（GLB · model-viewer）· 无模型时退化到多视角图 ─────────

// Viewer3D toggle state · 模块级 · 切 tab 后也保留
const envelopeHideMemory = { current: false };

// Node 名分类正则（build_models.py 拷的 Blender GLB · 节点名有语义）
const FLOOR_RX = /^(Floor|FloorMat|Ground|Site_Ground|Slab_F\d|Slab_Existing|Slab_New|Deck)/i;
// 只外墙四面 · 室内分隔墙（partition）保留
// 规则：cardinal direction (N/S/E/W/Back/Front/Left/Right) · _outer 后缀 · _Pier 外墩 · Wall_Existing_X_Y 双方位
const EXTERIOR_WALL_RX = /^Wall[_]?(?:N|S|E|W|North|South|East|West|Back|Front|Left|Right)(?![a-zA-Z])|_outer(?:_|$)|_Pier|_(?:Existing|New)_[NSEW]_[NSEW]$/i;
// 天花 / 屋顶 · 同 toggle 一起隐藏
const CEIL_RX = /Ceiling|Roof|Beam.*Roof|Slab_Roof|Eave|parapet/i;

function applyEnvelopeVisibility(mv, hideEnvelope) {
  if (!mv) return false;
  const sym = Object.getOwnPropertySymbols(mv).find(s => s.toString() === "Symbol(scene)");
  if (!sym) return false;
  const scene = mv[sym];
  if (!scene || typeof scene.traverse !== "function") return false;
  scene.traverse(obj => {
    const name = obj.name || "";
    // 地板白名单：永远可见（用户明确要求）
    if (FLOOR_RX.test(name)) {
      obj.visible = true;
      return;
    }
    // 只隐藏 外墙 + 天花/屋顶 · 室内 partition / glass wall / interior wall 保留
    if (EXTERIOR_WALL_RX.test(name) || CEIL_RX.test(name)) {
      obj.visible = !hideEnvelope;
    }
    // 其他（家具 / 室内墙 / 楼梯等）保持默认 visible
  });
  return true;
}

function Viewer3D() {
  useProject();
  const modelGlb = D.model_glb;
  const renders = D.renders || [];
  const mvRef = useRef(null);
  // 通过 module-level ref 持久化 · 切 tab 回来状态保留
  const [hideEnvelope, _setHideEnvelope] = useState(envelopeHideMemory.current);
  const setHideEnvelope = (v) => {
    const next = typeof v === "function" ? v(envelopeHideMemory.current) : v;
    envelopeHideMemory.current = next;
    _setHideEnvelope(next);
  };
  const [modelLoaded, setModelLoaded] = useState(false);

  // model 加载完成 OR toggle 变化 → apply
  useEffect(() => {
    const mv = mvRef.current;
    if (!mv) return;
    const onLoad = () => {
      setModelLoaded(true);
      applyEnvelopeVisibility(mv, hideEnvelope);
    };
    mv.addEventListener("load", onLoad);
    // 如果模型已加载（切换 tab 回来）· 直接 apply
    if (modelLoaded) applyEnvelopeVisibility(mv, hideEnvelope);
    return () => mv.removeEventListener("load", onLoad);
  }, [hideEnvelope, modelGlb, modelLoaded]);

  // 优先：有真 3D 模型 · 用 <model-viewer> 加载（drag/zoom/AR 内置）
  if (modelGlb) {
    const area = D.project?.area || 0;
    const variantId = D.active_variant_id;
    return (
      <section>
        <div className="view-head">
          <div>
            <h1 className="view-title">3D Viewer</h1>
            <div className="view-sub">
              真 3D 模型 · GLB · 拖拽旋转 · 滚轮缩放
              {variantId && <> · <b>variant: {variantId}</b></>}
              {area ? <> · {area} m²</> : null}
            </div>
          </div>
          <div style={{display:"flex", gap:8, alignItems:"center"}}>
            <button
              onClick={() => setHideEnvelope(v => !v)}
              style={{
                padding: "6px 14px",
                background: hideEnvelope ? "var(--text-1)" : "var(--bg-1)",
                color: hideEnvelope ? "var(--bg-0)" : "var(--text-1)",
                border: "1px solid " + (hideEnvelope ? "var(--text-1)" : "var(--line)"),
                borderRadius: 4,
                fontSize: 12,
                fontFamily: "var(--f-mono)",
                letterSpacing: "0.05em",
                cursor: "pointer",
                transition: "all 0.15s",
              }}
              title={hideEnvelope ? "显示墙壁 + 天花板" : "隐藏墙壁 + 天花板（地板保留）"}
            >
              {hideEnvelope ? "🏠 显示围护" : "🔲 仅家具"}
            </button>
          </div>
        </div>
        <div style={{background:"linear-gradient(180deg, var(--bg-1) 0%, var(--bg-2) 100%)", border:"1px solid var(--line)", borderRadius:6, overflow:"hidden"}}>
          <model-viewer
            ref={mvRef}
            src={modelGlb}
            alt="3D model"
            camera-controls
            auto-rotate
            auto-rotate-delay="3000"
            shadow-intensity="1"
            exposure="1.0"
            environment-image="neutral"
            style={{width:"100%", height:"560px", background:"transparent", "--progress-bar-color": "var(--text-1)"}}
          />
        </div>
        <div style={{marginTop:12, padding:"10px 14px", background:"var(--bg-1)", border:"1px solid var(--line)", borderRadius:4, fontSize:12, color:"var(--text-3)", fontFamily:"var(--f-mono)"}}>
          ← drag · scroll · ⌘-click = pan · GLB {modelGlb.split("/").pop()}
          {hideEnvelope && <span style={{marginLeft:12, color:"var(--accent)"}}>· envelope hidden（地板保留）</span>}
        </div>
      </section>
    );
  }

  // 退化：无 3D 模型但有渲染图 → 多视角图片选择器
  // 找 "3D" 感最强的视角（鸟瞰 / axon / birds-eye）
  const isoIndex = renders.findIndex(r => /bird|eye|iso|axon|top/i.test((r.tag || "") + " " + (r.title || "")));
  const [idx, setIdx] = useState(Math.max(0, isoIndex));
  const safeIdx = Math.min(idx, Math.max(0, renders.length - 1));
  const current = renders[safeIdx];
  const area = D.project?.area || 0;
  const variantId = D.active_variant_id;

  // 无 render 兜底：显示空态（不再用假的 CSS 几何体）
  if (!current) {
    return (
      <section>
        <div className="view-head">
          <div>
            <h1 className="view-title">3D Viewer</h1>
            <div className="view-sub">此 MVP 暂无 3D 渲染产出</div>
          </div>
        </div>
        <div style={{padding:60, textAlign:"center", color:"var(--text-3)", background:"var(--bg-1)", border:"1px dashed var(--line)", borderRadius:6}}>
          Pipeline 未跑完 · 此 MVP 的 8 视角渲染图尚未产出。<br/>
          Chat 里仍然可以：改面积 / 切合规 / 改保温 · 数据会真刷新。
        </div>
      </section>
    );
  }

  return (
    <section>
      <div className="view-head">
        <div>
          <h1 className="view-title">3D Viewer</h1>
          <div className="view-sub">
            真实渲染图 · {renders.length} 视角
            {variantId && <> · <b>variant: {variantId}</b></>}
            {area ? <> · {area} m²</> : null}
          </div>
        </div>
      </div>
      <div style={{position:"relative", background:"var(--bg-1)", border:"1px solid var(--line)", borderRadius:6, overflow:"hidden"}}>
        <div style={{aspectRatio: "16/10", background:"var(--bg-2)", display:"flex", alignItems:"center", justifyContent:"center"}}>
          <Img src={current.file} alt={current.title}
               style={{width:"100%", height:"100%", objectFit:"cover"}} />
        </div>
        <div style={{position:"absolute", top:14, left:14, padding:"4px 10px", background:"rgba(0,0,0,0.6)", color:"white", fontSize:10, fontFamily:"var(--f-mono)", letterSpacing:"0.08em", borderRadius:3}}>
          {current.tag || "view"}
        </div>
        <div style={{position:"absolute", bottom:14, left:14, padding:"6px 12px", background:"rgba(0,0,0,0.6)", color:"white", fontSize:13, fontFamily:"var(--f-display)", borderRadius:3}}>
          {current.title}
        </div>
      </div>
      <div style={{marginTop:16, display:"grid", gridTemplateColumns:"repeat(auto-fill, minmax(120px, 1fr))", gap:10}}>
        {renders.map((r,i)=>(
          <div key={i} onClick={()=>setIdx(i)}
               style={{
                 cursor:"pointer",
                 border: "2px solid " + (safeIdx===i ? "var(--text-1)" : "var(--line)"),
                 borderRadius:4, overflow:"hidden", background:"var(--bg-2)",
                 aspectRatio:"16/10", position:"relative",
                 transition:"border-color 0.15s",
               }}>
            <Img src={r.file} alt={r.title} style={{width:"100%", height:"100%", objectFit:"cover"}} />
            <div style={{position:"absolute", bottom:0, left:0, right:0, padding:"4px 8px", fontSize:9, fontFamily:"var(--f-mono)", background:"rgba(0,0,0,0.6)", color:"white", letterSpacing:"0.05em"}}>
              {r.tag || r.id}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

// ───────── BOQ ─────────
function BOQ() {
  useProject();
  const pricing = D.pricing || {};
  // 动态拿可用的地区键（排除空数据）· 按固定顺序
  const ORDER = ["HK", "CN", "US", "JP", "INTL"];
  const availableRegions = ORDER.filter(r => pricing[r] && (pricing[r].total || pricing[r].perM2 || (pricing[r].rows || []).length));
  const fallbackRegions = availableRegions.length ? availableRegions : ["HK"];
  const [region, setRegion] = useState(fallbackRegions[0]);
  const effectiveRegion = availableRegions.includes(region) ? region : fallbackRegions[0];
  const P = pricing[effectiveRegion] || { currency: "HK$", perM2: 0, total: "0", subtotal: "0", mep: "0", prelim: "0", cont: "0", rows: [] };
  const regionLabel = { HK: "HK · HK$", CN: "CN · ¥", US: "US · US$", JP: "JP · ¥", INTL: "Intl · US$" };
  return (
    <section>
      <div className="view-head">
        <div>
          <h1 className="view-title">Bill of Quantities</h1>
          <div className="view-sub">报价清单 · switch region to view prices</div>
        </div>
      </div>
      <div className="boq-head">
        <div className="boq-total-row">
          <div>
            <div className="lbl">Total · including fees</div>
            <div className="val">{P.currency}{P.total}</div>
          </div>
          <div>
            <div className="lbl">Per m²</div>
            <div className="val" style={{fontSize:24}}>{P.currency}{(P.perM2 || 0).toLocaleString()}<small>/ m²</small></div>
          </div>
        </div>
        <div className="boq-region-switch">
          {fallbackRegions.map(r => (
            <button key={r}
                    className={"boq-region-btn " + (effectiveRegion===r ? "on":"")}
                    onClick={()=>setRegion(r)}>{regionLabel[r] || r}</button>
          ))}
        </div>
      </div>
      <div className="boq-table">
        <table>
          <thead>
            <tr>
              <th>Cat</th>
              <th>Description</th>
              <th className="right">Quantity</th>
              <th className="right">Amount ({P.currency})</th>
            </tr>
          </thead>
          <tbody>
            {P.rows.map((r,i)=>(
              <tr key={i}>
                <td className="cat">{r.cat}</td>
                <td className="desc"><b>{r.desc}</b><span>{r.sub}</span></td>
                <td className="qty">{r.qty}</td>
                <td className="amt">{r.amt}</td>
              </tr>
            ))}
            <tr className="subtotal">
              <td></td><td>Direct work subtotal</td><td></td><td className="amt">{P.subtotal}</td>
            </tr>
            <tr>
              <td className="cat">MEP</td>
              <td className="desc"><b>Mechanical · Electrical · Plumbing</b><span>25% of direct work</span></td>
              <td className="qty">lot</td>
              <td className="amt">{P.mep}</td>
            </tr>
            <tr>
              <td className="cat">PRELIM</td>
              <td className="desc"><b>Preliminaries</b><span>Site, safety, management · 12%</span></td>
              <td className="qty">lot</td>
              <td className="amt">{P.prelim}</td>
            </tr>
            <tr>
              <td className="cat">CONT</td>
              <td className="desc"><b>Contingency</b><span>10% buffer</span></td>
              <td className="qty">lot</td>
              <td className="amt">{P.cont}</td>
            </tr>
            <tr className="grand">
              <td></td><td>Total</td><td></td><td className="amt">{P.currency}{P.total}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  );
}

// ───────── Energy ─────────
function Energy() {
  useProject();
  const E = D.energy || { eui: 0, limit: 150, annual: 0, engine: "EnergyPlus" };
  // End-use breakdown · 按 editable 里的 lighting_density_w_m2 推算 lighting 占比
  // 其他走经验默认（hvac 占最大 · equipment 中等）
  const lpd = D.editable?.lighting_density_w_m2 || 8;
  const lightPct = Math.max(10, Math.min(40, Math.round(lpd / E.eui * 500)));  // 粗估
  const hvacPct = Math.max(40, 72 - lightPct);
  const otherPct = Math.max(8, 100 - hvacPct - lightPct - 12);
  const bars = [
    { label:"HVAC", val: hvacPct, unit:"%", pct: hvacPct },
    { label:"Lighting", val: lightPct, unit:"%", pct: lightPct },
    { label:"Equipment", val: 12, unit:"%", pct: 12 },
    { label:"Other", val: otherPct, unit:"%", pct: otherPct }
  ];
  const area = D.project?.area || D.editable?.area_m2 || 40;
  const annual = E.annual || Math.round((E.eui || 0) * area);
  const co2 = D.derived?.co2_t_per_yr || Math.round((E.eui || 0) * area * 0.59 / 1000 * 100) / 100;
  const underPct = E.limit && E.eui ? Math.round((1 - E.eui / E.limit) * 100) : 0;
  return (
    <section>
      <div className="view-head">
        <div>
          <h1 className="view-title">Energy Performance</h1>
          <div className="view-sub">能耗仿真 · EnergyPlus simulation · Hong Kong climate</div>
        </div>
      </div>
      <div className="eui-hero">
        <div className="eui-left">
          <div style={{fontFamily:"var(--f-mono)",fontSize:10,color:"var(--text-3)",letterSpacing:"0.14em",textTransform:"uppercase"}}>Energy Use Intensity · annual</div>
          <div className="eui-big">
            <span className="val">{E.eui}</span>
            <span className="unit">kWh / m² · yr</span>
            <span className="delta">{underPct > 0 ? `${underPct}% under limit` : underPct < 0 ? `${-underPct}% over limit` : "at limit"}</span>
          </div>
          <div className="eui-baseline">
            <div><span>Code limit</span><b>{E.limit || 150}</b></div>
            <div><span>Region avg</span><b>122</b></div>
            <div><span>Annual total</span><b>{annual.toLocaleString()} kWh</b></div>
            <div><span>CO₂e</span><b>{co2} t / yr</b></div>
          </div>
        </div>
        <div className="eui-right">
          <div style={{fontFamily:"var(--f-mono)",fontSize:10,color:"var(--text-3)",letterSpacing:"0.14em",textTransform:"uppercase",marginBottom:4}}>End-use breakdown</div>
          {bars.map(b=>(
            <div key={b.label} className="eui-bar-row">
              <span className="lbl">{b.label}</span>
              <div className="track"><div className="fill" style={{width:b.pct+"%"}} /></div>
              <span className="num">{b.val}{b.unit}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ───────── Compliance ─────────
function Compliance() {
  useProject();
  const [code, setCode] = useState("HK");
  const C = (D.compliance || {})[code] || { verdict: "—", items: [] };
  const vclass = C.verdict === "COMPLIANT" ? "" : /REVIEW|ADVISORY|CONDITIONAL/i.test(C.verdict || "") ? "warn" : C.verdict === "—" ? "" : "fail";
  return (
    <section>
      <div className="view-head">
        <div>
          <h1 className="view-title">Compliance</h1>
          <div className="view-sub">合规检查 · switch code to re-check envelope &amp; envelope values</div>
        </div>
      </div>
      <div className="cmp-head">
        <div style={{fontFamily:"var(--f-mono)",fontSize:11,color:"var(--text-3)",letterSpacing:"0.1em",textTransform:"uppercase"}}>Select region / code</div>
        <div className="cmp-code-switch">
          {["HK","CN","US","JP"].map(c => (
            <button key={c} className={"cmp-code-btn " + (code===c ? "on":"")} onClick={()=>setCode(c)}>
              {c === "HK" ? "Hong Kong · BEEO" : c === "CN" ? "China · GB 50189" : c === "US" ? "USA · ASHRAE" : "Japan · 省エネ法"}
            </button>
          ))}
        </div>
      </div>
      <div className={"cmp-verdict " + vclass}>
        <div>
          <div className="v-lbl">{C.label}</div>
          <div className="v-val">{C.verdict}</div>
        </div>
        <div style={{textAlign:"right"}}>
          <div className="v-lbl">Score</div>
          <div className="v-val">{C.score}</div>
        </div>
      </div>
      <div className="cmp-table">
        {((C.items || C.checks) || []).map((it,i)=>(
          <div key={i} className={"cmp-row " + (it.status === "advisory" ? "warn" : it.status)}>
            <span className="cmp-dot" />
            <div className="cmp-check"><b>{it.check || it.name}</b><span>{it.zh || ""}</span></div>
            <div className="cmp-value">Current <b>{it.val !== undefined ? it.val : it.value}</b> {it.unit && it.unit !== "—" && it.unit}</div>
            <div className="cmp-limit">Limit {it.limit} {it.unit && it.unit !== "—" && it.unit}</div>
            <div className="cmp-status">{it.status === "pass" ? "Pass" : /advisory|warn/i.test(it.status) ? "Review" : "Fail"}</div>
          </div>
        ))}
      </div>
    </section>
  );
}

// ───────── What-If ─────────
function WhatIf() {
  const [v, setV] = useState({ area:40, wwr:25, insul:60, glazing:2, light:8 });
  // simple fake model — deltas relative to baseline
  const base = { cost:540, eui:84, co2:1.98, time:56 };
  const cost = Math.round(base.cost * (v.area/40) * (1 + (v.insul-60)/300 + (v.glazing-2)*0.04 + (v.light-8)*0.006));
  const eui = Math.max(30, Math.round(base.eui - (v.insul-60)*0.3 - (v.glazing-2)*1.4 + (v.wwr-25)*0.35 + (v.light-8)*1.2));
  const co2 = Math.round(eui * v.area * 0.59) / 1000;
  const time = Math.round(base.time * (0.6 + v.area/100));

  const sliders = [
    { key:"area", label:"Floor area", hint:"room size", min:20, max:120, step:1, unit:"m²" },
    { key:"wwr", label:"Window-to-wall ratio", hint:"facade openness", min:10, max:60, step:1, unit:"%" },
    { key:"insul", label:"Insulation thickness", hint:"XPS in wall", min:20, max:120, step:5, unit:"mm" },
    { key:"glazing", label:"Glazing U-value", hint:"lower = better", min:1.2, max:5.8, step:0.2, unit:"W/m²K" },
    { key:"light", label:"Lighting density", hint:"watts / m²", min:4, max:15, step:0.5, unit:"W/m²" }
  ];

  return (
    <section>
      <div className="view-head">
        <div>
          <h1 className="view-title">What-If Lab</h1>
          <div className="view-sub">实时模拟 · move sliders to see cost / energy / CO₂ update live</div>
        </div>
      </div>
      <div className="wi-panel">
        {sliders.map(s => (
          <div className="wi-slider" key={s.key}>
            <div className="wi-slider-head">
              <span className="lbl">{s.label}<small>{s.hint}</small></span>
              <span className="val">{v[s.key]}<small>{s.unit}</small></span>
            </div>
            <input type="range" min={s.min} max={s.max} step={s.step} value={v[s.key]}
                   onChange={e=>setV({...v, [s.key]: Number(e.target.value)})}/>
          </div>
        ))}
        <div className="wi-impact-grid">
          <div className="wi-impact">
            <div className="lbl">Total cost</div>
            <div className="val">HK${cost}<small>k</small></div>
            <div className={"delta " + (cost>base.cost ? "up":"dn")}>{cost>base.cost?"↑":"↓"} {Math.abs(cost-base.cost)}k vs baseline</div>
          </div>
          <div className="wi-impact">
            <div className="lbl">EUI · annual</div>
            <div className="val">{eui}<small>kWh/m²·yr</small></div>
            <div className={"delta " + (eui>base.eui ? "up":"dn")}>{eui>base.eui?"↑":"↓"} {Math.abs(eui-base.eui)} kWh vs baseline</div>
          </div>
          <div className="wi-impact">
            <div className="lbl">CO₂ emissions</div>
            <div className="val">{co2.toFixed(2)}<small>t / yr</small></div>
            <div className={"delta " + (co2>base.co2 ? "up":"dn")}>{co2>base.co2?"↑":"↓"} {Math.abs(co2-base.co2).toFixed(2)} t vs baseline</div>
          </div>
          <div className="wi-impact">
            <div className="lbl">Delivery time</div>
            <div className="val">{time}<small>min · brief → pkg</small></div>
            <div className={"delta dn"}>auto-generated</div>
          </div>
        </div>
      </div>
    </section>
  );
}

// ───────── A / B / C variants ─────────
function Variants() {
  const { current, dispatch } = useProject();
  const [loading, setLoading] = useState(null);   // variant id being loaded
  const [err, setErr] = useState(null);
  // 兼容两种 schema：legacy data.js 是 array · 新版是 {list: [...]}
  const variantArray = Array.isArray(D.variants) ? D.variants : (D.variants?.list || []);
  const activeVid = D.active_variant_id;

  const handleSelect = async (vid) => {
    if (!current?.slug || loading) return;   // 任何变体 loading 中都阻止新点击（防 race）
    setLoading(vid);
    setErr(null);
    try {
      const r = await fetch(`/data/mvps/${current.slug}/variants/${vid}.json`);
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const v = await r.json();
      // Overlay 变体数据到当前 state（与 backend apply-tools switch_variant 对齐）
      const merged = {
        ...current,
        active_variant_id: vid,
        project: { ...(current.project || {}), ...(v.project || {}) },
        renders: v.renders || current.renders,
        hero_img: v.hero_img || current.hero_img,
        thumb_img: v.thumb_img || current.thumb_img,
        floorplan: v.floorplan || current.floorplan,
        moodboard: v.moodboard || current.moodboard,
        zones: v.zones || current.zones,
        pricing: { ...(current.pricing || {}), ...(v.pricing || {}) },
        energy: { ...(current.energy || {}), ...(v.energy || {}) },
        compliance: { ...(current.compliance || {}), ...(v.compliance || {}) },
        editable: { ...(current.editable || {}), ...(v.editable || {}) },
        derived: v.derived || current.derived,
        timeline: [
          ...(current.timeline || []),
          { time: new Date().toISOString(), title: `Switched to ${v.name || vid}`, diff: `variant → ${vid}`, source: "click" },
        ],
      };
      dispatch({ type: "APPLY_EDIT", newState: merged });
    } catch (e) {
      setErr(`加载 variant 失败: ${e.message}`);
    } finally {
      setLoading(null);
    }
  };

  // 无 variants → 显示 single-scheme 提示
  if (variantArray.length === 0) {
    return (
      <section>
        <div className="view-head">
          <div>
            <h1 className="view-title">Variants</h1>
            <div className="view-sub">此 MVP 为单方案设计</div>
          </div>
        </div>
        <div style={{padding:40, background:"var(--bg-1)", border:"1px dashed var(--line)", borderRadius:6, textAlign:"center", color:"var(--text-3)"}}>
          这个 MVP 目前只有一套方案，没有多方案对比数据。<br/>
          Chat 里仍然可以改数值（面积 / 保温 / 合规地区）· 数据会实时刷新。
        </div>
      </section>
    );
  }

  return (
    <section>
      <div className="view-head">
        <div>
          <h1 className="view-title">Variants · {variantArray.length} 方案</h1>
          <div className="view-sub">点击卡片切换方案 · 整个项目数据（图 / BOQ / 合规）会真更新</div>
        </div>
      </div>
      {err && <div style={{padding:12, background:"rgba(216,87,42,0.1)", color:"#b54e2c", marginBottom:14, borderRadius:4, fontSize:13}}>{err}</div>}
      <div className="abc-grid">
        {variantArray.map(v => {
          const isActive = v.id === activeVid;
          const isLoading = loading === v.id;
          return (
            <div key={v.id}
                 className={"abc-variant " + (isActive ? "chosen" : "")}
                 onClick={() => handleSelect(v.id)}
                 style={{cursor: isLoading ? "wait" : "pointer", opacity: isLoading ? 0.5 : 1}}>
              <div className="abc-img">
                <div className="abc-label">{v.id}</div>
                <Img src={v.thumb || v.hero || v.img} alt={v.name} />
              </div>
              <div className="abc-body">
                <div className="abc-name">{v.name}{v.name_zh && <span className="zh">{v.name_zh}</span>}</div>
                <div className="abc-tagline">{v.desc || v.tagline || ""}</div>
                <div className="abc-choose">
                  {isLoading ? "Loading…" : isActive ? "✓ Selected" : "Click to switch"}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

// ───────── Decks ─────────
function Decks() {
  useProject();
  return (
    <section>
      <div className="view-head">
        <div>
          <h1 className="view-title">Stakeholder Decks</h1>
          <div className="view-sub">8 版本 · one story, 8 audiences · auto-tailored from the same source</div>
        </div>
      </div>
      <div className="deck-grid">
        {(D.decks || []).map(d => (
          <div key={d.num} className="deck-card" title="Preview">
            <div className="deck-thumb">
              <div className="deck-thumb-num">Deck {d.num} · {d.pages}p</div>
              <div className="deck-thumb-title">{d.to}<br/><span style={{fontSize:11,color:"var(--text-3)",fontFamily:"var(--f-sans)",fontWeight:400}}>{d.zh}</span></div>
            </div>
            <div className="deck-body">
              <div className="deck-title">For {d.to}</div>
              <div className="deck-pages">{d.pages} pages · PPTX · PDF</div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

// ───────── Timeline ─────────
function Timeline() {
  const { canUndo, canReset, dispatch, history } = useProject();
  const items = D.timeline || [];
  return (
    <section>
      <div className="view-head">
        <div>
          <h1 className="view-title">Timeline</h1>
          <div className="view-sub">
            修改历史 · {history.length} undoable step{history.length !== 1 ? "s" : ""}
            <span style={{color:"var(--text-3)", marginLeft:8, fontSize:11}}>(刷新页面 → 回到原始)</span>
          </div>
        </div>
        <div style={{display:"flex", gap:8}}>
          <button className="d3-btn" disabled={!canUndo}
                  onClick={()=>dispatch({type:"REWIND", index: history.length - 1})}
                  title="Undo last change">↶ Undo</button>
          <button className="d3-btn" disabled={!canReset}
                  onClick={()=>dispatch({type:"RESET"})}
                  title="Reset to original baseline">⟲ Reset</button>
        </div>
      </div>
      <div className="tl-wrap">
        {items.length === 0 && (
          <div style={{padding: "24px", color: "var(--text-3)", fontSize: 13}}>
            暂无修改 · 在 Chat 里说一句话试试（"make it warmer" / "scale to 60m²" / "check Tokyo code"）
          </div>
        )}
        {items.map((t,i)=>{
          // 时间可能是 ISO 或者 "15 min ago" 这种 legacy 格式
          const timeLabel = t.time && t.time.includes("T")
            ? new Date(t.time).toLocaleTimeString([], {hour: "2-digit", minute: "2-digit"})
            : t.time;
          return (
          <div key={i} className="tl-row">
            <div className="tl-time">{timeLabel}</div>
            <div className="tl-mark" />
            <div className="tl-content">
              <b>{t.title}</b>
              <p>{t.desc || t.source}</p>
              {t.diff && <div className="tl-diff"><i>+</i> {t.diff}</div>}
            </div>
          </div>
        );})}
      </div>
    </section>
  );
}

// ───────── Downloads ─────────
function Files() {
  useProject();
  return (
    <section>
      <div className="view-head">
        <div>
          <h1 className="view-title">Files</h1>
          <div className="view-sub">全部交付物 · 3D exports, floorplan, BOQ, reports, decks</div>
        </div>
      </div>
      <div className="dl-grid">
        {(D.downloads || []).map((f,i)=>(
          <div key={i} className="dl-file">
            <div className="dl-ext">{f.ext}</div>
            <div className="dl-name">{f.name}<span>{f.sub}</span></div>
            <div className="dl-size">{f.size}</div>
          </div>
        ))}
      </div>
      <div style={{marginTop:16,padding:"14px 20px",background:"var(--bg-1)",border:"1px solid var(--line)",borderRadius:6,display:"flex",justifyContent:"space-between",alignItems:"center"}}>
        <div>
          <div style={{fontFamily:"var(--f-mono)",fontSize:10,color:"var(--text-3)",letterSpacing:"0.12em",textTransform:"uppercase"}}>Bundle</div>
          <div style={{fontFamily:"var(--f-display)",fontSize:18,fontWeight:400,marginTop:2}}>All artifacts · one ZIP</div>
        </div>
        <a className="tb-btn primary"
           href={D.slug && D.slug !== "zen-tea" ? "#" : "/assets/zen-tea/bundle.zip"}
           download={`${D.slug || "zen-tea-room"}-bundle.zip`}
           onClick={e => {
             if (D.slug && D.slug !== "zen-tea") {
               e.preventDefault();
               showToast("当前 MVP 暂无打包 zip · zen-tea demo 可下");
             }
           }}
           style={{textDecoration: "none"}}>Download .zip</a>
      </div>
    </section>
  );
}

// ───────── Renders gallery (reuse overview) ─────────
function Renders() {
  useProject();
  const renders = D.renders || [];
  const [active, setActive] = useState(0);
  // 如果 state 切了 variant 导致 renders 换了，active index 可能超界
  const safeIdx = Math.min(active, Math.max(0, renders.length - 1));
  const r = renders[safeIdx];
  if (!r) {
    return (
      <section>
        <div className="view-head">
          <div>
            <h1 className="view-title">Renders</h1>
            <div className="view-sub">渲染图 · 暂无可用视角</div>
          </div>
        </div>
        <div style={{padding:60, textAlign:"center", color:"var(--text-3)"}}>
          此 MVP 暂无 3D 渲染图产出（pipeline 未跑完）· Chat 里可以改数值 / 切合规 / 切方案。
        </div>
      </section>
    );
  }
  return (
    <section>
      <div className="view-head">
        <div>
          <h1 className="view-title">Renders</h1>
          <div className="view-sub">渲染图 · {renders.length} views · 4K photoreal · re-generate from any modified model</div>
        </div>
      </div>
      <div className="render-feature">
        <div className="render-main">
          <Img src={r.file} alt={r.title} />
          <div className="render-overlay">
            <div className="render-tag">{r.tag}</div>
            <div className="render-title">{r.title}</div>
          </div>
        </div>
        <div className="render-thumbs">
          {renders.map((x,i)=>(
            <div key={i} className={"render-thumb " + (safeIdx===i?"active":"")} onClick={()=>setActive(i)}>
              <Img src={x.file} alt={x.title} />
              <div className="render-thumb-lbl">{x.tag}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ───────── Chat ─────────
// 注 · 旧 SYSTEM_PROMPT 已废弃（/api/chat-edit 在服务端自己构造带 tool schema 的 prompt）。

function Chat({ onNavigate }) {
  const { current, dispatch } = useProject();
  const [msgs, setMsgs] = useState([
    { role:"bot", text:"Hello — I'm your project assistant. Tell me what you'd like to change and I'll actually apply it to the data.", diff:null },
    { role:"sys", text:"Chat → real data edits · refresh 回到原始" }
  ]);
  const [input, setInput] = useState("");
  const [thinking, setThinking] = useState(false);
  const [models, setModels] = useState([]);  // 从 /data/models.json 加载
  const [model, setModel] = useState("deepseek-v3.2");  // 默认
  const bodyRef = useRef(null);

  // 加载可用模型清单
  useEffect(() => {
    fetch("/data/models.json")
      .then(r => r.ok ? r.json() : [])
      .then(list => {
        if (Array.isArray(list) && list.length > 0) {
          setModels(list);
          const def = list.find(m => m.default) || list[0];
          setModel(def.id);
        }
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (bodyRef.current) bodyRef.current.scrollTop = bodyRef.current.scrollHeight;
  }, [msgs, thinking]);

  const parseReply = (raw) => {
    if (!raw) return { text: "(no response)", diff: null };
    const lines = raw.trim().split(/\r?\n/).filter(Boolean);
    let diff = null;
    const textLines = [];
    for (const line of lines) {
      const m = line.match(/^\s*(?:\*\*)?DIFF[:：](?:\*\*)?\s*(.*)$/i);
      if (m) diff = m[1].trim();
      else textLines.push(line);
    }
    return { text: textLines.join(" ").trim(), diff };
  };

  const buildMessages = (history, userText) => {
    // Build Claude chat history from our message list, keeping only user/bot
    const turns = history.filter(m => m.role === "user" || m.role === "bot").map(m => ({
      role: m.role === "user" ? "user" : "assistant",
      content: m.role === "bot" && m.diff ? `${m.text}\nDIFF: ${m.diff}` : m.text
    }));
    turns.push({ role: "user", content: userText });
    return turns;
  };

  const send = async (text) => {
    if (!text.trim() || thinking) return;
    if (!current || !current.slug) {
      setMsgs(m => [...m, { role: "user", text }, { role: "bot", text: "项目数据还在加载，稍等一秒再问。", diff: null }]);
      return;
    }
    const userMsg = { role:"user", text };
    const nextMsgs = [...msgs, userMsg];
    setMsgs(nextMsgs);
    setInput("");
    setThinking(true);

    try {
      // 调 /api/chat-edit（tool-use 端点）· 失败时自动降级到 /api/chat（纯 LLM）
      const r = await fetch("/api/chat-edit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          slug: current.slug,
          userMessage: text,
          currentState: current,
          model,
          chatHistory: buildMessages(msgs, text).slice(0, -1),
        }),
      });
      if (!r.ok) {
        const err = await r.json().catch(() => ({}));
        console.warn("chat-edit failed:", r.status, err);
        // 友好化错误文案
        let friendly;
        if (r.status === 504 || /timeout|abort/i.test(err.error || "")) {
          friendly = `LLM 响应超时了 · 试试短一点的句子（如 "warmer" 而不是 "把整份围变得温暖一点"），或换个模型（上方 Model 下拉）再试`;
        } else if (r.status === 502 || r.status === 503) {
          friendly = `后端网关临时不通 (${r.status}) · 稍等几秒再试`;
        } else if (r.status === 500) {
          friendly = err.error?.includes("ZHIZENGZENG") ? `ZHIZENGZENG_API_KEY 未设 · 后端配置问题` : `后端内部错误 · ${err.detail?.slice(0, 80) || "unknown"}`;
        } else {
          friendly = `后端 error ${r.status}: ${err.error || "unknown"}${err.detail ? " · " + err.detail.slice(0, 80) : ""}`;
        }
        setMsgs(m => [...m, {
          role: "bot",
          text: friendly,
          error: true,
          retryable: err.retryable !== false && (r.status === 504 || r.status >= 500),
          retryInput: text,
        }]);
      } else {
        const data = await r.json();
        if (data.newState && data.applied && data.applied.length > 0) {
          dispatch({ type: "APPLY_EDIT", newState: data.newState });
          // 提示用户去看变化的 tab · 根据改了什么字段判断
          const affected = new Set();
          for (const a of data.applied) {
            const f = a.call?.args?.field || a.call?.name;
            if (f === "area_m2" || a.call?.name === "scale_editable") { affected.add("boq"); affected.add("energy"); }
            if (f === "insulation_mm" || f === "glazing_uvalue") { affected.add("compliance"); affected.add("energy"); }
            if (f === "lighting_cct" || f === "lighting_density_w_m2" || f === "wwr") { affected.add("energy"); }
            if (f === "region" || a.call?.name === "switch_region") { affected.add("compliance"); affected.add("boq"); }
            if (a.call?.name === "switch_variant") { affected.add("overview"); affected.add("3d"); }
          }
          const hints = Array.from(affected);
          if (hints.length) {
            setTimeout(() => showToast(`✓ 数据已更新 · 看 ${hints.slice(0, 2).map(t => ({boq:"BOQ", energy:"Energy", compliance:"Compliance", overview:"Overview", "3d":"3D"})[t]).join(" / ")} tab 的变化`), 100);
          }
        }
        setMsgs(m => [...m, {
          role: "bot",
          text: data.text || "(processed)",
          applied: data.applied || [],
          rejected: data.rejected || [],
          affectedTabs: Array.from(
            new Set((data.applied || []).flatMap(a => {
              const f = a.call?.args?.field;
              const n = a.call?.name;
              if (n === "switch_variant") return ["overview", "3d"];
              if (n === "switch_region" || f === "region") return ["compliance", "boq"];
              if (f === "area_m2" || n === "scale_editable") return ["boq", "energy"];
              if (f === "insulation_mm" || f === "glazing_uvalue") return ["compliance", "energy"];
              if (f === "lighting_cct" || f === "lighting_density_w_m2" || f === "wwr") return ["energy"];
              return [];
            }))
          ),
          model: data.model,
        }]);
      }
    } catch (err) {
      console.warn("chat-edit exception:", err);
      setMsgs(m => [...m, {
        role: "bot",
        text: `(Network error · ${err.message || err}) · 检查 ZHIZENGZENG_API_KEY 是否设了。`,
        error: true,
      }]);
    } finally {
      setThinking(false);
    }
  };

  // Used only if window.claude isn't available (e.g. local preview)
  const offlineFallback = (t) => {
    const lo = t.toLowerCase();
    if (/budget|cheap|cost down|便宜|减价/.test(lo))
      return "Generated a 20% cost-reduced variant. Rosewood swapped for walnut veneer; kept ink gallery and copper kettle. New total HK$432k, same EUI, same compliance.\nDIFF: −HK$108k · EUI unchanged · −3 rosewood items";
    if (/warmer|warm|暖/.test(lo))
      return "Dropped lighting CCT to 2700K and added two floor lamps by the tea table. Feel is noticeably warmer; EUI rose 4 points.\nDIFF: +2 fixtures · EUI 84→88 · CCT 3000K→2700K";
    if (/bigger|expand|扩大/.test(lo))
      return "Scaled the room to 50m² keeping the 6-zone layout in proportion. All furniture rescaled to fit.\nDIFF: +10m² · +HK$128k · EUI unchanged";
    if (/energy|eui|节能/.test(lo))
      return "Upgraded insulation 60→100mm and glazing U-value from 2.0 to 1.6. Passes all four code regions after change.\nDIFF: EUI 84→71 · +HK$28k · all codes pass";
    if (/japan|东京|日本|beijing|北京|code|合规/.test(lo))
      return "Switched compliance target. Three envelope values now flag red under Japan 省エネ法 2025. Recommended fix: +60mm rockwool on walls and roof, triple glazing.\nDIFF: 3 fails · +HK$94k to pass · +80mm insulation";
    if (/变/.test(t) || /change/.test(lo))
      return "Understood. Regenerating the affected artifacts. Timeline tab will show the diff within a minute.\nDIFF: 1 revision queued";
    return "Understood — I'll regenerate the affected artifacts and write the diff to the Timeline tab.\nDIFF: 1 revision queued";
  };

  // 根据 MVP 是否有 variants 动态选建议
  const hasVariants = (current?.variants?.list || []).length > 0;
  const firstVariant = (current?.variants?.list || [])[0];
  const chips = [
    "Make it warmer",
    "Scale up 25%",
    "Check Tokyo code",
    hasVariants && firstVariant ? `Show ${firstVariant.name || firstVariant.id}` : "Upgrade insulation to 100mm",
  ].filter(Boolean);

  return (
    <aside className="chat">
      <div className="chat-head">
        <div style={{flex: 1}}>
          <div className="chat-title">
            Assistant
            <span style={{
              marginLeft: 8, padding: "2px 7px", fontSize: 9,
              letterSpacing: "0.1em", textTransform: "uppercase",
              background: "rgba(76, 175, 80, 0.15)", color: "#4CAF50",
              borderRadius: 3, fontFamily: "var(--f-mono)",
              verticalAlign: "1px"
            }}>Live</span>
          </div>
          <div className="chat-sub">Editing · {current?.project?.name || current?.slug || "—"}{current?.active_variant_id ? " · " + current.active_variant_id : ""}</div>
        </div>
        <button className="tb-btn" onClick={()=>onNavigate("timeline")}>History</button>
      </div>
      {models.length > 0 && (
        <div style={{
          padding: "8px 14px", fontSize: 11,
          background: "rgba(0,0,0,0.02)", borderBottom: "1px solid var(--line)",
          display: "flex", alignItems: "center", gap: 8
        }}>
          <span style={{color: "var(--text-3)", fontFamily: "var(--f-mono)", fontSize: 10, letterSpacing: "0.1em", textTransform: "uppercase"}}>Model</span>
          <select
            value={model}
            onChange={e => setModel(e.target.value)}
            disabled={thinking}
            style={{
              flex: 1,
              background: "var(--bg-0)", color: "var(--text-1)",
              border: "1px solid var(--line)", borderRadius: 4,
              padding: "4px 8px", fontSize: 12, fontFamily: "var(--f-sans)",
              cursor: thinking ? "not-allowed" : "pointer",
            }}
          >
            {models.map(m => (
              <option key={m.id} value={m.id}>
                {m.label} · {m.vendor}
              </option>
            ))}
          </select>
        </div>
      )}
      <div className="chat-body" ref={bodyRef}>
        {msgs.map((m,i) => (
          m.role === "sys" ? (
            <div key={i} className="msg sys">{m.text}</div>
          ) : (
            <div key={i} className={"msg " + m.role + (m.error ? " error" : "")}>
              {m.text}
              {m.diff && <div className="msg-diff"><i>+</i>{m.diff}</div>}
              {m.applied && m.applied.length > 0 && (
                <div className="msg-diff" style={{background:"rgba(76,175,80,0.1)", color:"#2c7a2c"}}>
                  <i>✓</i>{m.applied.map(a => a.summary).join(" · ")}
                </div>
              )}
              {m.rejected && m.rejected.length > 0 && (
                <div className="msg-diff" style={{background:"rgba(216,87,42,0.1)", color:"#b54e2c"}}>
                  <i>✗</i>{m.rejected.map(r => {
                    const reason = r.reason || "";
                    if (reason.startsWith("Unknown editable field")) return "AI 引用了一个不存在的字段（已忽略这一步）";
                    if (reason.includes("out of range")) return `超出合法范围：${reason.replace(/.*out of range\s*/, "")}`;
                    if (reason.includes("variant_id") && reason.includes("not found")) return "AI 选了一个不存在的 variant（已忽略）";
                    if (reason.includes("no variants available")) return "这个 MVP 只有一套方案，无法切换";
                    return reason;
                  }).join(" · ")}
                </div>
              )}
              {m.affectedTabs && m.affectedTabs.length > 0 && (
                <div style={{marginTop:6, fontSize:11, color:"var(--text-3)"}}>
                  变化反映在：
                  {m.affectedTabs.map((t, i) => (
                    <span key={t}>
                      {i > 0 && " · "}
                      <a onClick={()=>onNavigate(t)}
                         style={{color:"var(--accent)", cursor:"pointer", textDecoration:"underline"}}>
                        {({boq:"BOQ", energy:"Energy", compliance:"Compliance", overview:"Overview", "3d":"3D Viewer"})[t] || t}
                      </a>
                    </span>
                  ))}
                </div>
              )}
              {m.retryable && m.retryInput && (
                <div style={{marginTop:6}}>
                  <button
                    onClick={() => send(m.retryInput)}
                    disabled={thinking}
                    style={{
                      padding:"4px 12px", fontSize:11, border:"1px solid var(--line)",
                      borderRadius:3, background:"var(--bg-1)", color:"var(--text-1)",
                      cursor: thinking ? "wait" : "pointer", fontFamily:"var(--f-mono)",
                    }}
                  >↻ 重试</button>
                </div>
              )}
              {m.model && (
                <div style={{
                  fontSize: 9, color: "var(--text-3)", marginTop: 4,
                  fontFamily: "var(--f-mono)", letterSpacing: "0.05em",
                  opacity: 0.6
                }}>— {m.model}</div>
              )}
            </div>
          )
        ))}
        {thinking && (
          <div className="msg bot">
            <span className="msg-thinking">
              <span></span><span></span><span></span>
            </span>
          </div>
        )}
      </div>
      <div className="chat-suggest">
        {chips.map(c => (<div key={c} className="chat-chip" onClick={()=>send(c)}>{c}</div>))}
      </div>
      <div className="chat-input-wrap">
        <input className="chat-input"
               placeholder={thinking ? "Regenerating…" : "告诉我你想改什么 · tell me what to change…"}
               value={input}
               disabled={thinking}
               onChange={e=>setInput(e.target.value)}
               onKeyDown={e=>e.key==="Enter" && send(input)} />
        <button className="chat-send" onClick={()=>send(input)} disabled={thinking}>↑</button>
      </div>
    </aside>
  );
}

// ───────── App ─────────
function App() {
  const [active, setActive] = useState("overview");
  const views = {
    overview: <Overview setActive={setActive} />,
    renders: <Renders />,
    floorplan: <Floorplan />,
    "3d": <Viewer3D />,
    boq: <BOQ />,
    energy: <Energy />,
    compliance: <Compliance />,
    whatif: <WhatIf />,
    variants: <Variants />,
    decks: <Decks />,
    timeline: <Timeline />,
    files: <Files />
  };

  return (
    <div className="app">
      <Topbar />
      <Sidebar active={active} setActive={setActive} />
      <main className="main">
        <div className="view" data-screen-label={active}>
          {views[active]}
        </div>
      </main>
      <Chat onNavigate={setActive} />
    </div>
  );
}

// ───────── Root · 先异步加载 MVP 数据再 render App ─────────
function Root() {
  const [status, setStatus] = useState("loading"); // loading | ready | notfound | error
  const [errMsg, setErrMsg] = useState("");
  const slug = getSlugFromUrl();
  const [projectState, dispatch] = useReducer(projectReducer, { current: null, original: null, history: [] });

  // ⚠️ 关键：必须在 render 期间就同步 stateHolder/window.ZEN_DATA
  // useEffect 是 render 之后才跑 · 那时子组件已读完旧 D.xxx · 会显示 stale 数据
  // 对 ref 的赋值是"副作用"但可重入 · 在 render 中做是安全的（React 文档 "Resetting state with a key" 类似模式）
  if (projectState.current && stateHolder.current !== projectState.current) {
    stateHolder.current = projectState.current;
    window.ZEN_DATA = projectState.current;
  }

  useEffect(() => {
    loadMvpData(slug)
      .then(data => {
        // 确保 slug 字段存在（默认 zen-tea 可能没有）
        if (!data.slug) data.slug = slug || "zen-tea";
        window.ZEN_DATA = data;
        stateHolder.current = data;
        dispatch({ type: "SET_ORIGINAL", data });
        setStatus("ready");
      })
      .catch(e => {
        setErrMsg(e.message || String(e));
        setStatus(slug ? "notfound" : "error");
      });
  }, []);

  if (status === "loading") {
    return (
      <div style={{
        minHeight: "100vh", display: "flex", flexDirection: "column",
        alignItems: "center", justifyContent: "center",
        fontFamily: "var(--f-sans)", background: "var(--bg-0)", color: "var(--text-2)"
      }}>
        <div style={{fontFamily: "var(--f-mono)", fontSize: 11, letterSpacing: "0.15em", textTransform: "uppercase", marginBottom: 16, color: "var(--text-3)"}}>Loading</div>
        <div style={{fontFamily: "var(--f-display)", fontSize: 28, fontWeight: 300}}>
          {slug || "Zen Tea Room"}
        </div>
        <div style={{fontSize: 12, color: "var(--text-3)", marginTop: 8}}>fetching project data…</div>
      </div>
    );
  }

  if (status === "notfound") {
    return (
      <div style={{
        minHeight: "100vh", display: "flex", flexDirection: "column",
        alignItems: "center", justifyContent: "center",
        fontFamily: "var(--f-sans)", background: "var(--bg-0)", color: "var(--text-1)", padding: 40, textAlign: "center"
      }}>
        <div style={{fontFamily: "var(--f-mono)", fontSize: 11, letterSpacing: "0.15em", textTransform: "uppercase", color: "#d9534f", marginBottom: 16}}>404 · MVP Not Found</div>
        <div style={{fontFamily: "var(--f-display)", fontSize: 32, fontWeight: 300, marginBottom: 12}}>{slug}</div>
        <div style={{fontSize: 14, color: "var(--text-3)", maxWidth: 480, lineHeight: 1.6}}>{errMsg}</div>
        <a href="/" style={{
          marginTop: 32, padding: "10px 20px", background: "var(--text-1)", color: "var(--bg-0)",
          textDecoration: "none", borderRadius: 4, fontSize: 13, fontFamily: "var(--f-sans)"
        }}>← 回主页画廊</a>
      </div>
    );
  }

  if (status === "error") {
    // slug 为空且加载失败（不应发生，但兜底）
    return (
      <div style={{minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", padding: 40}}>
        <div>加载失败: {errMsg}</div>
      </div>
    );
  }

  const ctxValue = {
    current: projectState.current,
    history: projectState.history,
    original: projectState.original,
    canUndo: projectState.history.length > 0,
    canReset: projectState.current !== projectState.original,
    dispatch,
  };

  return (
    <ProjectCtx.Provider value={ctxValue}>
      <App />
    </ProjectCtx.Provider>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<Root />);
