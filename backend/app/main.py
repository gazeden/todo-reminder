import logging
from contextlib import asynccontextmanager

from app.api.v1.router import api_router
from app.config import settings
from app.core.logging import setup_logging
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse

# Import appropriate producer based on configuration
if settings.USE_SCHEMA_REGISTRY:
    from app.kafka.producers.schema_registry_producer import (
        schema_registry_producer as kafka_producer,
    )
else:
    from app.kafka.producers.producer import kafka_producer

from app.db.session import init_db

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager for startup and shutdown events.
    """
    # Startup
    logger.info("Starting up application...")

    if settings.DEBUG:
        init_db()

    # Start Kafka producer
    if settings.USE_SCHEMA_REGISTRY:
        kafka_producer.start()  # Synchronous for schema registry
    else:
        await kafka_producer.start()  # Async for aiokafka

    logger.info("Kafka producer started")

    yield

    # Shutdown
    logger.info("Shutting down application...")

    if settings.USE_SCHEMA_REGISTRY:
        kafka_producer.stop()
    else:
        await kafka_producer.stop()

    logger.info("Kafka producer stopped")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
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
