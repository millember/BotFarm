from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from database import Base
import uuid
from datetime import datetime, timedelta, timezone

# Определяем московский часовой пояс
MOSCOW_TZ = timezone(timedelta(hours=3))


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(
        TIMESTAMP(timezone=True), default=lambda: datetime.now(MOSCOW_TZ)
    )
    login = Column(String, nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    project_id = Column(UUID(as_uuid=True), nullable=False)
    env = Column(String, nullable=False)
    domain = Column(String, nullable=False)
    locktime = Column(TIMESTAMP(timezone=True), nullable=True)
