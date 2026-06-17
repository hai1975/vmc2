import json
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import DateTime, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


class SessionStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"


class FormSession(Base):
    __tablename__ = "form_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    form_id: Mapped[str] = mapped_column(String(100), index=True)
    status: Mapped[str] = mapped_column(String(20), default=SessionStatus.DRAFT.value)
    language: Mapped[str] = mapped_column(String(5), default="en")
    answers_json: Mapped[str] = mapped_column(Text, default="{}")
    filled_pdf_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


engine = create_engine(
    settings.database_url.replace("sqlite:///", "sqlite:///"),
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def dumps_answers(answers: dict) -> str:
    return json.dumps(answers, ensure_ascii=False)


def loads_answers(raw: str) -> dict:
    return json.loads(raw or "{}")
