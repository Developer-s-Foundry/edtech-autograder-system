import httpx
from jose import jwt, JWTError
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.config import settings

router = APIRouter(prefix="/web", tags=["web-publish"])
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


@router.post("/instructor/assignments/{assignment_id}/publish")
async def publish_assignment_web(request: Request, assignment_id: int):
    user, resp = require_instructor_web(request)
    if resp:
        return resp

    api_base = get_api_base_url(request)

    async with httpx.AsyncClient() as client:
        await client.post(
            f"{api_base}/instructor/assignments/{assignment_id}/publish",
            headers={"Authorization": f"Bearer {user['token']}"},
        )

    return RedirectResponse(url="/web/instructor/dashboard", status_code=303)


@router.post("/instructor/assignments/{assignment_id}/unpublish")
async def unpublish_assignment_web(request: Request, assignment_id: int):
    user, resp = require_instructor_web(request)
    if resp:
        return resp

    api_base = get_api_base_url(request)

    async with httpx.AsyncClient() as client:
        await client.post(
            f"{api_base}/instructor/assignments/{assignment_id}/unpublish",
            headers={"Authorization": f"Bearer {user['token']}"},
        )

    return RedirectResponse(url="/web/instructor/dashboard", status_code=303)
