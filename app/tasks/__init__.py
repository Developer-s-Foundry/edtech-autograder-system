from app.tasks.grading import grade_submission  # noqa: F401 – registers task with Celery

__all__ = ["grade_submission"]
