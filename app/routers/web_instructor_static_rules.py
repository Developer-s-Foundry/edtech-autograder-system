import json
import httpx
from jose import jwt, JWTError
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, HTMLResponse

from app.config import settings

router = APIRouter(prefix="/web", tags=["web-static-rules"])
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


@router.get("/instructor/assignments/{assignment_id}/static-rules", response_class=HTMLResponse)
async def static_rules_page(request: Request, assignment_id: int):
    user, resp = require_instructor_web(request)
    if resp:
        return resp

    api_base = get_api_base_url(request)

    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{api_base}/instructor/assignments/{assignment_id}/static-rules",
            headers={"Authorization": f"Bearer {user['token']}"},
        )

    rule = None
    if r.status_code == 200:
        rule = r.json()
    elif r.status_code != 404:
        return templates.TemplateResponse(
            "forbidden.html",
            {"request": request, "message": "Unable to load static rules."},
            status_code=r.status_code,
        )

    # Provide a nice JSON textarea default
    default_json = json.dumps(
        rule
        or {
            "required_functions": ["solve"],
            "forbidden_imports": ["os", "sys"],
            "max_cyclomatic_complexity": 10,
            "points": 0,
        },
        indent=2,
    )

    return templates.TemplateResponse(
        "static_rules.html",
        {
            "request": request,
            "assignment_id": assignment_id,
            "rule": rule,
            "json_text": default_json,
            "error": None,
        },
    )


@router.post("/instructor/assignments/{assignment_id}/static-rules")
async def static_rules_submit(request: Request, assignment_id: int):
    user, resp = require_instructor_web(request)
    if resp:
        return resp

    form = await request.form()
    json_text = str(form.get("json_text", "")).strip()

    try:
        payload = json.loads(json_text)
    except json.JSONDecodeError as e:
        return templates.TemplateResponse(
            "static_rules.html",
            {
                "request": request,
                "assignment_id": assignment_id,
                "rule": None,
                "json_text": json_text,
                "error": f"Invalid JSON: {e.msg}",
            },
            status_code=400,
        )

    api_base = get_api_base_url(request)

    async with httpx.AsyncClient() as client:
        r = await client.put(
            f"{api_base}/instructor/assignments/{assignment_id}/static-rules",
            json=payload,
            headers={"Authorization": f"Bearer {user['token']}"},
        )

    if r.status_code >= 400:
        detail = None
        try:
            detail = r.json().get("detail")
        except Exception:
            detail = r.text

        return templates.TemplateResponse(
            "static_rules.html",
            {
                "request": request,
                "assignment_id": assignment_id,
                "rule": None,
                "json_text": json_text,
                "error": detail or "Failed to save static rules.",
            },
            status_code=400,
        )

    return RedirectResponse(url=f"/web/instructor/assignments/{assignment_id}/static-rules", status_code=303)
