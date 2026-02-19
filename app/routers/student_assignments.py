from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.models import Assignment
from app.schemas.assignment import StudentAssignmentOut
from app.dependencies.auth import require_student
from app.schemas.assignment import AssignmentOut
from app.schemas.student_assignment import (
    StudentAssignmentListOut,
    StudentAssignmentDetailOut,
)

router = APIRouter(
    prefix="/student/assignments",
    tags=["student-assignments"],
)

@router.get("", response_model=list[StudentAssignmentListOut])
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


@router.get("/{assignment_id}", response_model=StudentAssignmentDetailOut)
def get_published_assignment_detail(
    assignment_id: int,
    db: Session = Depends(get_db),
    student=Depends(require_student),
):
    assignment = (
        db.query(Assignment)
        .filter(Assignment.id == assignment_id)
        .first()
    )

    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    if not assignment.is_published:
        # Students must not see unpublished assignments
        raise HTTPException(status_code=404, detail="Assignment not found")

    return assignment

@router.get("", response_model=list[StudentAssignmentOut])


@router.get("", response_model=list[AssignmentOut])
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
