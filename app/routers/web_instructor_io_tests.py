import httpx
from jose import jwt, JWTError
from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, HTMLResponse

from app.config import settings

router = APIRouter(prefix="/web", tags=["web-io-tests"])
templates = Jinja2Templates(directory="app/templates")

COOKIE_NAME = "access_token"

def get_api_base_url(request: Request) -> str:
    return str(request.base_url).rstrip("/")

def _normalize_role(role_value):
    if role_value is None:
        return None
    if isinstance(role_value, str):
        return role_value
    if isinstance(role_value, (list, tuple)) and role_value:
        return role_value[0] if isinstance(role_value[0], str) else None
    return None

def get_user_from_cookie(request: Request):
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        role = _normalize_role(payload.get("role") or payload.get("user_role") or payload.get("roles"))
        return {"role": role, "token": token}
    except JWTError:
        return None

def require_instructor_web(request: Request):
    user = get_user_from_cookie(request)
    if not user:
        return None, RedirectResponse(url="/login", status_code=303)
    if user.get("role") != "instructor":
        return None, templates.TemplateResponse(
            "forbidden.html",
            {"request": request, "message": "Instructor access only."},
            status_code=403,
        )
    return user, None


@router.get("/instructor/assignments/{assignment_id}/io-tests", response_class=HTMLResponse)
async def io_tests_page(request: Request, assignment_id: int):
    user, resp = require_instructor_web(request)
    if resp:
        return resp

    api_base = get_api_base_url(request)

    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{api_base}/instructor/assignments/{assignment_id}/io-tests",
            headers={"Authorization": f"Bearer {user['token']}"},
        )

    if r.status_code >= 400:
        return templates.TemplateResponse(
            "forbidden.html",
            {"request": request, "message": "Unable to load IO test cases."},
            status_code=r.status_code,
        )

    test_cases = r.json()
    return templates.TemplateResponse(
        "io_tests.html",
        {"request": request, "assignment_id": assignment_id, "test_cases": test_cases, "error": None},
    )


@router.post("/instructor/assignments/{assignment_id}/io-tests")
async def io_tests_create(request: Request, assignment_id: int):
    user, resp = require_instructor_web(request)
    if resp:
        return resp

    form = await request.form()

    payload = {
        "name": str(form.get("name", "")).strip(),
        "stdin": (str(form.get("stdin", "")).strip() or None),
        "expected_stdout": str(form.get("expected_stdout", "")).strip(),
        "points": int(form.get("points", 1)),
        "is_hidden": str(form.get("is_hidden", "true")).lower() == "true",
        "order_index": int(form.get("order_index", 0)),
    }

    api_base = get_api_base_url(request)

    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{api_base}/instructor/assignments/{assignment_id}/io-tests",
            json=payload,
            headers={"Authorization": f"Bearer {user['token']}"},
        )

    if r.status_code >= 400:
        detail = None
        try:
            detail = r.json().get("detail")
        except Exception:
            detail = r.text

        # reload list so user sees existing cases + error
        async with httpx.AsyncClient() as client:
            r2 = await client.get(
                f"{api_base}/instructor/assignments/{assignment_id}/io-tests",
                headers={"Authorization": f"Bearer {user['token']}"},
            )
        test_cases = r2.json() if r2.status_code < 400 else []

        return templates.TemplateResponse(
            "io_tests.html",
            {
                "request": request,
                "assignment_id": assignment_id,
                "test_cases": test_cases,
                "error": detail or "Failed to create test case.",
            },
            status_code=400,
        )

    return RedirectResponse(url=f"/web/instructor/assignments/{assignment_id}/io-tests", status_code=303)
