"""Generate Agent 14 synthetic Phase-1 data with a strict prediction-time boundary.

Checkpoint features (week 6) are generated first. Historical end-of-semester outcomes are
then generated from noisy latent/future processes. Current rows intentionally have no outcomes.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import math
import numpy as np
import pandas as pd
from faker import Faker

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "processed"
SEED = 42
RNG = np.random.default_rng(SEED)
fake = Faker("en_IN"); Faker.seed(SEED)

DEPTS = [("DEPT_CSE", "CSE", "Computer Science and Engineering"), ("DEPT_ECE", "ECE", "Electronics and Communication Engineering")]
COHORTS = [(2023,7),(2024,5),(2025,3)]
SECTIONS=["A","B"]
MENTORS_PER_DEPT=6
N_PER_SECTION=30
CHECKPOINT_WEEK=6
ATTENDANCE_THRESHOLD=75.0
GPA_THRESHOLD=7.0

COURSES = {
"DEPT_CSE": {
1:[("CSE101","Programming Fundamentals",4),("CSE102","Engineering Mathematics I",4),("CSE103","Engineering Physics",3),("CSE104","Engineering Drawing",3),("CSE105","Communication Skills",3)],
2:[("CSE201","Data Structures",4),("CSE202","Engineering Mathematics II",4),("CSE203","Digital Logic Design",3),("CSE204","Object Oriented Programming",3),("CSE205","Environmental Science",3)],
3:[("CSE301","Database Systems",4),("CSE302","Computer Organization",4),("CSE303","Discrete Mathematics",3),("CSE304","Operating Systems Fundamentals",3),("CSE305","Web Technologies",3)],
4:[("CSE401","Design and Analysis of Algorithms",4),("CSE402","Computer Networks",4),("CSE403","Theory of Computation",3),("CSE404","Software Engineering",3),("CSE405","Probability and Statistics",3)],
5:[("CSE501","Operating Systems",4),("CSE502","Database Management Systems",4),("CSE503","Design and Analysis of Algorithms",3),("CSE504","Computer Networks",3),("CSE505","Software Engineering",3)],
6:[("CSE601","Artificial Intelligence",4),("CSE602","Machine Learning",4),("CSE603","Cloud Computing",3),("CSE604","Compiler Design",3),("CSE605","Information Security",3)],
7:[("CSE701","Distributed Systems",4),("CSE702","Big Data Analytics",4),("CSE703","Advanced Algorithms",3),("CSE704","Project Work I",3),("CSE705","Professional Elective",3)]},
"DEPT_ECE": {
1:[("ECE101","Engineering Mathematics I",4),("ECE102","Engineering Physics",3),("ECE103","Basic Electrical Engineering",3),("ECE104","Engineering Drawing",3),("ECE105","Communication Skills",3)],
2:[("ECE201","Electronic Devices",4),("ECE202","Engineering Mathematics II",4),("ECE203","Digital Logic Design",3),("ECE204","Circuit Theory",3),("ECE205","Programming for Engineers",3)],
3:[("ECE301","Signals and Systems",4),("ECE302","Analog Electronics",4),("ECE303","Network Theory",3),("ECE304","Electromagnetic Theory",3),("ECE305","Data Structures",3)],
4:[("ECE401","Digital Communication",4),("ECE402","Microprocessors",4),("ECE403","Control Systems",3),("ECE404","Probability and Statistics",3),("ECE405","Embedded Systems",3)],
5:[("ECE501","Digital Signal Processing",4),("ECE502","VLSI Design",4),("ECE503","Microprocessors",3),("ECE504","Control Systems",3),("ECE505","Communication Systems",3)],
6:[("ECE601","Computer Architecture",4),("ECE602","Wireless Communication",4),("ECE603","IoT Systems",3),("ECE604","Digital System Design",3),("ECE605","Embedded C Programming",3)],
7:[("ECE701","Advanced Communication Systems",4),("ECE702","Advanced VLSI",4),("ECE703","Image and Signal Processing",3),("ECE704","Project Work I",3),("ECE705","Professional Elective",3)]}}

def clip(x,lo,hi): return float(np.clip(x,lo,hi))
def sig(x): return 1/(1+math.exp(-max(-30,min(30,x))))

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    # master teachers
    teachers=[]
    for dept_id,code,_ in DEPTS:
        for i in range(MENTORS_PER_DEPT):
            tid=f"T{len(teachers)+1:03d}"
            teachers.append({"teacher_id":tid,"teacher_name":fake.name(),"role":"mentor","department":dept_id,"email":f"mentor{i+1}.{code.lower()}@vignan.ac.in"})
    teachers += [
        {"teacher_id":"H001","teacher_name":"HOD CSE","role":"hod","department":"DEPT_CSE","email":"hod.cse@vignan.ac.in"},
        {"teacher_id":"H002","teacher_name":"HOD ECE","role":"hod","department":"DEPT_ECE","email":"hod.ece@vignan.ac.in"},
        {"teacher_id":"D001","teacher_name":"Dean","role":"dean","department":"","email":"dean@vignan.ac.in"},
    ]
    teachers_df=pd.DataFrame(teachers)

    students=[]; assignments=[]; student_profiles={}; student_counter=1
    for batch,current_sem in COHORTS:
        for dept_id,code,_ in DEPTS:
            mentors=teachers_df[(teachers_df.role=="mentor")&(teachers_df.department==dept_id)].teacher_id.tolist()
            for section in SECTIONS:
                for j in range(N_PER_SECTION):
                    sid=f"S{student_counter:04d}"
                    seq=(student_counter-1)%10000+1
                    roll=f"{str(batch)[-2:]}{1 if code=='CSE' else 2}{seq:05d}"
                    # Fixed archetypes every mentor cohort: enough demo cases, but not all data are risk cases.
                    mentor_index=(j//5)%MENTORS_PER_DEPT
                    archetype=["critical","attendance","support","academic","normal","normal"][mentor_index%6]
                    ability=clip(RNG.normal(7.5,0.75),4.2,9.5)
                    attendance=clip(RNG.normal(84,6.5)+( -14 if archetype=="critical" else -18 if archetype=="attendance" else 3),45,98)
                    engagement=clip(RNG.normal(0.72,0.10)+(-0.22 if archetype in ("support","critical") else -0.1 if archetype=="academic" else 0),0.15,0.98)
                    fee_pressure=clip(RNG.beta(1.4,7)+(.35 if archetype=="support" else .08 if archetype=="critical" else 0),0,0.95)
                    trend=(-0.32 if archetype=="critical" else -0.12 if archetype in ("attendance","academic") else 0.0)
                    profile={"ability":ability,"attendance":attendance,"engagement":engagement,"fee_pressure":fee_pressure,"trend":trend,"archetype":archetype}
                    student_profiles[sid]=profile
                    students.append({"student_id":sid,"roll_number":roll,"student_name":fake.name(),"department":dept_id,"program":"B.Tech","batch":batch,"section":section,"academic_year":"2026-27","current_semester":current_sem})
                    assignments.append({"assignment_id":f"ASG{student_counter:04d}","student_id":sid,"teacher_id":mentors[mentor_index],"academic_year":"2026-27","semester":current_sem,"assignment_type":"mentor"})
                    student_counter+=1
    students_df=pd.DataFrame(students); assignments_df=pd.DataFrame(assignments)

    # longitudinal semester snapshots
    sem_rows=[]; semester_state={}
    for s in students:
        sid=s["student_id"]; p=student_profiles[sid]; current=int(s["current_semester"])
        prev_backlog=0
        for sem in range(1,current+1):
            cur=(sem==current); damp=1 if cur else 0.8
            gpa=clip(p["ability"]+p["trend"]*damp+RNG.normal(0,0.22),3.6,9.7)
            prev_gpa=clip(gpa-RNG.normal(p["trend"],0.35),3.3,9.7)
            attendance=clip(p["attendance"]+p["trend"]*4*damp+RNG.normal(0,3),40,99)
            att30=clip(attendance+RNG.normal(-1.5 if p["trend"]<0 else 0.5,2.6),35,99)
            engage=clip(p["engagement"]+p["trend"]*0.08+RNG.normal(0,0.03),0.05,0.99)
            current_backlog=max(0,prev_backlog+int(RNG.poisson(max(0.05,0.12+(7.0-gpa)*0.18)))-int(RNG.binomial(prev_backlog,0.20)))
            internal=clip(gpa*8.0+RNG.normal(0,5.5),15,95)
            mid=clip(internal+RNG.normal(0,5.5),10,95); quiz=clip(internal+RNG.normal(0,6),10,98)
            assign=clip(internal+8*engage+RNG.normal(0,5),10,100); practical=clip(internal+RNG.normal(2,6),10,100)
            pfa=clip(0.72*attendance+0.28*att30+p["trend"]*3+RNG.normal(0,1.4),35,99)
            consec=int(RNG.integers(5,12)) if att30<62 else int(RNG.integers(0,4))
            absent=int(clip((100-attendance)*0.55+RNG.normal(2,2),0,45))
            prolonged=bool(att30<58 or (attendance<68 and p["fee_pressure"]>0.55))
            fee="overdue" if RNG.random() < (0.04+0.35*p["fee_pressure"]) else "pending" if RNG.random()<0.05 else "paid"
            fee_amt=int(RNG.integers(5000,45000)) if fee=="overdue" else int(RNG.integers(500,4000)) if fee=="pending" else 0
            pay_delay=int(RNG.integers(8,70)) if fee=="overdue" else 0
            gpa_change=gpa-prev_gpa
            row={"student_id":sid,"roll_number":s["roll_number"],"cohort":s["batch"],"academic_year":"2026-27" if cur else f"{2020+sem}-{str(2021+sem)[-2:]}","semester":sem,"checkpoint_week":CHECKPOINT_WEEK,"department":s["department"],"batch":s["batch"],"section":s["section"],"snapshot_type":"current" if cur else "historical","current_gpa":round(gpa,2),"current_cgpa":round(clip((gpa+prev_gpa)/2+RNG.normal(0,.12),3,10),2),"previous_gpa":round(prev_gpa,2),"previous_cgpa":round(prev_gpa+RNG.normal(0,.18),2),"gpa_change":round(gpa-prev_gpa,2),"internal_marks_average":round(internal,1),"midterm_marks_average":round(mid,1),"quiz_average":round(quiz,1),"assignment_average":round(assign,1),"practical_marks_average":round(practical,1),"assessment_trend":"declining" if gpa_change<-0.25 else "improving" if gpa_change>0.25 else "stable","assignment_completion_rate":round(clip(engage+RNG.normal(0,.04),0,1),2),"current_attendance_percentage":round(attendance,1),"attendance_last_30_days":round(att30,1),"attendance_trend":"declining" if att30<attendance-1 else "improving" if att30>attendance+1 else "stable","consecutive_absence_days":consec,"total_absent_days":absent,"recent_absence_rate":round((100-att30)/100,2),"projected_final_attendance":round(pfa,1),"current_backlog_count":current_backlog,"previous_backlog_count":prev_backlog,"total_historical_backlogs":max(current_backlog,prev_backlog)+int(RNG.integers(0,3)),"new_backlogs_last_semester":int(RNG.poisson(max(.1,.18+(7.2-gpa)*.15))),"repeated_backlog_subject_count":1 if current_backlog>0 and prev_backlog>0 else 0,"backlog_growth_rate":round((current_backlog-prev_backlog)/max(1,prev_backlog+1),2),"assessment_participation_rate":round(clip(engage+RNG.normal(0,.04),0,1),2),"recent_engagement_score":round(engage,2),"engagement_trend":"declining" if p["trend"]<-.18 or engage<.45 else "improving" if p["trend"]>.15 and engage>.65 else "stable","fee_status":fee,"fee_arrears_amount":fee_amt,"payment_delay_days":pay_delay,"installment_pending":fee!="paid","prolonged_absence_flag":prolonged,"prolonged_absence_days":consec if prolonged else 0,"academic_decline_flag":bool(gpa_change<-.25 or internal<45),"repeated_backlog_flag":bool(current_backlog>0 and prev_backlog>0),"engagement_decline_flag":bool(engage<.45)}
            sem_rows.append(row); semester_state[(sid,sem)]=row; prev_backlog=current_backlog
    semester_df=pd.DataFrame(sem_rows)

    # course snapshots: historical rows get end-of-semester course failure outcomes; current rows are unlabeled.
    course_rows=[]
    for _,r in semester_df.iterrows():
        for cid,cname,credits in COURSES[r["department"]][int(r["semester"])]:
            difficulty=RNG.normal(0,2.8)
            internal=clip(r["internal_marks_average"]+difficulty+RNG.normal(0,5.0),5,98)
            mid=clip(internal+RNG.normal(0,6),5,98); quiz=clip(internal+RNG.normal(0,6.5),5,98)
            ass=clip(r["assignment_average"]+difficulty+RNG.normal(0,5),5,100); practical=clip(r["practical_marks_average"]+RNG.normal(0,5),5,100)
            catt=clip(r["current_attendance_percentage"]+RNG.normal(0,3.5),35,100)
            prior=int(RNG.choice([0,0,0,1],p=[.84,.08,.05,.03]))
            fail_p=sig(-1.25 + 0.085*(45-internal)+0.070*(70-catt)+0.80*prior+0.30*max(0,6.5-r["current_gpa"])+RNG.normal(0,.18))
            failed=bool(RNG.random()<fail_p) if r["snapshot_type"]=="historical" else None
            course_rows.append({"student_id":r["student_id"],"roll_number":r["roll_number"],"cohort":r["cohort"],"academic_year":r["academic_year"],"semester":int(r["semester"]),"checkpoint_week":CHECKPOINT_WEEK,"snapshot_type":r["snapshot_type"],"course_id":cid,"course_name":cname,"course_credits":credits,"internal_marks":round(internal,1),"midterm_marks":round(mid,1),"quiz_average":round(quiz,1),"assignment_average":round(ass,1),"practical_marks":round(practical,1),"course_attendance_percentage":round(catt,1),"course_attendance_trend":"declining" if catt<r["current_attendance_percentage"]-1 else "improving" if catt>r["current_attendance_percentage"]+1 else "stable","previous_course_attempts":prior,"previous_course_grade":None if prior==0 else str(RNG.choice(["D","F"])),"assessment_trend":r["assessment_trend"],"assignment_completion_rate":r["assignment_completion_rate"],"course_failed":failed})
    course_df=pd.DataFrame(course_rows)

    # historical outcomes: derive future outcomes with noise; course_failed is the aggregate of future course outcomes.
    hist=semester_df[semester_df.snapshot_type=="historical"].copy()
    fail_by=course_df[course_df.snapshot_type=="historical"].groupby(["student_id","semester"])["course_failed"].max()
    rows=[]
    for _,r in hist.iterrows():
        fail=bool(fail_by[(r.student_id,int(r.semester))])
        future_gpa=clip(r.current_gpa + 0.10*r.gpa_change + RNG.normal(0,.50) - 0.25*fail, 3,10)
        future_att=clip(0.62*r.current_attendance_percentage+0.38*r.attendance_last_30_days + RNG.normal(-1.0,3.0),35,100)
        gpa_low=bool(future_gpa<GPA_THRESHOLD)
        attendance_short=bool(future_att<ATTENDANCE_THRESHOLD)
        new_backlog=bool(RNG.random()<sig(-2.0+0.75*fail+0.55*r.current_backlog_count+0.6*int(r.academic_decline_flag)+RNG.normal(0,.5)))
        disc=bool(RNG.random()<sig(-2.95+2.05*int(r.prolonged_absence_flag)+1.70*int(r.engagement_decline_flag)+0.95*int(r.current_backlog_count>=2)+0.65*int(r.fee_status=="overdue")+0.55*int(r.current_attendance_percentage<70)+0.75*int(fail)+RNG.normal(0,.22)))
        rows.append({"student_id":r.student_id,"cohort":int(r.cohort),"academic_year":r.academic_year,"semester":int(r.semester),"checkpoint_week":CHECKPOINT_WEEK,"outcome_horizon":"end_of_semester","course_failed":fail,"new_backlog":new_backlog,"gpa_below_threshold":gpa_low,"attendance_shortage":attendance_short,"discontinued":disc})
    outcomes_df=pd.DataFrame(rows)

    # reference data
    ref=[]
    for did,_,dname in DEPTS:
        for sem,courses in COURSES[did].items():
            for cid,cname,credits in courses:
                ref.append({"department_id":did,"department_name":dname,"course_id":cid,"course_name":cname,"semester":sem,"course_credits":credits,"passing_marks":40,"attendance_threshold":ATTENDANCE_THRESHOLD,"gpa_threshold":GPA_THRESHOLD})
    ref_df=pd.DataFrame(ref)

    # demo alerts from current data only (operational data, not training labels)
    mentor_map=dict(zip(assignments_df.student_id,assignments_df.teacher_id))
    alerts=[]; n=1; base=datetime(2026,9,1); status_cycle=["NEW","ACKNOWLEDGED","ACTION_TAKEN","FOLLOW_UP","RESOLVED"]
    for _,r in semester_df[semester_df.snapshot_type=="current"].iterrows():
        scores={"attendance":clip(max(0,ATTENDANCE_THRESHOLD-r.current_attendance_percentage)*2.5 + max(0,r.consecutive_absence_days*2.2),0,100),"gpa":clip(max(0,GPA_THRESHOLD-r.current_gpa)*32+(15 if r.gpa_change<0 else 0),0,100),"backlog":clip(r.current_backlog_count*18+max(0,r.backlog_growth_rate)*25+(18 if r.academic_decline_flag else 0),0,100),"support_attention":clip(22*int(r.prolonged_absence_flag)+25*int(r.engagement_decline_flag)+18*int(r.fee_status=="overdue")+17*int(r.repeated_backlog_flag),0,100)}
        for typ,score in scores.items():
            if score<50: continue
            pri=round(score*.55 + (25 if typ in ("attendance","gpa","course") else 18) + RNG.uniform(0,8),1)
            st=RNG.choice(status_cycle,p=[.25,.2,.2,.2,.15])
            created=base-timedelta(days=int(RNG.integers(0,10)))
            alerts.append({"alert_id":f"ALT{n:05d}","student_id":r.student_id,"teacher_id":mentor_map[r.student_id],"risk_type":typ,"risk_score":round(score,1),"priority_score":pri,"confidence_level":"Medium","intervenability_score":"High" if typ=="attendance" and not r.academic_decline_flag else "Medium","created_at":created.strftime("%Y-%m-%d"),"alert_status":st,"intervention_id":f"INT{n:05d}" if st!="NEW" else "","intervention_type":"mentor_check_in" if st!="NEW" else "","suggested_action":{"attendance":"Review attendance barrier and create a recovery plan","gpa":"Review weak subjects and create an academic study plan","backlog":"Connect the student to remedial support","support_attention":"Initiate a supportive mentor check-in"}[typ],"action_taken":"Mentor follow-up completed" if st in ("ACTION_TAKEN","FOLLOW_UP","RESOLVED") else "","intervention_date":(created+timedelta(days=2)).strftime("%Y-%m-%d") if st!="NEW" else "","follow_up_date":(created+timedelta(days=8)).strftime("%Y-%m-%d") if st in ("FOLLOW_UP","RESOLVED") else "","outcome_status":"improved" if st=="RESOLVED" and RNG.random()<.75 else "no_change" if st=="RESOLVED" else "","outcome_notes":"Risk reduced after intervention." if st=="RESOLVED" else "","risk_score_after_intervention":round(max(0,score-RNG.uniform(10,30)),1) if st=="RESOLVED" else ""}); n+=1
    alerts_df=pd.DataFrame(alerts)

    # save
    for name,df in {"students":students_df,"teachers":teachers_df,"assignments":assignments_df,"student_semester_features":semester_df,"student_course_features":course_df,"historical_outcomes":outcomes_df,"academic_reference_data":ref_df,"alerts_interventions":alerts_df}.items():
        df.to_csv(OUT/f"{name}.csv",index=False)
    print(f"students={len(students_df)} teachers={len(teachers_df)} assignments={len(assignments_df)} semester={len(semester_df)} course={len(course_df)} outcomes={len(outcomes_df)} reference={len(ref_df)} alerts={len(alerts_df)}")
    print(outcomes_df[["course_failed","new_backlog","gpa_below_threshold","attendance_shortage","discontinued"]].mean().round(3).to_dict())

if __name__=="__main__": main()
