from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


# ------------------------------------------------------------------
# Ticket 4.2 — used as the immediate upload response
# ------------------------------------------------------------------
class SubmissionResponse(BaseModel):
    submission_id: int
    status: str


# ------------------------------------------------------------------
# Ticket 4.3 — GET /student/submissions/{submission_id}
# ------------------------------------------------------------------
class SubmissionStatusOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    submission_id: int
    assignment_id: int
    filename: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime


# ------------------------------------------------------------------
# Ticket 4.3 — building blocks for the result endpoint
# ------------------------------------------------------------------
class TestCaseResultOut(BaseModel):
    """
    Per-IO-test result returned to students.

    Intentionally excludes IOTestCase.stdin and IOTestCase.expected_stdout
    so hidden test inputs and expected outputs are never exposed.
    """
    model_config = ConfigDict(from_attributes=True)

    io_test_case_id: int
    passed: bool
    points_awarded: int
    stdout: Optional[str]
    stderr: Optional[str]
    status: Optional[str]
    time_ms: Optional[int]
    memory_kb: Optional[int]


class StaticAnalysisOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    passed: bool
    violations: Optional[list[dict]]
    cyclomatic_complexity: Optional[int]


# ------------------------------------------------------------------
# Ticket 4.3 — GET /student/submissions/{submission_id}/result
# ------------------------------------------------------------------
class GradingResultOut(BaseModel):
    """
    Grading result returned to students.

    When status is queued or running only `submission_id` and `status`
    are populated. Full breakdown is only present when status == completed.
    """
    submission_id: int
    status: str

    # Populated only when status == "completed"
    score_total: Optional[int] = None
    io_score: Optional[int] = None
    unit_score: Optional[int] = None
    static_score: Optional[int] = None
    feedback_summary: Optional[dict] = None
    ai_feedback: Optional[str] = None
    io_results: Optional[list[TestCaseResultOut]] = None
    static_analysis: Optional[StaticAnalysisOut] = None
    finished_at: Optional[datetime] = None
