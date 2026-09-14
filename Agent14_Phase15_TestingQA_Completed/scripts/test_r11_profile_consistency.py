"""R11 canonical student-status/profile consistency regression tests."""
from __future__ import annotations
import base64, json, os, sys, types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; BACKEND=ROOT/'backend'
sys.path[:0]=[str(BACKEND),str(ROOT)]
DB=BACKEND/'r11_profile_consistency_test.db'
if DB.exists(): DB.unlink()
os.environ['DATABASE_URL']=f'sqlite:///{DB}'; os.environ['JWT_SECRET']='r11-test-secret'

jose=types.ModuleType('jose'); jose.JWTError=type('JWTError',(Exception,),{})
class JWT:
    @staticmethod
    def encode(payload,secret,algorithm=None): return base64.urlsafe_b64encode(json.dumps(payload,default=str).encode()).decode()
    @staticmethod
    def decode(token,secret,algorithms=None): return json.loads(base64.urlsafe_b64decode(token.encode()).decode())
jose.jwt=JWT; sys.modules['jose']=jose
passlib=types.ModuleType('passlib'); context=types.ModuleType('passlib.context')
class CryptContext:
    def __init__(self,*a,**kw): pass
    def hash(self,p): return 'hashed:'+str(p)
    def verify(self,p,s): return s in {'hashed:'+str(p), str(p)}
context.CryptContext=CryptContext; sys.modules['passlib']=passlib; sys.modules['passlib.context']=context

from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models.domain import Assignment, RiskPrediction, SemesterFeature
from app.services.aggregation import student_summary


def login(c,email):
    r=c.post('/api/auth/login',json={'email':email,'password':'demo'}); r.raise_for_status(); return {'Authorization':'Bearer '+r.json()['token']}

try:
    with TestClient(app) as c:
        mentor=login(c,'mentor.one.cse@vignan.ac.in')
        with SessionLocal() as db:
            sid=db.query(Assignment.student_id).filter(Assignment.teacher_id=='T001',Assignment.assignment_type=='mentor').first()[0]
            sem=db.query(SemesterFeature).filter(SemesterFeature.student_id==sid).order_by(SemesterFeature.id.desc()).first()
            checkpoint=int((sem.data or {}).get('checkpoint_week',6))
            summary=student_summary(db,[sid],include_support_attention=True)[sid]
            visible=db.query(RiskPrediction).filter(RiskPrediction.student_id==sid,RiskPrediction.semester==sem.semester,RiskPrediction.checkpoint_week==checkpoint).all()
            assert visible, 'current canonical predictions missing'
            primary_candidates=[r for r in visible if r.risk_type!='discontinuation']
            from app.services.risk_engine import should_create_alert
            actionable=[r for r in primary_candidates if should_create_alert(r.risk_score,r.risk_level,r.priority_score)]
            pool=actionable or [r for r in primary_candidates if r.risk_score>=40] or primary_candidates
            expected=max(pool,key=lambda r:r.priority_score)
            assert summary['primary_risk']==expected.risk_type
            assert abs(summary['risk_score']-float(expected.risk_score))<1e-6
            assert abs(summary['priority_score']-float(expected.priority_score))<1e-6
            assert summary['risk_level']==expected.risk_level
        r=c.get(f'/api/predictions/student/{sid}',headers=mentor); r.raise_for_status(); d=r.json()
        assert d['current_status']['primary_risk']==summary['primary_risk']
        assert abs(d['current_status']['risk_score']-summary['risk_score'])<1e-6
        assert abs(d['current_status']['priority_score']-summary['priority_score'])<1e-6
        assert d['student_metrics']['semester']==5
        assert d['student_metrics']['academic_year']=='2026-27'
        assert 0<=d['student_metrics']['assignment_completion']<=100
        assert len(d['risks']['course_failure'])==5
        src=(ROOT/'frontend/src/pages/mentor/StudentProfile.tsx').read_text()
        assert 'key: "course_failure"' in src and "highestCourseRisk" in src
        assert 'profile?.student_metrics.assignment_completion ?? 0' in src
        assert 'profile.student_metrics.semester' in src and 'profile.student_metrics.academic_year' in src
        print('R11 PROFILE CONSISTENCY TEST PASSED')
finally:
    if DB.exists(): DB.unlink()
