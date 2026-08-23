import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ResumeAnalysis(Base):
    __tablename__ = "resume_analyses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    resume_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    skills: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    experience_years: Mapped[float | None] = mapped_column(
        nullable=True,
    )

    education: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    recommended_roles: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    strengths: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    missing_skills: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )