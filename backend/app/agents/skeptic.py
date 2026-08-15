from __future__ import annotations

from typing import Any


SENSITIVE_CATEGORIES = {
    "account_access",
    "security",
}

HIGH_RISK_LEVELS = {
    "high",
    "critical",
}

DANGEROUS_TERMS = {
    "delete",
    "format",
    "factory reset",
    "disable antivirus",
    "disable firewall",
    "remove security",
    "bypass",
    "credential",
    "password",
    "otp",
    "mfa",
    "payment",
    "bank",
    "malware",
    "ransomware",
    "phishing",
    "registry",
    "admin access",
}

WEAK_ACTION_TERMS = {
    "maybe",
    "probably",
    "possibly",
    "try anything",
    "unknown",
}


def normalize_text(
    value: str | None,
) -> str:
    return (
        value or ""
    ).lower().strip()


def collect_plan_text(
    plan: dict[str, Any],
) -> str:
    parts: list[str] = []

    summary = plan.get(
        "resolution_summary"
    )

    if summary:
        parts.append(
            str(summary)
        )

    steps = plan.get(
        "steps",
        [],
    )

    for step in steps:
        parts.append(
            str(step)
        )

    return " ".join(
        parts
    ).lower()


def find_terms(
    text: str,
    terms: set[str],
) -> list[str]:
    return sorted(
        term
        for term in terms
        if term in text
    )


def review_resolution(
    classification: dict[str, Any],
    plan: dict[str, Any],
    verification: dict[str, Any],
) -> dict[str, Any]:

    category = normalize_text(
        classification.get(
            "category"
        )
    )

    risk_level = normalize_text(
        classification.get(
            "risk_level"
        )
    )

    confidence = float(
        classification.get(
            "confidence",
            0.0,
        )
        or 0.0
    )

    plan_steps = plan.get(
        "steps",
        [],
    )

    plan_text = collect_plan_text(
        plan
    )

    dangerous_terms = find_terms(
        plan_text,
        DANGEROUS_TERMS,
    )

    weak_terms = find_terms(
        plan_text,
        WEAK_ACTION_TERMS,
    )

    verifier_safe = bool(
        verification.get(
            "safe_for_auto_resolution",
            False,
        )
    )

    verification_score = float(
        verification.get(
            "verification_score",
            0.0,
        )
        or 0.0
    )

    concerns: list[str] = []

    skeptic_score = 1.0

    # ========================================================
    # CHECK 1 - PLAN EXISTS
    # ========================================================

    if not plan_steps:
        concerns.append(
            "The resolver did not provide "
            "troubleshooting steps."
        )

        skeptic_score -= 0.45

    # ========================================================
    # CHECK 2 - CLASSIFICATION CONFIDENCE
    # ========================================================

    if confidence < 0.60:
        concerns.append(
            "Ticket classification confidence "
            "is too low."
        )

        skeptic_score -= 0.30

    elif confidence < 0.75:
        concerns.append(
            "Ticket classification confidence "
            "is moderate."
        )

        skeptic_score -= 0.10

    # ========================================================
    # CHECK 3 - HIGH RISK
    # ========================================================

    if risk_level in HIGH_RISK_LEVELS:
        concerns.append(
            "The issue has a high-risk "
            "classification."
        )

        skeptic_score -= 0.50

    # ========================================================
    # CHECK 4 - SENSITIVE CATEGORY
    # ========================================================

    if category in SENSITIVE_CATEGORIES:
        concerns.append(
            "Sensitive ticket category requires "
            "additional human verification."
        )

        skeptic_score -= 0.45

    # ========================================================
    # CHECK 5 - DANGEROUS ACTIONS
    # ========================================================

    if dangerous_terms:
        concerns.append(
            "Potentially sensitive or destructive "
            "actions were found in the plan."
        )

        skeptic_score -= 0.50

    # ========================================================
    # CHECK 6 - WEAK / UNCERTAIN LANGUAGE
    # ========================================================

    if weak_terms:
        concerns.append(
            "The resolution contains uncertain "
            "or weak troubleshooting language."
        )

        skeptic_score -= 0.15

    # ========================================================
    # CHECK 7 - SAFETY VERIFIER AGREEMENT
    # ========================================================

    if not verifier_safe:
        concerns.append(
            "The safety verifier did not approve "
            "automatic resolution."
        )

        skeptic_score -= 0.50

    if verification_score < 0.75:
        concerns.append(
            "The safety verification score is "
            "below the required threshold."
        )

        skeptic_score -= 0.25

    # ========================================================
    # NORMALIZE SCORE
    # ========================================================

    skeptic_score = max(
        0.0,
        min(
            skeptic_score,
            1.0,
        ),
    )

    skeptic_score = round(
        skeptic_score,
        2,
    )

    # ========================================================
    # FINAL SKEPTIC DECISION
    # ========================================================

    if (
        dangerous_terms
        or category in SENSITIVE_CATEGORIES
        or risk_level in HIGH_RISK_LEVELS
        or not verifier_safe
    ):
        decision = "reject"

        next_action = (
            "escalate_to_human"
        )

    elif (
        skeptic_score < 0.70
        or confidence < 0.60
        or verification_score < 0.75
    ):
        decision = (
            "review_required"
        )

        next_action = (
            "human_review"
        )

    else:
        decision = "approved"

        next_action = (
            "continue_resolution"
        )

    if decision == "approved":
        reasons = [
            (
                "The skeptic agent found no "
                "blocking contradiction in the "
                "resolver plan."
            ),
            (
                "Classification confidence and "
                "safety verification are within "
                "acceptable limits."
            ),
        ]
    else:
        reasons = concerns.copy()

    return {
        "decision": decision,

        "skeptic_score": (
            skeptic_score
        ),

        "category": category,

        "risk_level": risk_level,

        "classification_confidence": (
            confidence
        ),

        "verification_score": (
            verification_score
        ),

        "dangerous_terms": (
            dangerous_terms
        ),

        "weak_terms": (
            weak_terms
        ),

        "concerns": concerns,

        "reasons": reasons,

        "next_action": (
            next_action
        ),
    }