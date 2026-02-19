# Student Submissions API Guide

This document covers the student code submission endpoint implemented in **Ticket 4.2 – Student: Submit Code (File Upload Only)** (EPIC 4 – Student Features).

---

## Overview

Students upload their Python solution as a `.py` file for a specific published assignment. The system:

1. Validates the uploaded file (extension, MIME type, size, encoding).
2. Stores the code as plain text in the database.
3. Creates a submission record with `status = queued`.
4. Enqueues a Celery grading task (`grade_submission`).

**Security guarantee:** The uploaded file is never executed locally. All code execution happens exclusively through the hosted Judge0 service (wired in Ticket 5.1).

---

## Prerequisites

### 1. Running Server

```bash
source venv/bin/activate
uvicorn app.main:app --reload
```

### 2. Running Celery Worker

```bash
source venv/bin/activate
celery -A app.celery_app.celery_app worker --loglevel=info --pool=solo
```

### 3. A Published Assignment

The assignment must exist and have `is_published = true`. Use the instructor endpoints to create and publish one, or refer to the seed data.

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

Copy the `access_token` from the response.

---

## Endpoint

### POST `/student/assignments/{assignment_id}/submissions`

Submit a `.py` solution file for a published assignment.

**Content-Type:** `multipart/form-data`

**Path Parameter:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `assignment_id` | integer | ID of the published assignment to submit to |

**Form Field:**

| Field | Type | Description |
|-------|------|-------------|
| `file` | file | The `.py` source file to upload |

**Request:**

```bash
curl -s -X POST http://127.0.0.1:8000/student/assignments/1/submissions \
  -H "Authorization: Bearer <access_token>" \
  -F "file=@solution.py" \
  | python -m json.tool
```

**Success Response (201):**

```json
{
  "submission_id": 1,
  "status": "queued"
}
```

**Error Responses:**

| Status | Reason |
|--------|--------|
| 401 | Missing, invalid, or expired token |
| 403 | Authenticated user is not a student |
| 404 | Assignment does not exist or is not published |
| 413 | File exceeds the 1 MB size limit |
| 422 | File extension is not `.py` |
| 422 | File MIME type is not a recognised Python type |
| 422 | File content is not valid UTF-8 text |

---

## Validation Rules

Validations are applied in this order:

| Order | Rule | Error Returned |
|-------|------|----------------|
| 1 | Assignment exists and `is_published = true` | 404 Not Found |
| 2 | File extension is `.py` | 422 Unprocessable Entity |
| 3 | File MIME type is a recognised Python type | 422 Unprocessable Entity |
| 4 | File size does not exceed 1 MB (1,048,576 bytes) | 413 Request Entity Too Large |
| 5 | File content decodes as valid UTF-8 | 422 Unprocessable Entity |

### Accepted MIME Types

Browsers and operating systems report varying MIME types for `.py` files. The following are accepted:

| MIME Type | Source |
|-----------|--------|
| `text/x-python` | Standard Python MIME type |
| `text/x-python-script` | Variant used by some editors |
| `text/plain` | Reported by some browsers/OS |
| `application/x-python-code` | Alternate registration |
| `application/octet-stream` | Generic binary fallback used by many file managers |

The file extension (`.py`) is the primary enforcement gate. The MIME type check provides a secondary layer to reject clearly incorrect file types (e.g. `image/jpeg`, `application/zip`).

---

## Submission Lifecycle

After a successful upload, the submission progresses through the following states:

```
queued → running → completed
                 ↘ failed
```

| Status | Meaning |
|--------|---------|
| `queued` | Submission stored, Celery task enqueued, waiting for a worker |
| `running` | Grading worker has picked up the task and is calling Judge0 |
| `completed` | Grading finished successfully, results available |
| `failed` | Grading encountered an unrecoverable error |

> **Note:** The grading worker (Judge0 integration) is implemented in Ticket 5.1. In the current phase, the Celery task is enqueued and logged but does not yet call Judge0.

---

## Full Testing Flow

### Step 1 — Prepare a published assignment

