from pathlib import Path
import json
import joblib
import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(page_title="LunaShield AI", page_icon="🛰️", layout="wide")
BASE = Path(__file__).resolve().parent
OUT = BASE / "LunaShield_OLTARIS_PublicData" / "results"

MATERIALS = {
    "Aluminum": ("Al", 2.70),
    "Lithium Hydride (LiH)": ("LiH", 0.82),
    "Polyethylene (PE)": ("C2H4", 0.94),
    "Lithium Borohydride (LiBH4)": ("LiBH4", 0.66),
    "Ammonia Borane (NH3BH3)": ("NH3BH3", 0.78),
    "Beryllium Borohydride (Be(BH4)2)": ("Be(BH4)2", 0.604),
}
ATOMIC = {"H":1.008,"C":12.011,"N":14.007,"O":15.999,"B":10.81,"Li":6.94,"Be":9.0122,"Al":26.9815385}
FORMULAS = {
    "Al":{"Al":1}, "LiH":{"Li":1,"H":1}, "C2H4":{"C":2,"H":4},
    "LiBH4":{"Li":1,"B":1,"H":4}, "NH3BH3":{"N":1,"H":6,"B":1},
    "Be(BH4)2":{"Be":1,"B":2,"H":8}
}
ELEMENTS = ["H","C","N","O","B","Li","Be","Al"]

def fractions(formula):
    masses={e:ATOMIC[e]*n for e,n in FORMULAS[formula].items()}
    total=sum(masses.values())
    return {e:100*v/total for e,v in masses.items()}

def read_json(name):
    p=OUT/name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}

def build_features(weights, names, key, env, depth, data, feature_sets):
    infos=[MATERIALS[n] for n in names]
    density=1.0/sum(float(w)/info[1] for w,info in zip(weights,infos))
    elemental={e:0.0 for e in ELEMENTS}
    for w,info in zip(weights,infos):
        for e,pct in fractions(info[0]).items():
            elemental[e]+=float(w)*pct
    cols=feature_sets[key]
    subset=data[(data.radiation_type==env)&(data.target=="dose_equivalent_rate")]
    row={}
    if "areal_density_g_cm2" in cols: row["areal_density_g_cm2"]=depth
    if "density_g_cm3" in cols: row["density_g_cm3"]=density
    for e in ELEMENTS:
        col=f"{e}_wt_pct"
        if col in cols: row[col]=elemental[e]
    if "solar_modulation_MV" in cols:
        v=pd.to_numeric(subset.solar_modulation_MV,errors="coerce").dropna()
        row["solar_modulation_MV"]=float(v.median()) if len(v) else np.nan
    if "energy_MeV" in cols:
        v=pd.to_numeric(subset.energy_MeV,errors="coerce").dropna()
        row["energy_MeV"]=float(v.median()) if len(v) else np.nan
    if "particle" in cols:
        v=subset.particle.dropna().astype(str).mode()
        row["particle"]=v.iloc[0] if len(v) else "not_resolved"
    return {c:row.get(c,np.nan) for c in cols}

def optimize_mix(model,names,key,env,depth,data,feature_sets):
    # Same exploratory search concept as the original notebook:
    # equal proportions + pure-material boundaries + reproducible Dirichlet samples.
    n=len(names)
    rng=np.random.default_rng(42)
    candidates=[np.full(n,1.0/n)]
    candidates.extend(np.eye(n))
    candidates.extend(rng.dirichlet(np.ones(n)*0.7,size=6000))
    rows=[build_features(w,names,key,env,depth,data,feature_sets) for w in candidates]
    X=pd.DataFrame(rows,columns=feature_sets[key])
    preds=np.asarray(model.predict(X),dtype=float)
    valid=np.isfinite(preds)
    if not valid.any():
        raise RuntimeError("The model did not return any valid predictions.")
    safe=np.where(valid,preds,np.inf)
    idx=int(np.argmin(safe))
    return np.asarray(candidates[idx]),float(preds[idx])

st.markdown("""
<style>
.stApp{background:linear-gradient(135deg,#071426,#102b49);color:#edf5ff}
[data-testid="stSidebar"]{background:#09182a}
.block-container{max-width:1400px;padding-top:2rem}
div[data-testid="stMetric"]{background:#102846;border:1px solid #285078;padding:14px;border-radius:14px}
</style>
""",unsafe_allow_html=True)
st.title("🛰️ LunaShield AI")
st.caption("Public research interface • Original OLTARIS-trained models")

required=["feature_sets.json","OLTARIS_public_training_data_normalized.csv"]
missing=[x for x in required if not (OUT/x).exists()]
if missing:
    st.error("ملفات الموديل/البيانات الأصلية غير موجودة. شغّل Notebook التدريب الأصلي، ثم انسخ مجلد results كاملًا إلى LunaShield_OLTARIS_PublicData/results/. لن يتم عرض بيانات تجريبية.")
    st.write("الملفات الناقصة:",", ".join(missing))
    st.stop()

data=pd.read_csv(OUT/"OLTARIS_public_training_data_normalized.csv")
feature_sets=read_json("feature_sets.json")
metrics_path=OUT/"training_metrics_leave_one_material_out.csv"
metrics=pd.read_csv(metrics_path) if metrics_path.exists() else None
card=read_json("model_card.json")

