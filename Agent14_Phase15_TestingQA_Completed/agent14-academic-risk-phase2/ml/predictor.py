from __future__ import annotations
from functools import lru_cache
import joblib
import numpy as np
import pandas as pd
from .config import MODEL_DIR, MODEL_NAMES, confidence_level, risk_level
from .feature_sets import feature_label

@lru_cache(maxsize=10)
def _load(model_key):
    artifact=joblib.load(MODEL_DIR/MODEL_NAMES[model_key])
    if isinstance(artifact,dict) and "pipeline" in artifact:
        return artifact["pipeline"], float(artifact.get("decision_threshold",0.5)), artifact.get("metadata",{})
    return artifact, 0.5, {}

def _source_feature(transformed: str) -> str:
    raw=transformed.split("__",1)[-1]
    # OneHotEncoder output is usually <source>_<category>. Recover the source
    # using known feature names rather than treating the category as a feature.
    return raw

def _top_factors(pipeline, row, top_n=3):
    pre=pipeline.named_steps["preprocessor"]
    model=pipeline.named_steps["model"]
    transformed=list(pre.get_feature_names_out())
    importances=getattr(model,"feature_importances_",np.zeros(len(transformed)))
    source_features=list(getattr(pre,"feature_names_in_",[]))
    grouped={}
    for feature,importance in zip(transformed,importances):
        raw=feature.split("__",1)[-1]
        source=next((c for c in sorted(source_features,key=len,reverse=True) if raw==c or raw.startswith(c+"_")),raw)
        grouped[source]=grouped.get(source,0.0)+float(importance)
    ranked=sorted(grouped.items(),key=lambda x:x[1],reverse=True)[:top_n]
    return [{"feature":feature_label(k),"raw_feature":k,"value":row.get(k),"importance":round(v,4)} for k,v in ranked]

def _predict(model_key,row):
    pipeline,threshold,meta=_load(model_key)
    p=float(pipeline.predict_proba(pd.DataFrame([row]))[:,1][0])
    return {"risk_probability":round(p,4),"risk_score":round(p*100,1),"risk_level":risk_level(p),"confidence":confidence_level(p),"decision_threshold":threshold,"top_factors":_top_factors(pipeline,row),"model_version":meta.get("trained_at", "unknown"),"model_key":meta.get("model_key", model_key)}


def _predict_batch(model_key: str, frame: pd.DataFrame) -> list[dict]:
    pipeline, threshold, meta = _load(model_key)
    probabilities = pipeline.predict_proba(frame)[:, 1]
    return [
        {
            "risk_probability": round(float(p), 4),
            "risk_score": round(float(p) * 100, 1),
            "risk_level": risk_level(float(p)),
            "confidence": confidence_level(float(p)),
            "decision_threshold": threshold,
            "top_factors": [],
            "model_version": meta.get("trained_at", "unknown"),
            "model_key": meta.get("model_key", model_key),
        }
        for p in probabilities
    ]


def predict_student_batch(rows: list[dict], model_keys=("backlog", "gpa_threshold", "attendance_shortage", "discontinuation")) -> dict[str, list[dict]]:
    frame = pd.DataFrame(rows)
    return {key: _predict_batch(key, frame) for key in model_keys}


def predict_course_batch(student_rows: list[dict], course_rows: list[dict]) -> list[dict]:
    if not course_rows:
        return []
    merged = []
    for student, course in zip(student_rows, course_rows):
        merged.append({**student, **course})
    return _predict_batch("course_failure", pd.DataFrame(merged))


def predict_all_risks(student_data,course_records=None):
    result={"student_id":student_data.get("student_id"),"risks":{}}
    result["risks"]["course_failure"]=[]
    for course in course_records or []:
        result["risks"]["course_failure"].append({"course_id":course.get("course_id"),"course_name":course.get("course_name"),**_predict("course_failure",{**student_data,**course})})
    for key in ("backlog","gpa_threshold","attendance_shortage","discontinuation"):
        result["risks"][key]=_predict(key,student_data)
    return result
