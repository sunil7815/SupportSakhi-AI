from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.agents.classifier import (
    classify_ticket,
)
from app.agents.planner import (
    create_resolution_plan,
)
from app.agents.skeptic import (
    review_resolution,
)
from app.agents.verifier import (
    verify_resolution,
)
from app.services.knowledge_service import (
    retrieve_relevant_knowledge,
)


def build_final_agent_decision(
    verification: dict[str, Any],
    skeptic_review: dict[str, Any],
) -> dict[str, Any]:

    verifier_decision = verification.get(
        "decision",
        "review_required",
    )

    verifier_next_action = verification.get(
        "next_action",
        "collect_more_information",
    )

    skeptic_decision = skeptic_review.get(
        "decision",
        "review_required",
    )

    skeptic_next_action = skeptic_review.get(
        "next_action",
        "human_review",
    )

    reasons: list[str] = []

    # ========================================================
    # HARD REJECTION
    # ========================================================

    if (
        verifier_decision == "rejected"
        or verifier_next_action == "escalate_to_human"
        or skeptic_decision == "reject"
        or skeptic_next_action == "escalate_to_human"
    ):

        reasons.append(
            "At least one verification agent "
            "rejected automatic resolution."
        )

        return {
            "decision": "rejected",
            "next_action": "escalate_to_human",
            "all_agents_approved": False,
            "reasons": reasons,
        }

    # ========================================================
    # HUMAN REVIEW REQUIRED
    # ========================================================

    if (
        verifier_decision == "review_required"
        or skeptic_decision == "review_required"
        or skeptic_next_action == "human_review"
    ):

        reasons.append(
            "At least one verification agent "
            "requires human review."
        )

        return {
            "decision": "review_required",
            "next_action": "human_review",
            "all_agents_approved": False,
            "reasons": reasons,
        }

    # ========================================================
    # MORE INFORMATION REQUIRED
    # ========================================================

    if verifier_next_action == "collect_more_information":

        reasons.append(
            "The verifier requires additional "
            "information before resolution."
        )

        return {
            "decision": "more_information_required",
            "next_action": "collect_more_information",
            "all_agents_approved": False,
            "reasons": reasons,
        }

    # ========================================================
    # ALL AGENTS APPROVED
    # ========================================================

    if (
        verifier_decision == "approved"
        and skeptic_decision == "approved"
    ):

        reasons.extend(
            [
                (
                    "The safety verifier approved "
                    "the proposed resolution."
                ),
                (
                    "The skeptic agent found no "
                    "blocking contradiction."
                ),
            ]
        )

        return {
            "decision": "approved",
            "next_action": "request_user_confirmation",
            "all_agents_approved": True,
            "reasons": reasons,
        }

    # ========================================================
    # SAFE FALLBACK
    # ========================================================

    reasons.append(
        "The multi-agent system could not "
        "reach a safe approval decision."
    )

    return {
        "decision": "review_required",
        "next_action": "human_review",
        "all_agents_approved": False,
        "reasons": reasons,
    }


def run_support_agent(
    title: str,
    description: str,
    db: Session | None = None,
) -> dict[str, Any]:

    # ========================================================
    # AGENT 1 - CLASSIFIER
    # ========================================================

    classification = classify_ticket(
        title=title,
        description=description,
    )

    category = classification.get(
        "category",
        "other",
    )

    # ========================================================
    # RAG - KNOWLEDGE RETRIEVAL
    # ========================================================

    knowledge_results: list[
        dict[str, Any]
    ] = []

    knowledge_retrieval_status = (
        "not_requested"
    )

    if db is not None:

        query_text = (
            f"{title} {description}"
        ).strip()

        try:
            knowledge_results = (
                retrieve_relevant_knowledge(
                    db=db,
                    query_text=query_text,
                    category=category,
                    limit=3,
                    minimum_score=0.15,
                )
            )

            if knowledge_results:
                knowledge_retrieval_status = (
                    "matched"
                )
            else:
                knowledge_retrieval_status = (
                    "no_match"
                )

        except Exception:
            # Knowledge retrieval is an enhancement.
            # A KB failure must not crash the support agent.
            knowledge_results = []

            knowledge_retrieval_status = (
                "unavailable"
            )

    # ========================================================
    # AGENT 2 - RAG-AWARE RESOLVER / PLANNER
    # ========================================================

    plan = create_resolution_plan(
        classification=classification,
        title=title,
        description=description,
        knowledge_results=knowledge_results,
    )

    # ========================================================
    # AGENT 3 - SAFETY VERIFIER
    # ========================================================

    verification = verify_resolution(
        classification=classification,
        plan=plan,
        title=title,
        description=description,
    )

    # ========================================================
    # AGENT 4 - SKEPTIC
    # ========================================================

    skeptic_review = review_resolution(
        classification=classification,
        plan=plan,
        verification=verification,
    )

    # ========================================================
    # FINAL MULTI-AGENT DECISION
    # ========================================================

    multi_agent_verification = (
        build_final_agent_decision(
            verification=verification,
            skeptic_review=skeptic_review,
        )
    )

    final_next_action = (
        multi_agent_verification.get(
            "next_action",
            "human_review",
        )
    )

    # ========================================================
    # KNOWLEDGE METADATA
    # ========================================================

    knowledge_sources = []

    for item in knowledge_results:
        knowledge_sources.append(
            {
                "id": item.get("id"),
                "title": item.get("title"),
                "category": item.get(
                    "category"
                ),
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
        "classification": classification,

        "knowledge_retrieval": {
            "status": (
                knowledge_retrieval_status
            ),
            "used": bool(
                knowledge_results
            ),
            "result_count": len(
                knowledge_results
            ),
            "sources": (
                knowledge_sources
            ),
        },

        "plan": plan,

        "verification": verification,

        "skeptic_review": (
            skeptic_review
        ),

        "multi_agent_verification": (
            multi_agent_verification
        ),

        "agent_decision": (
            final_next_action
        ),
    }