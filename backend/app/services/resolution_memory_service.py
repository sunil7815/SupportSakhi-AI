from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from typing import Any

from sqlalchemy.orm import Session

from app.db.models.resolution_attempt import ResolutionAttempt


VALID_OUTCOMES = {
    "success",
    "failed",
    "unknown",
}


def normalize_action(
    action_text: str,
) -> str:
    text = action_text.lower().strip()

    return re.sub(
        r"\s+",
        " ",
        text,
    )


def build_action_key(
    action_text: str,
) -> str:
    normalized = normalize_action(
        action_text
    )

    digest = hashlib.sha256(
        normalized.encode("utf-8")
    ).hexdigest()

    return digest[:24]


def remember_attempt(
    db: Session,
    ticket_id: int,
    action_text: str,
    outcome: str,
    category: str | None = None,
    confidence: float | None = None,
    failure_reason: str | None = None,
    source: str = "agent",
) -> ResolutionAttempt:
    clean_outcome = outcome.lower().strip()

    if clean_outcome not in VALID_OUTCOMES:
        raise ValueError(
            f"Unsupported outcome: {outcome}"
        )

    attempt = ResolutionAttempt(
        ticket_id=ticket_id,
        category=category,
        action_key=build_action_key(
            action_text
        ),
        action_text=action_text.strip(),
        outcome=clean_outcome,
        confidence=confidence,
        failure_reason=failure_reason,
        source=source,
    )

    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    return attempt


def remember_failure(
    db: Session,
    ticket_id: int,
    action_text: str,
    category: str | None = None,
    confidence: float | None = None,
    failure_reason: str | None = None,
) -> ResolutionAttempt:
    return remember_attempt(
        db=db,
        ticket_id=ticket_id,
        action_text=action_text,
        outcome="failed",
        category=category,
        confidence=confidence,
        failure_reason=failure_reason,
    )


def remember_success(
    db: Session,
    ticket_id: int,
    action_text: str,
    category: str | None = None,
    confidence: float | None = None,
) -> ResolutionAttempt:
    return remember_attempt(
        db=db,
        ticket_id=ticket_id,
        action_text=action_text,
        outcome="success",
        category=category,
        confidence=confidence,
    )


def get_attempts(
    db: Session,
    category: str | None = None,
    ticket_id: int | None = None,
    outcome: str | None = None,
    limit: int = 200,
) -> list[ResolutionAttempt]:
    query = db.query(
        ResolutionAttempt
    )

    if category:
        query = query.filter(
            ResolutionAttempt.category
            == category
        )

    if ticket_id is not None:
        query = query.filter(
            ResolutionAttempt.ticket_id
            == ticket_id
        )

    if outcome:
        query = query.filter(
            ResolutionAttempt.outcome
            == outcome
        )

    return (
        query
        .order_by(
            ResolutionAttempt.created_at.desc()
        )
        .limit(limit)
        .all()
    )


def get_failed_attempts(
    db: Session,
    category: str | None = None,
    ticket_id: int | None = None,
    limit: int = 100,
) -> list[ResolutionAttempt]:
    return get_attempts(
        db=db,
        category=category,
        ticket_id=ticket_id,
        outcome="failed",
        limit=limit,
    )


def get_successful_attempts(
    db: Session,
    category: str | None = None,
    ticket_id: int | None = None,
    limit: int = 100,
) -> list[ResolutionAttempt]:
    return get_attempts(
        db=db,
        category=category,
        ticket_id=ticket_id,
        outcome="success",
        limit=limit,
    )


def get_action_statistics(
    db: Session,
    category: str | None = None,
) -> dict[str, dict[str, Any]]:
    attempts = get_attempts(
        db=db,
        category=category,
        limit=500,
    )

    stats: dict[
        str,
        dict[str, Any],
    ] = defaultdict(
        lambda: {
            "successes": 0,
            "failures": 0,
            "attempts": 0,
            "score": 0.0,
            "action_text": "",
        }
    )

    for attempt in attempts:
        item = stats[
            attempt.action_key
        ]

        item["action_text"] = (
            attempt.action_text
        )

        item["attempts"] += 1

        confidence = (
            attempt.confidence
            if attempt.confidence
            is not None
            else 0.5
        )

        if attempt.outcome == "success":
            item["successes"] += 1
            item["score"] += (
                2.0 * confidence
            )

        elif attempt.outcome == "failed":
            item["failures"] += 1
            item["score"] -= (
                1.0 * confidence
            )

    for item in stats.values():
        item["score"] = round(
            item["score"],
            3,
        )

    return dict(stats)


