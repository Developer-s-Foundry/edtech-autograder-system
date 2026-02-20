# Student Assignments API Guide

This document covers the student-facing assignment endpoints implemented in **Ticket 4.1 – Student: List & View Published Assignments** (EPIC 4 – Student Features).

---

## Overview

Students can view assignments that have been explicitly published by an instructor. The API enforces the following rules:

- Only assignments where `is_published = true` are returned.
- Only authenticated users with role `student` may access these endpoints.
- Responses never include internal test case definitions (IO test cases, unit test specs, static rules) or internal tuning parameters.

---

## Prerequisites

### 1. Running Server

```bash
source venv/bin/activate
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.
Swagger UI is at `http://127.0.0.1:8000/docs`.

### 2. A Published Assignment

These endpoints only return published assignments. Use the instructor endpoints or seed data to create and publish an assignment first.

---

## Authentication

All endpoints require a valid student JWT access token in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

To obtain a token, log in as a student:

```bash
curl -s -X POST http://127.0.0.1:8000/auth/login \
  -d "username=student1.demo@autograder.local&password=demo_password_123" \
  | python -m json.tool
```


Copy the `access_token` from the response.

---

## Endpoints

### GET `/student/assignments`

List all published assignments.

**Request:**

```bash
curl -s http://127.0.0.1:8000/student/assignments \
  -H "Authorization: Bearer <access_token>" \
  | python -m json.tool
```

**Success Response (200):**

```json
[
  {
    "id": 1,
    "title": "Hello World",
    "description": "Write a program that prints Hello, World!",
    "instructions": "Use a print statement.",
    "language": "python",
    "weight_io": 70,
    "weight_unit": 20,
    "weight_static": 10,
    "created_at": "2026-02-18T10:00:00+00:00",
    "updated_at": "2026-02-18T10:00:00+00:00"
  }
]
```

Returns an empty array `[]` if no assignments are currently published.

**Error Responses:**

| Status | Reason |
|--------|--------|
| 401 | Missing, invalid, or expired token |
| 403 | Authenticated user is not a student |

---

### GET `/student/assignments/{assignment_id}`

Retrieve full metadata for a single published assignment.

**Request:**

```bash
curl -s http://127.0.0.1:8000/student/assignments/1 \
  -H "Authorization: Bearer <access_token>" \
  | python -m json.tool
```

**Path Parameter:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `assignment_id` | integer | The ID of the assignment to retrieve |

**Success Response (200):**

```json
{
  "id": 1,
  "title": "Hello World",
  "description": "Write a program that prints Hello, World!",
  "instructions": "Use a print statement.",
  "language": "python",
  "weight_io": 70,
  "weight_unit": 20,
  "weight_static": 10,
  "created_at": "2026-02-18T10:00:00+00:00",
  "updated_at": "2026-02-18T10:00:00+00:00"
}
```

**Error Responses:**

| Status | Reason |
|--------|--------|
| 401 | Missing, invalid, or expired token |
| 403 | Authenticated user is not a student |
| 404 | Assignment does not exist or is not published |

---

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Unique assignment identifier |
| `title` | string | Assignment title |
| `description` | string | High-level description of the task |
| `instructions` | string \| null | Detailed instructions (may be null) |
| `language` | string | Programming language (e.g. `"python"`) |
| `weight_io` | integer | Percentage weight for IO test grading |
| `weight_unit` | integer | Percentage weight for unit test grading |
| `weight_static` | integer | Percentage weight for static analysis grading |
| `created_at` | datetime | When the assignment was created (ISO 8601, UTC) |
| `updated_at` | datetime | When the assignment was last updated (ISO 8601, UTC) |

### Fields Intentionally Excluded

The following fields are present on the assignment model but are **never** returned to students:

| Field | Reason |
|-------|--------|
| `instructor_id` | Internal ownership metadata |
| `is_published` | Internal state flag |
| `max_runtime_ms` | Internal execution limit |
| `max_memory_kb` | Internal memory limit |
| IO test cases | Exposing expected outputs would allow cheating |
| Unit test specs | Contains test code students must not see |
| Static rule definitions | Internal grading rules |

---

## Full Testing Flow

This matches the acceptance criteria in Ticket 4.1.

### Step 1 — Log in as instructor and create an unpublished assignment

```bash
# Login as instructor
INSTRUCTOR_TOKEN=$(curl -s -X POST http://127.0.0.1:8000/auth/login \
  -d "username=instructor.demo@autograder.local&password=demo_password_123" \
  | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Create an unpublished assignment
curl -s -X POST http://127.0.0.1:8000/instructor/assignments \
  -H "Authorization: Bearer $INSTRUCTOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Ticket 4.1 Test Assignment",
    "description": "A test assignment for Ticket 4.1 verification.",
    "language": "python",
    "is_published": false,
    "weight_io": 70,
    "weight_unit": 20,
    "weight_static": 10
  }' | python -m json.tool
```

Note the `id` from the response (e.g. `1`).

### Step 2 — Log in as student and list assignments

```bash
STUDENT_TOKEN=$(curl -s -X POST http://127.0.0.1:8000/auth/login \
  -d "username=student1.demo@autograder.local&password=demo_password_123" \
  | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -s http://127.0.0.1:8000/student/assignments \
  -H "Authorization: Bearer $STUDENT_TOKEN" \
  | python -m json.tool
```

**Expected:** The unpublished assignment does **not** appear in the list.

### Step 3 — Attempt to fetch the unpublished assignment directly

```bash
curl -s http://127.0.0.1:8000/student/assignments/1 \
  -H "Authorization: Bearer $STUDENT_TOKEN"
# Expected: 404 Not Found
```

### Step 4 — Publish the assignment as instructor

```bash
curl -s -X PUT http://127.0.0.1:8000/instructor/assignments/1 \
  -H "Authorization: Bearer $INSTRUCTOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "is_published": true,
    "weight_io": 70,
    "weight_unit": 20,
    "weight_static": 10
  }' | python -m json.tool
```

### Step 5 — List assignments again as student

```bash
curl -s http://127.0.0.1:8000/student/assignments \
  -H "Authorization: Bearer $STUDENT_TOKEN" \
  | python -m json.tool
```

**Expected:** The assignment now appears in the list.

### Step 6 — Fetch the assignment detail

```bash
curl -s http://127.0.0.1:8000/student/assignments/1 \
  -H "Authorization: Bearer $STUDENT_TOKEN" \
  | python -m json.tool
```

**Expected:** Full assignment metadata returned, no test case data visible.

### Step 7 — Verify role enforcement

```bash
# Instructor token must not access student endpoints
curl -s http://127.0.0.1:8000/student/assignments \
  -H "Authorization: Bearer $INSTRUCTOR_TOKEN"
# Expected: 403 Forbidden

# No token
curl -s http://127.0.0.1:8000/student/assignments
# Expected: 401 Unauthorized
```

---

## Using Swagger UI

1. Open `http://127.0.0.1:8000/docs` in your browser.
2. Log in via **POST /auth/login** and copy the `access_token`.
3. Click **Authorize** (top right), paste the token, and click **Authorize**.
4. Use **GET /student/assignments** and **GET /student/assignments/{assignment_id}** to test interactively.

---

## Files Changed

| File | Change |
|------|--------|
| `app/schemas/assignment.py` | Added `StudentAssignmentOut` schema |
| `app/routers/student_assignments.py` | New router with list and detail endpoints |
| `app/main.py` | Registered `student_assignments_router` |
