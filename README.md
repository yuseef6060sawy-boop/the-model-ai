# LunaShield AI — Web Platform Starter

واجهة React + TypeScript متصلة بواجهة Python FastAPI. لا تنشئ بيانات تدريب أو مقاييس وهمية.

## 1) المتطلبات
- Python 3.10 أو أحدث
- Node.js 20 أو أحدث
- ملفات النتائج الحقيقية التي ينتجها Notebook الحالي

## 2) ضع نتائج Notebook في المكان الصحيح
انسخ مجلد النتائج الذي ينتجه Notebook إلى:

`backend/LunaShield_OLTARIS_PublicData/results/`

يجب أن يحتوي (حسب ما أنتجه تدريبك فعليًا) على:
- `GCR__dose_equivalent_rate.joblib`
- `SPE__dose_equivalent_rate.joblib`
- `feature_sets.json`
- `training_metrics_leave_one_material_out.csv`
- `OLTARIS_public_training_data_normalized.csv`
- `model_card.json`

ليس مطلوبًا أن توجد كل الملفات لكل بيئة؛ الواجهة ستوضح الملفات المفقودة. لا تنشئ ملفات فارغة لتجاوز الفحص.

## 3) تشغيل Backend
افتح Terminal داخل مجلد `backend`:

Windows PowerShell:
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

واجهة API التوثيقية:
`http://127.0.0.1:8000/docs`

## 4) تشغيل Frontend
افتح Terminal آخر داخل مجلد `frontend`:
```powershell
npm install
npm run dev
```
افتح الرابط الذي يظهر في Terminal، غالبًا `http://localhost:5173`.

## 5) حدود علمية مهمة
- مخرجات تحليل الخلطات موسومة صراحة بأنها تقديرات استكشافية غير متحقق منها.
- نموذج Notebook الأصلي مدرّب على مواد مرجعية منفردة؛ لا يعني ذلك أنه صالح للتنبؤ الموثوق بالخلطات الجديدة.
- الكثافة في بناء خصائص الخلطة تستخدم تقريب جمع الحجوم المثالي.
- لا تعرض قيمة على أنها "نسبة حماية" ما لم يوجد خط أساس غير محمي مطابق، وتحقق مستقل من الوحدات والنتائج.
- لا تستخدم هذه الواجهة لاتخاذ قرارات تصنيع أو تعامل مادي. بعض المواد في القائمة تتطلب تقييم سلامة متخصصًا.
- لا تضع ملفات `.joblib` من مصدر غير موثوق؛ تحميل Joblib/Pickle قد ينفذ تعليمات برمجية.

## 6) قبل العرض في مسابقة
1. احتفظ بنسخة من مصدر البيانات ورابط الدراسة وبصمة SHA-256.
2. تحقق يدويًا من أسماء الأعمدة والوحدات في ملفات OLTARIS الأصلية.
3. اعرض نتائج Leave-One-Material-Out كما هي، ولا تخفِ المواد أو folds التي أخفق فيها النموذج.
4. اختبر توقعات النموذج مقابل نتائج OLTARIS جديدة مستقلة قبل تقديم ادعاء أداء.
5. اذكر بوضوح أن النظام نموذج بحثي أولي وليس درعًا إشعاعيًا معتمدًا.
