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


def utc_now() -> datetime:
    return datetime.now(
        UTC
    ).replace(tzinfo=None)


class KnowledgeItem(Base):
    __tablename__ = "knowledge_items"

    # ========================================================
    # PRIMARY KEY
    # ========================================================

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    # ========================================================
    # KNOWLEDGE TITLE
    # ========================================================

    title = Column(
        String(255),
        nullable=False,
        index=True,
    )

    # ========================================================
    # ISSUE CATEGORY
    #
    # Examples:
    # network
    # email
    # software
    # hardware
    # how_to
    # ========================================================

    category = Column(
        String(100),
        nullable=True,
        index=True,
    )

    # ========================================================
    # PROBLEM DESCRIPTION
    # ========================================================

    problem_text = Column(
        Text,
        nullable=False,
    )

    # ========================================================
    # VERIFIED / RECOMMENDED SOLUTION
    # ========================================================

    solution_text = Column(
        Text,
        nullable=False,
    )

    # ========================================================
    # SEARCH KEYWORDS
    #
    # Example:
    # [
    #     "wifi",
    #     "internet",
    #     "network"
    # ]
    # ========================================================

    keywords = Column(
        JSON,
        nullable=True,
    )

    # ========================================================
    # SOURCE TYPE
    #
    # manual
    # verified_ticket
    # admin_playbook
    # imported_document
    # ========================================================

    source_type = Column(
        String(50),
        nullable=False,
        default="manual",
        index=True,
    )

    # ========================================================
    # OPTIONAL SOURCE TICKET
    #
    # Used when knowledge was learned from
    # a successfully resolved ticket.
    # ========================================================

    source_ticket_id = Column(
        Integer,
        ForeignKey("tickets.id"),
        nullable=True,
        index=True,
    )

    # ========================================================
    # OPTIONAL SOURCE REFERENCE
    #
    # Example:
    # internal article name
    # document name
    # playbook reference
    # ========================================================

    source_reference = Column(
        String(255),
        nullable=True,
    )

    # ========================================================
    # KNOWLEDGE CONFIDENCE
    #
    # Range:
    # 0.0 → 1.0
    # ========================================================

    confidence = Column(
        Float,
        nullable=False,
        default=0.50,
        index=True,
    )

    # ========================================================
    # SUCCESS / FAILURE MEMORY
    # ========================================================

    success_count = Column(
        Integer,
        nullable=False,
        default=0,
    )

    failure_count = Column(
        Integer,
        nullable=False,
        default=0,
    )

    # ========================================================
    # ADMIN APPROVAL
    #
    # Auto-learned knowledge can remain unapproved
    # until an admin reviews it.
    # ========================================================

    is_approved = Column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    # ========================================================
    # ACTIVE STATUS
    # ========================================================

    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    # ========================================================
    # CREATED AT
    # ========================================================

    created_at = Column(
        DateTime,
        nullable=False,
        default=utc_now,
    )

    # ========================================================
    # UPDATED AT
    # ========================================================

    updated_at = Column(
        DateTime,
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )