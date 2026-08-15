from __future__ import annotations

import re
from typing import Any


CATEGORY_RULES = {
    "account_access": [
        "password",
        "login",
        "log in",
        "sign in",
        "signin",
        "account locked",
        "locked out",
        "forgot password",
        "password reset",
        "access denied",
        "authentication",
        "mfa",
        "otp",
    ],
    "network": [
        "wifi",
        "wi-fi",
        "internet",
        "network",
        "vpn",
        "dns",
        "lan",
        "connection",
        "connectivity",
        "offline",
        "no internet",
    ],
    "email": [
        "outlook",
        "email",
        "mail",
        "inbox",
        "smtp",
        "imap",
        "cannot send mail",
        "cannot receive mail",
    ],
    "software": [
        "application",
        "software",
        "app",
        "crash",
        "crashing",
        "installation",
        "install",
        "update",
        "not opening",
        "not responding",
        "error message",
    ],
    "hardware": [
        "laptop",
        "desktop",
        "monitor",
        "keyboard",
        "mouse",
        "printer",
        "battery",
        "camera",
        "hard disk",
        "ssd",
        "ram",
        "hardware",
    ],
    "security": [
        "phishing",
        "malware",
        "virus",
        "ransomware",
        "hacked",
        "compromised",
        "data breach",
        "suspicious login",
        "unauthorized access",
        "security incident",
    ],
    "how_to": [
        "how to",
        "how can i",
        "how do i",
        "guide",
        "steps to",
        "help me configure",
        "help me setup",
        "help me set up",
    ],
}


CRITICAL_SIGNALS = [
    "ransomware",
    "data breach",
    "production down",
    "system down",
    "company wide outage",
    "company-wide outage",
    "hacked",
    "compromised",
    "unauthorized access",
]

HIGH_PRIORITY_SIGNALS = [
    "unable to access",
    "cannot access",
    "can't access",
    "not working",
    "vpn down",
    "service unavailable",
    "multiple users",
    "business impact",
    "blocked",
    "urgent",
]

LOW_PRIORITY_SIGNALS = [
    "how to",
    "how can i",
    "guide",
    "information",
    "question",
    "request",
]


AUTO_RESOLVE_ALLOWED_CATEGORIES = {
    "network",
    "email",
    "software",
    "how_to",
}

AUTO_RESOLVE_BLOCKED_TERMS = [
    "password",
    "credential",
    "account",
    "mfa",
    "otp",
    "admin access",
    "delete",
    "payment",
    "financial",
    "security",
    "malware",
    "virus",
    "ransomware",
    "phishing",
    "data breach",
    "compromised",
    "unauthorized",
]


def _normalize(value: str | None) -> str:
    value = value or ""
    value = value.lower().strip()
    value = re.sub(r"\s+", " ", value)
    return value


def _contains(text: str, phrase: str) -> bool:
    return phrase.lower() in text


def _matched_keywords(
    text: str,
    keywords: list[str],
) -> list[str]:
    return [
        keyword
        for keyword in keywords
        if _contains(text, keyword)
    ]


def classify_category(
    title: str,
    description: str,
) -> tuple[str, float, list[str]]:
    text = _normalize(
        f"{title} {description}"
    )

    scores: dict[str, list[str]] = {}

    for category, keywords in CATEGORY_RULES.items():
        matches = _matched_keywords(
            text,
            keywords,
        )

        if matches:
            scores[category] = matches

    if not scores:
        return (
            "other",
            0.50,
            [],
        )

    category = max(
        scores,
        key=lambda item: len(scores[item]),
    )

    matches = scores[category]

    confidence = min(
        0.95,
        0.60 + (len(matches) * 0.08),
    )

    return (
        category,
        round(confidence, 2),
        matches,
    )


def classify_priority(
    title: str,
    description: str,
    category: str,
) -> tuple[str, list[str]]:
    text = _normalize(
        f"{title} {description}"
    )

    critical_matches = _matched_keywords(
        text,
        CRITICAL_SIGNALS,
    )

    if critical_matches:
        return "urgent", critical_matches

    high_matches = _matched_keywords(
        text,
        HIGH_PRIORITY_SIGNALS,
    )

    if (
        category == "security"
        or high_matches
    ):
        return "high", high_matches

    low_matches = _matched_keywords(
        text,
        LOW_PRIORITY_SIGNALS,
    )

    if low_matches:
        return "low", low_matches

    return "medium", []


def classify_risk(
    title: str,
    description: str,
    category: str,
) -> tuple[str, list[str]]:
    text = _normalize(
        f"{title} {description}"
    )

    blocked_matches = _matched_keywords(
        text,
        AUTO_RESOLVE_BLOCKED_TERMS,
    )

    if category == "security":
        return "high", blocked_matches

    if category == "account_access":
        return "medium", blocked_matches

    if blocked_matches:
        return "medium", blocked_matches

    return "low", []


def can_auto_resolve(
    category: str,
    confidence: float,
    risk_level: str,
    title: str,
    description: str,
) -> bool:
    text = _normalize(
        f"{title} {description}"
    )

    if category not in AUTO_RESOLVE_ALLOWED_CATEGORIES:
        return False

    if confidence < 0.75:
        return False

    if risk_level != "low":
        return False

    if any(
        term in text
        for term in AUTO_RESOLVE_BLOCKED_TERMS
    ):
        return False

    return True


def classify_ticket(
    title: str,
    description: str,
) -> dict[str, Any]:
    (
        category,
        confidence,
        category_matches,
    ) = classify_category(
        title,
        description,
    )

    (
        priority,
        priority_matches,
    ) = classify_priority(
        title,
        description,
        category,
    )

    (
        risk_level,
        risk_matches,
    ) = classify_risk(
        title,
        description,
        category,
    )

    auto_resolve_candidate = can_auto_resolve(
        category=category,
        confidence=confidence,
        risk_level=risk_level,
        title=title,
        description=description,
    )

    return {
        "category": category,
        "priority": priority,
        "confidence": confidence,
        "risk_level": risk_level,
        "auto_resolve_candidate": auto_resolve_candidate,
        "matched_signals": {
            "category": category_matches,
            "priority": priority_matches,
            "risk": risk_matches,
        },
        "reason": (
            "Ticket classified using SupportSakhi "
            "rule-based agent safety policies."
        ),
    }