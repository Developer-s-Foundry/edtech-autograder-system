from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.models import Assignment
from app.schemas.assignment import StudentAssignmentOut
from app.dependencies.auth import require_student

router = APIRouter(
    prefix="/student/assignments",
    tags=["student-assignments"],
)


@router.get("", response_model=list[StudentAssignmentOut])
def list_published_assignments(
    db: Session = Depends(get_db),
    student=Depends(require_student),
):
    """List all published assignments visible to students."""
    return (
        db.query(Assignment)
        .filter(Assignment.is_published == True)  # noqa: E712
        .order_by(Assignment.created_at.desc())
        .all()
    )


@router.get("/{assignment_id}", response_model=StudentAssignmentOut)
def get_published_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    student=Depends(require_student),
):
    """Retrieve a single published assignment by ID."""
    assignment = (
        db.query(Assignment)
        .filter(
            Assignment.id == assignment_id,
            Assignment.is_published == True,  # noqa: E712
        )
        .first()
    )

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found",
        )

    return assignment
