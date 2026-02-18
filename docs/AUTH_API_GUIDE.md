# Authentication API Guide

This document explains how to set up and test the authentication endpoints for the EdTech Autograder System.

---

## Prerequisites

### 1. Environment Variables

Add the following to your `.env` file in the project root:

```env
DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/autograder_db
REDIS_URL=redis://localhost:6379/0
JWT_SECRET_KEY=your-secret-key-here
```

Generate a secure secret key:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Optional JWT settings (these have defaults):

```env
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
```

### 2. Install Dependencies

```bash
python -m venv venv
source venv/bin/activate        # Linux/macOS
# venv\Scripts\activate         # Windows

pip install -r requirements.txt
```

### 3. Run Database Migrations

```bash
alembic upgrade head
```

### 4. Seed Demo Data (Optional)

```bash
python scripts/seed.py
```

This creates three demo users (password for all: `demo_password_123`):

| Email | Role |
|-------|------|
| `instructor.demo@autograder.local` | instructor |
| `student1.demo@autograder.local` | student |
| `student2.demo@autograder.local` | student |

### 5. Start the Server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.
Swagger UI is at `http://127.0.0.1:8000/docs`.

---

## Endpoints

### POST `/auth/register`

Create a new user account.

**Request:**

```bash
curl -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "password": "securepass123",
    "full_name": "New User",
    "role": "student"
  }'
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `email` | string | yes | Must be a valid email |
| `password` | string | yes | 8-128 characters |
| `full_name` | string | no | Display name |
| `role` | string | yes | `"student"` or `"instructor"` |

**Success Response (201):**

```json
{
  "id": 4,
  "email": "newuser@example.com",
  "role": "student",
  "full_name": "New User",
  "is_active": true,
  "created_at": "2026-02-18T12:00:00+00:00"
}
```

**Error Responses:**

| Status | Reason |
|--------|--------|
| 409 | Email already exists |
| 422 | Validation error (bad email, short password, invalid role) |

---

### POST `/auth/login`

Authenticate and receive JWT tokens.

**Request:**

```bash
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=instructor.demo@autograder.local&password=demo_password_123"
```

> **Note:** This endpoint uses OAuth2 form format. The `username` field takes the user's **email**.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `username` | string | yes | The user's email address |
| `password` | string | yes | The user's password |

**Success Response (200):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6...",
  "token_type": "bearer"
}
```

**Error Responses:**

| Status | Reason |
|--------|--------|
| 401 | Invalid email or password |
| 403 | Account is deactivated |

---

### GET `/auth/me`

Get the currently authenticated user's profile.

**Request:**

```bash
curl http://127.0.0.1:8000/auth/me \
  -H "Authorization: Bearer <access_token>"
```

Replace `<access_token>` with the token from the login response.

**Success Response (200):**

```json
{
  "id": 1,
  "email": "instructor.demo@autograder.local",
  "role": "instructor",
  "full_name": "Demo Instructor",
  "is_active": true,
  "created_at": "2026-02-18T12:00:00+00:00"
}
```

**Error Responses:**

| Status | Reason |
|--------|--------|
| 401 | Missing, invalid, or expired token |
| 403 | Account is deactivated |

---

### POST `/auth/refresh`

Exchange a refresh token for a new access token.

**Request:**

```bash
curl -X POST http://127.0.0.1:8000/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "<refresh_token>"
  }'
```

Replace `<refresh_token>` with the token from the login response.

**Success Response (200):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6...",
  "token_type": "bearer"
}
```

**Error Responses:**

| Status | Reason |
|--------|--------|
| 401 | Invalid or expired refresh token |

---

## Full Testing Flow

Here is a step-by-step flow you can run to verify everything works end to end.

### Step 1 — Register a new user

```bash
curl -s -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testdev@example.com",
    "password": "testpass123",
    "full_name": "Test Developer",
    "role": "student"
  }' | python -m json.tool
```

### Step 2 — Log in

```bash
curl -s -X POST http://127.0.0.1:8000/auth/login \
  -d "username=testdev@example.com&password=testpass123" | python -m json.tool
```

Copy the `access_token` and `refresh_token` from the response.

### Step 3 — Access protected endpoint

```bash
curl -s http://127.0.0.1:8000/auth/me \
  -H "Authorization: Bearer <paste_access_token_here>" | python -m json.tool
```

### Step 4 — Refresh the token

```bash
curl -s -X POST http://127.0.0.1:8000/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "<paste_refresh_token_here>"}' | python -m json.tool
```

### Step 5 — Verify error handling

**Bad credentials:**

```bash
curl -s -X POST http://127.0.0.1:8000/auth/login \
  -d "username=testdev@example.com&password=wrongpassword"
# Expected: 401
```

**No token:**

```bash
curl -s http://127.0.0.1:8000/auth/me
# Expected: 401
```

**Duplicate registration:**

```bash
curl -s -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "testdev@example.com", "password": "testpass123", "role": "student"}'
# Expected: 409
```

---

## Using Swagger UI

Instead of curl, you can test interactively:

1. Open `http://127.0.0.1:8000/docs` in your browser
2. Use **POST /auth/register** to create a user
3. Use **POST /auth/login** to get tokens
4. Click the **Authorize** button (top right), paste the `access_token`, and click **Authorize**
5. All protected endpoints (like **GET /auth/me**) will now work automatically

---

## Token Details

| Token | Lifetime | Use |
|-------|----------|-----|
| Access token | 30 minutes | Sent in `Authorization: Bearer <token>` header for protected endpoints |
| Refresh token | 7 days | Sent to `POST /auth/refresh` to get a new access token without re-entering credentials |

Access tokens carry the user's `role` in the payload, which is used by the role-based access control system for future endpoints (e.g., only instructors can create assignments).
