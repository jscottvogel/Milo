from app.config import Settings
from fastapi import APIRouter, Response, status
from sqlalchemy import create_engine, text

router = APIRouter(prefix="/v1", tags=["health"])


@router.get("/health", status_code=status.HTTP_200_OK)
def health_check(response: Response):
    db_ok = False
    try:
        settings = Settings()
        engine = create_engine(str(settings.database_url), connect_args={"connect_timeout": 3})
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    if not db_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "api": "ok",
        "database": "ok" if db_ok else "error",
    }
