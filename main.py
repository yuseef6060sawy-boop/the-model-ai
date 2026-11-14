from pathlib import Path
import json
import math
import re
import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

APP_DIR = Path(__file__).resolve().parent
PROJECT_DIR = APP_DIR.parent.parent
RESULTS_DIR = PROJECT_DIR / "LunaShield_OLTARIS_PublicData" / "results"

app = FastAPI(
    title="LunaShield Research API",
    version="1.0.0",
    description="Research interface for published OLTARIS-derived data and explicitly labeled surrogate predictions."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

ATOMIC_MASS = {
    "H": 1.008, "C": 12.011, "N": 14.007, "O": 15.999,
    "B": 10.81, "Li": 6.94, "Be": 9.0122, "Al": 26.9815385
}
FORMULAS = {
    "Al": {"Al": 1},
    "LiH": {"Li": 1, "H": 1},
    "C2H4": {"C": 2, "H": 4},
    "LiBH4": {"Li": 1, "B": 1, "H": 4},
    "NH3BH3": {"N": 1, "H": 6, "B": 1},
    "Be(BH4)2": {"Be": 1, "B": 2, "H": 8},
}
MATERIALS = {
    "Al": {"name": "Aluminum", "density": 2.70, "formula": "Al"},
    "LiH": {"name": "Lithium Hydride", "density": 0.82, "formula": "LiH"},
    "C2H4": {"name": "Polyethylene (PE)", "density": 0.94, "formula": "C2H4"},
    "LiBH4": {"name": "Lithium Borohydride", "density": 0.66, "formula": "LiBH4"},
    "NH3BH3": {"name": "Ammonia Borane", "density": 0.78, "formula": "NH3BH3"},
    "Be(BH4)2": {"name": "Beryllium Borohydride", "density": 0.604, "formula": "Be(BH4)2"},
}
ELEMENTS = ["H", "C", "N", "O", "B", "Li", "Be", "Al"]

def mass_fractions(formula: str) -> dict:
    counts = FORMULAS[formula]
    masses = {el: ATOMIC_MASS[el] * count for el, count in counts.items()}
    total = sum(masses.values())
    return {el: 100.0 * mass / total for el, mass in masses.items()}

def load_json(path: Path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))

def available_files():
    return {
        "metrics": RESULTS_DIR / "training_metrics_leave_one_material_out.csv",
        "features": RESULTS_DIR / "feature_sets.json",
        "model_card": RESULTS_DIR / "model_card.json",
        "data": RESULTS_DIR / "OLTARIS_public_training_data_normalized.csv",
    }

def get_artifacts(environment: str):
    key = f"{environment}__dose_equivalent_rate"
    model_path = RESULTS_DIR / f"{key}.joblib"
    feature_sets = load_json(available_files()["features"])
    data_path = available_files()["data"]
    if not model_path.exists() or feature_sets is None or not data_path.exists():
        raise HTTPException(
            status_code=503,
            detail="النموذج أو ملفاته غير موجودة. شغّل Notebook التدريب أولًا وانسخ مجلد results كما هو."
        )
    try:
        model = joblib.load(model_path)
        data = pd.read_csv(data_path)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"تعذر تحميل ملفات البحث: {exc}")
    if key not in feature_sets:
        raise HTTPException(status_code=404, detail=f"لا يوجد نموذج محفوظ للبيئة {environment}.")
    return key, model, feature_sets[key], data

class Component(BaseModel):
    material: str
    percentage: float = Field(ge=0, le=100)

class AnalyzeRequest(BaseModel):
    environment: str
    areal_density_g_cm2: float = Field(gt=0, le=100)
    components: list[Component] = Field(min_length=1, max_length=6)

    @field_validator("environment")
    @classmethod
    def valid_environment(cls, value):
        value = value.upper()
        if value not in {"GCR", "SPE"}:
            raise ValueError("environment must be GCR or SPE")
        return value

    @field_validator("components")
    @classmethod
    def valid_components(cls, values):
        names = [v.material for v in values]
        if len(names) != len(set(names)):
            raise ValueError("لا يمكن تكرار المادة نفسها.")
        unknown = [n for n in names if n not in MATERIALS]
        if unknown:
            raise ValueError(f"مواد غير مدعومة: {unknown}")
        total = sum(v.percentage for v in values)
        if not math.isclose(total, 100.0, abs_tol=0.05):
            raise ValueError(f"مجموع النسب يجب أن يساوي 100%. المجموع الحالي: {total:.2f}%")
        return values

