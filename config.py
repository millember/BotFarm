from sqlalchemy import text
from datetime import timedelta, timezone
import os

POSTGRES_USER = os.getenv("POSTGRES_USER", "oppennec")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "db")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "botfarm")

DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# App
APP_NAME = os.getenv("APP_NAME", "BotFarm")
DEBUG = os.getenv("DEBUG", "").lower() in ("1", "true", "yes")
SQL_ECHO = os.getenv("SQL_ECHO", "").lower() in ("1", "true", "yes")

# Lock settings
LOCK_DURATION_MINUTES = int(os.getenv("LOCK_DURATION_MINUTES", "30"))

# Timezone
MOSCOW_TZ = timezone(timedelta(hours=3))

_LOCK_ONE_USER_SQL = text("""
WITH picked AS (
    SELECT id
    FROM users
    WHERE locktime IS NULL OR locktime < :now
    ORDER BY created_at
    LIMIT 1
    FOR UPDATE SKIP LOCKED
)
UPDATE users AS u
SET locktime = :new_lock
FROM picked
WHERE u.id = picked.id
RETURNING u.id
""")