import httpx
from jose import jwt, JWTError
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, HTMLResponse

from app.config import settings

router = APIRouter(prefix="/web", tags=["web-student"])
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


@router.get("/student/dashboard", response_class=HTMLResponse)
async def student_dashboard(request: Request):
    user = get_user_from_cookie(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    if user.get("role") != "student":
        return RedirectResponse(url="/dashboard", status_code=303)

    api_base = get_api_base_url(request)
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{api_base}/student/assignments",
            headers={"Authorization": f"Bearer {user['token']}"},
        )

    assignments = r.json() if r.status_code < 400 else []
    return templates.TemplateResponse(
        "student_dashboard.html",
        {"request": request, "user": user, "assignments": assignments},
    )
