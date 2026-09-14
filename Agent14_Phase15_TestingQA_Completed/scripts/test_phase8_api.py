"""Phase 8 intervention workflow regression tests."""
from __future__ import annotations
import base64, json, os, sys, types
from pathlib import Path
from datetime import date, timedelta

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND)); sys.path.insert(0, str(ROOT))
os.environ["DATABASE_URL"] = f"sqlite:///{BACKEND / 'phase8_test.db'}"
os.environ["JWT_SECRET"] = "phase8-test-secret"

def install_test_auth_stubs():
    if "jose" not in sys.modules:
        jose = types.ModuleType("jose"); jose.JWTError = type("JWTError", (Exception,), {})
        class _JWT:
            @staticmethod
            def encode(payload, secret, algorithm=None): return base64.urlsafe_b64encode(json.dumps(payload, default=str).encode()).decode()
            @staticmethod
            def decode(token, secret, algorithms=None): return json.loads(base64.urlsafe_b64decode(token.encode()).decode())
        jose.jwt = _JWT; sys.modules["jose"] = jose
    if "passlib.context" not in sys.modules:
        passlib = types.ModuleType("passlib"); context = types.ModuleType("passlib.context")
        class CryptContext:
            def __init__(self, *args, **kwargs): pass
            def hash(self, password): return str(password)
            def verify(self, password, stored): return str(password) == str(stored)
        context.CryptContext = CryptContext; sys.modules["passlib"] = passlib; sys.modules["passlib.context"] = context
install_test_auth_stubs()

from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models.domain import AlertIntervention, InterventionRecord


def login(client, email):
    r = client.post('/api/auth/login', json={'email': email, 'password': 'demo'}); r.raise_for_status()
    return {'Authorization': f"Bearer {r.json()['token']}"}


def pick_alert(client, headers):
    r = client.get('/api/mentor/alerts', headers=headers); r.raise_for_status()
    items = r.json()['items']
    assert items
    return next((item for item in items if item["status"] in {"NEW", "ACKNOWLEDGED"}), items[0])


def main():
    try:
        with TestClient(app) as client:
            mentor = login(client, 'mentor.one.cse@vignan.ac.in')
            hod = login(client, 'hod.cse@vignan.ac.in')
            dean = login(client, 'dean@vignan.ac.in')
            admin = login(client, 'admin@vignan.ac.in')

            before = client.get('/api/interventions/summary', headers=mentor); before.raise_for_status()
            assert before.json()['assigned_students'] > 0
            assert client.get('/api/interventions/summary', headers=admin).status_code == 403

            alert = pick_alert(client, mentor)
            alert_id = alert['alert_id']

            detail = client.get(f'/api/interventions/{alert_id}', headers=mentor); detail.raise_for_status()
            d = detail.json(); assert 'allowed_next_statuses' in d and d['can_intervene'] is True

            # Mentor can acknowledge and history is created.
            if alert['status'] == 'NEW':
                ack = client.post(f'/api/mentor/alerts/{alert_id}/acknowledge', headers=mentor); ack.raise_for_status()
                assert ack.json()['status'] == 'ACKNOWLEDGED'

            # Action requires notes.
            bad = client.patch(f'/api/interventions/{alert_id}', headers=mentor, json={'status':'ACTION_TAKEN','notes':'','follow_up_date':None})
            assert bad.status_code == 400

            action = client.patch(f'/api/interventions/{alert_id}', headers=mentor, json={'status':'ACTION_TAKEN','notes':'Discussed recovery plan with student.'})
            action.raise_for_status(); assert action.json()['status'] == 'ACTION_TAKEN'

            # Follow-up requires both notes and a future date.
            bad_follow = client.patch(f'/api/interventions/{alert_id}', headers=mentor, json={'status':'FOLLOW_UP','notes':'Plan set'})
            assert bad_follow.status_code == 400
            due = (date.today() + timedelta(days=7)).isoformat()
            follow = client.patch(f'/api/interventions/{alert_id}', headers=mentor, json={'status':'FOLLOW_UP','notes':'Check attendance recovery next week.','follow_up_date':due})
            follow.raise_for_status(); assert follow.json()['overdue'] is False

            history = client.get(f'/api/interventions/{alert_id}/history', headers=mentor); history.raise_for_status()
            assert len(history.json()['items']) >= 2

            # HOD/Dean can review but cannot mutate.
            hq = client.get('/api/interventions/queue?status=FOLLOW_UP', headers=hod); hq.raise_for_status(); assert all(x['status']=='FOLLOW_UP' for x in hq.json()['items'])
            hsummary = client.get('/api/interventions/summary', headers=hod); hsummary.raise_for_status(); assert hsummary.json()['follow_up'] >= 1
            dsummary = client.get('/api/interventions/summary', headers=dean); dsummary.raise_for_status()
            forbidden = client.patch(f'/api/interventions/{alert_id}', headers=hod, json={'status':'RESOLVED','notes':'HOD should not mutate'})
            assert forbidden.status_code == 403

            resolved = client.patch(f'/api/interventions/{alert_id}', headers=mentor, json={'status':'RESOLVED','notes':'Recovery action completed and reviewed.'})
            resolved.raise_for_status(); assert resolved.json()['status'] == 'RESOLVED'
            assert client.patch(f'/api/interventions/{alert_id}', headers=mentor, json={'status':'FOLLOW_UP','notes':'Attempt reopen'}) .status_code == 400

            with SessionLocal() as db:
                records = db.query(InterventionRecord).filter(InterventionRecord.alert_id == alert_id).all()
                persisted = db.get(AlertIntervention, alert_id)
                assert len(records) >= 3
                assert persisted.status == 'RESOLVED'

            after = client.get('/api/interventions/summary', headers=mentor); after.raise_for_status()
            assert after.json()['resolved'] >= before.json()['resolved']

        print('PHASE 8 INTERVENTION TESTS PASSED')
    finally:
        db_path = BACKEND / 'phase8_test.db'
        if db_path.exists(): db_path.unlink()

if __name__ == '__main__': main()
