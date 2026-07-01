from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.routers import research, documents
from app.core.config import get_settings

settings = get_settings()

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(research.router, prefix="/api/v1", tags=["research"])
app.include_router(documents.router, prefix="/api/v1", tags=["documents"])


@app.get("/")
def health_check():
    return {
        "status": "running",
        "app": settings.app_name,
        "version": settings.app_version
    }