Postman testing plan for Celery and grading task changes

What you are verifying

API: Submit .py file returns immediately with 201 and status: "queued" (no blocking).
Enqueue: Celery task is enqueued (worker must be running to consume it).
Status lifecycle: Submission status moves queued → running → completed (visible via GET submission status).

Auth: Student JWT is required for submit and for GET submission/result.

Prerequisites

Services running

FastAPI: e.g. uvicorn app.main:app --reload (default base URL: http://127.0.0.1:8000 or http://localhost:8000).
Celery worker: celery -A app.celery_app worker --loglevel=info.



Redis: available at CELERY_BROKER_URL (and Postgres/DB as usual).



Data

At least one student user (role student).
At least one published assignment (so POST .../submissions is allowed).
A valid .py file on disk (e.g. a one-line print("hello") script) for upload.



Postman

Base URL: set a collection or environment variable base_url (e.g. http://127.0.0.1:8000).
Auth: you will store access_token after login and use it as Bearer token for student endpoints.


Postman collection structure
Use one folder (e.g. “Celery / Grading flow”) with the requests below in order. Use collection or environment variables: base_url, access_token, assignment_id, submission_id.



1. Login (student)

Purpose: Obtain JWT for student so submit and GET submission/result are authorized.

Method: POST
URL: {{base_url}}/auth/login
Body: form-data

username: student email (e.g. student@example.com) — OAuth2 form uses username for email.
password: student password.

Expected response: 200 OK
Body example: { "access_token": "<jwt>", "refresh_token": "<jwt>", "token_type": "bearer" }.

Postman: In a Test script, save the access token, e.g.
pm.collectionVariables.set("access_token", pm.response.json().access_token);
Use it in subsequent requests: Authorization → Bearer Token → {{access_token}}.



2. Submit .py file (trigger grading task)

Purpose: Create a submission and enqueue grade_submission; API must return immediately with status: "queued".





Method: POST



URL: {{base_url}}/student/assignments/{{assignment_id}}/submissions



Headers: Authorization: Bearer {{access_token}}



Body: form-data





Key: file (type: File).



Value: select a valid .py file from your machine.

Expected response: 201 Created
Body: { "submission_id": <int>, "status": "queued" }.

Postman: In Tests, save submission_id for the next requests, e.g.
pm.collectionVariables.set("submission_id", pm.response.json().submission_id);

Acceptance: Response returns in a short time (no long wait). Status in body is "queued". If the Celery worker is running, it will pick up the task within a few seconds.



3. Get submission status (right after submit)

Purpose: Confirm the submission was stored and is still queued (or already running if worker is very fast).


Method: GET
URL: {{base_url}}/student/submissions/{{submission_id}}



Headers: Authorization: Bearer {{access_token}}

Expected response: 200 OK
Body includes: submission_id, assignment_id, filename, status, created_at, updated_at.
status should be one of: "queued", "running", or "completed" (if worker already finished).



4. Get submission status again (after ~2 seconds)

Purpose: Confirm status transition. The grading task sets running, then time.sleep(1), then completed. So after 1–2 seconds, status should be "completed" (with worker running).


Method: GET

URL: {{base_url}}/student/submissions/{{submission_id}}
Headers: Authorization: Bearer {{access_token}}

Expected response: 200 OK
status: "completed" (with Celery worker running and no errors). If you run this request immediately after request 3, you may still see "running"; send again after a short delay.

Optional: Add a Postman “Wait” or run request 4 two times with a 1–2 second pause (e.g. manually or via a simple script) to observe running → completed.



5. Get submission result (optional)

Purpose: For completed (or failed) submissions, the result endpoint returns the grading view (skeleton does not fill full result yet).



Method: GET
URL: {{base_url}}/student/submissions/{{submission_id}}/result


Headers: Authorization: Bearer {{access_token}}

Expected response: 200 OK for completed/failed submissions; body structure per app/routers/student_results.py and app/schemas/submission.py (status, score, feedback, etc.). Skeleton may return minimal data until Judge0 is wired.

Environment / variables checklist


Variable

Example / note

base_url

http://127.0.0.1:8000

access_token

Set from Login response (Test script)
assignment_id

ID of a published assignment (set manually or from GET student assignments)

submission_id



Set from Submit response (Test script)



Optional: GET published assignments

If you do not know assignment_id, add a request before “Submit .py file”:





Method: GET



URL: {{base_url}}/student/assignments



Headers: Authorization: Bearer {{access_token}}

Use an ID from the list (only published assignments appear). Set assignment_id in the environment or use it in the submit URL.



Negative / validation cases (optional)





Submit without token: POST .../submissions without Authorization → expect 401.



Submit with wrong assignment ID: Use a non-existent or unpublished assignment ID → expect 404 or 404 as per your API.



Submit non-.py file: Upload a .txt or other file → expect 422 (only .py accepted).



GET submission status for another student’s submission: Use a submission_id that belongs to a different student → expect 403.



Verifying Celery worker (outside Postman)





Worker logs: In the terminal where the Celery worker is running, you should see:





Task received for grade_submission.



Log line for “execution start” (from app/tasks/grading.py).



Redis: Celery connects via CELERY_BROKER_URL; if the worker starts without broker errors, the connection is fine.



DB: After the flow, the submission row should have status = 'completed' (or 'failed' if the task raised).



Summary flow

sequenceDiagram
  participant Postman
  participant API
  participant Redis
  participant Worker

  Postman->>API: 1. POST /auth/login
  API->>Postman: access_token
  Postman->>API: 2. POST .../submissions (file)
  API->>Redis: enqueue grade_submission(id)
  API->>Postman: 201 submission_id, status=queued
  Postman->>API: 3. GET .../submissions/{id}
  API->>Postman: status queued or running
  Worker->>Redis: pull task
  Worker->>Worker: run, set running, sleep, set completed
  Postman->>API: 4. GET .../submissions/{id} (after delay)
  API->>Postman: status completed

No edits to the codebase are required; this is a testing plan only. You can implement it as a Postman Collection (and optionally an Environment) with the requests and variables above.