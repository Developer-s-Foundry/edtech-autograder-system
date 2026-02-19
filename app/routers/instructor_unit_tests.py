from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies.auth import require_instructor
from app.models.models import Assignment, UnitTestSpec
from app.schemas.unit_test_spec import UnitTestSpecUpsert, UnitTestSpecOut

router = APIRouter(
    prefix="/instructor/assignments",
    tags=["instructor-unit-tests"],
)


def _get_owned_assignment(db: Session, assignment_id: int, instructor_id: int) -> Assignment:
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    if assignment.instructor_id != instructor_id:
        raise HTTPException(status_code=403, detail="Not allowed")
    return assignment


@router.post(
    "/{assignment_id}/unit-tests",
    response_model=UnitTestSpecOut,
    status_code=status.HTTP_201_CREATED,
)
def upsert_unit_test_spec(
    assignment_id: int,
    payload: UnitTestSpecUpsert,
    db: Session = Depends(get_db),
    instructor=Depends(require_instructor),
):
    _get_owned_assignment(db, assignment_id, instructor.id)

    spec = (
        db.query(UnitTestSpec)
        .filter(UnitTestSpec.assignment_id == assignment_id)
        .first()
    )

    if spec:
        # update existing
        spec.name = payload.name
        spec.test_code = payload.test_code
        spec.points = payload.points
        spec.is_hidden = payload.is_hidden
        db.commit()
        db.refresh(spec)
        return spec

    # create new
    spec = UnitTestSpec(
        assignment_id=assignment_id,
        name=payload.name,
        test_code=payload.test_code,
        points=payload.points,
        is_hidden=payload.is_hidden,
    )
    db.add(spec)
    db.commit()
    db.refresh(spec)
    return spec


@router.get(
    "/{assignment_id}/unit-tests",
    response_model=UnitTestSpecOut,
)
def get_unit_test_spec(
    assignment_id: int,
    db: Session = Depends(get_db),
    instructor=Depends(require_instructor),
):
    _get_owned_assignment(db, assignment_id, instructor.id)

    spec = (
        db.query(UnitTestSpec)
        .filter(UnitTestSpec.assignment_id == assignment_id)
        .first()
    )
    if not spec:
        raise HTTPException(status_code=404, detail="Unit test spec not found")

    return spec
