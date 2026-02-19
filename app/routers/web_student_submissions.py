import httpx
from jose import jwt, JWTError
from fastapi import APIRouter, Request, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, HTMLResponse

from app.config import settings

router = APIRouter(prefix="/web", tags=["web-student-submissions"])
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


@router.get("/student/assignments/{assignment_id}/submit", response_class=HTMLResponse)
async def submit_page(request: Request, assignment_id: int):
    user = get_user_from_cookie(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    if user.get("role") != "student":
        return RedirectResponse(url="/dashboard", status_code=303)

    return templates.TemplateResponse(
        "student_submit.html",
        {"request": request, "assignment_id": assignment_id, "error": None, "result": None},
    )


@router.post("/student/assignments/{assignment_id}/submit", response_class=HTMLResponse)
async def submit_file(
    request: Request,
    assignment_id: int,
    file: UploadFile = File(...),
):
    user = get_user_from_cookie(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    if user.get("role") != "student":
        return RedirectResponse(url="/dashboard", status_code=303)

    api_base = get_api_base_url(request)

    files = {
        "file": (file.filename, await file.read(), file.content_type or "application/octet-stream")
    }

    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{api_base}/student/assignments/{assignment_id}/submissions",
            files=files,
            headers={"Authorization": f"Bearer {user['token']}"},
        )

    if r.status_code >= 400:
        detail = None
        try:
            detail = r.json().get("detail")
        except Exception:
            detail = r.text
        return templates.TemplateResponse(
            "student_submit.html",
            {"request": request, "assignment_id": assignment_id, "error": detail or "Upload failed.", "result": None},
            status_code=400,
        )

    return templates.TemplateResponse(
        "student_submit.html",
        {"request": request, "assignment_id": assignment_id, "error": None, "result": r.json()},
    )
