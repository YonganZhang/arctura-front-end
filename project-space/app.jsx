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
    case "SET_ORIGINAL":
      return { current: action.data, original: action.data, history: [] };
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
    case "RESET":
      return { ...state, current: state.original, history: [] };
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
function getSlugFromUrl() {
  const q = new URLSearchParams(location.search).get("mvp");
  if (q) return q;
  const parts = location.pathname.split("/").filter(Boolean);
  if (parts[0] === "project" && parts[1]) return parts[1];
  return null; // 用默认 zen-tea
}

async function loadMvpData(slug) {
  if (!slug) return window.ZEN_DATA; // 用 data.js 默认 zen-tea
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
  const items = [
    { id:"overview", label:"Overview", count:"—" },
    { id:"renders", label:"Renders", count:"4" },
    { id:"floorplan", label:"Floorplan", count:"6" },
    { id:"3d", label:"3D Viewer", count:"115" },
    { id:"boq", label:"BOQ · Pricing", count:"3" },
    { id:"energy", label:"Energy", count:"EUI 84" },
    { id:"compliance", label:"Compliance", count:"4" },
    { id:"whatif", label:"What-If", count:"5" },
    { id:"variants", label:"A / B / C", count:"3" },
    { id:"decks", label:"Decks", count:"8" },
    { id:"timeline", label:"Timeline", count:"4" },
    { id:"files", label:"Files", count:"9" }
  ];
  return (
    <aside className="sidebar">
      <div className="sb-project">
        <div className="sb-proj-name">Zen Tea Room</div>
        <div className="sb-proj-zh">禅意茶室 · 新中式</div>
        <div className="sb-proj-meta">40 m² · Hong Kong · v1</div>
      </div>
      <div className="sb-section">
        <div className="sb-label">Artifacts</div>
        {items.map(it => (
          <div key={it.id}
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
  const mainRender = (D.renders || [])[0];
  const [thumb, setThumb] = useState(0);
  const current = (D.renders || [])[thumb];
  return (
    <section>
      <div className="view-head">
        <div>
          <h1 className="view-title">Zen Tea Room</h1>
          <div className="view-sub">禅意茶室 · New-Chinese · 40 m² · Hong Kong · Delivered in 56 min</div>
        </div>
      </div>

      <div className="ov-grid-3">
        <div className="card">
          <div className="card-head"><span className="card-lbl">Total Cost</span><span className="card-tag ok">HK</span></div>
          <div className="card-value">HK$540<small>k</small></div>
          <div className="card-sub">13,510 HK$ / m² · within budget</div>
          <div className="card-footer"><span>BOQ · 7 categories</span><span>v1</span></div>
        </div>
        <div className="card">
          <div className="card-head"><span className="card-lbl">Energy (EUI)</span><span className="card-tag ok">Pass</span></div>
          <div className="card-value">84<small>kWh/m²·yr</small></div>
          <div className="card-sub">44% below HK BEEO limit · 3,358 kWh/yr</div>
          <div className="card-footer"><span>HVAC 62% · Light 24%</span><span>EnergyPlus</span></div>
        </div>
        <div className="card">
          <div className="card-head"><span className="card-lbl">Compliance</span><span className="card-tag ok">HK · BEEO</span></div>
          <div className="card-value">7<small>/ 8</small></div>
          <div className="card-sub">OTTV pending facade finalization</div>
          <div className="card-footer"><span>Tap to switch region</span><span onClick={()=>setActive("compliance")} style={{cursor:"pointer",color:"var(--accent)"}}>View →</span></div>
        </div>
      </div>

      <div className="render-feature">
        <div className="render-main" onClick={()=>setActive("renders")}>
          <Img src={current.file} alt={current.title} />
          <div className="render-overlay">
            <div className="render-tag">{current.tag} · click to expand gallery</div>
            <div className="render-title">{current.title}</div>
          </div>
        </div>
        <div className="render-thumbs">
          {D.renders.map((r, i) => (
            <div key={r.id} className={"render-thumb " + (thumb===i ? "active":"")} onClick={()=>setThumb(i)}>
              <Img src={r.file} alt={r.title} />
              <div className="render-thumb-lbl">{r.tag}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="ov-grid">
        <div className="card" style={{cursor:"pointer"}} onClick={()=>setActive("floorplan")}>
          <div className="card-head"><span className="card-lbl">Floorplan</span><span className="card-tag ok">6 zones</span></div>
          <div style={{fontFamily:"var(--f-display)",fontSize:22,fontWeight:400,letterSpacing:"-0.01em"}}>Interactive · drag furniture</div>
          <div className="card-sub">Hover any zone for details. Drag chairs to reposition the tea ceremony.</div>
          <div className="card-footer"><span>Entry · Tea · Ink · Display · Boil · Zen Garden</span><span>Open →</span></div>
        </div>
        <div className="card" style={{cursor:"pointer"}} onClick={()=>setActive("3d")}>
          <div className="card-head"><span className="card-lbl">3D Viewer</span><span className="card-tag ok">115 objects</span></div>
          <div style={{fontFamily:"var(--f-display)",fontSize:22,fontWeight:400,letterSpacing:"-0.01em"}}>Rotate · zoom · pan</div>
          <div className="card-sub">Real BIM-grade geometry. Exports to GLB / OBJ / FBX / IFC.</div>
          <div className="card-footer"><span>IFC · BIM ready</span><span>Open →</span></div>
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

  return (
    <section>
      <div className="view-head">
        <div>
          <h1 className="view-title">Floorplan</h1>
          <div className="view-sub">平面图 · 6 zones · 40 m² · hover + drag</div>
        </div>
      </div>
      <div className="fp-wrap" ref={wrapRef}>
        <div className="fp-canvas">
          {D.zones.map(z => (
            <div key={z.id}
                 className={"fp-zone " + (hovered.id===z.id ? "hover":"")}
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
          <div className="fp-info-name">{hovered.name}</div>
          <div className="fp-info-zh">{hovered.zh}</div>
          <div className="fp-info-row"><span>Area</span><b>{hovered.area} m²</b></div>
          <div className="fp-info-row"><span>Share</span><b>{Math.round(hovered.area/40*100)}%</b></div>
          <div style={{marginTop:10,fontSize:11,fontFamily:"var(--f-sans)",color:"var(--text-2)",lineHeight:1.5}}>{hovered.notes}</div>
        </div>
        <div className="fp-hint">Drag chairs · table to try layouts</div>
      </div>
    </section>
  );
}

// ───────── 3D Viewer (CSS 3D) ─────────
function Viewer3D() {
  const [rot, setRot] = useState({ x:55, z:-20 });
  const [zoom, setZoom] = useState(1);
  const stageRef = useRef(null);
  const dragRef = useRef(null);

  const onDown = (e) => {
    dragRef.current = { sx:e.clientX, sy:e.clientY, rx:rot.x, rz:rot.z };
    const move = (ev) => {
      const dx = ev.clientX - dragRef.current.sx;
      const dy = ev.clientY - dragRef.current.sy;
      setRot({
        x: Math.max(20, Math.min(85, dragRef.current.rx - dy*0.4)),
        z: dragRef.current.rz - dx*0.4
      });
    };
    const up = () => {
      window.removeEventListener("mousemove", move);
      window.removeEventListener("mouseup", up);
    };
    window.addEventListener("mousemove", move);
    window.addEventListener("mouseup", up);
  };

  const onWheel = (e) => {
    e.preventDefault();
    setZoom(z => Math.max(0.5, Math.min(2.2, z - e.deltaY*0.001)));
  };

  return (
    <section>
      <div className="view-head">
        <div>
          <h1 className="view-title">3D Viewer</h1>
          <div className="view-sub">3D 模型 · 115 objects · BIM-grade · drag to rotate · scroll to zoom</div>
        </div>
      </div>
      <div className="d3-wrap" ref={stageRef} onMouseDown={onDown} onWheel={onWheel} style={{cursor:"grab"}}>
        <div className="d3-stage">
          <div className="d3-room" style={{ transform: `rotateX(${rot.x}deg) rotateZ(${rot.z}deg) scale(${zoom})` }}>
            <div className="d3-floor" />
            <div className="d3-wall n" />
            <div className="d3-wall s" />
            <div className="d3-wall w" />
            <div className="d3-wall e" />
            <div className="d3-obj table"><div className="top" /></div>
            <div className="d3-obj chair c1"><div className="top" /></div>
            <div className="d3-obj chair c2"><div className="top" /></div>
            <div className="d3-obj chair c3"><div className="top" /></div>
            <div className="d3-obj chair c4"><div className="top" /></div>
            <div className="d3-obj cabinet"><div className="top" /></div>
            <div className="d3-obj zen"><div className="top" /></div>
            <div className="d3-obj screen"><div className="top" /></div>
            <div className="d3-obj counter"><div className="top" /></div>
          </div>
        </div>
        <div className="d3-controls">
          <button className="d3-btn" onClick={()=>setRot({x:55, z:-20})} title="Reset">⟲</button>
          <button className="d3-btn" onClick={()=>setZoom(z=>Math.min(2.2, z+0.2))} title="Zoom in">+</button>
          <button className="d3-btn" onClick={()=>setZoom(z=>Math.max(0.5, z-0.2))} title="Zoom out">−</button>
          <button className="d3-btn" onClick={()=>setRot({x:90, z:0})} title="Top">T</button>
          <button className="d3-btn" onClick={()=>setRot({x:75, z:-45})} title="Iso">I</button>
        </div>
        <div className="d3-hint">◀ drag to orbit · scroll to zoom ▶</div>
        <div className="d3-legend">
          <div>Room <b>40 m²</b></div>
          <div>Height <b>2.8 m</b></div>
          <div>Rot <b>{Math.round(rot.x)}° / {Math.round(rot.z)}°</b></div>
        </div>
      </div>
    </section>
  );
}

// ───────── BOQ ─────────
function BOQ() {
  useProject();
  const [region, setRegion] = useState("HK");
  const P = (D.pricing || {})[region] || { currency: "HK$", perM2: 0, total: 0, rows: [] };
  return (
    <section>
      <div className="view-head">
        <div>
          <h1 className="view-title">Bill of Quantities</h1>
          <div className="view-sub">报价清单 · switch region to regenerate prices instantly</div>
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
            <div className="val" style={{fontSize:24}}>{P.currency}{P.perM2.toLocaleString()}<small>/ m²</small></div>
          </div>
        </div>
        <div className="boq-region-switch">
          {["HK","CN","INTL"].map(r => (
            <button key={r}
                    className={"boq-region-btn " + (region===r ? "on":"")}
                    onClick={()=>setRegion(r)}>{r === "INTL" ? "Intl · US$" : r === "HK" ? "HK · HK$" : "CN · ¥"}</button>
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
  const bars = [
    { label:"HVAC", val:52, unit:"%", pct:52 },
    { label:"Lighting", val:20, unit:"%", pct:20 },
    { label:"Equipment", val:12, unit:"%", pct:12 },
    { label:"Other", val:16, unit:"%", pct:16 }
  ];
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
            <span className="delta">44% under limit</span>
          </div>
          <div className="eui-baseline">
            <div><span>HK BEEO limit</span><b>150</b></div>
            <div><span>HK average</span><b>122</b></div>
            <div><span>Annual total</span><b>3,358 kWh</b></div>
            <div><span>CO₂e</span><b>1.98 t / yr</b></div>
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
  useProject();
  const [chosen, setChosen] = useState("A");
  // 兼容两种 schema：legacy data.js 是 array · 新版是 {list: [...]}
  const variantArray = Array.isArray(D.variants) ? D.variants : (D.variants?.list || []);
  return (
    <section>
      <div className="view-head">
        <div>
          <h1 className="view-title">A / B / C Variants</h1>
          <div className="view-sub">方案对比 · three complete design directions · side by side</div>
        </div>
      </div>
      <div className="abc-grid">
        {variantArray.map(v => (
          <div key={v.id} className={"abc-variant " + (chosen===v.id ? "chosen":"")} onClick={()=>setChosen(v.id)}>
            <div className="abc-img">
              <div className="abc-label">Option {v.id}</div>
              <Img src={v.img} alt={v.name} />
            </div>
            <div className="abc-body">
              <div className="abc-name">{v.name}<span className="zh">{v.zh}</span></div>
              <div className="abc-tagline">{v.tagline}</div>
              <div className="abc-specs">
                <div className="abc-spec"><div className="lbl">Cost</div><div className="val">HK${v.cost}</div></div>
                <div className="abc-spec"><div className="lbl">EUI</div><div className="val">{v.eui}<small>kWh</small></div></div>
              </div>
              <div className="abc-choose">{chosen===v.id ? "✓ Selected" : "Choose this direction"}</div>
            </div>
          </div>
        ))}
      </div>

      <div style={{background:"var(--bg-1)",border:"1px solid var(--line)",borderRadius:6,padding:"18px 22px"}}>
        <div style={{fontFamily:"var(--f-mono)",fontSize:10,color:"var(--text-3)",textTransform:"uppercase",letterSpacing:"0.12em",marginBottom:12}}>Difference matrix</div>
        <table style={{width:"100%",fontSize:13,borderCollapse:"collapse"}}>
          <thead>
            <tr style={{color:"var(--text-3)",fontFamily:"var(--f-mono)",fontSize:10,textTransform:"uppercase",letterSpacing:"0.08em"}}>
              <th style={{textAlign:"left",padding:"8px 0"}}>Aspect</th>
              <th style={{textAlign:"left"}}>A · Scholar</th>
              <th style={{textAlign:"left"}}>B · Temple Minimal</th>
              <th style={{textAlign:"left"}}>C · Tea Merchant</th>
            </tr>
          </thead>
          <tbody style={{color:"var(--text-2)"}}>
            {[
              ["Primary wood","Deep rosewood","Bleached oak","Warm walnut"],
              ["Wall treatment","Hemp plaster","Raw concrete","Veneer + brass"],
              ["Floor","Dark tile","Tatami panels","Herringbone wood"],
              ["Feel","Scholarly quiet","Austere, still","Warm hospitality"],
              ["EUI","84","78","92"],
              ["Cost","HK$540k","HK$485k","HK$612k"]
            ].map((r,i)=>(
              <tr key={i} style={{borderTop:"1px dashed var(--line)"}}>
                {r.map((c,j)=>(<td key={j} style={{padding:"10px 8px 10px 0",color: (j===0?"var(--text-3)":"var(--text-2)"), fontFamily: j===0?"var(--f-mono)":"inherit", fontSize: j===0?11:13, textTransform: j===0?"uppercase":"none", letterSpacing: j===0?"0.06em":0}}>{c}</td>))}
              </tr>
            ))}
          </tbody>
        </table>
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
  const { canUndo, canReset, dispatch } = useProject();
  const items = D.timeline || [];
  return (
    <section>
      <div className="view-head">
        <div>
          <h1 className="view-title">Timeline</h1>
          <div className="view-sub">修改历史 · every change, every diff, every minute</div>
        </div>
        <div style={{display:"flex", gap:8}}>
          <button className="d3-btn" disabled={!canUndo}
                  onClick={()=>dispatch({type:"REWIND", index: Math.max(0, (items.length - 2))})}
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
const SYSTEM_PROMPT = `You are the project assistant inside Arctura Labs — a tool that turns a one-sentence brief into a complete, buildable interior space (3D model, floorplan, BOQ, energy report, compliance check, stakeholder decks).

You are currently open on the "Zen Tea Room" project:
- 禅意茶室 · New-Chinese style · 40 m² · Hong Kong
- Current total cost: HK$540k (HK$13,510/m²)
- Current EUI: 84 kWh/m²·yr (44% under HK BEEO limit of 150)
- Compliance: HK · BEEO — 7/8 passed (OTTV pending facade finalization)
- 6 zones: Tea Ceremony 16m², Ink Gallery 6m², Tea Display 4m², Boiling Station 4m², Zen Garden 4m², Foyer 3m²
- Delivered in 56 min, 1 day ago
- Has 3 design variants: A-Scholar (HK$540k, EUI 84), B-Temple Minimal (HK$485k, EUI 78), C-Tea Merchant (HK$612k, EUI 92)

The user can ask you to change anything — budget, material, code region, feel, dimensions, energy target. Respond as if you are actually regenerating the affected artifacts.

Response format (STRICT — always exactly this shape):
1. One short paragraph (1–3 sentences, max 50 words) explaining what you changed and the visible impact.
2. A single line starting with "DIFF:" giving 2–4 numeric deltas separated by " · ", e.g. "DIFF: −HK$108k · EUI 84→71 · insulation +40mm". Use − for decrease, + for increase. Omit the DIFF line only if the message is a clarifying question.

Tone: confident, specific, numeric. Never generic. Mix in Chinese only if the user writes in Chinese. Do not use bullet points or markdown headers. Do not ask "anything else?" — keep it tight.`;

function Chat({ onNavigate }) {
  const [msgs, setMsgs] = useState([
    { role:"bot", text:"Hello — I'm your project assistant. Tell me what you'd like to change and I'll regenerate the affected artifacts.", diff:null },
    { role:"sys", text:"v1 · new-chinese · delivered 1 day ago" }
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
    const userMsg = { role:"user", text };
    const nextMsgs = [...msgs, userMsg];
    setMsgs(nextMsgs);
    setInput("");
    setThinking(true);

    let replyRaw;
    let fromModel = null;
    try {
      // 1. 首选：/api/chat Edge Function → 智增增 gateway
      const r = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model,
          system: SYSTEM_PROMPT,
          messages: buildMessages(msgs, text),
          max_tokens: 800,
        }),
      });
      if (r.ok) {
        const data = await r.json();
        replyRaw = data.text || "";
        fromModel = data.model;
      } else {
        // 2. API 失败 → 用降级关键词匹配
        const err = await r.json().catch(() => ({}));
        console.warn("chat API failed:", r.status, err);
        replyRaw = offlineFallback(text) + "\n\n(fell back · api error " + r.status + ")";
      }
    } catch (err) {
      // 3. 网络 / 超时 → 降级
      console.warn("chat API exception:", err);
      replyRaw = offlineFallback(text) + "\n\n(fell back · " + (err.message || "network error") + ")";
    }

    const { text: replyText, diff } = parseReply(replyRaw);
    setThinking(false);
    setMsgs(m => [...m, { role:"bot", text: replyText, diff, model: fromModel }]);
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

  const chips = [
    "Show me a budget variant",
    "Check Beijing code",
    "Make it warmer",
    "Reduce EUI further"
  ];

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
          <div className="chat-sub">Editing · Zen Tea Room · v1</div>
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
            <div key={i} className={"msg " + m.role}>
              {m.text}
              {m.diff && <div className="msg-diff"><i>+</i>{m.diff}</div>}
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

  // 每次 state 变化 → 同步到 stateHolder / window.ZEN_DATA · 让 D Proxy 读到新值
  useEffect(() => {
    stateHolder.current = projectState.current;
    window.ZEN_DATA = projectState.current;
  }, [projectState.current]);

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
