import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routers.evaluation import router
from app.config import get_settings
from app.logging_config import setup_logging

settings = get_settings()
setup_logging(debug=settings.app_debug)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Engineering Report Evaluation API",
    description="AI-powered multi-agent evaluation pipeline for engineering reports",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

# Serve the built frontend when available (production mode).
# API routes above take precedence; this only handles non-API paths.
_frontend_dist = os.path.join(os.path.dirname(__file__), "frontend", "dist")
if os.path.isdir(_frontend_dist):
    app.mount("/", StaticFiles(directory=_frontend_dist, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn

    logger.info(
        "Starting server on %s:%s (debug=%s, model=%s)",
        settings.app_host,
        settings.app_port,
        settings.app_debug,
        settings.gemini_model,
    )
    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_debug,
    )
