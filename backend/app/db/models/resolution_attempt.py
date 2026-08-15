from datetime import UTC, datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)

from app.db.database import Base


class ResolutionAttempt(Base):
    __tablename__ = "resolution_attempts"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    ticket_id = Column(
        Integer,
        ForeignKey("tickets.id"),
        nullable=False,
        index=True,
    )

    category = Column(
        String(100),
        nullable=True,
        index=True,
    )

    action_key = Column(
        String(150),
        nullable=False,
        index=True,
    )

    action_text = Column(
        Text,
        nullable=False,
    )

    outcome = Column(
        String(30),
        nullable=False,
        default="unknown",
        index=True,
    )

    confidence = Column(
        Float,
        nullable=True,
    )

    source = Column(
        String(50),
        nullable=False,
        default="agent",
    )

    failure_reason = Column(
        Text,
        nullable=True,
    )

    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(
            UTC
        ).replace(tzinfo=None),
    )