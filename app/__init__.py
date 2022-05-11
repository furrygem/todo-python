import fastapi
from app.internal.config import Config
from app.internal.exceptions import http_exception_handler
from .main import main_router
from .admin import admin_router


Config("config.yaml")

api = fastapi.FastAPI()

api.include_router(main_router)
api.include_router(admin_router)
# api = fastapi.APIRouter(prefix="/api")

api.add_exception_handler(fastapi.exceptions.HTTPException,
                          http_exception_handler)
