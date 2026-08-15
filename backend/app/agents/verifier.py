from __future__ import annotations

from typing import Any


HIGH_RISK_CATEGORIES = {
    "security",
    "account_access",
}


BLOCKED_AUTO_RESOLVE_TERMS = {
    "password",
    "credential",
    "mfa",
    "otp",
    "admin access",
    "delete account",
    "payment",
    "financial",
    "malware",
    "virus",
    "ransomware",
    "phishing",
    "data breach",
    "compromised",
    "unauthorized access",
}


MIN_AUTO_RESOLVE_CONFIDENCE = 0.75


def _normalize(value: str | None) -> str:
    return (value or "").lower().strip()


def find_blocked_terms(
    title: str,
    description: str,
) -> list[str]:
    text = _normalize(
        f"{title} {description}"
    )

    return sorted(
        term
        for term in BLOCKED_AUTO_RESOLVE_TERMS
        if term in text
    )


def calculate_verification_score(
    classification: dict[str, Any],
    plan: dict[str, Any],
) -> float:
    confidence = float(
        classification.get(
            "confidence",
            0.0,
        )
    )

    score = confidence

    risk_level = classification.get(
        "risk_level",
        "medium",
    )

    if risk_level == "low":
        score += 0.05

    if risk_level == "medium":
        score -= 0.20

    if risk_level == "high":
        score -= 0.40

    if plan.get(
        "requires_human",
        False,
    ):
        score -= 0.10

    if not plan.get("steps"):
        score -= 0.20

    return round(
        max(
            0.0,
            min(
                1.0,
                score,
            ),
        ),
        2,
    )


def verify_resolution(
    classification: dict[str, Any],
    plan: dict[str, Any],
    title: str = "",
    description: str = "",
) -> dict[str, Any]:
    category = classification.get(
        "category",
        "other",
    )

    risk_level = classification.get(
        "risk_level",
        "medium",
    )

    confidence = float(
        classification.get(
            "confidence",
            0.0,
        )
    )

    blocked_terms = find_blocked_terms(
        title=title,
        description=description,
    )

    verification_score = (
        calculate_verification_score(
            classification=classification,
            plan=plan,
        )
    )

    reasons: list[str] = []

    safe_for_auto_resolution = True

    if category in HIGH_RISK_CATEGORIES:
        safe_for_auto_resolution = False
        reasons.append(
            "Sensitive ticket category requires human handling."
        )

    if risk_level != "low":
        safe_for_auto_resolution = False
        reasons.append(
            "Only low-risk tickets can be automatically resolved."
        )

    if confidence < MIN_AUTO_RESOLVE_CONFIDENCE:
        safe_for_auto_resolution = False
        reasons.append(
            "Classification confidence is below the "
            "auto-resolution threshold."
        )

    if blocked_terms:
        safe_for_auto_resolution = False
        reasons.append(
            "Sensitive terms detected in the ticket."
        )

    if not plan.get(
        "can_attempt_auto_resolution",
        False,
    ):
        safe_for_auto_resolution = False
        reasons.append(
            "Planner did not approve automatic resolution."
        )

    if verification_score < MIN_AUTO_RESOLVE_CONFIDENCE:
        safe_for_auto_resolution = False
        reasons.append(
            "Verification score is below the required threshold."
        )

    if safe_for_auto_resolution:
        decision = "approved"
        next_action = "request_user_confirmation"
        reasons.append(
            "Ticket passed automatic resolution safety checks."
        )

    elif plan.get(
        "requires_human",
        False,
    ):
        decision = "rejected"
        next_action = "escalate_to_human"

    else:
        decision = "review_required"
        next_action = "collect_more_information"

    return {
        "decision": decision,
        "safe_for_auto_resolution": (
            safe_for_auto_resolution
        ),
        "verification_score": (
            verification_score
        ),
        "classification_confidence": (
            confidence
        ),
        "risk_level": risk_level,
        "blocked_terms": blocked_terms,
        "reasons": reasons,
        "next_action": next_action,
    }