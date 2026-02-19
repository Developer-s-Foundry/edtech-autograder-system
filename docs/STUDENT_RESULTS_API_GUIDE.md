# Student Results API Guide

This document covers the submission status and grading result endpoints implemented in **Ticket 4.3 – Student: Retrieve Submission Status & Results** (EPIC 4 – Student Features).

---

## Overview

After submitting code (Ticket 4.2), students can:

1. **Poll submission status** — check whether grading is queued, running, completed, or failed.
2. **Retrieve full grading results** — once grading completes, view score breakdown, IO test results, static analysis, and feedback.

Access control is strict:
- Only the student who created the submission may view it.
- Hidden test case inputs and expected outputs are **never** exposed.
- Internal Judge0 tokens are **never** exposed.

---

## Prerequisites

### 1. Running Server

```bash
source venv/bin/activate
uvicorn app.main:app --reload
```

### 2. An Existing Submission

Follow the flow in [STUDENT_SUBMISSIONS_API_GUIDE.md](./STUDENT_SUBMISSIONS_API_GUIDE.md) to create a submission first. Note the `submission_id` returned.

---

## Authentication

All endpoints require a valid student JWT access token:

```
Authorization: Bearer <access_token>
```

Log in as a student to obtain a token:

```bash
curl -s -X POST http://127.0.0.1:8000/auth/login \
  -d "username=student1.demo@autograder.local&password=demo_password_123" \
  | python -m json.tool
```

---

## Endpoints

### GET `/student/submissions/{submission_id}`

Retrieve submission metadata and current status.

**Request:**

```bash
curl -s http://127.0.0.1:8000/student/submissions/1 \
  -H "Authorization: Bearer <access_token>" \
  | python -m json.tool
```

**Success Response (200):**

```json
{
  "submission_id": 1,
  "assignment_id": 1,
  "filename": "solution.py",
  "status": "queued",
  "created_at": "2026-02-19T10:00:00+00:00",
  "updated_at": "2026-02-19T10:00:00+00:00"
}
```

**Error Responses:**

| Status | Reason |
|--------|--------|
| 401 | Missing, invalid, or expired token |
| 403 | Authenticated user is not a student |
| 403 | Submission belongs to a different student |
| 404 | Submission does not exist |

---

### GET `/student/submissions/{submission_id}/result`

Retrieve grading results for a submission.

Response content depends on the current submission status:

- **`queued` / `running`** — returns status only (grading not yet finished).
- **`completed` / `failed`** — returns full score breakdown, IO test results, static analysis, and feedback.

**Request:**

```bash
curl -s http://127.0.0.1:8000/student/submissions/1/result \
  -H "Authorization: Bearer <access_token>" \
  | python -m json.tool
```

**Response when queued or running (200):**

```json
{
  "submission_id": 1,
  "status": "queued"
}
```

**Response when completed (200):**

```json
{
  "submission_id": 1,
  "status": "completed",
  "score_total": 85,
  "io_score": 60,
  "unit_score": 15,
  "static_score": 10,
  "feedback_summary": {
    "io": "Passed 6 of 8 test cases.",
    "unit": "All unit tests passed.",
    "static": "No violations found."
  },
  "ai_feedback": "Good overall structure. Consider handling edge cases for empty input.",
  "io_results": [
    {
      "io_test_case_id": 1,
      "passed": true,
      "points_awarded": 10,
      "stdout": "Hello, World!\n",
      "stderr": null,
      "status": "Accepted",
      "time_ms": 42,
      "memory_kb": 8192
    },
    {
      "io_test_case_id": 2,
      "passed": false,
      "points_awarded": 0,
      "stdout": "",
      "stderr": "IndexError: list index out of range",
      "status": "Runtime Error",
      "time_ms": 38,
      "memory_kb": 8100
    }
  ],
  "static_analysis": {
    "passed": true,
    "violations": [],
    "cyclomatic_complexity": 3
  },
  "finished_at": "2026-02-19T10:01:05+00:00"
}
```

**Error Responses:**

| Status | Reason |
|--------|--------|
| 401 | Missing, invalid, or expired token |
| 403 | Authenticated user is not a student |
| 403 | Submission belongs to a different student |
| 404 | Submission does not exist |

---

## Response Fields Reference

### `GET /student/submissions/{submission_id}`

| Field | Type | Description |
|-------|------|-------------|
| `submission_id` | integer | Unique submission identifier |
| `assignment_id` | integer | Assignment this submission belongs to |
| `filename` | string \| null | Uploaded filename |
| `status` | string | Current status (`queued`, `running`, `completed`, `failed`) |
| `created_at` | datetime | When the submission was created (ISO 8601, UTC) |
| `updated_at` | datetime | When the submission was last updated (ISO 8601, UTC) |

### `GET /student/submissions/{submission_id}/result`

**Top-level:**

| Field | Type | Present when |
|-------|------|-------------|
| `submission_id` | integer | Always |
| `status` | string | Always |
| `score_total` | integer | `completed` or `failed` |
| `io_score` | integer | `completed` or `failed` |
| `unit_score` | integer | `completed` or `failed` |
| `static_score` | integer | `completed` or `failed` |
| `feedback_summary` | object \| null | `completed` or `failed` |
| `ai_feedback` | string \| null | `completed` or `failed` |
| `io_results` | array | `completed` or `failed` |
| `static_analysis` | object \| null | `completed` or `failed` |
| `finished_at` | datetime \| null | `completed` or `failed` |

**`io_results` items:**

