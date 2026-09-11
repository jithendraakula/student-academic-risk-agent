# Agent 14 — Student Academic Risk Agent

Early-warning academic risk intelligence platform. See `docs/` for the PRD,
architecture, and the resumable project state checkpoint.

## Quick Start

### Frontend
```
cd frontend
npm install
cp .env.example .env
npm run dev
```

### Backend
```
cd backend
python3 -m venv venv
. venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Demo accounts (any non-empty password):
- mentor1@vignan.ac.in / mentor2@vignan.ac.in
- hod.cse@vignan.ac.in
- dean@vignan.ac.in
- admin@vignan.ac.in
