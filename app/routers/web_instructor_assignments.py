import httpx
from jose import jwt, JWTError
from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, HTMLResponse
from app.config import settings

router = APIRouter(prefix="/web", tags=["web-instructor"])
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
        return {"email": payload.get("sub") or payload.get("email"), "role": role, "token": token}
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


@router.get("/instructor/dashboard", response_class=HTMLResponse)
async def instructor_dashboard(request: Request):
    user, resp = require_instructor_web(request)
    if resp:
        return resp

    api_base = get_api_base_url(request)

    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{api_base}/instructor/assignments",
            headers={"Authorization": f"Bearer {user['token']}"},
        )

    assignments = []
    if r.status_code < 400:
        assignments = r.json()

    return templates.TemplateResponse(
        "instructor_dashboard.html",
        {"request": request, "user": user, "assignments": assignments},
    )


@router.get("/instructor/assignments/new", response_class=HTMLResponse)
async def new_assignment_page(request: Request):
    user, resp = require_instructor_web(request)
    if resp:
        return resp
    return templates.TemplateResponse("assignment_new.html", {"request": request, "error": None})


@router.post("/instructor/assignments/new")
async def new_assignment_submit(
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    instructions: str = Form(""),
    language: str = Form("python"),
    is_published: str = Form("false"),
    weight_io: int = Form(70),
    weight_unit: int = Form(20),
    weight_static: int = Form(10),
    max_runtime_ms: int = Form(2000),
    max_memory_kb: int = Form(128000),
):
    user, resp = require_instructor_web(request)
    if resp:
        return resp

    payload = {
        "title": title,
        "description": description,
        "instructions": instructions or None,
        "language": language,
        "is_published": (is_published.lower() == "true"),
        "weight_io": int(weight_io),
        "weight_unit": int(weight_unit),
        "weight_static": int(weight_static),
        "max_runtime_ms": int(max_runtime_ms),
        "max_memory_kb": int(max_memory_kb),
    }

    api_base = get_api_base_url(request)

    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{api_base}/instructor/assignments",
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
            "assignment_new.html",
            {"request": request, "error": detail or "Failed to create assignment."},
            status_code=400,
        )

    return RedirectResponse(url="/web/instructor/dashboard", status_code=303)


@router.get("/instructor/assignments/{assignment_id}/edit", response_class=HTMLResponse)
async def edit_assignment_page(request: Request, assignment_id: int):
    user, resp = require_instructor_web(request)
    if resp:
        return resp

    api_base = get_api_base_url(request)

    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{api_base}/instructor/assignments/{assignment_id}",
            headers={"Authorization": f"Bearer {user['token']}"},
        )

    if r.status_code >= 400:
        return templates.TemplateResponse(
            "forbidden.html",
            {"request": request, "message": "Unable to load assignment."},
            status_code=r.status_code,
        )

    assignment = r.json()
    return templates.TemplateResponse(
        "assignment_edit.html",
        {"request": request, "assignment": assignment, "error": None},
    )


@router.post("/instructor/assignments/{assignment_id}/edit")
async def edit_assignment_submit(
    request: Request,
    assignment_id: int,
    title: str = Form(...),
    description: str = Form(...),
    instructions: str = Form(""),
    language: str = Form("python"),
    is_published: str = Form("false"),
    weight_io: int = Form(70),
    weight_unit: int = Form(20),
    weight_static: int = Form(10),
    max_runtime_ms: int = Form(2000),
    max_memory_kb: int = Form(128000),
):
    user, resp = require_instructor_web(request)
    if resp:
        return resp

    payload = {
        "title": title,
        "description": description,
        "instructions": instructions or None,
        "language": language,
        "is_published": (is_published.lower() == "true"),
        "weight_io": int(weight_io),
        "weight_unit": int(weight_unit),
        "weight_static": int(weight_static),
        "max_runtime_ms": int(max_runtime_ms),
        "max_memory_kb": int(max_memory_kb),
    }

    api_base = get_api_base_url(request)

    async with httpx.AsyncClient() as client:
        r = await client.put(
            f"{api_base}/instructor/assignments/{assignment_id}",
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
            "assignment_edit.html",
            {"request": request, "assignment": {"id": assignment_id, **payload}, "error": detail or "Failed to update."},
            status_code=400,
        )

    return RedirectResponse(url="/web/instructor/dashboard", status_code=303)