| Field | Type | Description |
|-------|------|-------------|
| `io_test_case_id` | integer | Test case identifier |
| `passed` | boolean | Whether the test case passed |
| `points_awarded` | integer | Points scored for this test case |
| `stdout` | string \| null | Student code's actual output |
| `stderr` | string \| null | Error output (if any) |
| `status` | string \| null | Judge0 status (e.g. `Accepted`, `Runtime Error`, `Time Limit Exceeded`) |
| `time_ms` | integer \| null | Execution time in milliseconds |
| `memory_kb` | integer \| null | Peak memory usage in kilobytes |

**`static_analysis` object:**

| Field | Type | Description |
|-------|------|-------------|
| `passed` | boolean | Whether all static rules were satisfied |
| `violations` | array \| null | List of rule violations (if any) |
| `cyclomatic_complexity` | integer \| null | Measured cyclomatic complexity |

### Fields Intentionally Excluded

| Field | Reason |
|-------|--------|
| `IOTestCase.stdin` | Hidden test input — exposing it would allow cheating |
| `IOTestCase.expected_stdout` | Hidden expected output — same reason |
| `GradingRun.judge0_io_tokens` | Internal Judge0 submission tokens |
| `GradingRun.judge0_unit_token` | Internal Judge0 submission token |
| `UnitTestSpec.test_code` | Hidden unit test assertions |
| `code_text` | Student's own code is not echoed back |

---

## Submission Status Reference

| Status | Meaning |
|--------|---------|
| `queued` | Celery task enqueued, waiting for a worker to pick it up |
| `running` | Grading worker is actively calling Judge0 |
| `completed` | Grading finished, full results available |
| `failed` | Grading encountered an unrecoverable error |

Poll `GET /student/submissions/{id}` to track progress. When status becomes `completed` or `failed`, call `/result` for the full breakdown.

---

## Full Testing Flow

### Step 1 — Submit a solution and note the submission ID

```bash
STUDENT_TOKEN=$(curl -s -X POST http://127.0.0.1:8000/auth/login \
  -d "username=student1.demo@autograder.local&password=demo_password_123" \
  | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

echo 'print("Hello, World!")' > solution.py

SUBMISSION_ID=$(curl -s -X POST http://127.0.0.1:8000/student/assignments/1/submissions \
  -H "Authorization: Bearer $STUDENT_TOKEN" \
  -F "file=@solution.py" \
  | python -c "import sys,json; print(json.load(sys.stdin)['submission_id'])")

echo "Submission ID: $SUBMISSION_ID"
```

### Step 2 — Immediately check status (expect queued)

```bash
curl -s http://127.0.0.1:8000/student/submissions/$SUBMISSION_ID \
  -H "Authorization: Bearer $STUDENT_TOKEN" \
  | python -m json.tool
# Expected: { "status": "queued", ... }
```

### Step 3 — Check result while queued (expect status only)

```bash
curl -s http://127.0.0.1:8000/student/submissions/$SUBMISSION_ID/result \
  -H "Authorization: Bearer $STUDENT_TOKEN" \
  | python -m json.tool
# Expected: { "submission_id": ..., "status": "queued" }
```

### Step 4 — After grading completes, retrieve full results

```bash
curl -s http://127.0.0.1:8000/student/submissions/$SUBMISSION_ID/result \
  -H "Authorization: Bearer $STUDENT_TOKEN" \
  | python -m json.tool
# Expected: full breakdown with score_total, io_results, static_analysis, etc.
```

### Step 5 — Attempt to access another student's submission (expect 403)

```bash
# Login as a second student
STUDENT2_TOKEN=$(curl -s -X POST http://127.0.0.1:8000/auth/login \
  -d "username=student2.demo@autograder.local&password=demo_password_123" \
  | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -s http://127.0.0.1:8000/student/submissions/$SUBMISSION_ID \
  -H "Authorization: Bearer $STUDENT2_TOKEN"
# Expected: 403 — You do not have access to this submission

curl -s http://127.0.0.1:8000/student/submissions/$SUBMISSION_ID/result \
  -H "Authorization: Bearer $STUDENT2_TOKEN"
# Expected: 403 — You do not have access to this submission
```

### Step 6 — Access a non-existent submission (expect 404)

```bash
curl -s http://127.0.0.1:8000/student/submissions/99999 \
  -H "Authorization: Bearer $STUDENT_TOKEN"
# Expected: 404 — Submission not found
```

### Step 7 — Verify role enforcement

```bash
INSTRUCTOR_TOKEN=$(curl -s -X POST http://127.0.0.1:8000/auth/login \
  -d "username=instructor.demo@autograder.local&password=demo_password_123" \
  | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -s http://127.0.0.1:8000/student/submissions/$SUBMISSION_ID \
  -H "Authorization: Bearer $INSTRUCTOR_TOKEN"
# Expected: 403 Forbidden (role is not student)
```

---

## Using Swagger UI

1. Open `http://127.0.0.1:8000/docs` in your browser.
2. Log in via **POST /auth/login** and copy the `access_token`.
3. Click **Authorize** (top right), paste the token, and click **Authorize**.
4. Use **GET /student/submissions/{submission_id}** to check status.
5. Use **GET /student/submissions/{submission_id}/result** for the full breakdown.

---

## Files Changed

| File | Change |
|------|--------|
| `app/schemas/submission.py` | Added `SubmissionStatusOut`, `TestCaseResultOut`, `StaticAnalysisOut`, `GradingResultOut` |
| `app/routers/student_results.py` | New — status and result endpoints |
| `app/main.py` | Updated — registered `student_results_router` |
