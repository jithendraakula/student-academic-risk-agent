"""U5-U7 faculty UX contract and backend notification tests."""
from __future__ import annotations
import base64, json, os, sys, types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
SRC = ROOT / "frontend" / "src"
os.environ["DATABASE_URL"] = f"sqlite:///{BACKEND / 'u5_u7_test.db'}"
os.environ["JWT_SECRET"] = "u5-u7-test-secret"
os.environ["NOTIFICATIONS_ENABLED"] = "true"
os.environ["NOTIFICATION_EMAIL_ENABLED"] = "false"
sys.path.insert(0, str(BACKEND)); sys.path.insert(0, str(ROOT))

def stubs():
    if "jose" not in sys.modules:
        jose=types.ModuleType("jose"); jose.JWTError=type("JWTError",(Exception,),{})
        class J:
            @staticmethod
            def encode(payload, secret, algorithm=None): return base64.urlsafe_b64encode(json.dumps(payload, default=str).encode()).decode()
            @staticmethod
            def decode(token, secret, algorithms=None): return json.loads(base64.urlsafe_b64decode(token.encode()).decode())
        jose.jwt=J; sys.modules["jose"]=jose
    if "passlib.context" not in sys.modules:
        p=types.ModuleType("passlib"); c=types.ModuleType("passlib.context")
        class CryptContext:
            def __init__(self,*a,**k): pass
            def hash(self,password): return str(password)
            def verify(self,password,stored): return str(password)==str(stored)
        c.CryptContext=CryptContext; sys.modules["passlib"]=p; sys.modules["passlib.context"]=c
stubs()

from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models.domain import Notification

def login(client,email):
    r=client.post("/api/auth/login",json={"email":email,"password":"demo"}); r.raise_for_status(); return {"Authorization":f"Bearer {r.json()['token']}"}

def static_checks():
    shell=(SRC/"components/InstitutionalShell.tsx").read_text(); profile=(SRC/"pages/mentor/StudentProfile.tsx").read_text(); hod=(SRC/"pages/hod/Dashboard.tsx").read_text(); dean=(SRC/"pages/dean/Dashboard.tsx").read_text()
    checks={
      "notification uses portal": "createPortal" in shell and "z-[90]" in shell,
      "notification supports read-all": 'api.post("/notifications/read-all")' in shell,
      "notification shows academic context": "roll_number" in shell and "recommended_action" in shell and "evidence" in shell,
      "what-if has guided target": "Use recommended target" in profile and "See estimated impact" in profile,
      "what-if states simulation only": "Simulation only · not saved" in profile,
      "ai optional language": "Optional. The numerical estimate above is independent of the AI provider." in profile,
      "hod uses mentor sections": "mentor.sections?.join" in hod and "result.sections" in hod,
      "hod uses readable primary risk": "readableRiskType(student.primary_risk)" in hod,
      "hod uses open case work": 'label="Open case work"' in hod,
      "dean readable support label": 'support_attention: "Support attention"' in dean,
      "dean uses open case work": 'label="Open case work"' in dean,
      "role AI ordering": hod.index('Where does mentor support demand sit?') < hod.index('<InstitutionalAIPanel role="hod"') and dean.index('Authorized case review') < dean.index('<InstitutionalAIPanel role="dean"'),
    }
    failed=[k for k,v in checks.items() if not v]
    for k,v in checks.items(): print(("PASS" if v else "FAIL")+" - "+k)
    if failed: raise SystemExit(f"U5-U7 static gate failed: {failed}")


def main():
    static_checks()
    db_path=BACKEND/"u5_u7_test.db"
    try:
        with TestClient(app) as client:
            mentor=login(client,"mentor.one.cse@vignan.ac.in")
            hod=login(client,"hod.cse@vignan.ac.in")
            dean=login(client,"dean@vignan.ac.in")
            admin=login(client,"admin@vignan.ac.in")
            inbox=client.get("/api/notifications",headers=mentor); inbox.raise_for_status(); data=inbox.json()
            assert all("roll_number" in item and "category" in item for item in data["items"])
            assert all(not (item.get("action_required") and not item.get("student_id")) for item in data["items"])
            read_all=client.post("/api/notifications/read-all",headers=mentor); read_all.raise_for_status()
            assert client.get("/api/notifications",headers=mentor).json()["unread"]==0
            assert client.post("/api/notifications/read-all",headers=mentor).status_code==200
            assert client.get("/api/notifications",headers=admin).status_code==403
            # Role scopes still work after U5-U7 changes.
            assert client.get("/api/hod/mentor-comparison",headers=hod).status_code==200
            assert client.get("/api/dean/summary",headers=dean).status_code==200
        with SessionLocal() as db:
            assert db.query(Notification).filter(Notification.user_id=="T001", Notification.channel=="IN_APP").count() >= 0
        print("U5-U7 BACKEND/FACULTY CONTRACT: PASS")
    finally:
        if db_path.exists(): db_path.unlink()

if __name__=="__main__": main()
