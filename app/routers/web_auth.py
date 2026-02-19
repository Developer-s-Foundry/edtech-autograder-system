import httpx
from jose import jwt, JWTError
from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, HTMLResponse

from app.config import settings

router = APIRouter(tags=["web"])
templates = Jinja2Templates(directory="app/templates")

# Cookie key name (you choose this). The browser stores the JWT under this name.
COOKIE_NAME = "access_token"


def get_api_base_url(request: Request) -> str:
    """Build API base URL from the incoming request (works in local/dev/proxy setups)."""
    return str(request.base_url).rstrip("/")


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request, "error": None})


@router.post("/register")
async def register_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(...),
    role: str = Form(...),  # "student" or "instructor"
):
    payload = {
        "email": email,
        "password": password,
        "full_name": full_name,
        "role": role,
    }

    api_base = get_api_base_url(request)

    async with httpx.AsyncClient() as client:
        r = await client.post(f"{api_base}/auth/register", json=payload)

    if r.status_code >= 400:
        detail = None
        try:
            detail = r.json().get("detail")
        except Exception:
            detail = r.text

        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": detail or "Registration failed."},
            status_code=400,
        )

    return RedirectResponse(url="/login", status_code=303)


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@router.post("/login")
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
):
    # Backend likely uses OAuth2PasswordRequestForm:
    # username=<email>&password=<pw> as x-www-form-urlencoded
    data = {"username": email, "password": password}

    api_base = get_api_base_url(request)

    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{api_base}/auth/login",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    if r.status_code >= 400:
        detail = None
        try:
            detail = r.json().get("detail")
        except Exception:
            detail = r.text

        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": detail or "Login failed."},
            status_code=400,
        )

    token = r.json().get("access_token")
    if not token:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "No token returned from /auth/login."},
            status_code=500,
        )

    resp = RedirectResponse(url="/dashboard", status_code=303)

    resp.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=False,  # set True in production with HTTPS
        samesite="lax",
        max_age=60 * 60 * 24,  # 1 day (ideally match your JWT exp)
        path="/",
    )
    return resp


@router.get("/logout")
async def logout():
    resp = RedirectResponse(url="/login", status_code=303)
    resp.delete_cookie(COOKIE_NAME, path="/")
    return resp


def _normalize_role(role_value) -> str | None:
    """
    Normalize role from JWT payload.
    Supports:
      - "role": "student"
      - "user_role": "student"
      - "roles": ["student"] or "roles": "student"
    Returns a single role string or None.
    """
    if role_value is None:
        return None

    if isinstance(role_value, str):
        return role_value

    if isinstance(role_value, (list, tuple)) and role_value:
        # Prefer the first role if multiple are present
        first = role_value[0]
        return first if isinstance(first, str) else None

    return None


def get_current_user_from_cookie(request: Request):
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        role = _normalize_role(
            payload.get("role") or payload.get("user_role") or payload.get("roles")
        )

        return {
            "email": payload.get("sub") or payload.get("email"),
            "role": role,
        }

    except JWTError:
        return None


@router.get("/dashboard")
async def dashboard(request: Request):
    user = get_current_user_from_cookie(request)

    if not user:
        return RedirectResponse(url="/login", status_code=303)

    role = user.get("role")

    if role == "instructor":
        return RedirectResponse(url="/web/instructor/dashboard", status_code=303)

    if role == "student":
        return RedirectResponse(url="/web/student/dashboard", status_code=303)

    # fallback safety
    return RedirectResponse(url="/login", status_code=303)


@router.get("/instructor-area", response_class=HTMLResponse)
async def instructor_area(request: Request):
    user = get_current_user_from_cookie(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    if user.get("role") != "instructor":
        return templates.TemplateResponse(
            "forbidden.html",
            {"request": request, "message": "Instructor access only."},
            status_code=403,
        )

    return HTMLResponse(f"<h2>Instructor Area</h2><p>Welcome {user.get('email')}</p>")

@router.get("/student/dashboard", response_class=HTMLResponse)
async def student_dashboard(request: Request):
    user = get_current_user_from_cookie(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    if user.get("role") != "student":
        return RedirectResponse(url="/dashboard", status_code=303)

    return templates.TemplateResponse(
        "student_dashboard.html",
        {"request": request, "user": user},
    )




@router.get("/student-area", response_class=HTMLResponse)
async def student_area(request: Request):
    user = get_current_user_from_cookie(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    if user.get("role") != "student":
        return templates.TemplateResponse(
            "forbidden.html",
            {"request": request, "message": "Student access only."},
            status_code=403,
        )

    return HTMLResponse(f"<h2>Student Area</h2><p>Welcome {user.get('email')}</p>")
