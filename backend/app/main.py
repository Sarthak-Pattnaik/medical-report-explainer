import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.auth import router as auth_router
from app.api.reports import router as reports_router
from app.core.database import Base, engine, get_db

# These look unused, but importing them registers their tables on
# Base.metadata, which create_all() below needs. Do not remove.
from app.models import (  # noqa: F401
    ChatMessage,
    MedicalReport,
    ReportAnalysis,
    User,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs once when the server starts, not when this file is imported.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Medical Report Explainer API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://medical-report-explainer-lake.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(auth_router)
app.include_router(reports_router)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "medical-report-explainer"
    }


@app.get("/health/database")
def database_health_check(
    db: Session = Depends(get_db)
):
    try:
        db.execute(text("SELECT 1"))

        return {
            "status": "ok",
            "database": "connected"
        }

    except Exception:
        logger.exception("Database health check failed")

        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "error",
                "database": "connection failed"
            },
        )


@app.get("/")
def root():
    return {
        "message": "Welcome to Medical Report Explainer API",
        "status": "running"
    }