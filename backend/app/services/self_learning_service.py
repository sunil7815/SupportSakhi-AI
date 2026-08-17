from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models.knowledge_item import KnowledgeItem
from app.services.knowledge_service import (
    create_knowledge_item,
    normalize_text,
    tokenize,
)


# ============================================================
# SELF-LEARNING KNOWLEDGE DRAFT
# ============================================================

def create_resolution_knowledge_draft(
    db: Session,
    ticket_id: int,
    title: str,
    problem_text: str,
    successful_steps: list[str],
    category: str | None = None,
    confidence: float = 0.5,
) -> KnowledgeItem | None:
    """
    Create a pending knowledge-base draft from a successfully
    auto-resolved support ticket.

    Rules:
    - At least one successful troubleshooting step is required.
    - Only one active self-learning draft is created per ticket.
    - Draft is NOT automatically approved.
    - Admin approval is required before RAG can use it.
    """

    # --------------------------------------------------------
    # CLEAN SUCCESSFUL STEPS
    # --------------------------------------------------------

    cleaned_steps = [
        step.strip()
        for step in successful_steps
        if isinstance(step, str)
        and step.strip()
    ]

    if not cleaned_steps:
        return None

    # --------------------------------------------------------
    # DUPLICATE PROTECTION
    # --------------------------------------------------------

    existing_draft = (
        db.query(KnowledgeItem)
        .filter(
            KnowledgeItem.source_type
            == "self_learning",

            KnowledgeItem.source_ticket_id
            == ticket_id,

            KnowledgeItem.is_active.is_(True),
        )
        .first()
    )

    if existing_draft:
        return existing_draft

    # --------------------------------------------------------
    # BUILD SOLUTION TEXT
    # --------------------------------------------------------

    solution_text = "\n".join(
        f"{index}. {step}"
        for index, step in enumerate(
            cleaned_steps,
            start=1,
        )
    )

    # --------------------------------------------------------
    # BUILD KEYWORDS
    # --------------------------------------------------------

    keywords: list[str] = []

    normalized_category = normalize_text(
        category
    )

    if normalized_category:
        keywords.append(
            normalized_category
        )

    title_tokens = sorted(
        tokenize(title)
    )

    for token in title_tokens:
        if token not in keywords:
            keywords.append(token)

    keywords = keywords[:12]

    # --------------------------------------------------------
    # SAFE CONFIDENCE
    # --------------------------------------------------------

    try:
        safe_confidence = float(
            confidence
        )
    except (TypeError, ValueError):
        safe_confidence = 0.5

    safe_confidence = max(
        0.0,
        min(
            safe_confidence,
            1.0,
        ),
    )

    # --------------------------------------------------------
    # SAFE TITLE
    # --------------------------------------------------------

    clean_title = (
        title.strip()
        if title
        and title.strip()
        else f"Resolved Ticket #{ticket_id}"
    )

    # --------------------------------------------------------
    # SAFE PROBLEM
    # --------------------------------------------------------

    clean_problem = (
        problem_text.strip()
        if problem_text
        and problem_text.strip()
        else clean_title
    )

    # --------------------------------------------------------
    # CREATE PENDING KNOWLEDGE DRAFT
    # --------------------------------------------------------

    knowledge_draft = create_knowledge_item(
        db=db,
        title=clean_title,
        problem_text=clean_problem,
        solution_text=solution_text,
        category=category,
        keywords=keywords,
        source_type="self_learning",
        source_ticket_id=ticket_id,
        source_reference=(
            f"Auto-resolved ticket #{ticket_id}"
        ),
        confidence=safe_confidence,
        is_approved=False,
    )

    return knowledge_draft