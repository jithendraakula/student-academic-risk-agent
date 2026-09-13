from __future__ import annotations
import json
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, balanced_accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from .config import METRICS_DIR, MODEL_DIR, MODEL_NAMES, SEED, HOLDOUT_COHORT, LABELS
from .evaluate import timestamp
from .feature_sets import select_features
from .preprocessing import make_preprocessor

def _best_f1_threshold(probabilities, y_true) -> float:
    candidates=np.linspace(0.10,0.90,81); y=np.asarray(y_true,dtype=int); best=(0.5,-1.0)
    for t in candidates:
        pred=(probabilities>=t).astype(int); tp=((pred==1)&(y==1)).sum(); fp=((pred==1)&(y==0)).sum(); fn=((pred==0)&(y==1)).sum(); pr=tp/max(1,tp+fp); re=tp/max(1,tp+fn); f1=2*pr*re/max(1e-12,pr+re)
        if f1>best[1]: best=(float(t),float(f1))
    return best[0]

def train_one(name, frame, target_column, train_frame, test_frame):
    features=select_features(frame,name); x_train=train_frame[features].copy(); x_test=test_frame[features].copy(); y_train=train_frame[target_column].astype(int); y_test=test_frame[target_column].astype(int)
    if y_train.nunique()<2 or y_test.nunique()<2: raise ValueError(f'{name}: train/test must both contain two classes')
    internal_x, val_x, internal_y, val_y=train_test_split(x_train,y_train,test_size=.20,stratify=y_train,random_state=SEED)
    pre_val=make_preprocessor(internal_x,features); est_val=RandomForestClassifier(n_estimators=120,max_depth=7,min_samples_leaf=3,class_weight='balanced_subsample',random_state=SEED,n_jobs=-1); val_pipe=Pipeline([('preprocessor',pre_val),('model',est_val)]); val_pipe.fit(internal_x,internal_y); threshold=_best_f1_threshold(val_pipe.predict_proba(val_x)[:,1],val_y)
    pre=make_preprocessor(x_train,features); est=RandomForestClassifier(n_estimators=120,max_depth=7,min_samples_leaf=3,class_weight='balanced_subsample',random_state=SEED,n_jobs=-1); pipeline=Pipeline([('preprocessor',pre),('model',est)]); pipeline.fit(x_train,y_train)
    prob=pipeline.predict_proba(x_test)[:,1]; pred=(prob>=threshold).astype(int); metrics={'accuracy':round(float(accuracy_score(y_test,pred)),4),'balanced_accuracy':round(float(balanced_accuracy_score(y_test,pred)),4),'precision':round(float(precision_score(y_test,pred,zero_division=0)),4),'recall':round(float(recall_score(y_test,pred,zero_division=0)),4),'f1':round(float(f1_score(y_test,pred,zero_division=0)),4),'roc_auc':round(float(roc_auc_score(y_test,prob)),4)}
    transformed=pipeline.named_steps['preprocessor'].get_feature_names_out().tolist(); imps=pipeline.named_steps['model'].feature_importances_
    meta={'model_key':name,'model':'RandomForestClassifier','target':LABELS[name],'target_column':target_column,'train_cohorts':[int(x) for x in sorted(train_frame.cohort.unique())],'held_out_cohort':int(HOLDOUT_COHORT),'train_samples':int(len(x_train)),'test_samples':int(len(x_test)),'positive_train':int(y_train.sum()),'negative_train':int((y_train==0).sum()),'positive_test':int(y_test.sum()),'negative_test':int((y_test==0).sum()),'feature_columns':features,'transformed_feature_count':len(transformed),'decision_threshold':threshold,'threshold_selection':'20% training-only validation split optimized for F1','top_global_features':[{'feature':f,'importance':round(float(i),6)} for f,i in sorted(zip(transformed,imps),key=lambda z:z[1],reverse=True)[:10]],'trained_at':timestamp(),**metrics}
    MODEL_DIR.mkdir(exist_ok=True); METRICS_DIR.mkdir(exist_ok=True); joblib.dump({'pipeline':pipeline,'decision_threshold':threshold,'metadata':meta},MODEL_DIR/MODEL_NAMES[name]); (METRICS_DIR/f'{name}_metrics.json').write_text(json.dumps(meta,indent=2),encoding='utf-8'); return meta
