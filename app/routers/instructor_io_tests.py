from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies.auth import require_instructor
from app.models.models import Assignment, IOTestCase
from app.schemas.io_test_case import IOTestCaseCreate, IOTestCaseOut

router = APIRouter(
    prefix="/instructor/assignments",
    tags=["instructor-io-tests"],
)

def _get_owned_assignment(db: Session, assignment_id: int, instructor_id: int) -> Assignment:
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    if assignment.instructor_id != instructor_id:
        raise HTTPException(status_code=403, detail="Not allowed")
    return assignment


@router.post(
    "/{assignment_id}/io-tests",
    response_model=IOTestCaseOut,
    status_code=status.HTTP_201_CREATED,
)
def create_io_test_case(
    assignment_id: int,
    payload: IOTestCaseCreate,
    db: Session = Depends(get_db),
    instructor=Depends(require_instructor),
):
    _get_owned_assignment(db, assignment_id, instructor.id)

    tc = IOTestCase(
        assignment_id=assignment_id,
        name=payload.name,
        stdin=payload.stdin,
        expected_stdout=payload.expected_stdout,
        points=payload.points,
        is_hidden=payload.is_hidden,
        order_index=payload.order_index,
    )
    db.add(tc)
    db.commit()
    db.refresh(tc)
    return tc


@router.get(
    "/{assignment_id}/io-tests",
    response_model=list[IOTestCaseOut],
)
def list_io_test_cases(
    assignment_id: int,
    db: Session = Depends(get_db),
    instructor=Depends(require_instructor),
):
    _get_owned_assignment(db, assignment_id, instructor.id)

    return (
        db.query(IOTestCase)
        .filter(IOTestCase.assignment_id == assignment_id)
        .order_by(IOTestCase.order_index.asc(), IOTestCase.id.asc())
        .all()
    )
