from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship

from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    # ============================================================
    # PRIMARY KEY
    # ============================================================

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # ============================================================
    # USER NAME
    # ============================================================

    name = Column(
        String(255),
        nullable=False
    )

    # ============================================================
    # EMAIL
    # ============================================================

    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )

    # ============================================================
    # PASSWORD
    # ============================================================

    password = Column(
        String(255),
        nullable=False
    )

    # ============================================================
    # ROLE
    # ============================================================

    role = Column(
        String(50),
        default="user",
        nullable=False
    )

    # ============================================================
    # ACTIVE STATUS
    # ============================================================

    is_active = Column(
        Boolean,
        default=True,
        nullable=False
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
    # TICKETS CREATED BY THIS USER
    # ============================================================

    tickets = relationship(
        "Ticket",
        foreign_keys="Ticket.user_id",
        back_populates="user"
    )

    # ============================================================
    # TICKETS ASSIGNED TO THIS USER
    # ============================================================

    assigned_tickets = relationship(
        "Ticket",
        foreign_keys="Ticket.assigned_to_id",
        back_populates="assigned_to"
    )