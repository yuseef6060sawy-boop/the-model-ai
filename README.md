# LunaShield AI — Public Web App

This is a browser interface around the **original trained OLTARIS models**. The training estimators and training pipeline are not replaced.

## Required real outputs
Run the original training notebook, then copy its complete `LunaShield_OLTARIS_PublicData/results/` folder into this project. It must contain:
- `feature_sets.json`
- `OLTARIS_public_training_data_normalized.csv`
- `GCR__dose_equivalent_rate.joblib` and/or `SPE__dose_equivalent_rate.joblib`
- `training_metrics_leave_one_material_out.csv` and `model_card.json` (recommended)

The app stops rather than showing fake data if core files are missing.

## Local run (Windows PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

## Public Render deployment
1. Add this project and the real results folder to a GitHub repository.
2. Create a Render Blueprint from that repository.
3. Render reads `render.yaml` and gives you a public `https://...onrender.com` URL.

## Scientific limitation
The reference models were trained on individual materials, not custom mixtures. The automatic mixture search is therefore exploratory and unvalidated. Do not present its candidate percentages or dose estimates as proven shielding performance; validate with an independent radiation-transport simulation.