page=st.sidebar.radio("القسم",["Automatic Mixture Designer","Model Performance","Dataset & Research"])
if page=="Automatic Mixture Designer":
    st.header("Automatic Mixture Designer")
    st.write("حدد عدد المواد والمواد نفسها، وسيبحث الموديل عن نسب كتلية مرشحة تحقق أقل استجابة إشعاعية متوقعة.")
    st.warning("تنبيه علمي مهم: موديلات التدريب الأصلية اتدربت على مواد مرجعية منفردة، وليس على خلطات مخصصة. لذلك نسب الخليط والنتيجة تقديرات استكشافية غير مُثبتة، ولا تمثل نسبة حماية معتمدة أو أداءً مثبتًا.")
    c1,c2=st.columns(2)
    env=c1.selectbox("Radiation environment",["GCR","SPE"])
    depth=c2.number_input("Areal density (g/cm²)",min_value=0.01,value=15.0,step=0.5)
    names=st.multiselect("اختار المواد التي تريد أن يبحث بينها الموديل",list(MATERIALS),default=["Polyethylene (PE)","Aluminum"])
    st.caption("الموديل هو الذي يختار النسب؛ لا تحتاج إلى إدخال نسب بنفسك.")
    if names and st.button("Find optimized proportions",type="primary",use_container_width=True):
        key=f"{env}__dose_equivalent_rate"
        model_path=OUT/f"{key}.joblib"
        if not model_path.exists():
            st.error(f"الموديل المدرّب الخاص بـ {env} غير موجود: {model_path.name}")
        else:
            with st.spinner("Searching candidate compositions with the trained model..."):
                model=joblib.load(model_path)
                try:
                    weights,pred=optimize_mix(model,names,key,env,depth,data,feature_sets)
                    st.subheader("Suggested virtual composition")
                    table=pd.DataFrame({"Material":names,"Optimized mass proportion (%)":weights*100})
                    st.dataframe(table,use_container_width=True,hide_index=True)
                    a,b,c=st.columns(3)
                    a.metric("Predicted response",f"{pred:.6g}")
                    b.metric("Environment",env)
                    c.metric("Areal density",f"{depth:g} g/cm²")
                    subset=data[(data.radiation_type==env)&(data.target=="dose_equivalent_rate")]
                    min_depth=pd.to_numeric(subset.areal_density_g_cm2,errors="coerce").min()
                    reduction=None
                    if pd.notna(min_depth) and min_depth<=0.05:
                        baseline_X=pd.DataFrame([build_features(weights,names,key,env,0.0,data,feature_sets)],columns=feature_sets[key])
                        baseline=float(model.predict(baseline_X)[0])
                        if np.isfinite(baseline) and baseline>0:
                            reduction=(1-pred/baseline)*100
                            st.metric("Exploratory reduction vs. modeled zero-depth baseline",f"{reduction:.2f}%")
                        else:
                            st.info("تعذر حساب نسبة التخفيض لأن قيمة baseline غير صالحة.")
                    else:
                        st.info("نسبة التخفيض غير متاحة: بيانات التدريب لا تحتوي baseline قريبًا من صفر g/cm².")
                    st.caption("النتيجة هي أفضل مرشح داخل البحث العددي الحالي فقط، وليست ضمانًا بأن الخليط الحقيقي سيحقق هذه النتيجة. يلزم اختبار مستقل بمحاكاة نقل إشعاعي مناسبة.")
                    result=table.copy()
                    result["environment"]=env
                    result["areal_density_g_cm2"]=depth
                    result["predicted_response"]=pred
                    result["estimated_reduction_percent"]=reduction
                    result["validation_status"]="exploratory_unvalidated_mixture_estimate"
                    st.download_button("Download research result (CSV)",result.to_csv(index=False).encode(),"lunashield_optimized_candidate.csv","text/csv")
                except Exception as exc:
                    st.error(f"Optimization could not be completed: {exc}")
    elif not names:
        st.info("اختار مادة واحدة على الأقل.")

elif page=="Model Performance":
    st.header("Model Performance — Leave-One-Material-Out")
    if metrics is not None: st.dataframe(metrics,use_container_width=True,hide_index=True)
    else: st.info("ملف metrics غير موجود.")

else:
    st.header("Dataset & Research")
    a,b,c=st.columns(3)
    a.metric("Normalized records",f"{len(data):,}")
    b.metric("Reference materials",str(data.material.nunique()))
    c.metric("Radiation environments",str(data.radiation_type.nunique()))
    audit=data.groupby(["radiation_type","target","material"]).agg(records=("value","size"),min_depth=("areal_density_g_cm2","min"),max_depth=("areal_density_g_cm2","max")).reset_index()
    st.dataframe(audit,use_container_width=True,hide_index=True)
    if card: st.json(card)
    st.info("البيانات هي مخرجات محاكاة OLTARIS منشورة وليست قياسات معملية. لا تشمل طينًا مصريًا أو lunar regolith simulant أو طوبة مركبة أو هندسة متعددة الطبقات مخصصة.")
