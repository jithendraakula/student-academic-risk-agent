from __future__ import annotations
from datetime import datetime, timezone
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, balanced_accuracy_score


def evaluate_model(model, x_test, y_test) -> dict:
    p = model.predict_proba(x_test)[:, 1]
    pred = (p >= 0.5).astype(int)
    return {
        "accuracy": round(float(accuracy_score(y_test, pred)), 4),
        "balanced_accuracy": round(float(balanced_accuracy_score(y_test, pred)), 4),
        "precision": round(float(precision_score(y_test, pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_test, pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y_test, pred, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, p)), 4) if y_test.nunique() == 2 else None,
    }


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()
