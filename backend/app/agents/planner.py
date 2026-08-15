from __future__ import annotations

from typing import Any


PLAYBOOKS = {
    "network": [
        "Confirm whether the issue affects only one device or multiple users.",
        "Check Wi-Fi or Ethernet connectivity.",
        "Verify that the device has a valid IP address.",
        "Test basic internet connectivity.",
        "Disconnect and reconnect the VPN if the issue is VPN-related.",
        "Restart the affected network adapter or application.",
        "Escalate if the network remains unavailable.",
    ],
    "email": [
        "Confirm whether the issue affects sending, receiving, or both.",
        "Check internet connectivity.",
        "Verify the email application is online.",
        "Restart the email application.",
        "Check mailbox storage and synchronization status.",
        "Retry sending or receiving email.",
        "Escalate if the issue continues.",
    ],
    "software": [
        "Confirm the application name and exact error message.",
        "Restart the application.",
        "Check whether the application is up to date.",
        "Restart the device if appropriate.",
        "Verify required services or dependencies are running.",
        "Retry the affected operation.",
        "Escalate if the application still fails.",
    ],
    "hardware": [
        "Confirm the affected hardware component.",
        "Check power and physical connections.",
        "Reconnect the device where safe.",
        "Restart the computer or peripheral.",
        "Check whether the device is detected by the operating system.",
        "Test with another port or cable if available.",
        "Escalate for hardware replacement or repair if required.",
    ],
    "account_access": [
        "Confirm the username or account involved.",
        "Check whether the account is locked or disabled.",
        "Verify the user is using the approved login method.",
        "Do not request or expose the user's password.",
        "Use the authorized password reset or access recovery process.",
        "Escalate privileged or sensitive access changes to an administrator.",
    ],
    "security": [
        "Do not make automated changes to the affected account or device.",
        "Preserve relevant incident details.",
        "Disconnect the affected device from the network if organizational policy requires it.",
        "Avoid deleting suspicious files or evidence.",
        "Escalate immediately to the security or administrator team.",
    ],
    "how_to": [
        "Identify the exact task the user wants to complete.",
        "Provide clear step-by-step instructions.",
        "Ask the user to confirm the expected result.",
        "If unsuccessful, collect the exact error message.",
        "Escalate only if the documented procedure does not resolve the issue.",
    ],
    "other": [
        "Collect additional information about the issue.",
        "Confirm the expected behavior.",
        "Capture any error message or relevant context.",
        "Try a safe basic troubleshooting step.",
        "Escalate if the issue cannot be safely diagnosed.",
    ],
}


def build_resolution_summary(
    category: str,
    priority: str,
    risk_level: str,
) -> str:

    if risk_level == "high":
        return (
            "High-risk ticket detected. "
            "Automatic resolution is disabled and "
            "human escalation is required."
        )

    if risk_level == "medium":
        return (
            "Ticket requires controlled troubleshooting. "
            "Human confirmation or approval may be required "
            "before resolution."
        )

    return (
        f"Low-risk {category} ticket classified with "
        f"{priority} priority. Safe troubleshooting steps "
        "can be suggested automatically."
    )


def build_knowledge_steps(
    knowledge_results: list[dict[str, Any]] | None,
) -> list[str]:

    if not knowledge_results:
        return []

    steps: list[str] = []
    seen: set[str] = set()

    for item in knowledge_results[:3]:
        solution = str(
            item.get("solution_text") or ""
        ).strip()

        if not solution:
            continue

        title = str(
            item.get("title")
            or "Knowledge Base"
        ).strip()

        step = (
            f"Knowledge Base [{title}]: "
            f"{solution}"
        )

        key = step.lower()

        if key in seen:
            continue

        seen.add(key)
        steps.append(step)

    return steps


def create_resolution_plan(
    classification: dict[str, Any],
    title: str = "",
    description: str = "",
    knowledge_results: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:

    category = classification.get(
        "category",
        "other",
    )

    priority = classification.get(
        "priority",
        "medium",
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

    auto_resolve_candidate = bool(
        classification.get(
            "auto_resolve_candidate",
            False,
        )
    )

    playbook_steps = PLAYBOOKS.get(
        category,
        PLAYBOOKS["other"],
    ).copy()

    knowledge_steps = build_knowledge_steps(
        knowledge_results
    )

    # More specific retrieved knowledge first,
    # then generic built-in playbook steps.
    steps = knowledge_steps + playbook_steps

    requires_human = (
        risk_level in {
            "medium",
            "high",
        }
        or category in {
            "account_access",
            "security",
        }
    )

    user_confirmation_required = (
        auto_resolve_candidate
        and not requires_human
    )

    can_attempt_auto_resolution = (
        auto_resolve_candidate
        and risk_level == "low"
        and confidence >= 0.75
        and not requires_human
    )

    if requires_human:
        next_action = "escalate_to_human"

    elif can_attempt_auto_resolution:
        next_action = "suggest_resolution"

    else:
        next_action = "collect_more_information"

    knowledge_items = []

    for item in (knowledge_results or [])[:3]:
        knowledge_items.append(
            {
                "id": item.get("id"),
                "title": item.get("title"),
                "relevance_score": item.get(
                    "relevance_score"
                ),
                "quality_score": item.get(
                    "quality_score"
                ),
                "confidence": item.get(
                    "confidence"
                ),
            }
        )

    return {
        "title": title,
        "description": description,
        "category": category,
        "priority": priority,
        "risk_level": risk_level,
        "confidence": confidence,

        "steps": steps,

        "playbook_steps": playbook_steps,

        "knowledge_steps": knowledge_steps,

        "knowledge_used": bool(
            knowledge_steps
        ),

        "knowledge_items": knowledge_items,

        "resolution_summary": (
            build_resolution_summary(
                category=category,
                priority=priority,
                risk_level=risk_level,
            )
        ),

        "requires_human": requires_human,

        "user_confirmation_required": (
            user_confirmation_required
        ),

        "can_attempt_auto_resolution": (
            can_attempt_auto_resolution
        ),

        "next_action": next_action,
    }