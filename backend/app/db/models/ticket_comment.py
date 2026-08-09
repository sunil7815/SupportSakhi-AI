from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    Text,
    DateTime,
    ForeignKey,
)

from app.db.database import Base


class TicketComment(Base):
    __tablename__ = "ticket_comments"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    ticket_id = Column(
        Integer,
        ForeignKey("tickets.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    comment = Column(
        Text,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )