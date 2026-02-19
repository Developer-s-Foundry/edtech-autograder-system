import logging
import time

from app.celery_app import celery_app
from app.db import SessionLocal
from app.models.models import Submission, SubmissionStatus

logger = logging.getLogger(__name__)

@celery_app.task(name="app.tasks.grading.grade_submission", bind=True, max_retries=3)
def grade_submission(self, submission_id: int) -> None:
    """
    Celery task: grade a student submission.

    Phase 1 stub — Judge0 integration is wired in Ticket 5.1.
    This task is enqueued immediately after a submission is created
    so the queue infrastructure is validated end-to-end now.
    """
    logger.info("grade_submission task received: submission_id=%s", submission_id)
    db = SessionLocal()
    try:
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            logger.warning("Submission not found: submission_id=%s", submission_id)
            return

        submission.status = SubmissionStatus.running.value
        db.commit()
        logger.info("grade_submission execution start: submission_id=%s", submission_id)

        # Simulate processing (temporary stub until Judge0)
        time.sleep(1)

        submission.status = SubmissionStatus.completed.value
        db.commit()
    except Exception as exc:
        db.rollback()
        try:
            submission = db.query(Submission).filter(Submission.id == submission_id).first()
            if submission:
                submission.status = SubmissionStatus.failed.value
                db.commit()
        except Exception:
            db.rollback()
        logger.exception("grade_submission failed: submission_id=%s", submission_id)
        raise exc
    finally:
        db.close()
