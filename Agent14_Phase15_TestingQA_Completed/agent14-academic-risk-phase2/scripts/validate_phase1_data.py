from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/'data'/'processed'; ERR=[]
def req(df, cols, name):
    miss=set(cols)-set(df.columns)
    if miss: ERR.append(f'{name} missing {sorted(miss)}')
    if df.empty: ERR.append(f'{name} is empty')
def unique(df,cols,name):
    if not df.empty and df.duplicated(cols).any(): ERR.append(f'{name} has duplicate keys: {cols}')
def load(n):
    p=DATA/n
    if not p.exists(): ERR.append(f'missing {n}'); return pd.DataFrame()
    return pd.read_csv(p)
def main():
    st=load('students.csv'); te=load('teachers.csv'); a=load('assignments.csv'); sem=load('student_semester_features.csv'); co=load('student_course_features.csv'); ho=load('historical_outcomes.csv'); ref=load('academic_reference_data.csv'); al=load('alerts_interventions.csv')
    req(st,['student_id','roll_number','batch','department','section','current_semester'],'students'); req(te,['teacher_id','role','department','email'],'teachers'); req(a,['assignment_id','student_id','teacher_id','semester'],'assignments')
    req(sem,['student_id','cohort','semester','checkpoint_week','snapshot_type','current_gpa','current_attendance_percentage','projected_final_attendance'],'semester')
    req(co,['student_id','cohort','semester','snapshot_type','course_id','course_failed'],'course'); req(ho,['student_id','cohort','semester','checkpoint_week','course_failed','new_backlog','gpa_below_threshold','attendance_shortage','discontinued'],'outcomes'); req(ref,['department_id','semester','course_id','attendance_threshold','gpa_threshold'],'reference')
    if not st.empty:
        unique(st,['student_id'],'students'); unique(st,['roll_number'],'roll numbers')
        if len(st)!=360: ERR.append(f'expected 360 students, got {len(st)}')
        if not st.student_id.str.match(r'^S\d{4}$').all(): ERR.append('invalid student id format')
        if not st.roll_number.astype(str).str.match(r'^\d{8}$').all(): ERR.append('invalid 8-digit roll number format')
    if not te.empty:
        unique(te,['teacher_id'],'teachers'); unique(te,['email'],'teacher emails')
        if set(te.role)!= {'mentor','hod','dean'}: ERR.append('unexpected teacher roles')
        if len(te)!=15: ERR.append(f'expected 15 teachers, got {len(te)}')
    if not a.empty:
        unique(a,['assignment_id'],'assignments'); unique(a,['student_id'],'active mentor assignments')
        if len(a)!=len(st): ERR.append('not exactly one active mentor assignment per student')
        mentors=set(te.loc[te.role.eq('mentor'),'teacher_id'])
        if not set(a.teacher_id).issubset(mentors): ERR.append('non-mentor present in mentor assignments')
    if not sem.empty and not ho.empty:
        unique(sem,['student_id','semester','checkpoint_week'],'semester checkpoints'); unique(ho,['student_id','semester','checkpoint_week'],'historical outcomes')
        hist=sem[sem.snapshot_type.eq('historical')]; cur=sem[sem.snapshot_type.eq('current')]
        if len(cur)!=len(st): ERR.append('current snapshot is not one per student')
        left=set(map(tuple,hist[['student_id','cohort','semester','checkpoint_week']].to_numpy())); right=set(map(tuple,ho[['student_id','cohort','semester','checkpoint_week']].to_numpy()))
        if left!=right: ERR.append('historical snapshots and outcomes are not 1:1 aligned')
        for c,lo,hi in [('current_gpa',0,10),('current_attendance_percentage',0,100),('projected_final_attendance',0,100),('recent_engagement_score',0,1)]:
            if c in sem and not sem[c].between(lo,hi).all(): ERR.append(f'{c} outside range')
        if not co.empty and not co.loc[co.snapshot_type.eq('current'),'course_failed'].isna().all(): ERR.append('current course_failed must be null')
    if not ho.empty:
        unique(ho,['student_id','semester','checkpoint_week'],'outcomes')
        for c in ['course_failed','new_backlog','gpa_below_threshold','attendance_shortage','discontinued']:
            if c in ho:
                r=float(ho[c].mean())
                if not (0.01<=r<=0.95): ERR.append(f'{c} class rate {r:.3f} outside expected range')
        h=sem[sem.snapshot_type.eq('historical')].copy().sort_values(['student_id','semester']); o=ho.sort_values(['student_id','semester'])
        for label,target,feature in [('gpa','gpa_below_threshold','current_gpa'),('att','attendance_shortage','projected_final_attendance'),('backlog','new_backlog','current_backlog_count')]:
            if target in o and feature in h:
                direct=h[feature].lt(7 if label=='gpa' else 75).astype(int) if label!='backlog' else h[feature].gt(0).astype(int)
                if direct.to_numpy().shape==o[target].to_numpy().shape and np.array_equal(direct.to_numpy(),o[target].to_numpy()): ERR.append(f'direct target leakage copy detected for {label}')
    if ERR:
        print('PHASE 1 DATA VALIDATION FAILED'); print('\n'.join('ERROR: '+e for e in ERR)); return 1
    print('PHASE 1 DATA VALIDATION PASSED'); print(f'students={len(st)} teachers={len(te)} assignments={len(a)} semester_snapshots={len(sem)} course_snapshots={len(co)} historical_outcomes={len(ho)} reference_rows={len(ref)} alerts={len(al)}'); print(f'cohorts={sorted(st.batch.unique().tolist())}; current_semesters={sorted(st.current_semester.unique().tolist())}'); print(ho[['course_failed','new_backlog','gpa_below_threshold','attendance_shortage','discontinued']].mean().round(3).to_dict() if not ho.empty else {})
    return 0
if __name__=='__main__': raise SystemExit(main())
