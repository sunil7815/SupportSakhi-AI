from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)

from app.db.database import Base


class ResolutionProof(Base):
    __tablename__ = "resolution_proofs"

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

    resolution_attempt_id = Column(
        Integer,
        ForeignKey("resolution_attempts.id"),
        nullable=True,
        index=True,
    )

    confirmed_by_user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    proof_status = Column(
        String(30),
        nullable=False,
        default="pending",
        index=True,
    )

    proof_type = Column(
        String(30),
        nullable=False,
        default="user_confirmation",
    )

    successful_action = Column(
        Text,
        nullable=True,
    )

    user_confirmed = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    agent_confidence = Column(
        Float,
        nullable=True,
    )

    verification_score = Column(
        Float,
        nullable=True,
    )

    safety_decision = Column(
        String(50),
        nullable=True,
    )

    safe_for_auto_resolution = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    evidence = Column(
        JSON,
        nullable=True,
    )

    resolution_reason = Column(
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

    verified_at = Column(
        DateTime,
        nullable=True,
    )