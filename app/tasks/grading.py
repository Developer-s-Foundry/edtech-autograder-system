# # app/tasks/grading.py
from __future__ import annotations

import math
from typing import Optional

from sqlalchemy.orm import Session

from app.celery_app import celery_app
from app.db import SessionLocal
from app.models.models import (
    Assignment,
    IOTestCase,
    UnitTestSpec,
    Submission,
    GradingRun,
    TestCaseResult,
    SubmissionStatus,
    GradingRunStatus,
)
from app.services.judge0_client import submit_code, poll_result


def _normalize_output(s: Optional[str]) -> str:
    """
    Normalize stdout and expected output:
    - handle None
    - normalize line endings
    - strip surrounding whitespace
    """
    if not s:
        return ""
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    return s.strip()


def _seconds_to_ms(time_value) -> Optional[int]:
    """
    Judge0 often returns time as string seconds e.g. "0.012"
    """
    if time_value is None:
        return None
    try:
        sec = float(time_value)
        return int(math.floor(sec * 1000))
    except (ValueError, TypeError):
        return None


def _indent_asserts(assert_block: str) -> str:
    lines = (assert_block or "").strip().splitlines()
    cleaned = [ln.strip() for ln in lines if ln.strip()]
    if not cleaned:
        return "    pass"
    return "\n".join("    " + ln for ln in cleaned)

def _build_unit_harness(student_code: str, instructor_asserts: str) -> str:
    indented = _indent_asserts(instructor_asserts)

    # IMPORTANT: no f-strings in this template
    return (
        "globals()['__name__'] = '__unit_test__'\n"
        + student_code
        + "\n\n"
        + "def __run_unit_tests():\n"
        + indented
        + "\n\n"
        + "try:\n"
        + "    __run_unit_tests()\n"
        + "    print('UNIT_TESTS_PASSED')\n"
        + "except AssertionError:\n"
        + "    print('UNIT_TESTS_FAILED: AssertionError')\n"
        + "except Exception as e:\n"
        + "    print('UNIT_TESTS_FAILED: ' + type(e).__name__)\n"
    )


