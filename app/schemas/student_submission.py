from pydantic import BaseModel
from typing import Optional, Any


class StudentSubmissionOut(BaseModel):
    submission_id: int
    assignment_id: int
    status: str
    created_at: Optional[str] = None  # keep simple; can change to datetime if you want
    filename: Optional[str] = None


class StudentSubmissionResultOut(BaseModel):
    submission_id: int
    status: str

    # only present when completed
    score_total: Optional[int] = None
    io_score: Optional[int] = None
    unit_score: Optional[int] = None
    static_score: Optional[int] = None
    unit_total_points: int = 0
    unit_assert_count: int = 0

    feedback_summary: Optional[Any] = None
    ai_feedback: Optional[str] = None

    # optional failure info, only if failed
    error_message: Optional[str] = None
