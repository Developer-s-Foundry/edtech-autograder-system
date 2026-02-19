from fastapi import FastAPI
from app.config import get_settings
from app.utils.logging import setup_logging
from fastapi.staticfiles import StaticFiles
from app.routers import health_router, auth_router
from app.routers.auth import router as auth_router
from app.routers.web_auth import router as web_router
from app.routers.instructor_assignments import router as instructor_assignments_router
from app.routers.web_instructor_assignments import router as web_instructor_assignments_router
from app.routers.instructor_io_tests import router as instructor_io_tests_router
from app.routers.web_instructor_io_tests import router as web_instructor_io_tests_router
from app.routers.instructor_unit_tests import router as instructor_unit_tests_router
from app.routers.web_instructor_unit_tests import router as web_instructor_unit_tests_router




settings = get_settings()
setup_logging(settings.log_level)

app = FastAPI(title=settings.app_name)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(auth_router, prefix="/auth")
app.include_router(web_router)
app.include_router(web_instructor_assignments_router)
app.include_router(instructor_assignments_router)
app.include_router(instructor_io_tests_router)
app.include_router(web_instructor_io_tests_router)
app.include_router(instructor_unit_tests_router)
app.include_router(web_instructor_unit_tests_router)