@celery_app.task
def grade_submission(submission_id: int):
    """
    Ticket 5.3 - IO grading only.

    For each IO test case:
    - execute student code with test stdin
    - poll until done or timeout
    - compare stdout to expected stdout (normalized)
    - store TestCaseResult
    - accumulate io_score
    """
    db: Session = SessionLocal()
    try:
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            return {"ok": False, "error": "Submission not found"}

        assignment = db.query(Assignment).filter(Assignment.id == submission.assignment_id).first()
        if not assignment:
            submission.status = SubmissionStatus.failed.value
            db.commit()
            return {"ok": False, "error": "Assignment not found"}

        # Create grading run
        gr = GradingRun(
            submission_id=submission.id,
            status=GradingRunStatus.running.value,
        )
        db.add(gr)
        db.commit()
        db.refresh(gr)

        # Link submission to latest run + mark running
        submission.latest_grading_run_id = gr.id
        submission.status = SubmissionStatus.running.value
        db.commit()

        # Fetch IO test cases for assignment (independent execution per case)
        test_cases = (
            db.query(IOTestCase)
            .filter(IOTestCase.assignment_id == assignment.id)
            .order_by(IOTestCase.order_index.asc(), IOTestCase.id.asc())
            .all()
        )

        total_points_possible = sum(tc.points for tc in test_cases)
        io_score = 0

        # Breakdown summary (do not expose expected outputs)
        visible_case_summaries = []
        hidden_total = 0
        hidden_passed = 0
        hidden_points_awarded = 0

        for tc in test_cases:
            stdin = tc.stdin if tc.stdin is not None else None

            token = None
            result = None

            try:
                token = submit_code(submission.code_text, stdin=stdin)
                result = poll_result(token)
            except Exception as e:
                # Controlled failure for this test only
                result = {
                    "stdout": "",
                    "stderr": f"Execution failed: {e}",
                    "status": "failed",
                    "time": None,
                    "memory": None,
                }

            student_stdout_raw = result.get("stdout") or ""
            student_stderr_raw = result.get("stderr") or ""
            exec_status = result.get("status") or "Unknown"

            student_stdout_norm = _normalize_output(student_stdout_raw)
            expected_norm = _normalize_output(tc.expected_stdout)

            passed = (exec_status != "failed") and (student_stdout_norm == expected_norm)
            points_awarded = tc.points if passed else 0

            # store per-test result
            tcr = TestCaseResult(
                grading_run_id=gr.id,
                io_test_case_id=tc.id,
                passed=passed,
                points_awarded=points_awarded,
                stdout=student_stdout_raw,
                stderr=student_stderr_raw,
                status=exec_status,
                time_ms=_seconds_to_ms(result.get("time")),
                memory_kb=result.get("memory"),
            )
            db.add(tcr)

            io_score += points_awarded

            # Summaries: hide hidden tests details
            if tc.is_hidden:
                hidden_total += 1
                if passed:
                    hidden_passed += 1
                hidden_points_awarded += points_awarded
            else:
                visible_case_summaries.append(
                    {
                        "test_case_id": tc.id,
                        "name": tc.name,
                        "passed": passed,
                        "points_awarded": points_awarded,
                        "status": exec_status,
                        "time_ms": _seconds_to_ms(result.get("time")),
                        "memory_kb": result.get("memory"),
                    }
                )

        # ---------------------------
        # UNIT TEST GRADING
        # ---------------------------

        unit_score = 0
        unit_summary = None

        unit_spec = (
            db.query(UnitTestSpec)
            .filter(UnitTestSpec.assignment_id == assignment.id)
            .first()
        )

        if unit_spec:

            harness_code = _build_unit_harness(
                submission.code_text,
                unit_spec.test_code
            )

            try:
                token = submit_code(harness_code)
                result = poll_result(token)

                stdout = (result.get("stdout") or "").strip()
                stderr = (result.get("stderr") or "").strip()
                status = result.get("status")

                execution_status = status.get("description") if isinstance(status, dict) else status

                passed = False
                failure_summary = None

                if "UNIT_TESTS_PASSED" in stdout:
                    passed = True
                    unit_score = unit_spec.points
                else:
                    passed = False

                    # Summarize failure safely
                    if "AssertionError" in stdout:
                        failure_summary = "Assertion failed"
                    elif "SyntaxError" in stderr:
                        failure_summary = "Syntax error"
                    elif stderr:
                        failure_summary = stderr.splitlines()[-1]
                    else:
                        failure_summary = "Unit tests failed"

                unit_summary = {
                    "passed": passed,
                    "points_awarded": unit_score,
                    "points_possible": unit_spec.points,
                    "execution_status": execution_status,
                    "failure_summary": failure_summary,
                }

            except Exception as e:
                unit_summary = {
                    "passed": False,
                    "points_awarded": 0,
                    "points_possible": unit_spec.points,
                    "execution_status": "error",
                    "failure_summary": "Execution error",
                }
                unit_score = 0        
        
        # Commit all test case results
        db.commit()

        # Update grading run scores (unit/static still placeholders)
        gr.io_score = io_score
        gr.unit_score = unit_score
        gr.static_score = 0
        gr.score_total = gr.io_score + gr.unit_score + gr.static_score

        # Store IO, Unit, and Static summary in grading run (safe, no expected output)
        gr.feedback_summary = {
            "io": {
                "io_score": io_score,
                "io_points_possible": total_points_possible,
                "total_tests": len(test_cases),
                "visible_tests": len(visible_case_summaries),
                "hidden_tests": hidden_total,
                "hidden_passed": hidden_passed,
                "hidden_points_awarded": hidden_points_awarded,
                "visible_breakdown": visible_case_summaries,
            },
            "unit": unit_summary,

            "note": "IO & UNIT grading complete. Static grading not enabled yet.",
        }

        gr.status = GradingRunStatus.completed.value
        submission.status = SubmissionStatus.completed.value

        db.commit()
        db.refresh(gr)

        return {
            "ok": True,
            "submission_id": submission.id,
            "io_score": io_score,
            "io_total_points_possible": total_points_possible,
            "unit_score": unit_score,
            "unit_total_points_possible": unit_spec.points,
            "static_score": 0,
            "total_score": io_score + unit_score + 0,
            "status": submission.status,
        }

    except Exception as e:
        # Do not crash worker. Mark failed.
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
