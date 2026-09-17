from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.auth import router as auth_router
from app.core.database import get_db


app = FastAPI(
    title="Medical Report Explainer API",
    version="0.1.0"
)


app.include_router(auth_router)


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
        return {
            "status": "error",
            "database": "connection failed"
        }