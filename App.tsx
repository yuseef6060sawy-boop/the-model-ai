import { useEffect, useMemo, useState } from 'react';
import { Activity, Atom, Database, FlaskConical, Gauge, Layers3, Menu, Microscope, ShieldCheck, SlidersHorizontal, Sparkles } from 'lucide-react';

const API = 'http://127.0.0.1:8000/api';
type Material = { id:string; name:string; formula:string; reference_density_g_cm3:number; elemental_mass_percent:Record<string,number>; data_note:string };
type Component = { material:string; percentage:number };
type Result = { status:string; predicted_response:number; unit:string; limitations:string[]; estimated_mixture_density_g_cm3:number };
const nav = [
  {label:'Overview', icon:Activity, id:'overview'},
  {label:'Materials Library', icon:Atom, id:'materials'},
  {label:'Mixture Designer', icon:FlaskConical, id:'designer'},
  {label:'Radiation Analysis', icon:Gauge, id:'analysis'},
  {label:'Research Data', icon:Database, id:'data'},
];
export default function App(){
  const [page,setPage]=useState('overview');
  const [materials,setMaterials]=useState<Material[]>([]);
  const [health,setHealth]=useState<any>(null);
  const [metrics,setMetrics]=useState<any>(null);
  const [selected,setSelected]=useState<Component[]>([]);
  const [environment,setEnvironment]=useState('GCR');
  const [depth,setDepth]=useState('5');
  const [result,setResult]=useState<Result|null>(null);
  const [busy,setBusy]=useState(false);
  const [error,setError]=useState('');
  const [language,setLanguage]=useState<'EN'|'AR'>('EN');
  const isAr=language==='AR';

  useEffect(()=>{ refresh(); },[]);
  async function refresh(){
    try{
      const [m,h,mt]=await Promise.all([fetch(`${API}/materials`),fetch(`${API}/health`),fetch(`${API}/metrics`)]);
      if(m.ok)setMaterials(await m.json());
      if(h.ok)setHealth(await h.json());
      if(mt.ok)setMetrics(await mt.json());
    }catch{setHealth({status:'offline'});}
  }
  const total=useMemo(()=>selected.reduce((s,x)=>s+x.percentage,0),[selected]);
  const chosen=useMemo(()=>materials.filter(m=>selected.some(s=>s.material===m.id)),[materials,selected]);
  function addMaterial(id:string){
    if(selected.some(x=>x.material===id))return;
    if(selected.length>=6)return;
    const next=[...selected,{material:id,percentage:0}];
    const share=100/next.length;
    setSelected(next.map(x=>({...x,percentage:share})));
    setResult(null);setError('');
  }
  function removeMaterial(id:string){
    const next=selected.filter(x=>x.material!==id);
    const share=next.length?100/next.length:0;
    setSelected(next.map(x=>({...x,percentage:share})));
    setResult(null);
  }
  function changePct(id:string,value:number){
    setSelected(old=>old.map(x=>x.material===id?{...x,percentage:value}:x));
    setResult(null);
  }
  async function analyze(){
    setError('');setResult(null);
    if(selected.length===0){setError(isAr?'اختر مادة واحدة على الأقل.':'Select at least one material.');return;}
    if(Math.abs(total-100)>0.05){setError(isAr?`مجموع النسب الحالي ${total.toFixed(2)}%. يجب أن يساوي 100%.`:`Current total is ${total.toFixed(2)}%. It must equal 100%.`);return;}
    setBusy(true);
    try{
      const response=await fetch(`${API}/mixture/analyze`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({environment,areal_density_g_cm2:Number(depth),components:selected})});
      const body=await response.json();
      if(!response.ok)throw new Error(body.detail||'Analysis failed');
      setResult(body);
    }catch(e:any){setError(e.message||'API unavailable');}
    finally{setBusy(false);}
  }
  const t=(en:string,ar:string)=>isAr?ar:en;
  return <div className={isAr?'app rtl':'app'} dir={isAr?'rtl':'ltr'}>
    <aside className="sidebar">
      <div className="brand"><div className="brand-mark"><ShieldCheck size={23}/></div><div><b>LunaShield</b><small>RESEARCH PLATFORM</small></div></div>
      <div className="workspace-label">{t('WORKSPACE','مساحة العمل')}</div>
      {nav.map(n=><button key={n.id} className={`nav-item ${page===n.id?'active':''}`} onClick={()=>setPage(n.id)}><n.icon size={18}/><span>{t(n.label,({'Overview':'نظرة عامة','Materials Library':'مكتبة المواد','Mixture Designer':'مصمم الخلطات','Radiation Analysis':'تحليل الإشعاع','Research Data':'بيانات البحث'} as any)[n.label])}</span></button>)}
      <div className="sidebar-bottom"><div className="status-dot"/><span>{t('Research API connection','اتصال واجهة البحث')}</span><b>{health?.status==='online'?'ONLINE':'OFFLINE'}</b></div>
    </aside>
    <main className="main">
      <header className="topbar"><div><div className="eyebrow">LUNASHIELD / {page.toUpperCase()}</div><h1>{t(nav.find(n=>n.id===page)?.label||'Overview',({'Overview':'نظرة عامة','Materials Library':'مكتبة المواد','Mixture Designer':'مصمم الخلطات','Radiation Analysis':'تحليل الإشعاع','Research Data':'بيانات البحث'} as any)[nav.find(n=>n.id===page)?.label||'Overview'])}</h1></div><div className="top-actions"><span className={`connection ${health?.status==='online'?'good':''}`}><i/>{health?.status==='online'?t('API Connected','متصل بالنظام'):t('API Offline','النظام غير متصل')}</span><button className="lang" onClick={()=>setLanguage(isAr?'EN':'AR')}>{isAr?'EN':'عربي'}</button><div className="avatar">LS</div></div></header>

      {page==='overview'&&<><section className="hero"><div className="hero-copy"><div className="pill"><Sparkles size={14}/> RESEARCH & ENGINEERING</div><h2>{t('Explore radiation shielding materials with transparent AI.','استكشف مواد الحماية الإشعاعية باستخدام ذكاء اصطناعي شفاف.')}</h2><p>{t('Analyze supported reference materials and inspect model readiness. Every result is labeled with its data source and limitations.','حلّل المواد المرجعية المتاحة وتحقق من جاهزية النماذج. كل نتيجة موضّح مصدرها وحدودها.')}</p><button className="primary" onClick={()=>setPage('designer')}>{t('Open Mixture Designer','افتح مصمم الخلطات')} <span>↗</span></button></div><div className="hero-orbit"><div className="orbit o1"/><div className="orbit o2"/><div className="planet"><Atom size={54}/></div><div className="orbit-tag">AI / MATERIALS</div></div></section>
      <div className="section-head"><div><h3>{t('System readiness','جاهزية النظام')}</h3><p>{t('Live status from your local research files','حالة مباشرة من ملفات البحث المحلية')}</p></div><button className="subtle" onClick={refresh}>↻ {t('Refresh','تحديث')}</button></div>
      <div className="stat-grid"><Stat icon={<Database/>} label={t('Training data','بيانات التدريب')} value={health?.required_files?.data?'FOUND':'NOT FOUND'} detail="Normalized OLTARIS CSV"/><Stat icon={<Sparkles/>} label={t('Saved models','النماذج المحفوظة')} value={Object.values(health?.models||{}).filter(Boolean).length+'/2'} detail="GCR / SPE dose models"/><Stat icon={<Gauge/>} label={t('Validation report','تقرير التقييم')} value={health?.required_files?.metrics?'FOUND':'NOT FOUND'} detail="Leave-One-Material-Out"/></div>
      <div className="notice"><ShieldCheck size={20}/><div><b>{t('Research integrity mode is enabled','وضع النزاهة البحثية مفعّل')}</b><p>{t('The interface does not generate sample records. Missing files or unsupported predictions are reported instead of being replaced with invented values.','الواجهة لا تنشئ سجلات تجريبية. عند غياب الملفات أو عدم دعم التوقع، ستظهر رسالة واضحة بدل اختلاق بيانات.')}</p></div></div></>}

      {page==='materials'&&<><div className="section-head"><div><h3>{t('Reference materials','المواد المرجعية')}</h3><p>{t('Catalog entries defined in the research notebook','المواد المعرفة في Notebook البحث')}</p></div><span className="count">{materials.length} {t('materials','مواد')}</span></div><div className="material-grid">{materials.map(m=><div className="material-card" key={m.id}><div className="material-icon"><Atom/></div><div className="formula">{m.formula}</div><h3>{m.name}</h3><p>Reference density</p><strong>{m.reference_density_g_cm3} <small>g/cm³</small></strong><div className="element-list">{Object.entries(m.elemental_mass_percent).map(([k,v])=><span key={k}>{k} {v.toFixed(1)}%</span>)}</div><button className="outline" onClick={()=>{addMaterial(m.id);setPage('designer')}}>{t('Add to design','أضف للتصميم')} +</button></div>)}</div><p className="footnote">ⓘ {t('Reference properties are not measured properties of a manufactured composite.','الخواص المرجعية ليست قياسات لمركّب تم تصنيعه.')}</p></>}

      {page==='designer'&&<><div className="designer-layout"><section className="panel"><div className="panel-title"><div><h3>{t('Build your virtual mixture','كوّن الخلطة الافتراضية')}</h3><p>{t('Choose materials, then adjust their mass percentages.','اختر المواد ثم عدّل النسب الكتلية.')}</p></div><span className="step">01 / 02</span></div><div className="library-mini"><b>{t('MATERIAL LIBRARY','مكتبة المواد')}</b><div className="mini-grid">{materials.map(m=><button key={m.id} disabled={selected.some(x=>x.material===m.id)||selected.length>=6} onClick={()=>addMaterial(m.id)} className="mini-material"><span>{m.formula}</span><small>{m.name}</small><i>+</i></button>)}</div></div><div className="composition-head"><b>{t('YOUR COMPOSITION','تركيبك الحالي')}</b><span className={Math.abs(total-100)<.05?'valid':'invalid'}>{t('TOTAL','الإجمالي')} {total.toFixed(2)}%</span></div>
      {selected.length===0?<div className="empty"><Layers3 size={30}/><b>{t('No materials selected','لم تختر أي مواد')}</b><span>{t('Choose materials from the library above to begin.','اختر مواد من المكتبة بالأعلى للبدء.')}</span></div>:selected.map(c=>{const m=materials.find(x=>x.id===c.material)!;return <div className="composition-row" key={c.material}><div className="comp-info"><b>{m.formula}</b><span>{m.name}</span><button onClick={()=>removeMaterial(c.material)}>×</button></div><div className="slider-line"><input type="range" min="0" max="100" step=".5" value={c.percentage} onChange={e=>changePct(c.material,Number(e.target.value))}/><input className="number" type="number" min="0" max="100" step=".5" value={Number(c.percentage.toFixed(1))} onChange={e=>changePct(c.material,Math.max(0,Math.min(100,Number(e.target.value))))}/><span>%</span></div></div>})}
      <div className="total-track"><div style={{width:`${Math.min(total,100)}%`}}/></div><div className="total-label"><span>{t('Mass percentage total','إجمالي النسب الكتلية')}</span><b>{total.toFixed(1)} / 100%</b></div></section>
      <section className="panel parameters"><div className="panel-title"><div><h3>{t('Analysis settings','إعدادات التحليل')}</h3><p>{t('Set the conditions for the model input.','حدد ظروف مدخلات النموذج.')}</p></div><SlidersHorizontal/></div><label>{t('Radiation environment','بيئة الإشعاع')}</label><div className="segmented"><button className={environment==='GCR'?'chosen':''} onClick={()=>setEnvironment('GCR')}>GCR</button><button className={environment==='SPE'?'chosen':''} onClick={()=>setEnvironment('SPE')}>SPE</button></div><label>{t('Areal density','الكثافة المساحية')}</label><div className="input-unit"><input type="number" min=".01" step=".1" value={depth} onChange={e=>setDepth(e.target.value)}/><span>g/cm²</span></div><div className="callout"><Microscope size={18}/><p>{t('Predictions are exploratory only. The current model was trained on individual reference materials, not custom mixtures.','التوقعات استكشافية فقط. النموذج الحالي تدرب على مواد مرجعية منفردة وليس خلطات مخصصة.')}</p></div><button className="primary full" disabled={busy||!selected.length} onClick={analyze}>{busy?t('Analyzing…','جارٍ التحليل…'):t('Run AI analysis','تشغيل تحليل الذكاء الاصطناعي')} <span>→</span></button>{error&&<div className="error">{error}</div>}</section></div>
      {result&&<section className="result-panel"><div className="result-title"><div><span className="pill">MODEL OUTPUT</span><h3>{t('Exploratory prediction','توقع استكشافي')}</h3></div><span className="unverified">UNVALIDATED MIXTURE</span></div><div className="result-value">{Number(result.predicted_response).toPrecision(5)}<small>{result.unit}</small></div><p>{t('Estimated mixture density','الكثافة التقديرية للخلطة')}: <b>{result.estimated_mixture_density_g_cm3.toFixed(4)} g/cm³</b></p><div className="limitations">{result.limitations.map(x=><p key={x}>• {x}</p>)}</div></section>}</>}

      {page==='analysis'&&<section className="panel"><h3>{t('Model validation results','نتائج تقييم النماذج')}</h3><p>{t('Metrics are read only from the actual training output CSV. No example metrics are displayed.','المقاييس تُقرأ فقط من ملف نتائج التدريب الفعلي. لا نعرض مقاييس تجريبية.')}</p>{metrics?.available? <div className="table-wrap"><table><thead><tr>{Object.keys(metrics.records[0]||{}).map(k=><th key={k}>{k}</th>)}</tr></thead><tbody>{metrics.records.map((r:any,i:number)=><tr key={i}>{Object.values(r).map((v:any,j:number)=><td key={j}>{v===null?'—':String(v)}</td>)}</tr>)}</tbody></table></div>:<div className="empty"><Database/><b>{t('No validation report found','لم يتم العثور على تقرير تقييم')}</b><span>{metrics?.message||t('Connect the real training results folder.','اربط مجلد نتائج التدريب الحقيقي.')}</span></div>}</section>}

      {page==='data'&&<section className="panel"><h3>{t('Research data provenance','مصادر بيانات البحث')}</h3><p>{t('This page reports the model card produced by the training notebook.','تعرض هذه الصفحة بطاقة النموذج الناتجة من Notebook التدريب.')}</p>{health?.required_files?.model_card?<div className="notice"><ShieldCheck/><div><b>model_card.json detected</b><p>{t('Open the API endpoint /api/model-card to inspect source, DOI, archive hash, validation and limitations.','افتح المسار /api/model-card لمراجعة المصدر وDOI وبصمة الأرشيف والتقييم والقيود.')}</p></div></div>:<div className="empty"><Database/><b>{t('Model card not found','بطاقة النموذج غير موجودة')}</b><span>{t('No provenance details will be invented. Run the training notebook and place its real results in the expected folder.','لن نخترع تفاصيل للمصدر. شغّل Notebook التدريب وضع النتائج الحقيقية في المجلد المطلوب.')}</span></div>}<div className="data-path"><code>backend/LunaShield_OLTARIS_PublicData/results/</code><span>{t('Expected location for the real artifacts','المكان المتوقع لملفات النتائج الفعلية')}</span></div></section>}
      <footer> LUNASHIELD AI <span>•</span> Research prototype / Not a certified radiation protection design</footer>
    </main>
  </div>
}
function Stat({icon,label,value,detail}:any){return <div className="stat"><div className="stat-icon">{icon}</div><div><span>{label}</span><b>{value}</b><small>{detail}</small></div></div>}
