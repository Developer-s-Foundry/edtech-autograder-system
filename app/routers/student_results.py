from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.db import get_db
from app.dependencies.auth import require_student
from app.models.models import GradingRun, Submission
from app.schemas.submission import (
    GradingResultOut,
    StaticAnalysisOut,
    SubmissionStatusOut,
    TestCaseResultOut,
)
from app.schemas.student_submission import (
    StudentSubmissionOut, 
    StudentSubmissionResultOut,
)


router = APIRouter(
    prefix="/student/submissions",
    tags=["student-results"],
)


def _get_owned_submission(submission_id: int, student_id: int, db: Session) -> Submission:
    """
    Fetch a submission by ID and enforce ownership.

    Raises 404 if the submission does not exist.
    Raises 403 if the submission belongs to a different student.
    """
    submission = db.query(Submission).filter(Submission.id == submission_id).first()

    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found",
        )

    if submission.student_id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this submission",
        )

    return submission

@router.get("/student/submissions/{submission_id}", response_model=StudentSubmissionOut)
def get_submission_status(
    submission_id: int,
    db: Session = Depends(get_db),
    student=Depends(require_student),
):
    submission = _get_owned_submission(db, submission_id, student.id)

    return StudentSubmissionOut(
        submission_id=submission.id,
        assignment_id=submission.assignment_id,
        status=submission.status,
        created_at=submission.created_at.isoformat() if getattr(submission, "created_at", None) else None,
        filename=submission.filename,
    )


@router.get("/student/submissions/{submission_id}/result", response_model=StudentSubmissionResultOut)
def get_submission_result(
    submission_id: int,
    db: Session = Depends(get_db),
    student=Depends(require_student),
):
    submission = _get_owned_submission(db, submission_id, student.id)

    # If queued/running, return status only
    if submission.status in ("queued", "running"):
        return StudentSubmissionResultOut(
            submission_id=submission.id,
            status=submission.status,
        )

    # If failed, include safe error message only
    if submission.status == "failed":
        # prefer latest grading run error if available
        error_msg = None

        if submission.latest_grading_run_id:
            gr = db.query(GradingRun).filter(GradingRun.id == submission.latest_grading_run_id).first()
            if gr:
                error_msg = gr.error_message

        return StudentSubmissionResultOut(
            submission_id=submission.id,
            status=submission.status,
            error_message=error_msg or "Grading failed.",
        )

    # If completed, show summary breakdown only (no hidden test details)
    if submission.status == "completed":
        gr = None

        if submission.latest_grading_run_id:
            gr = db.query(GradingRun).filter(GradingRun.id == submission.latest_grading_run_id).first()

        # Placeholder-safe behavior: grading run missing but submission marked completed
        if not gr:
            return StudentSubmissionResultOut(
                submission_id=submission.id,
                status=submission.status,
                score_total=0,
                io_score=0,
                unit_score=0,
                static_score=0,
                feedback_summary={"note": "Results unavailable yet (placeholder)."},
                ai_feedback=None,
            )

        return StudentSubmissionResultOut(
            submission_id=submission.id,
            status=submission.status,
            score_total=gr.score_total,
            io_score=gr.io_score,
            unit_score=gr.unit_score,
            static_score=gr.static_score,
            feedback_summary=gr.feedback_summary,  # should be safe summary JSON
            ai_feedback=gr.ai_feedback,
        )

    # Unknown status safety
    return StudentSubmissionResultOut(
        submission_id=submission.id,
        status=submission.status,
    )

@router.get("/{submission_id}", response_model=SubmissionStatusOut)
def get_submission_status(
    submission_id: int,
    db: Session = Depends(get_db),
    student=Depends(require_student),
):
    """
    Return submission metadata and current status.

    Ownership enforced: only the submitting student may access.
    """
    submission = _get_owned_submission(submission_id, student.id, db)

    return SubmissionStatusOut(
        submission_id=submission.id,
        assignment_id=submission.assignment_id,
        filename=submission.filename,
        status=submission.status,
        created_at=submission.created_at,
        updated_at=submission.updated_at,
    )


@router.get("/{submission_id}/result", response_model=GradingResultOut)
def get_submission_result(
    submission_id: int,
    db: Session = Depends(get_db),
    student=Depends(require_student),
):
    """
    Return grading results for a submission.

    - queued / running: returns status only.
    - completed / failed: returns full breakdown.

    Hidden test inputs and expected outputs are never included.
    Ownership enforced: only the submitting student may access.
    """
    submission = _get_owned_submission(submission_id, student.id, db)

    # Not yet graded — return lightweight status-only response
    if submission.status in ("queued", "running"):
        return GradingResultOut(
            submission_id=submission.id,
            status=submission.status,
        )

    # Grading finished (completed or failed) — load the latest grading run
    run = (
        db.query(GradingRun)
        .options(
            joinedload(GradingRun.test_case_results),
            joinedload(GradingRun.static_analysis_report),
        )
        .filter(GradingRun.id == submission.latest_grading_run_id)
        .first()
        if submission.latest_grading_run_id is not None
        else None
    )

    if run is None:
        # Grading run record not yet written (edge case: status updated before run saved)
        return GradingResultOut(
            submission_id=submission.id,
            status=submission.status,
        )

    # Build IO test case results — hide stdin / expected_stdout
    io_results = [
        TestCaseResultOut(
            io_test_case_id=tcr.io_test_case_id,
            passed=tcr.passed,
            points_awarded=tcr.points_awarded,
            stdout=tcr.stdout,
            stderr=tcr.stderr,
            status=tcr.status,
            time_ms=tcr.time_ms,
            memory_kb=tcr.memory_kb,
        )
        for tcr in run.test_case_results
    ]

    # Build static analysis block if present
    static_analysis = None
    if run.static_analysis_report is not None:
        sar = run.static_analysis_report
        static_analysis = StaticAnalysisOut(
            passed=sar.passed,
            violations=sar.violations,
            cyclomatic_complexity=sar.cyclomatic_complexity,
        )

    return GradingResultOut(
        submission_id=submission.id,
        status=submission.status,
        score_total=run.score_total,
        io_score=run.io_score,
        unit_score=run.unit_score,
        static_score=run.static_score,
        feedback_summary=run.feedback_summary,
        ai_feedback=run.ai_feedback,
        io_results=io_results,
        static_analysis=static_analysis,
        finished_at=run.finished_at,
    )