@app.get("/api/health")
def health():
    f = available_files()
    return {
        "status": "online",
        "results_directory_exists": RESULTS_DIR.exists(),
        "required_files": {name: path.exists() for name, path in f.items()},
        "models": {
            env: (RESULTS_DIR / f"{env}__dose_equivalent_rate.joblib").exists()
            for env in ("GCR", "SPE")
        }
    }

@app.get("/api/materials")
def materials():
    return [
        {
            "id": formula,
            "name": info["name"],
            "formula": formula,
            "reference_density_g_cm3": info["density"],
            "elemental_mass_percent": mass_fractions(formula),
            "data_note": "مرجع تركيبي من تعريفات Notebook؛ ليس إثباتًا لأداء درع أو توصية تصنيع."
        }
        for formula, info in MATERIALS.items()
    ]

@app.get("/api/metrics")
def metrics():
    path = available_files()["metrics"]
    if not path.exists():
        return {"available": False, "message": "ملف المقاييس غير موجود. لم يتم إنشاء أرقام بديلة."}
    try:
        df = pd.read_csv(path)
        return {"available": True, "records": df.replace({np.nan: None}).to_dict(orient="records")}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"تعذر قراءة المقاييس: {exc}")

@app.get("/api/model-card")
def model_card():
    card = load_json(available_files()["model_card"])
    if card is None:
        return {"available": False, "message": "Model Card غير موجود؛ شغّل Notebook التدريب أولًا."}
    return {"available": True, "card": card}

@app.post("/api/mixture/analyze")
def analyze_mixture(request: AnalyzeRequest):
    key, model, feature_cols, data = get_artifacts(request.environment)
    subset = data[
        (data["radiation_type"] == request.environment) &
        (data["target"] == "dose_equivalent_rate")
    ].copy()
    if subset.empty:
        raise HTTPException(status_code=422, detail="لا توجد سجلات تدريب مطابقة لهذه البيئة والاستجابة.")

    weights = np.array([c.percentage / 100.0 for c in request.components], dtype=float)
    selected = [MATERIALS[c.material] for c in request.components]

    # Ideal volume-additivity approximation: an explicit modeling assumption.
    density = 1.0 / sum(float(w) / float(item["density"]) for w, item in zip(weights, selected))
    elemental = {el: 0.0 for el in ELEMENTS}
    for w, component in zip(weights, request.components):
        for element, pct in mass_fractions(component.material).items():
            elemental[element] += float(w) * float(pct)

    row = {}
    if "areal_density_g_cm2" in feature_cols:
        row["areal_density_g_cm2"] = request.areal_density_g_cm2
    if "density_g_cm3" in feature_cols:
        row["density_g_cm3"] = density
    for element, pct in elemental.items():
        col = f"{element}_wt_pct"
        if col in feature_cols:
            row[col] = pct
    if "solar_modulation_MV" in feature_cols:
        vals = pd.to_numeric(subset.get("solar_modulation_MV"), errors="coerce").dropna()
        row["solar_modulation_MV"] = float(vals.median()) if not vals.empty else np.nan
    if "energy_MeV" in feature_cols:
        vals = pd.to_numeric(subset.get("energy_MeV"), errors="coerce").dropna()
        row["energy_MeV"] = float(vals.median()) if not vals.empty else np.nan
    if "particle" in feature_cols:
        modes = subset["particle"].dropna().astype(str).mode()
        row["particle"] = modes.iloc[0] if not modes.empty else "not_resolved"

    X = pd.DataFrame([{col: row.get(col, np.nan) for col in feature_cols}])
    try:
        prediction = float(model.predict(X)[0])
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"فشل التنبؤ: {exc}")

    return {
        "status": "exploratory_unvalidated_mixture_estimate",
        "model_key": key,
        "predicted_response": prediction,
        "unit": "نفس وحدة عمود الاستجابة الأصلي في OLTARIS؛ راجع مصدر البيانات قبل عرضها",
        "environment": request.environment,
        "areal_density_g_cm2": request.areal_density_g_cm2,
        "estimated_mixture_density_g_cm3": density,
        "components": [c.model_dump() for c in request.components],
        "limitations": [
            "النموذج دُرّب على مواد مرجعية منفردة، وليس على هذه الخلطة المخصصة.",
            "النتيجة توقع استكشافي غير متحقق تجريبيًا أو بمحاكاة OLTARIS مستقلة.",
            "الكثافة تستخدم تقريب جمع الحجوم المثالي ولا تمثل المسامية أو التفاعلات.",
            "لا تستخدم النتيجة كادعاء حماية مثبت أو كتعليمات تصنيع/تعامل مع المواد."
        ]
    }