```bash
# Login as instructor
INSTRUCTOR_TOKEN=$(curl -s -X POST http://127.0.0.1:8000/auth/login \
  -d "username=instructor.demo@autograder.local&password=demo_password_123" \
  | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Create and publish an assignment
curl -s -X POST http://127.0.0.1:8000/instructor/assignments \
  -H "Authorization: Bearer $INSTRUCTOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Hello World",
    "description": "Print Hello, World!",
    "language": "python",
    "is_published": true,
    "weight_io": 70,
    "weight_unit": 20,
    "weight_static": 10
  }' | python -m json.tool
```

Note the `id` from the response (e.g. `1`).

### Step 2 — Create a valid solution file

```bash
echo 'print("Hello, World!")' > solution.py
```

### Step 3 — Login as student and submit

```bash
STUDENT_TOKEN=$(curl -s -X POST http://127.0.0.1:8000/auth/login \
  -d "username=student1.demo@autograder.local&password=demo_password_123" \
  | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -s -X POST http://127.0.0.1:8000/student/assignments/1/submissions \
  -H "Authorization: Bearer $STUDENT_TOKEN" \
  -F "file=@solution.py" \
  | python -m json.tool
```

**Expected:**

```json
{
  "submission_id": 1,
  "status": "queued"
}
```

Verify in the Celery worker logs that a `grade_submission` task was received.

### Step 4 — Verify invalid file rejections

**Wrong extension (.txt):**

```bash
echo 'print("hello")' > solution.txt
curl -s -X POST http://127.0.0.1:8000/student/assignments/1/submissions \
  -H "Authorization: Bearer $STUDENT_TOKEN" \
  -F "file=@solution.txt"
# Expected: 422 — Only .py files are accepted
```

**Wrong extension (.js):**

```bash
echo 'console.log("hello")' > solution.js
curl -s -X POST http://127.0.0.1:8000/student/assignments/1/submissions \
  -H "Authorization: Bearer $STUDENT_TOKEN" \
  -F "file=@solution.js"
# Expected: 422 — Only .py files are accepted
```

**File too large (over 1 MB):**

```bash
python -c "print('x = 1  ' * 200000)" > big.py
curl -s -X POST http://127.0.0.1:8000/student/assignments/1/submissions \
  -H "Authorization: Bearer $STUDENT_TOKEN" \
  -F "file=@big.py"
# Expected: 413 — File too large. Maximum allowed size is 1 MB.
```

### Step 5 — Verify unpublished assignment is rejected

```bash
# Create an unpublished assignment
curl -s -X POST http://127.0.0.1:8000/instructor/assignments \
  -H "Authorization: Bearer $INSTRUCTOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Draft Assignment",
    "description": "Not published yet",
    "language": "python",
    "is_published": false,
    "weight_io": 70,
    "weight_unit": 20,
    "weight_static": 10
  }' | python -m json.tool
# Note the id, e.g. 2

curl -s -X POST http://127.0.0.1:8000/student/assignments/2/submissions \
  -H "Authorization: Bearer $STUDENT_TOKEN" \
  -F "file=@solution.py"
# Expected: 404 — Assignment not found
```

### Step 6 — Verify role enforcement

```bash
# Instructor token must not access student submission endpoint
curl -s -X POST http://127.0.0.1:8000/student/assignments/1/submissions \
  -H "Authorization: Bearer $INSTRUCTOR_TOKEN" \
  -F "file=@solution.py"
# Expected: 403 Forbidden

# No token
curl -s -X POST http://127.0.0.1:8000/student/assignments/1/submissions \
  -F "file=@solution.py"
# Expected: 401 Unauthorized
```

---

## Using Swagger UI

1. Open `http://127.0.0.1:8000/docs` in your browser.
2. Log in via **POST /auth/login** and copy the `access_token`.
3. Click **Authorize** (top right), paste the token, and click **Authorize**.
4. Use **POST /student/assignments/{assignment_id}/submissions**.
5. Click **Try it out**, enter the `assignment_id`, upload a `.py` file using the file picker, and click **Execute**.

---

## Files Changed

| File | Change |
|------|--------|
| `app/schemas/submission.py` | New — `SubmissionResponse` schema |
| `app/tasks/grading.py` | New — `grade_submission` Celery task stub |
| `app/tasks/__init__.py` | Updated — imports grading task for Celery autodiscovery |
| `app/routers/student_submissions.py` | New — submission upload endpoint |
| `app/main.py` | Updated — registered `student_submissions_router` |
