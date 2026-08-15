from __future__ import annotations

import re
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db.models.knowledge_item import KnowledgeItem


# ============================================================
# TEXT HELPERS
# ============================================================

def normalize_text(value: str | None) -> str:
    if not value:
        return ""

    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    value = re.sub(r"\s+", " ", value)

    return value


def tokenize(value: str | None) -> set[str]:
    normalized = normalize_text(value)

    if not normalized:
        return set()

    return {
        token
        for token in normalized.split()
        if len(token) > 1
    }


# ============================================================
# SERIALIZE KNOWLEDGE ITEM
# ============================================================

def serialize_knowledge_item(
    item: KnowledgeItem,
) -> dict[str, Any]:

    return {
        "id": item.id,
        "title": item.title,
        "category": item.category,
        "problem_text": item.problem_text,
        "solution_text": item.solution_text,
        "keywords": item.keywords or [],
        "source_type": item.source_type,
        "source_ticket_id": item.source_ticket_id,
        "source_reference": item.source_reference,
        "confidence": float(item.confidence or 0.0),
        "success_count": item.success_count or 0,
        "failure_count": item.failure_count or 0,
        "is_approved": item.is_approved,
        "is_active": item.is_active,
        "created_at": (
            item.created_at.isoformat()
            if item.created_at
            else None
        ),
        "updated_at": (
            item.updated_at.isoformat()
            if item.updated_at
            else None
        ),
    }


# ============================================================
# CREATE KNOWLEDGE ITEM
# ============================================================

