import logging

from app.celery_app import celery_app

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
    # TODO (Ticket 5.1): fetch submission from DB, call Judge0, store results
