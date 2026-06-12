from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.evaluation import router
from app.config import get_settings

settings = get_settings()

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

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_debug,
    )
