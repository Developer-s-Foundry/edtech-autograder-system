from fastapi import FastAPI
from app.config import get_settings
from app.utils.logging import setup_logging
from app.routers import health_router, auth_router

settings = get_settings()
setup_logging(settings.log_level)

app = FastAPI(title=settings.app_name)

app.include_router(health_router)
app.include_router(auth_router)
