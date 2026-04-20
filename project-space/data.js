// Project Space data — zen-tea demo（/project/ 无 slug 时的默认数据）
window.ZEN_DATA = {
  slug: "zen-tea",
  complete: true,
  cat: "hospitality",
  type: "P1-interior",
  // 真 3D 模型 · Blender 导出的 GLB（禅意茶室 · 新中式）
  model_glb: "/assets/mvps/20-zen-tea-room/variants/v1-new-chinese/model.glb",
  hero_img: "/assets/zen-tea/render-01-hero.png",
  thumb_img: "/assets/zen-tea/render-01-hero.png",
  // 可编辑字段默认值 · chat-edit 首次交互的 baseline
  editable: { area_m2: 40, insulation_mm: 60, glazing_uvalue: 2.0, lighting_cct: 3000, lighting_density_w_m2: 11, wwr: 0.25, region: "HK" },
  // derived · 初始值 · chat 改后 recompute 覆盖
  derived: { eui_kwh_m2_yr: 84, cost_total: 540392, cost_per_m2: 13510, co2_t_per_yr: 1.98, compliance_fails: 0, compliance_verdict: "COMPLIANT" },
  project: { name: "Zen Tea Room", zh: "禅意茶室 · 新中式", area: 40, location: "Hong Kong", budgetHKD: 360000, style: "Neo-Chinese" },
  renders: [
    { id: "01", file: "/assets/zen-tea/render-01-hero.png", title: "Hero corner · 品茶区", tag: "01 / Hero" },
    { id: "03", file: "/assets/zen-tea/render-03-main.png", title: "Main tea zone · 主品茶区", tag: "03 / Main" },
    { id: "04", file: "/assets/zen-tea/render-04-feature.png", title: "Feature wall · 水墨展示区", tag: "04 / Feature" },
    { id: "08", file: "/assets/zen-tea/render-08-birds-eye.png", title: "Bird's-eye · 俯视图", tag: "08 / Plan" }
  ],
  zones: [
    { id:"tea", name:"Tea Ceremony", zh:"品茶区", area:16, notes:"Rosewood table 2.0×0.8m + 4 chairs + copper kettle", x:22, y:28, w:42, h:44 },
    { id:"ink", name:"Ink Gallery", zh:"水墨展示区", area:6, notes:"3 ink paintings + spot lights + antique shelf", x:22, y:6, w:42, h:18 },
    { id:"display", name:"Tea Display", zh:"茶叶展示柜", area:4, notes:"Rosewood curio shelf + 6 porcelain jars", x:70, y:14, w:24, h:22 },
    { id:"boil", name:"Boiling Station", zh:"煮水区", area:4, notes:"Copper induction + filter + rosewood counter", x:6, y:62, w:16, h:24 },
    { id:"zen", name:"Zen Garden", zh:"禅意庭院角", area:4, notes:"Miniature dry garden + moss + bamboo", x:70, y:62, w:24, h:24 },
    { id:"entry", name:"Foyer", zh:"入口玄关", area:3, notes:"Screen + shoe rack + umbrella stand", x:70, y:38, w:24, h:20 }
  ],
  furniture: [
    { id:"table", label:"Tea table", x:36, y:40, w:18, h:22, color:"#6b4a32" },
    { id:"chair1", label:"Chair", x:27, y:46, w:7, h:10, color:"#8b5a3c" },
    { id:"chair2", label:"Chair", x:57, y:46, w:7, h:10, color:"#8b5a3c" },
    { id:"chair3", label:"Chair", x:42, y:32, w:8, h:8, color:"#8b5a3c" },
    { id:"chair4", label:"Chair", x:42, y:63, w:8, h:8, color:"#8b5a3c" }
  ],
  pricing: {
    HK: { label:"Hong Kong", currency:"HK$", perM2:13510, rows:[
      {cat:"STRUCTURE", desc:"Floor slab · RC 120mm + formwork", sub:"40 m² · struct", qty:"40 m²", amt:"48,000"},
      {cat:"STRUCTURE", desc:"Exterior walls · brick 200mm (U≤1.2)", sub:"78 m² · envelope", qty:"78 m²", amt:"66,300"},
      {cat:"STRUCTURE", desc:"Interior partitions · gypsum board", sub:"50 m² · double-sided", qty:"50 m²", amt:"21,168"},
      {cat:"OPENINGS", desc:"Windows · thermal-break Low-E double", sub:"23.4 m² · U≤2.2", qty:"23 m²", amt:"88,920"},
      {cat:"OPENINGS", desc:"Doors · solid wood 900mm + hardware", sub:"6 ea · complete", qty:"6 ea", amt:"51,000"},
      {cat:"FINISH", desc:"Floor finishes · ceramic tile, all zones", sub:"40 m² · supply + install", qty:"40 m²", amt:"15,200"},
      {cat:"STRUCTURE", desc:"Roof · RC + 60mm XPS + membrane", sub:"40 m² · U≤0.50", qty:"40 m²", amt:"68,000"}
    ], subtotal:"358,588", mep:"89,647", prelim:"43,031", cont:"49,127", total:"540,392" },
    CN: { label:"Mainland China", currency:"¥", perM2:4320, rows:[
      {cat:"STRUCTURE", desc:"Floor slab · RC 120mm + formwork", sub:"40 m² · struct", qty:"40 m²", amt:"15,600"},
      {cat:"STRUCTURE", desc:"Exterior walls · brick 200mm", sub:"78 m² · envelope", qty:"78 m²", amt:"21,000"},
      {cat:"STRUCTURE", desc:"Interior partitions · gypsum", sub:"50 m² · double-sided", qty:"50 m²", amt:"6,750"},
      {cat:"OPENINGS", desc:"Windows · thermal-break Low-E", sub:"23.4 m² · U≤2.2", qty:"23 m²", amt:"28,080"},
      {cat:"OPENINGS", desc:"Doors · solid wood + hardware", sub:"6 ea · complete", qty:"6 ea", amt:"15,300"},
      {cat:"FINISH", desc:"Floor finishes · ceramic tile", sub:"40 m² · supply + install", qty:"40 m²", amt:"4,800"},
      {cat:"STRUCTURE", desc:"Roof · RC + 60mm XPS + membrane", sub:"40 m²", qty:"40 m²", amt:"21,600"}
    ], subtotal:"113,130", mep:"28,283", prelim:"13,575", cont:"15,500", total:"172,488" },
    INTL: { label:"International", currency:"US$", perM2:1730, perSqft:161, rows:[
      {cat:"STRUCTURE", desc:"Floor slab · RC 120mm + formwork", sub:"40 m² · struct", qty:"40 m²", amt:"6,150"},
      {cat:"STRUCTURE", desc:"Exterior walls · brick 200mm", sub:"78 m² · envelope", qty:"78 m²", amt:"8,500"},
      {cat:"STRUCTURE", desc:"Interior partitions · gypsum", sub:"50 m² · double-sided", qty:"50 m²", amt:"2,700"},
      {cat:"OPENINGS", desc:"Windows · Low-E double", sub:"23.4 m² · U≤2.2", qty:"23 m²", amt:"11,400"},
      {cat:"OPENINGS", desc:"Doors · solid wood + hardware", sub:"6 ea · complete", qty:"6 ea", amt:"6,540"},
      {cat:"FINISH", desc:"Floor finishes · ceramic tile", sub:"40 m² · supply + install", qty:"40 m²", amt:"1,940"},
      {cat:"STRUCTURE", desc:"Roof · RC + 60mm XPS + membrane", sub:"40 m²", qty:"40 m²", amt:"8,700"}
    ], subtotal:"45,930", mep:"11,483", prelim:"5,512", cont:"6,293", total:"69,218" }
  },
  energy: { eui:84, limit:150, annual:3358, hvac:52, light:20, equip:12 },
  compliance: {
    HK: { label:"HK · BEEO 2021", verdict:"COMPLIANT", score:"7/8 passed", items:[
      {check:"Wall U-value", zh:"外墙 U 值", val:"0.555", unit:"W/m²K", limit:"1.8", status:"pass"},
      {check:"Roof U-value", zh:"屋顶 U 值", val:"0.498", unit:"W/m²K", limit:"0.8", status:"pass"},
      {check:"Window U-value", zh:"窗户 U 值", val:"2.0", unit:"W/m²K", limit:"5.8", status:"pass"},
      {check:"Window SHGC", zh:"太阳能得热", val:"0.4", unit:"—", limit:"0.6", status:"pass"},
      {check:"OTTV", zh:"整体热传透值", val:"needs facade", unit:"W/m²", limit:"25", status:"warn"},
      {check:"Lighting Power Density", zh:"照明功率密度", val:"8.0", unit:"W/m²", limit:"10.0", status:"pass"},
      {check:"Fresh Air (ACH)", zh:"新风换气", val:"0.7", unit:"ACH", limit:"0.5", status:"pass"},
      {check:"EUI", zh:"能耗强度", val:"84", unit:"kWh/m²·yr", limit:"150", status:"pass"}
    ]},
    CN: { label:"GB 50189 · Cold Zone", verdict:"REVIEW NEEDED", score:"5/8 passed", items:[
      {check:"Wall U-value", zh:"外墙 U 值", val:"0.555", unit:"W/m²K", limit:"0.45", status:"fail"},
      {check:"Roof U-value", zh:"屋顶 U 值", val:"0.498", unit:"W/m²K", limit:"0.35", status:"fail"},
      {check:"Window U-value", zh:"窗户 U 值", val:"2.0", unit:"W/m²K", limit:"2.5", status:"pass"},
      {check:"Window SHGC", zh:"太阳能得热", val:"0.4", unit:"—", limit:"0.5", status:"pass"},
      {check:"OTTV", zh:"整体热传透值", val:"needs facade", unit:"W/m²", limit:"20", status:"warn"},
      {check:"Lighting Power Density", zh:"照明功率密度", val:"8.0", unit:"W/m²", limit:"9.0", status:"pass"},
      {check:"Fresh Air (ACH)", zh:"新风换气", val:"0.7", unit:"ACH", limit:"0.5", status:"pass"},
      {check:"EUI", zh:"能耗强度", val:"84", unit:"kWh/m²·yr", limit:"95", status:"pass"}
    ]},
    US: { label:"ASHRAE 90.1-2022", verdict:"COMPLIANT", score:"7/8 passed", items:[
      {check:"Wall U-value", zh:"外墙 U 值", val:"0.555", unit:"W/m²K", limit:"0.7", status:"pass"},
      {check:"Roof U-value", zh:"屋顶 U 值", val:"0.498", unit:"W/m²K", limit:"0.5", status:"pass"},
      {check:"Window U-value", zh:"窗户 U 值", val:"2.0", unit:"W/m²K", limit:"3.4", status:"pass"},
      {check:"Window SHGC", zh:"太阳能得热", val:"0.4", unit:"—", limit:"0.4", status:"warn"},
      {check:"OTTV", zh:"整体热传透值", val:"needs facade", unit:"W/m²", limit:"—", status:"warn"},
      {check:"Lighting Power Density", zh:"照明功率密度", val:"8.0", unit:"W/m²", limit:"9.5", status:"pass"},
      {check:"Fresh Air (ACH)", zh:"新风换气", val:"0.7", unit:"ACH", limit:"0.5", status:"pass"},
      {check:"EUI", zh:"能耗强度", val:"84", unit:"kWh/m²·yr", limit:"120", status:"pass"}
    ]},
    JP: { label:"省エネ法 2025", verdict:"NON-COMPLIANT", score:"4/8 passed", items:[
      {check:"Wall U-value", zh:"外墙 U 值", val:"0.555", unit:"W/m²K", limit:"0.30", status:"fail"},
      {check:"Roof U-value", zh:"屋顶 U 值", val:"0.498", unit:"W/m²K", limit:"0.25", status:"fail"},
      {check:"Window U-value", zh:"窗户 U 值", val:"2.0", unit:"W/m²K", limit:"1.9", status:"fail"},
      {check:"Window SHGC", zh:"太阳能得热", val:"0.4", unit:"—", limit:"0.55", status:"pass"},
      {check:"OTTV", zh:"整体热传透值", val:"needs facade", unit:"W/m²", limit:"—", status:"warn"},
      {check:"Lighting Power Density", zh:"照明功率密度", val:"8.0", unit:"W/m²", limit:"8.5", status:"pass"},
      {check:"Fresh Air (ACH)", zh:"新风换气", val:"0.7", unit:"ACH", limit:"0.5", status:"pass"},
      {check:"EUI", zh:"能耗强度", val:"84", unit:"kWh/m²·yr", limit:"75", status:"fail"}
    ]}
  },
  variants: [
    { id:"A", name:"Scholar's Retreat", zh:"文人书斋", img:"/assets/zen-tea/render-01-hero.png", tagline:"Deep rosewood + ink paintings. The quiet classical.", cost:"540k", eui:"84", chosen:true },
    { id:"B", name:"Temple Minimal", zh:"禅寺极简", img:"/assets/zen-tea/render-03-main.png", tagline:"Bleached oak + raw concrete. Austere and still.", cost:"485k", eui:"78" },
    { id:"C", name:"Tea Merchant", zh:"茶商宅邸", img:"/assets/zen-tea/render-04-feature.png", tagline:"Warm walnut + brass. Hospitality-forward.", cost:"612k", eui:"92" }
  ],
  timeline: [
    { time:"14:22 · today", title:"Beijing compliance switch requested", desc:"Client asked to check against GB 50189. Three envelope values fall short.", diff:"+60mm rockwool suggested · passes 6/7 after change" },
    { time:"13:08 · today", title:"Budget variant generated", desc:"Client requested a 20% budget reduction. Economy scheme generated.", diff:"−HK$108k · swapped rosewood → walnut veneer" },
    { time:"09:44 · today", title:"Feature wall updated", desc:"Changed from 3 scrolls to 5 smaller ones per client note.", diff:"5 pieces · reduced frame cost" },
    { time:"Yesterday", title:"Initial delivery", desc:"Full package delivered: 3D model (115 objects), 4 renders, floorplan, BOQ, energy report, 8 stakeholder decks.", diff:"56 min total · brief → complete package" }
  ],
  decks: [
    { to:"Client", zh:"客户版", num:"01", pages:11 },
    { to:"Investor", zh:"投资人", num:"02", pages:14 },
    { to:"Designer", zh:"设计师", num:"03", pages:9 },
    { to:"Contractor", zh:"承包商", num:"04", pages:12 },
    { to:"BIM Engineer", zh:"BIM 工程师", num:"05", pages:10 },
    { to:"Operations", zh:"运营", num:"06", pages:8 },
    { to:"Marketing", zh:"市场", num:"07", pages:9 },
    { to:"School Leader", zh:"空间负责人", num:"08", pages:10 }
  ],
  downloads: [
    { ext:"GLB", name:"zen-tea-v1-new-chinese.glb", sub:"3D web-ready", size:"2.1 MB" },
    { ext:"OBJ", name:"zen-tea-v1-new-chinese.obj", sub:"Universal 3D", size:"1.8 MB" },
    { ext:"FBX", name:"zen-tea-v1-new-chinese.fbx", sub:"Animation · Unity", size:"3.2 MB" },
    { ext:"IFC", name:"zen-tea-v1-new-chinese.ifc", sub:"BIM · industry foundation", size:"1.4 MB" },
    { ext:"DXF", name:"floorplan.dxf", sub:"CAD · dimensioned", size:"340 KB" },
    { ext:"PNG", name:"floorplan.png", sub:"Floorplan · rendered", size:"180 KB" },
    { ext:"PDF", name:"deck-client.pdf", sub:"Client presentation", size:"4.8 MB" },
    { ext:"CSV", name:"boq-HK.csv", sub:"Bill of quantities", size:"12 KB" },
    { ext:"MD", name:"compliance-HK.md", sub:"Compliance report", size:"6 KB" }
  ]
};
