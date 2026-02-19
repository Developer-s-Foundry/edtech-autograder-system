from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.models import Assignment
from app.schemas.assignment import (
    AssignmentCreate,
    AssignmentUpdate,
    AssignmentOut,
)
from app.dependencies.auth import require_instructor

router = APIRouter(
    prefix="/instructor/assignments",
    tags=["instructor-assignments"],
)


# -------------------------------------------------------
# Create Assignment
# -------------------------------------------------------
@router.post(
    "",
    response_model=AssignmentOut,
    status_code=status.HTTP_201_CREATED,
)
def create_assignment(
    payload: AssignmentCreate,
    db: Session = Depends(get_db),
    instructor=Depends(require_instructor),
):
    assignment = Assignment(
        instructor_id=instructor.id,
        title=payload.title,
        description=payload.description,
        instructions=payload.instructions,
        language=payload.language,
        is_published=payload.is_published,
        weight_io=payload.weight_io,
        weight_unit=payload.weight_unit,
        weight_static=payload.weight_static,
        max_runtime_ms=payload.max_runtime_ms,
        max_memory_kb=payload.max_memory_kb,
    )

    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    return assignment


# -------------------------------------------------------
# Update Assignment
# -------------------------------------------------------
@router.put(
    "/{assignment_id}",
    response_model=AssignmentOut,
)
def update_assignment(
    assignment_id: int,
    payload: AssignmentUpdate,
    db: Session = Depends(get_db),
    instructor=Depends(require_instructor),
):
    assignment = (
        db.query(Assignment)
        .filter(Assignment.id == assignment_id)
        .first()
    )

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found",
        )

    # Ensure instructor owns this assignment
    if assignment.instructor_id != instructor.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to edit this assignment",
        )

    update_data = payload.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(assignment, field, value)

    db.commit()
    db.refresh(assignment)

    return assignment


@router.get("", response_model=list[AssignmentOut])
def list_assignments(
    db: Session = Depends(get_db),
    instructor=Depends(require_instructor),
):
    return (
        db.query(Assignment)
        .filter(Assignment.instructor_id == instructor.id)
        .order_by(Assignment.created_at.desc())
        .all()
    )


@router.get("/{assignment_id}", response_model=AssignmentOut)
def get_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    instructor=Depends(require_instructor),
):
    assignment = (
        db.query(Assignment)
        .filter(Assignment.id == assignment_id)
        .first()
    )
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    if assignment.instructor_id != instructor.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    return assignment

@router.post("/{assignment_id}/publish", response_model=AssignmentOut)
def publish_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    instructor=Depends(require_instructor),
):
    assignment = (
        db.query(Assignment)
        .filter(Assignment.id == assignment_id)
        .first()
    )
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    if assignment.instructor_id != instructor.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    if not assignment.is_published:
        assignment.is_published = True
        db.commit()
        db.refresh(assignment)

    return assignment


@router.post("/{assignment_id}/unpublish", response_model=AssignmentOut)
def unpublish_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    instructor=Depends(require_instructor),
):
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    if assignment.instructor_id != instructor.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    if assignment.is_published:
        assignment.is_published = False
        db.commit()
        db.refresh(assignment)

    return assignment
