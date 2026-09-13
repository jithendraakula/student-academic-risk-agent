from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import require_roles
from app.db.session import get_db
from app.models.domain import User
from app.schemas.ai import CopilotRequest
from app.services.ai import run_copilot

router = APIRouter()


@router.post("/copilot/{student_id}")
def mentor_copilot(
    student_id: str,
    payload: CopilotRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles("mentor")),
):
    return run_copilot(db, student_id, user, payload)
