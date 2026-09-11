from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, mentor, hod, dean, admin, predictions
from app.api import interventions
from app.db.session import init_db

app = FastAPI(
    title="Agent 14 — Student Academic Risk Agent API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(mentor.router, prefix="/api/mentor", tags=["mentor"])
app.include_router(hod.router, prefix="/api/hod", tags=["hod"])
app.include_router(dean.router, prefix="/api/dean", tags=["dean"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(predictions.router, prefix="/api/predictions", tags=["predictions"])
app.include_router(interventions.router, prefix="/api/interventions", tags=["interventions"])


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "agent14-backend"}
