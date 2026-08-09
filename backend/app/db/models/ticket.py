from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
)

from sqlalchemy.orm import relationship

from app.db.database import Base


class Ticket(Base):
    __tablename__ = "tickets"

    # ============================================================
    # PRIMARY KEY
    # ============================================================

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # ============================================================
    # TITLE
    # ============================================================

    title = Column(
        String(200),
        nullable=False
    )

    # ============================================================
    # DESCRIPTION
    # ============================================================

    description = Column(
        Text,
        nullable=False
    )

    # ============================================================
    # CATEGORY
    # AI DETECTED CATEGORY
    # ============================================================

    category = Column(
        String(100),
        nullable=True
    )

    # ============================================================
    # PRIORITY
    # ============================================================

    priority = Column(
        String(50),
        default="medium",
        nullable=False
    )

    # ============================================================
    # STATUS
    # ============================================================

    status = Column(
        String(50),
        default="open",
        nullable=False
    )

    # ============================================================
    # TICKET CREATOR
    # ============================================================

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    # ============================================================
    # ASSIGNED ADMIN / AGENT
    # ============================================================

    assigned_to_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        index=True
    )

    # ============================================================
    # AI GENERATED SOLUTION
    # ============================================================

    ai_solution = Column(
        Text,
        nullable=True
    )

    # ============================================================
    # SLA DUE DATE
    # ============================================================

    sla_due_at = Column(
        DateTime,
        nullable=True,
        index=True
    )

    # ============================================================
    # SLA STATUS
    #
    # Values:
    # within_sla
    # near_breach
    # breached
    # completed
    # ============================================================

    sla_status = Column(
        String(30),
        default="within_sla",
        nullable=True,
        index=True
    )

    # ============================================================
    # SLA BREACH TIME
    # ============================================================

    sla_breached_at = Column(
        DateTime,
        nullable=True
    )

    # ============================================================
    # CREATED AT
    # ============================================================

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # ============================================================
    # UPDATED AT
    # ============================================================

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # ============================================================
    # RELATIONSHIP - TICKET CREATOR
    # ============================================================

    user = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="tickets"
    )

    # ============================================================
    # RELATIONSHIP - ASSIGNED USER
    # ============================================================

    assigned_to = relationship(
        "User",
        foreign_keys=[assigned_to_id],
        back_populates="assigned_tickets"
    )
