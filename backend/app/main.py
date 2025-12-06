from app.api.v1.router import api_router
from app.config import settings
from fastapi import FastAPI

app = FastAPI(
    title=settings.PROJECT_NAME,
)


# Root endpoint
@app.get("/")
async def root() -> dict[str, str]:
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}!",
        "version": settings.VERSION,
        "docs": "/docs",
    }


# Health check
@app.get("/health")
async def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "version": settings.VERSION,
    }


# Include API Router
app.include_router(api_router, prefix=settings.API_V1_STR)