def create_knowledge_item(
    db: Session,
    title: str,
    problem_text: str,
    solution_text: str,
    category: str | None = None,
    keywords: list[str] | None = None,
    source_type: str = "manual",
    source_ticket_id: int | None = None,
    source_reference: str | None = None,
    confidence: float = 0.5,
    is_approved: bool = False,
) -> KnowledgeItem:

    confidence = max(
        0.0,
        min(float(confidence), 1.0),
    )

    clean_keywords: list[str] = []

    for keyword in keywords or []:
        normalized_keyword = normalize_text(keyword)

        if (
            normalized_keyword
            and normalized_keyword not in clean_keywords
        ):
            clean_keywords.append(
                normalized_keyword
            )

    item = KnowledgeItem(
        title=title.strip(),
        problem_text=problem_text.strip(),
        solution_text=solution_text.strip(),
        category=(
            normalize_text(category)
            if category
            else None
        ),
        keywords=clean_keywords,
        source_type=source_type,
        source_ticket_id=source_ticket_id,
        source_reference=source_reference,
        confidence=confidence,
        success_count=0,
        failure_count=0,
        is_approved=is_approved,
        is_active=True,
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    return item


# ============================================================
# QUALITY SCORE
# ============================================================

def calculate_quality_score(
    item: KnowledgeItem,
) -> float:

    confidence = float(
        item.confidence or 0.0
    )

    success_count = (
        item.success_count or 0
    )

    failure_count = (
        item.failure_count or 0
    )

    total_attempts = (
        success_count + failure_count
    )

    if total_attempts > 0:
        success_rate = (
            success_count
            / total_attempts
        )
    else:
        success_rate = 0.5

    quality_score = (
        confidence * 0.60
        + success_rate * 0.40
    )

    return round(
        min(
            max(quality_score, 0.0),
            1.0,
        ),
        4,
    )


# ============================================================
# RELEVANCE SCORE
# ============================================================

def calculate_relevance_score(
    item: KnowledgeItem,
    query_text: str,
    category: str | None = None,
) -> float:

    query_tokens = tokenize(
        query_text
    )

    if not query_tokens:
        return 0.0

    title_tokens = tokenize(
        item.title
    )

    problem_tokens = tokenize(
        item.problem_text
    )

    solution_tokens = tokenize(
        item.solution_text
    )

    keyword_tokens: set[str] = set()

    for keyword in item.keywords or []:
        keyword_tokens.update(
            tokenize(keyword)
        )

    def overlap_score(
        candidate_tokens: set[str],
    ) -> float:

        if not candidate_tokens:
            return 0.0

        overlap = (
            query_tokens
            & candidate_tokens
        )

        return (
            len(overlap)
            / len(query_tokens)
        )

    score = 0.0

    score += (
        overlap_score(title_tokens)
        * 0.20
    )

    score += (
        overlap_score(problem_tokens)
        * 0.30
    )

    score += (
        overlap_score(solution_tokens)
        * 0.10
    )

    score += (
        overlap_score(keyword_tokens)
        * 0.25
    )

    if (
        category
        and item.category
        and normalize_text(category)
        == normalize_text(item.category)
    ):
        score += 0.25

    score += (
        calculate_quality_score(item)
        * 0.15
    )

    return round(
        score,
        4,
    )


# ============================================================
# RETRIEVE RELEVANT KNOWLEDGE
# ============================================================

def retrieve_relevant_knowledge(
    db: Session,
    query_text: str,
    category: str | None = None,
    limit: int = 5,
    minimum_score: float = 0.15,
) -> list[dict[str, Any]]:

    query = (
        db.query(KnowledgeItem)
        .filter(
            KnowledgeItem.is_active.is_(True),
            KnowledgeItem.is_approved.is_(True),
        )
    )

    if category:
        normalized_category = (
            normalize_text(category)
        )

        query = query.filter(
            or_(
                KnowledgeItem.category
                == normalized_category,
                KnowledgeItem.category.is_(None),
            )
        )

    candidates = (
        query
        .order_by(
            KnowledgeItem.confidence.desc()
        )
        .limit(200)
        .all()
    )

    ranked_results: list[
        dict[str, Any]
    ] = []

    for item in candidates:

        relevance_score = (
            calculate_relevance_score(
                item=item,
                query_text=query_text,
                category=category,
            )
        )

        if (
            relevance_score
            < minimum_score
        ):
            continue

        serialized = (
            serialize_knowledge_item(item)
        )

        serialized[
            "relevance_score"
        ] = relevance_score

        serialized[
            "quality_score"
        ] = calculate_quality_score(
            item
        )

        ranked_results.append(
            serialized
        )

    ranked_results.sort(
        key=lambda result: (
            result[
                "relevance_score"
            ],
            result[
                "quality_score"
            ],
        ),
        reverse=True,
    )

    safe_limit = max(
        1,
        min(limit, 20),
    )

    return ranked_results[
        :safe_limit
    ]


# ============================================================
# BUILD KNOWLEDGE CONTEXT
# ============================================================

def build_knowledge_context(
    knowledge_results: list[
        dict[str, Any]
    ],
) -> str:

    if not knowledge_results:
        return ""

    sections: list[str] = []

    for index, item in enumerate(
        knowledge_results,
        start=1,
    ):

        section = (
            f"Knowledge Item {index}\n"
            f"Title: {item.get('title')}\n"
            f"Category: {item.get('category')}\n"
            f"Problem: {item.get('problem_text')}\n"
            f"Solution: {item.get('solution_text')}\n"
            f"Confidence: {item.get('confidence')}\n"
            f"Relevance: {item.get('relevance_score')}"
        )

        sections.append(
            section
        )

    return "\n\n".join(
        sections
    )


# ============================================================
# RECORD KNOWLEDGE OUTCOME
# ============================================================

def record_knowledge_outcome(
    db: Session,
    knowledge_item_id: int,
    successful: bool,
) -> KnowledgeItem | None:

    item = (
        db.query(KnowledgeItem)
        .filter(
            KnowledgeItem.id
            == knowledge_item_id
        )
        .first()
    )

    if not item:
        return None

    if successful:
        item.success_count = (
            item.success_count or 0
        ) + 1

    else:
        item.failure_count = (
            item.failure_count or 0
        ) + 1

    success_count = (
        item.success_count or 0
    )

    failure_count = (
        item.failure_count or 0
    )

    total = (
        success_count
        + failure_count
    )

    if total > 0:

        success_rate = (
            success_count
            / total
        )

        old_confidence = float(
            item.confidence or 0.5
        )

        item.confidence = round(
            (
                old_confidence
                * 0.7
                + success_rate
                * 0.3
            ),
            4,
        )

    db.commit()
    db.refresh(item)

    return item


# ============================================================
# APPROVE KNOWLEDGE ITEM
# ============================================================

def approve_knowledge_item(
    db: Session,
    knowledge_item_id: int,
) -> KnowledgeItem | None:

    item = (
        db.query(KnowledgeItem)
        .filter(
            KnowledgeItem.id
            == knowledge_item_id
        )
        .first()
    )

    if not item:
        return None

    item.is_approved = True
    item.is_active = True

    db.commit()
    db.refresh(item)

    return item


# ============================================================
# DEACTIVATE KNOWLEDGE ITEM
# ============================================================

def deactivate_knowledge_item(
    db: Session,
    knowledge_item_id: int,
) -> KnowledgeItem | None:

    item = (
        db.query(KnowledgeItem)
        .filter(
            KnowledgeItem.id
            == knowledge_item_id
        )
        .first()
    )

    if not item:
        return None

    item.is_active = False

    db.commit()
    db.refresh(item)

    return item