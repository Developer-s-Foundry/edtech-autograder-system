import httpx
from jose import jwt, JWTError
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, HTMLResponse

from app.config import settings

router = APIRouter(prefix="/web", tags=["web-student-assignments"])
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


@router.get("/student/assignments/{assignment_id}", response_class=HTMLResponse)
async def student_assignment_detail_page(request: Request, assignment_id: int):
    user = get_user_from_cookie(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    if user.get("role") != "student":
        return RedirectResponse(url="/dashboard", status_code=303)

    api_base = get_api_base_url(request)

    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{api_base}/student/assignments/{assignment_id}",
            headers={"Authorization": f"Bearer {user['token']}"},
        )

    if r.status_code == 404:
        return templates.TemplateResponse(
            "forbidden.html",
            {"request": request, "message": "Assignment not found."},
            status_code=404,
        )

    if r.status_code >= 400:
        return templates.TemplateResponse(
            "forbidden.html",
            {"request": request, "message": "Unable to load assignment."},
            status_code=r.status_code,
        )

    assignment = r.json()
    return templates.TemplateResponse(
        "student_assignment_detail.html",
        {"request": request, "user": user, "assignment": assignment},
    )
