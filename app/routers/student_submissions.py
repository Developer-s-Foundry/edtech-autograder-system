import logging
import os

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies.auth import require_student
from app.models.models import Assignment, Submission, SubmissionStatus
from app.schemas.submission import SubmissionResponse
from app.tasks.grading import grade_submission

logger = logging.getLogger(__name__)

# 1 MB hard limit for uploaded .py files
MAX_FILE_SIZE_BYTES = 1_048_576

# Acceptable MIME types for Python source files.
# Browsers and OS file managers vary, so we allow the common variants.
ALLOWED_MIME_TYPES = {
    "text/x-python",
    "text/x-python-script",
    "text/plain",
    "application/x-python-code",
    "application/octet-stream",
}

router = APIRouter(
    prefix="/student/assignments",
    tags=["student-submissions"],
)


@router.post(
    "/{assignment_id}/submissions",
    response_model=SubmissionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_code(
    assignment_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    student=Depends(require_student),
):
    """
    Upload a .py solution file for a published assignment.

    Validation enforced:
    - Assignment must exist and be published.
    - File extension must be .py.
    - File MIME type must be a recognised Python content type.
    - File size must not exceed 1 MB.

    Security: file contents are stored as plain text and never executed locally.
    Only Judge0 executes student code (wired in Ticket 5.1).
    """
    # ------------------------------------------------------------------
    # 1. Validate assignment exists and is published
    # ------------------------------------------------------------------
    assignment = (
        db.query(Assignment)
        .filter(
            Assignment.id == assignment_id,
            Assignment.is_published == True,  # noqa: E712
        )
        .first()
    )
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found",
        )

    # ------------------------------------------------------------------
    # 2. Validate file extension
    # ------------------------------------------------------------------
    filename = file.filename or ""
    _, ext = os.path.splitext(filename)
    if ext.lower() != ".py":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only .py files are accepted",
        )

    # ------------------------------------------------------------------
    # 3. Validate MIME type
    # ------------------------------------------------------------------
    content_type = (file.content_type or "").split(";")[0].strip().lower()
    if content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid file type '{content_type}'. Only Python source files are accepted.",
        )

    # ------------------------------------------------------------------
    # 4. Read file and enforce size limit
    #    Read one extra byte so we can detect over-limit without reading
    #    the entire huge file into memory.
    # ------------------------------------------------------------------
    contents = await file.read(MAX_FILE_SIZE_BYTES + 1)
    if len(contents) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large. Maximum allowed size is 1 MB.",
        )

    # Decode as UTF-8 text; treat content as untrusted — never execute locally
    try:
        code_text = contents.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="File must be valid UTF-8 encoded text.",
        )

    # ------------------------------------------------------------------
    # 5. Persist submission record
    # ------------------------------------------------------------------
    submission = Submission(
        assignment_id=assignment_id,
        student_id=student.id,
        filename=filename,
        code_text=code_text,
        status=SubmissionStatus.queued.value,
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    logger.info(
        "Submission created: submission_id=%s student_id=%s assignment_id=%s",
        submission.id,
        student.id,
        assignment_id,
    )

    # ------------------------------------------------------------------
    # 6. Enqueue Celery grading task
    # ------------------------------------------------------------------
    grade_submission.delay(submission.id)

    logger.info("grade_submission task enqueued for submission_id=%s", submission.id)

    return SubmissionResponse(submission_id=submission.id, status=submission.status)
