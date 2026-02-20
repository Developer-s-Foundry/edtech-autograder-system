# import logging

# from app.celery_app import celery_app

# logger = logging.getLogger(__name__)

# @celery_app.task(name="app.tasks.grading.grade_submission", bind=True, max_retries=3)
# def grade_submission(self, submission_id: int) -> None:
#     """
#     Celery task: grade a student submission.

#     Phase 1 stub — Judge0 integration is wired in Ticket 5.1.
#     This task is enqueued immediately after a submission is created
#     so the queue infrastructure is validated end-to-end now.
#     """
#     logger.info("grade_submission task received: submission_id=%s", submission_id)
#     return {"submission_id": submission_id, "status": "queued"}
#     # TODO (Ticket 5.1): fetch submission from DB, call Judge0, store results


# app/tasks/grading.py
from __future__ import annotations

from sqlalchemy.orm import Session

from app.celery_app import celery_app
from app.db import SessionLocal
from app.models.models import Submission, GradingRun, SubmissionStatus, GradingRunStatus
from app.services.judge0_client import submit_code, poll_result


@celery_app.task
def grade_submission(submission_id: int):
    """
    Placeholder execution task:
    - marks submission running
    - runs code on Judge0 (no tests yet)
    - stores Judge0 output into GradingRun.feedback_summary["execution"]
    - updates status completed/failed
    """
    db: Session = SessionLocal()
    try:
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            return {"ok": False, "error": "Submission not found"}

        # Create grading run (placeholder)
        gr = GradingRun(
            submission_id=submission.id,
            status=GradingRunStatus.running.value,
        )
        db.add(gr)
        db.commit()
        db.refresh(gr)

        # Point submission to latest run and set running
        submission.latest_grading_run_id = gr.id
        submission.status = SubmissionStatus.running.value
        db.commit()

        # Execute on Judge0 (placeholder stdin None)
        token = submit_code(submission.code_text, stdin=None)
        result = poll_result(token)

        # Store safe execution result (no hidden test details)
        gr.status = GradingRunStatus.completed.value if result.get("status") != "failed" else GradingRunStatus.failed.value
        gr.feedback_summary = {
            "execution": result,
            "note": "Placeholder execution only. Grading logic not applied yet.",
        }

        # Placeholder scoring until grading logic:
        gr.io_score = 0
        gr.unit_score = 0
        gr.static_score = 0
        gr.score_total = 0

        if result.get("status") == "failed":
            gr.error_message = result.get("stderr") or "Execution failed"
            submission.status = SubmissionStatus.failed.value
        else:
            submission.status = SubmissionStatus.completed.value

        db.commit()
        db.refresh(gr)

        return {"ok": True, "submission_id": submission.id, "status": submission.status}

    except Exception as e:
        # Never crash the worker; mark failed if possible
        try:
            submission = db.query(Submission).filter(Submission.id == submission_id).first()
            if submission:
                submission.status = SubmissionStatus.failed.value
                db.commit()
        except Exception:
            pass
        return {"ok": False, "error": str(e)}

    finally:
        db.close()
