from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import require_roles
from app.db.session import get_db
from app.models.domain import User
from app.schemas.institutional_ai import InstitutionalAIRequest
from app.services.institutional_ai import run_institutional_analysis

router = APIRouter()


@router.post("/analyze")
def analyze_institutional_risk(
    payload: InstitutionalAIRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("hod", "dean")),
):
    return run_institutional_analysis(db, user, payload)
