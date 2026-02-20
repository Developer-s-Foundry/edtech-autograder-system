# EdTech Autograder System - API Test README (curl)

This README contains copy-paste `curl` commands to verify all API
endpoints implemented so far.

------------------------------------------------------------------------

## 1) Run Services

### Terminal 1 - API
```
uvicorn app.main:app --reload
```

### Terminal 2 - Celery Worker
```
celery -A app.celery_app.celery_app worker --loglevel=info --pool=solo
```
------------------------------------------------------------------------

## 2) Set Base URL
```
export BASE_URL="http://127.0.0.1:8000"
```
------------------------------------------------------------------------

## 3) Register Instructor

```
POST /auth/register
```
```
curl -X POST "$BASE_URL/auth/register"\ -H "Content-Type: application/json" \
-d '{ "email":"instructor1@example.com", "password":"Pass12345!",
"full_name":"Instructor One", "role":"instructor" }'
```
------------------------------------------------------------------------

## 4) Register Student
```
POST /auth/register
```
```
curl -X POST "$BASE_URL/auth/register" \
-H "Content-Type: application/json" \
-d '{ "email":"student2@example.com", "password":"Pass12345!",
"full_name":"Student One", "role":"student" }'
```
------------------------------------------------------------------------

## 5) Login Instructor
```
POST /auth/login
```
```
export INSTRUCTOR_TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
-H "Content-Type: application/x-www-form-urlencoded" \
-d "username=instructor1@example.com&password=Pass12345!" \
\| python -c "import sys, json;
print(json.load(sys.stdin).get('access_token',''))")
```
------------------------------------------------------------------------

## 6) Create Assignment
```
POST /instructor/assignments
```
```
export
ASSIGNMENT_ID=$(curl -s -X POST "$BASE_URL/instructor/assignments" \
-H "Authorization: Bearer \$INSTRUCTOR_TOKEN" \
-H "Content-Type: application/json" \
-d '{ 
    "title":"Multiply Two Numbers", 
    "description":"Write solve(a,b) to return a\*b.", 
    "instructions":"Implement solve(a, b).",
    "language":"python", 
    "is_published": false, 
    "weight_io": 70,
    "weight_unit": 20, 
    "weight_static": 10, 
    "max_runtime_ms": 2000,
    "max_memory_kb": 128000 }' \| python -c "import sys, json;
print(json.load(sys.stdin)\['id'\])")
```
------------------------------------------------------------------------

## 7) Edit assignment
```
PUT /instructor/assignments/{id}
```
```
curl -s -X PUT "$BASE_URL/instructor/assignments/$ASSIGNMENT_ID" \
  -H "Authorization: Bearer $INSTRUCTOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title":"Guessing Game v2",
    "description":"Updated description.",
    "instructions":"Updated instructions.",
    "language":"python",
    "is_published": false,
    "weight_io": 70,
    "weight_unit": 20,
    "weight_static": 10,
    "max_runtime_ms": 2000,
    "max_memory_kb": 128000
  }'
```
------------------------------------------------------------------------

## 8) Add IO test case
```
POST /instructor/assignments/{assignment_id}/io-tests
```
```
curl -s -X POST "$BASE_URL/instructor/assignments/$ASSIGNMENT_ID/io-tests" \
  -H "Authorization: Bearer $INSTRUCTOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name":"Basic Addition",
    "stdin":"2 3",
    "expected_stdout":"5",
    "points":5,
    "is_hidden": true,
    "order_index": 0
  }'
  ```
------------------------------------------------------------------------

## 9) List IO test cases
```
GET /instructor/assignments/{assignment_id}/io-tests
```
```
curl -s "$BASE_URL/instructor/assignments/$ASSIGNMENT_ID/io-tests" \
  -H "Authorization: Bearer $INSTRUCTOR_TOKEN"
```
------------------------------------------------------------------------

### 10) Create or update Unit Test Spec (upsert)
```
POST /instructor/assignments/{assignment_id}/unit-tests
```
```
curl -s -X POST "$BASE_URL/instructor/assignments/$ASSIGNMENT_ID/unit-tests" \
  -H "Authorization: Bearer $INSTRUCTOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name":"Basic Function Tests",
    "test_code":"assert solve(2,3) == 5\nassert solve(-1,1) == 0",
    "points":20,
    "is_hidden": true
  }'
```
------------------------------------------------------------------------

