# Phase 4 ML Foundation

Run from the project root using the backend virtual environment. Training and serving must use the same Python environment because joblib artifacts contain scikit-learn preprocessing objects.

```powershell
backend\venv\Scripts\python.exe -m ml.train_all
backend\venv\Scripts\python.exe -m ml.smoke_test
```

The pipeline loads the Phase 3 CSVs from `data/processed`, validates required inputs, derives five binary targets, trains reproducible `RandomForestClassifier` baselines, and saves complete preprocessing-plus-model pipelines in `ml/models/`. Metrics and training metadata are written to `ml/metrics/`.

Targets use only checkpoint-available signals. Course failure uses the generated `course_failed` label. Backlog uses whether the current backlog count is positive, GPA risk uses the configured 7.0 threshold, and attendance risk uses projected final attendance below 75%. Historical discontinuation contains no positive active-student labels, so discontinuation uses a clearly labeled support-only synthetic warning proxy built from absence, fee, engagement, and repeated-backlog signals; those source columns are excluded from its features.

Feature importance is global Random Forest importance, surfaced as a lightweight explanation. It is not a causal or fully local explanation of an individual prediction. Discontinuation output is support-only and must never be used for admission, scholarship, placement, or punitive decisions.
