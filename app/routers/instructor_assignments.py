from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies.auth import require_role
from app.models.models import Assignment, User
from app.schemas.assignment import (
    AssignmentCreate,
    AssignmentResponse,
    AssignmentUpdate,
)

router = APIRouter(prefix="/instructor/assignments", tags=["instructor", "assignments"])


@router.post(
    "",
    response_model=AssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_assignment(
    payload: AssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("instructor")),
) -> Assignment:
    assignment = Assignment(
        instructor_id=current_user.id,
        **payload.model_dump(),
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


@router.put(
    "/{id}",
    response_model=AssignmentResponse,
)
def update_assignment(
    id: int,
    payload: AssignmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("instructor")),
) -> Assignment:
    assignment = db.execute(
        select(Assignment).where(Assignment.id == id)
    ).scalar_one_or_none()
    if assignment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found",
        )
    if assignment.instructor_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit your own assignments",
        )

    update_data = payload.model_dump(exclude_unset=True)

    # Validate merged weights when any weight is being updated
    weight_keys = ("weight_io", "weight_unit", "weight_static")
    if any(k in update_data for k in weight_keys):
        weight_io = update_data.get("weight_io", assignment.weight_io)
        weight_unit = update_data.get("weight_unit", assignment.weight_unit)
        weight_static = update_data.get("weight_static", assignment.weight_static)
        if weight_io < 0 or weight_unit < 0 or weight_static < 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Weights must be non-negative",
            )
        if weight_io + weight_unit + weight_static != 100:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="weight_io + weight_unit + weight_static must equal 100",
            )

    for key, value in update_data.items():
        setattr(assignment, key, value)

    db.commit()
    db.refresh(assignment)
    return assignment
