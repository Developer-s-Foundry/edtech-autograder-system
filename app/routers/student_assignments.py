from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies.auth import require_student
from app.models.models import Assignment
from app.schemas.assignment import AssignmentOut

router = APIRouter(prefix="/student/assignments", tags=["student-assignments"])


@router.get("", response_model=list[AssignmentOut])
def list_published_assignments(
    db: Session = Depends(get_db),
    student=Depends(require_student),
):
    return (
        db.query(Assignment)
        .filter(Assignment.is_published == True)  # noqa: E712
        .order_by(Assignment.created_at.desc())
        .all()
    )
