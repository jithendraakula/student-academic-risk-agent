"""R5 student academic profile workflow test."""
from __future__ import annotations
import base64, json, os, sys, types
from pathlib import Path
from fastapi.testclient import TestClient

ROOT=Path(__file__).resolve().parents[1]
BACKEND=ROOT/'backend'
sys.path[:0]=[str(BACKEND),str(ROOT)]
os.environ['DATABASE_URL']=f"sqlite:///{BACKEND/'r5_test.db'}"
os.environ['JWT_SECRET']='r5-test-secret-change-me'
for path in [BACKEND/'r5_test.db']:
    try: path.unlink()
    except FileNotFoundError: pass

jose=types.ModuleType('jose'); jose.JWTError=type('JWTError',(Exception,),{})
class _JWT:
    @staticmethod
    def encode(payload,secret,algorithm=None): return base64.urlsafe_b64encode(json.dumps(payload,default=str).encode()).decode()
    @staticmethod
    def decode(token,secret,algorithms=None): return json.loads(base64.urlsafe_b64decode(token.encode()).decode())
jose.jwt=_JWT; sys.modules['jose']=jose
passlib=types.ModuleType('passlib'); context=types.ModuleType('passlib.context')
class CryptContext:
    def __init__(self,*a,**k): pass
    def hash(self,password): return 'hashed:'+password
    def verify(self,password,stored): return stored=='hashed:'+password or stored==password
context.CryptContext=CryptContext; sys.modules['passlib']=passlib; sys.modules['passlib.context']=context

from app.main import app
from app.db.session import SessionLocal
from app.models.domain import Assignment

def login(c,email):
    r=c.post('/api/auth/login',json={'email':email,'password':'demo'}); r.raise_for_status(); return {'Authorization':'Bearer '+r.json()['token']}

with TestClient(app) as c:
    h=login(c,'mentor.one.cse@vignan.ac.in')
    with SessionLocal() as db:
        sid=db.query(Assignment.student_id).filter(Assignment.teacher_id=='T001').first()[0]
    r=c.get(f'/api/predictions/student/{sid}',headers=h); r.raise_for_status(); d=r.json()
    assert d['student']['student_id']==sid
    assert 'case_management' in d
    assert isinstance(d['case_management']['items'],list)
    assert 'academic_context' in d
    assert 'observations' in d['academic_context']
    assert 'risk_source' in d and d['risk_source']=='risk_predictions'
    assert len(d['risks']['course_failure'])==5
    # All expected faculty-facing sections are represented in the profile contract.
    for key in ('current_gpa','current_cgpa','attendance','backlogs','internal_marks'):
        assert key in d['student_metrics']
    print('R5 STUDENT PROFILE TEST PASSED')
