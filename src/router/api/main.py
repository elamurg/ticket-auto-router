import logging
import os

import psycopg
from fastapi import FastAPI, HTTPException

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Ticket Router API",
    version="0.1.0",
)


# getenv() - optional variable, set with fallback
# environ() - variable is manditory or it causes an error
@app.get("/health")
def health() -> dict[str, str]:
    try:
        with psycopg.connect(
            host=os.getenv("POSTGRES_HOST", "db"),
            dbname=os.environ["POSTGRES_DB"],
            user=os.environ["POSTGRES_USER"],
            password=os.environ["POSTGRES_PASSWORD"],
            connect_timeout=3,
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")

        return {"status": "ok"}
    except (psycopg.Error, KeyError) as exc:
        logger.exception("Database health check failed")
        raise HTTPException(
            status_code=503,
            detail="Database unavailable",
        ) from exc