## 11) Get Unit Test Spec
```
GET /instructor/assignments/{assignment_id}/unit-tests
```
```
curl -s "$BASE_URL/instructor/assignments/$ASSIGNMENT_ID/unit-tests" \
  -H "Authorization: Bearer $INSTRUCTOR_TOKEN"
```
------------------------------------------------------------------------

## 12) Create or update static rules
```
PUT /instructor/assignments/{assignment_id}/static-rules
```
```
curl -s -X PUT "$BASE_URL/instructor/assignments/$ASSIGNMENT_ID/static-rules" \
  -H "Authorization: Bearer $INSTRUCTOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "required_functions":["solve"],
    "forbidden_imports":["os","sys"],
    "max_cyclomatic_complexity":10,
    "points":10
  }'
```
------------------------------------------------------------------------

## 13) Get static rules
```
GET /instructor/assignments/{assignment_id}/static-rules
```
```
curl -s "$BASE_URL/instructor/assignments/$ASSIGNMENT_ID/static-rules" \
  -H "Authorization: Bearer $INSTRUCTOR_TOKEN"
```
------------------------------------------------------------------------

## 14) Publish Assignment
```
POST /instructor/assignments/{assignment_id}/publish
```
```
curl -X POST "$BASE_URL/instructor/assignments/$ASSIGNMENT_ID/publish" \
-H "Authorization: Bearer \$INSTRUCTOR_TOKEN"
```
------------------------------------------------------------------------

## 15) Unpublish Assignment
```
POST /instructor/assignments/{assignment_id}/unpublish
```
```
curl -s -X POST "$BASE_URL/instructor/assignments/$ASSIGNMENT_ID/unpublish" \
  -H "Authorization: Bearer $INSTRUCTOR_TOKEN"
```
## 16) Student Login
```
POST /auth/login
```
```
export STUDENT_TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
-H "Content-Type: application/x-www-form-urlencoded" \
-d "username=student1@example.com&password=Pass12345!" \
\| python -c "import sys, json;
print(json.load(sys.stdin).get('access_token',''))")
```
------------------------------------------------------------------------

## 17) Student List Published Assignments
```
GET /student/assignments
```
```
curl "\$BASE_URL/student/assignments" \
-H "Authorization: Bearer \$STUDENT_TOKEN"
```
------------------------------------------------------------------------

## 18) Student view assignment detail (published only)
```
GET /student/assignments/{assignment_id}
```
```
curl -s "$BASE_URL/student/assignments/$ASSIGNMENT_ID" \
  -H "Authorization: Bearer $STUDENT_TOKEN"
```
------------------------------------------------------------------------

## 19) Submit Python code file
```
POST /student/assignments/{assignment_id}/submissions
```

### Create file:
```
cat \> solution.py \<\<'PY' def solve(a, b): return a \* b

print(solve(2, 3)) PY
```

### Upload:
```
export
SUBMISSION_ID=$(curl -s -X POST "$BASE_URL/student/assignments/\$ASSIGNMENT_ID/submissions" \
-H "Authorization: Bearer \$STUDENT_TOKEN" \
-F "file=@solution.py;type=text/x-python" \
\| python -c "import sys, json;
print(json.load(sys.stdin).get('submission_id',''))")
```
------------------------------------------------------------------------

## 20) Get submission status/metadata
```
GET /student/submissions/{submission_id}
```
```
curl -s "$BASE_URL/student/submissions/$SUBMISSION_ID" \
  -H "Authorization: Bearer $STUDENT_TOKEN"
```
------------------------------------------------------------------------



# Working on the next endpoint,
## 21) Get Submission Result
```
curl "$BASE_URL/student/submissions/$SUBMISSION_ID/result" \
-H "Authorization: Bearer \$STUDENT_TOKEN"
```
------------------------------------------------------------------------

## Notes

-   Ensure Redis is running for Celery.
-   Ensure Judge0 credentials are set in .env.
-   If using Windows, you may need Git Bash for export commands.
