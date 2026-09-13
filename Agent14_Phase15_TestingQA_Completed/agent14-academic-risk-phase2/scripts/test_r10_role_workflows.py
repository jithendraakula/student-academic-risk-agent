"""R10 role workflow corrections regression tests."""
from __future__ import annotations
import base64, json, os, sys, types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; BACKEND=ROOT/'backend'
sys.path.insert(0,str(BACKEND)); sys.path.insert(0,str(ROOT))
os.environ['DATABASE_URL']=f"sqlite:///{BACKEND/'r10_role_workflow_test.db'}"; os.environ['JWT_SECRET']='r10-test-secret'
os.environ['AI_PROVIDER']='gemini'; os.environ['AI_API_KEY']='test-key'; os.environ['AI_MODEL']='r10-test'
def install_stubs():
    if 'jose' not in sys.modules:
        jose=types.ModuleType('jose'); jose.JWTError=type('JWTError',(Exception,),{})
        class JWT:
            @staticmethod
            def encode(payload,secret,algorithm=None): return base64.urlsafe_b64encode(json.dumps(payload,default=str).encode()).decode()
            @staticmethod
            def decode(token,secret,algorithms=None): return json.loads(base64.urlsafe_b64decode(token.encode()).decode())
        jose.jwt=JWT; sys.modules['jose']=jose
    if 'passlib.context' not in sys.modules:
        passlib=types.ModuleType('passlib'); context=types.ModuleType('passlib.context')
        class CryptContext:
            def __init__(self,*a,**kw): pass
            def hash(self,p): return str(p)
            def verify(self,p,s): return str(p)==str(s)
        context.CryptContext=CryptContext; sys.modules['passlib']=passlib; sys.modules['passlib.context']=context
install_stubs()
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models.domain import Assignment, Teacher
import app.services.ai as ai

def login(client,email):
    r=client.post('/api/auth/login',json={'email':email,'password':'demo'}); r.raise_for_status(); return {'Authorization':f"Bearer {r.json()['token']}"}
def main():
    db_path=BACKEND/'r10_role_workflow_test.db'; original_call=ai._call_provider
    try:
        with TestClient(app) as client:
            hod=login(client,'hod.cse@vignan.ac.in'); mentor=login(client,'mentor.one.cse@vignan.ac.in'); dean=login(client,'dean@vignan.ac.in'); admin=login(client,'admin@vignan.ac.in')
            with SessionLocal() as db:
                mentor_id=db.query(Teacher.id).filter(Teacher.email=='mentor.one.cse@vignan.ac.in').first()[0]
                student_id=db.query(Assignment.student_id).filter(Assignment.teacher_id==mentor_id,Assignment.assignment_type=='mentor').first()[0]
            drill=client.get(f'/api/hod/mentors/{mentor_id}/students',headers=hod); drill.raise_for_status(); data=drill.json()
            assert data['sections']==sorted(data['sections']); assert set(data['sections']).issubset({'CSE-A','CSE-B'})
            for sec in data['sections']:
                filtered=client.get(f'/api/hod/mentors/{mentor_id}/students',params={'section':sec},headers=hod); filtered.raise_for_status(); assert all(row['section']==sec for row in filtered.json()['items'])
            profile=client.get(f'/api/predictions/student/{student_id}',headers=mentor); profile.raise_for_status(); p=profile.json(); st=p['current_status']
            assert st['source']=='canonical_student_summary'; assert st['risk_level'] in {'LOW','MODERATE','HIGH','CRITICAL'}; assert 0<=st['risk_score']<=100; assert 0<=st['priority_score']<=100
            assert client.get(f'/api/predictions/student/{student_id}',headers=hod).status_code==200
            assert client.get(f'/api/predictions/student/{student_id}',headers=dean).status_code==200
            assert client.post(f'/api/mentor/ai/copilot/{student_id}',json={'intent':'risk_summary'},headers=hod).status_code==403
            assert client.post(f'/api/mentor/ai/copilot/{student_id}',json={'intent':'risk_summary'},headers=dean).status_code==403
            assert client.post(f'/api/mentor/ai/copilot/{student_id}',json={'intent':'risk_summary'},headers=admin).status_code==403
            profile_src=(ROOT/'frontend/src/pages/mentor/StudentProfile.tsx').read_text(); hod_src=(ROOT/'frontend/src/pages/hod/Dashboard.tsx').read_text()
            assert 'user?.role === "mentor" ? (' in profile_src; assert 'profile.current_status.risk_level' in profile_src; assert '<option value="A">A</option>' not in hod_src; assert '<option value="B">B</option>' not in hod_src; assert 'mentorSections.map' in hod_src
        print('R10 ROLE WORKFLOW TESTS PASSED')
    finally:
        ai._call_provider=original_call
        if db_path.exists(): db_path.unlink()
if __name__=='__main__': main()