def get_ticket_failed_keys(
    db: Session,
    ticket_id: int,
) -> set[str]:
    attempts = get_failed_attempts(
        db=db,
        ticket_id=ticket_id,
    )

    return {
        attempt.action_key
        for attempt in attempts
    }


def rank_resolution_steps(
    db: Session,
    steps: list[str],
    category: str | None = None,
    ticket_id: int | None = None,
) -> dict[str, Any]:
    category_stats = (
        get_action_statistics(
            db=db,
            category=category,
        )
    )

    ticket_failed_keys: set[str] = set()

    if ticket_id is not None:
        ticket_failed_keys = (
            get_ticket_failed_keys(
                db=db,
                ticket_id=ticket_id,
            )
        )

    ranked_steps: list[
        tuple[float, int, str]
    ] = []

    skipped_same_ticket: list[str] = []

    memory_details: list[
        dict[str, Any]
    ] = []

    for original_index, step in enumerate(
        steps
    ):
        action_key = build_action_key(
            step
        )

        if (
            action_key
            in ticket_failed_keys
        ):
            skipped_same_ticket.append(
                step
            )

            memory_details.append(
                {
                    "step": step,
                    "decision": (
                        "hard_skip"
                    ),
                    "reason": (
                        "Previously failed "
                        "on this ticket."
                    ),
                }
            )

            continue

        historical = (
            category_stats.get(
                action_key,
                {},
            )
        )

        historical_score = float(
            historical.get(
                "score",
                0.0,
            )
        )

        successes = int(
            historical.get(
                "successes",
                0,
            )
        )

        failures = int(
            historical.get(
                "failures",
                0,
            )
        )

        rank_score = historical_score

        ranked_steps.append(
            (
                rank_score,
                original_index,
                step,
            )
        )

        memory_details.append(
            {
                "step": step,
                "decision": "rank",
                "historical_score": (
                    historical_score
                ),
                "successes": successes,
                "failures": failures,
            }
        )

    ranked_steps.sort(
        key=lambda item: (
            -item[0],
            item[1],
        )
    )

    usable_steps = [
        item[2]
        for item in ranked_steps
    ]

    repeated_failure_count = len(
        skipped_same_ticket
    )

    escalation_recommended = (
        repeated_failure_count >= 3
        or not usable_steps
    )

    return {
        "usable_steps": usable_steps,

        "skipped_failed_steps": (
            skipped_same_ticket
        ),

        "failure_memory_used": bool(
            skipped_same_ticket
            or any(
                detail.get(
                    "historical_score",
                    0,
                )
                != 0
                for detail
                in memory_details
            )
        ),

        "memory_details": (
            memory_details
        ),

        "repeated_failure_count": (
            repeated_failure_count
        ),

        "escalation_recommended": (
            escalation_recommended
        ),
    }


def filter_failed_steps(
    db: Session,
    steps: list[str],
    category: str | None = None,
    ticket_id: int | None = None,
) -> dict[str, Any]:
    return rank_resolution_steps(
        db=db,
        steps=steps,
        category=category,
        ticket_id=ticket_id,
    )


def get_memory_summary(
    db: Session,
    category: str | None = None,
) -> dict[str, Any]:
    failed = get_failed_attempts(
        db=db,
        category=category,
    )

    successful = (
        get_successful_attempts(
            db=db,
            category=category,
        )
    )

    statistics = (
        get_action_statistics(
            db=db,
            category=category,
        )
    )

    ranked_actions = sorted(
        statistics.values(),
        key=lambda item: item[
            "score"
        ],
        reverse=True,
    )

    return {
        "category": category,

        "failed_attempts": len(
            failed
        ),

        "successful_attempts": len(
            successful
        ),

        "best_known_actions": (
            ranked_actions[:10]
        ),

        "known_failed_actions": [
            attempt.action_text
            for attempt in failed[:10]
        ],

        "known_successful_actions": [
            attempt.action_text
            for attempt
            in successful[:10]
        ],
    }