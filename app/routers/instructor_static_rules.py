from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies.auth import require_instructor
from app.models.models import Assignment, StaticRule
from app.schemas.static_rule import StaticRuleUpsert, StaticRuleOut

router = APIRouter(
    prefix="/instructor/assignments",
    tags=["instructor-static-rules"],
)


def _get_owned_assignment(db: Session, assignment_id: int, instructor_id: int) -> Assignment:
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    if assignment.instructor_id != instructor_id:
        raise HTTPException(status_code=403, detail="Not allowed")
    return assignment


@router.put(
    "/{assignment_id}/static-rules",
    response_model=StaticRuleOut,
)
def upsert_static_rules(
    assignment_id: int,
    payload: StaticRuleUpsert,
    db: Session = Depends(get_db),
    instructor=Depends(require_instructor),
):
    _get_owned_assignment(db, assignment_id, instructor.id)

    rule = db.query(StaticRule).filter(StaticRule.assignment_id == assignment_id).first()

    if rule:
        rule.required_functions = payload.required_functions
        rule.forbidden_imports = payload.forbidden_imports
        rule.max_cyclomatic_complexity = payload.max_cyclomatic_complexity
        rule.points = payload.points
        db.commit()
        db.refresh(rule)
        return rule

    rule = StaticRule(
        assignment_id=assignment_id,
        required_functions=payload.required_functions,
        forbidden_imports=payload.forbidden_imports,
        max_cyclomatic_complexity=payload.max_cyclomatic_complexity,
        points=payload.points,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.get(
    "/{assignment_id}/static-rules",
    response_model=StaticRuleOut,
)
def get_static_rules(
    assignment_id: int,
    db: Session = Depends(get_db),
    instructor=Depends(require_instructor),
):
    _get_owned_assignment(db, assignment_id, instructor.id)

    rule = db.query(StaticRule).filter(StaticRule.assignment_id == assignment_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Static rules not found")
    return rule
