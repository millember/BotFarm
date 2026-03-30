from sqlalchemy import select, text
from datetime import timedelta, timezone

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