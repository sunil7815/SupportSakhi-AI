from __future__ import annotations

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.agents.agent import run_support_agent
from app.core.security import get_current_user
from app.db.database import get_db
from app.db.models.ticket import Ticket
from app.db.models.user import User

from app.services.resolution_memory_service import (
    filter_failed_steps,
    get_memory_summary,
    remember_failure,
    remember_success,
)

from app.services.resolution_proof_service import (
    create_resolution_proof,
    get_proof_summary,
)

from app.services.sla_service import (
    sync_ticket_sla,
)


router = APIRouter(
    prefix="/chat",
    tags=["Agentic Chat"],
)


# ============================================================
# REQUEST MODELS
# ============================================================

class ChatMessageRequest(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=2000,
    )

    ticket_id: int | None = None


class ResolutionConfirmationRequest(BaseModel):
    resolved: bool

    attempted_steps: list[str] = Field(
        default_factory=list,
        max_length=20,
    )

    failure_reason: str | None = Field(
        default=None,
        max_length=1000,
    )


# ============================================================
# ACCESS CONTROL
# ============================================================

def get_ticket_for_user(
    db: Session,
    ticket_id: int,
    current_user: User,
) -> Ticket:

    ticket = (
        db.query(Ticket)
        .filter(
            Ticket.id == ticket_id
        )
        .first()
    )

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found",
        )

    if (
        ticket.user_id != current_user.id
        and ticket.assigned_to_id
        != current_user.id
        and current_user.role != "admin"
    ):
        raise HTTPException(
            status_code=403,
            detail=(
                "You do not have permission "
                "to access this ticket"
            ),
        )

    return ticket


# ============================================================
# PROOF SERIALIZER
# ============================================================

def serialize_resolution_proof(
    proof,
) -> dict:

    return {
        "id": proof.id,

        "ticket_id": proof.ticket_id,

        "resolution_attempt_id": (
            proof.resolution_attempt_id
        ),

        "confirmed_by_user_id": (
            proof.confirmed_by_user_id
        ),

        "proof_status": (
            proof.proof_status
        ),

        "proof_type": (
            proof.proof_type
        ),

        "successful_action": (
            proof.successful_action
        ),

        "user_confirmed": (
            proof.user_confirmed
        ),

        "agent_confidence": (
            proof.agent_confidence
        ),

        "verification_score": (
            proof.verification_score
        ),

        "safety_decision": (
            proof.safety_decision
        ),

        "safe_for_auto_resolution": (
            proof.safe_for_auto_resolution
        ),

        "evidence": (
            proof.evidence
        ),

        "resolution_reason": (
            proof.resolution_reason
        ),

        "created_at": (
            proof.created_at.isoformat()
            if proof.created_at
            else None
        ),

        "verified_at": (
            proof.verified_at.isoformat()
            if proof.verified_at
            else None
        ),
    }


# ============================================================
# MULTI-AGENT GATE
# ============================================================

def get_multi_agent_gate(
    agent_result: dict,
) -> dict:

    verification = agent_result.get(
        "verification",
        {},
    )

    skeptic_review = agent_result.get(
        "skeptic_review",
        {},
    )

    multi_agent = agent_result.get(
        "multi_agent_verification",
        {},
    )

    verifier_approved = (
        verification.get("decision")
        == "approved"
        and bool(
            verification.get(
                "safe_for_auto_resolution",
                False,
            )
        )
    )

    skeptic_approved = (
        skeptic_review.get("decision")
        == "approved"
    )

    all_agents_approved = bool(
        multi_agent.get(
            "all_agents_approved",
            False,
        )
    )

    next_action = multi_agent.get(
        "next_action",
        agent_result.get(
            "agent_decision",
            "human_review",
        ),
    )

    auto_resolution_allowed = bool(
        verifier_approved
        and skeptic_approved
        and all_agents_approved
    )

    human_review_required = (
        next_action
        in {
            "human_review",
            "escalate_to_human",
        }
        or not auto_resolution_allowed
    )

    return {
        "verifier_approved": (
            verifier_approved
        ),

        "skeptic_approved": (
            skeptic_approved
        ),

        "all_agents_approved": (
            all_agents_approved
        ),

        "auto_resolution_allowed": (
            auto_resolution_allowed
        ),

        "human_review_required": (
            human_review_required
        ),

        "next_action": (
            next_action
        ),
    }


# ============================================================
# CHAT REPLY BUILDER
# ============================================================

def build_chat_reply(
    agent_result: dict,
    usable_steps: list[str],
    skipped_steps: list[str],
    failure_memory_used: bool,
    escalation_recommended: bool,
) -> str:

    gate = get_multi_agent_gate(
        agent_result
    )

    next_action = gate[
        "next_action"
    ]

    if (
        escalation_recommended
        or next_action
        in {
            "human_review",
            "escalate_to_human",
        }
    ):
        return (
            "The multi-agent verification system "
            "did not approve fully autonomous "
            "resolution. Human support or "
            "administrator review is required."
        )

    if skipped_steps and usable_steps:
        return (
            "I remember which troubleshooting steps "
            "already failed on this ticket. I skipped "
            "those steps and prepared alternative "
            "solutions for you."
        )

    if failure_memory_used and usable_steps:
        return (
            "I used previous troubleshooting outcomes "
            "to prioritize the solutions most likely "
            "to work. The resolver, safety verifier, "
            "and skeptic agent reviewed the plan."
        )

    if next_action == "request_user_confirmation":
        return (
            "The proposed troubleshooting plan passed "
            "multi-agent verification. Try the "
            "suggested steps and tell me whether "
            "the issue is solved."
        )

    if next_action == "collect_more_information":
        return (
            "The agents need more information before "
            "they can safely recommend a resolution. "
            "Please provide the exact error message "
            "and describe what happens when you retry."
        )

    return (
        "I analyzed your support request using "
        "multiple verification agents and prepared "
        "the safest available next action."
    )


# ============================================================
# AGENT + SMART MEMORY PIPELINE
# ============================================================

def run_memory_aware_agent(
    db: Session,
    title: str,
    description: str,
    ticket_id: int | None = None,
) -> dict:

    agent_result = run_support_agent(
        title=title,
        description=description,
        db=db,
    )

    classification = agent_result.get(
        "classification",
        {},
    )

    plan = agent_result.get(
        "plan",
        {},
    )

    category = classification.get(
        "category",
        "other",
    )

    original_steps = plan.get(
        "steps",
        [],
    )

    memory_result = filter_failed_steps(
        db=db,
        steps=original_steps,
        category=category,
        ticket_id=ticket_id,
    )

    return {
        "agent_result": (
            agent_result
        ),

        "category": (
            category
        ),

        "original_steps": (
            original_steps
        ),

        "usable_steps": (
            memory_result.get(
                "usable_steps",
                [],
            )
        ),

        "skipped_steps": (
            memory_result.get(
                "skipped_failed_steps",
                [],
            )
        ),

        "failure_memory_used": (
            memory_result.get(
                "failure_memory_used",
                False,
            )
        ),

        "memory_details": (
            memory_result.get(
                "memory_details",
                [],
            )
        ),

        "repeated_failure_count": (
            memory_result.get(
                "repeated_failure_count",
                0,
            )
        ),

        "escalation_recommended": (
            memory_result.get(
                "escalation_recommended",
                False,
            )
        ),
    }


# ============================================================
# HEALTH
# ============================================================

@router.get("/health")
def chat_health():

    return {
        "status": "healthy",

        "service": (
            "SupportSakhi "
            "Multi-Agent Proof-Aware Chat"
        ),

        "failure_memory": True,

        "smart_ranking": True,

        "ticket_specific_memory": True,

        "proof_of_resolution": True,

        "multi_agent_verification": True,

        "skeptic_agent": True,

        "knowledge_base": True,

        "rag_retrieval": True,
    }


# ============================================================
# USER CONTEXT
# ============================================================

@router.get("/context")
def chat_context(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):

    tickets = (
        db.query(Ticket)
        .filter(
            Ticket.user_id
            == current_user.id
        )
        .all()
    )

    return {
        "user": {
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email,
            "role": current_user.role,
        },

        "ticket_count": len(
            tickets
        ),

        "tickets": tickets,
    }


# ============================================================
# AGENTIC CHAT MESSAGE
# ============================================================

@router.post("/message")
def send_chat_message(
    data: ChatMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):

    clean_message = (
        data.message.strip()
    )

    ticket: Ticket | None = None

    if data.ticket_id is not None:

        ticket = get_ticket_for_user(
            db=db,
            ticket_id=data.ticket_id,
            current_user=current_user,
        )

        title = ticket.title

        description = (
            f"{ticket.description}\n\n"
            f"Latest user message: "
            f"{clean_message}"
        )

    else:

        title = (
            "Support Chat Request"
        )

        description = (
            clean_message
        )

    pipeline = run_memory_aware_agent(
        db=db,
        title=title,
        description=description,
        ticket_id=(
            ticket.id
            if ticket is not None
            else None
        ),
    )

    agent_result = pipeline[
        "agent_result"
    ]

    usable_steps = pipeline[
        "usable_steps"
    ]

    skipped_steps = pipeline[
        "skipped_steps"
    ]

    verification = agent_result.get(
        "verification",
        {},
    )

    skeptic_review = agent_result.get(
        "skeptic_review",
        {},
    )

    multi_agent_verification = (
        agent_result.get(
            "multi_agent_verification",
            {},
        )
    )

    multi_agent_gate = (
        get_multi_agent_gate(
            agent_result
        )
    )

    memory_escalation = bool(
        pipeline[
            "escalation_recommended"
        ]
    )

    multi_agent_escalation = (
        multi_agent_gate[
            "next_action"
        ]
        in {
            "human_review",
            "escalate_to_human",
        }
    )

    should_escalate = bool(
        memory_escalation
        or multi_agent_escalation
    )

    reply = build_chat_reply(
        agent_result=agent_result,
        usable_steps=usable_steps,
        skipped_steps=skipped_steps,
        failure_memory_used=(
            pipeline[
                "failure_memory_used"
            ]
        ),
        escalation_recommended=(
            should_escalate
        ),
    )

    if should_escalate:

        agent_decision = (
            "escalate_to_human"
        )

    else:

        agent_decision = (
            multi_agent_gate[
                "next_action"
            ]
        )

    can_auto_resolve = bool(
        multi_agent_gate[
            "auto_resolution_allowed"
        ]
        and not should_escalate
    )

    return {
        "ticket_id": (
            ticket.id
            if ticket is not None
            else None
        ),

        "user_message": (
            clean_message
        ),

        "reply": (
            reply
        ),

        "classification": (
            agent_result.get(
                "classification",
                {},
            )
        ),

        "knowledge_retrieval": (
            agent_result.get(
                "knowledge_retrieval",
                {},
            )
        ),

        "troubleshooting_steps": (
            []
            if should_escalate
            else usable_steps
        ),

        "skipped_failed_steps": (
            skipped_steps
        ),

        "failure_memory_used": (
            pipeline[
                "failure_memory_used"
            ]
        ),

        "repeated_failure_count": (
            pipeline[
                "repeated_failure_count"
            ]
        ),

        "escalation_recommended": (
            should_escalate
        ),

        "verification": (
            verification
        ),

        "skeptic_review": (
            skeptic_review
        ),

        "multi_agent_verification": (
            multi_agent_verification
        ),

        "multi_agent_gate": (
            multi_agent_gate
        ),

        "agent_decision": (
            agent_decision
        ),

        "can_auto_resolve": (
            can_auto_resolve
        ),

        "proof_required_before_resolution": (
            True
        ),
    }


# ============================================================
# CONFIRM RESOLUTION
# ============================================================

@router.post(
    "/tickets/{ticket_id}/confirm-resolution"
)
def confirm_ticket_resolution(
    ticket_id: int,
    data: ResolutionConfirmationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):

    ticket = get_ticket_for_user(
        db=db,
        ticket_id=ticket_id,
        current_user=current_user,
    )

    pipeline = run_memory_aware_agent(
        db=db,
        title=ticket.title,
        description=ticket.description,
        ticket_id=ticket.id,
    )

    agent_result = pipeline[
        "agent_result"
    ]

    classification = (
        agent_result.get(
            "classification",
            {},
        )
    )

    verification = (
        agent_result.get(
            "verification",
            {},
        )
    )

    skeptic_review = (
        agent_result.get(
            "skeptic_review",
            {},
        )
    )

    multi_agent_verification = (
        agent_result.get(
            "multi_agent_verification",
            {},
        )
    )

    multi_agent_gate = (
        get_multi_agent_gate(
            agent_result
        )
    )

    category = classification.get(
        "category",
        "other",
    )

    confidence = float(
        classification.get(
            "confidence",
            0.0,
        )
        or 0.0
    )

    verification_score = float(
        verification.get(
            "verification_score",
            0.0,
        )
        or 0.0
    )

    verifier_decision = (
        verification.get(
            "decision"
        )
    )

    multi_agent_decision = (
        multi_agent_verification.get(
            "decision",
            "review_required",
        )
    )

    all_agents_approved = bool(
        multi_agent_gate[
            "auto_resolution_allowed"
        ]
    )

    attempted_steps = [
        step.strip()
        for step
        in data.attempted_steps
        if step.strip()
    ]

    # ========================================================
    # USER CONFIRMED ISSUE SOLVED
    # ========================================================

    if data.resolved:

        successful_attempt_ids: list[int] = []

        for step in attempted_steps:

            successful_attempt = (
                remember_success(
                    db=db,
                    ticket_id=ticket.id,
                    action_text=step,
                    category=category,
                    confidence=confidence,
                )
            )

            successful_attempt_ids.append(
                successful_attempt.id
            )

        latest_attempt_id = (
            successful_attempt_ids[-1]
            if successful_attempt_ids
            else None
        )

        successful_action = (
            " -> ".join(
                attempted_steps
            )
            if attempted_steps
            else None
        )

        # ----------------------------------------------------
        # USER CONFIRMATION ALONE IS NOT ENOUGH
        # ----------------------------------------------------

        has_resolution_evidence = bool(
            attempted_steps
        )

        proof_safe_for_auto_resolution = bool(
            has_resolution_evidence
            and all_agents_approved
        )

        if not has_resolution_evidence:

            proof_reason = (
                "The user reported the issue as solved, "
                "but no troubleshooting action was "
                "provided as resolution evidence."
            )

        elif not all_agents_approved:

            proof_reason = (
                "The user confirmed successful "
                "resolution, but the multi-agent "
                "verification system did not approve "
                "autonomous ticket closure."
            )

        elif verification_score < 0.75:

            proof_reason = (
                "The user confirmed successful "
                "resolution, but the verification "
                "score is below the required threshold."
            )

        else:

            proof_reason = (
                "The user confirmed successful "
                "resolution, resolution evidence was "
                "recorded, the safety verifier approved "
                "the plan, the skeptic agent approved "
                "the plan, and multi-agent consensus "
                "was achieved."
            )

        resolution_proof = (
            create_resolution_proof(
                db=db,

                ticket_id=(
                    ticket.id
                ),

                resolution_attempt_id=(
                    latest_attempt_id
                ),

                confirmed_by_user_id=(
                    current_user.id
                ),

                successful_action=(
                    successful_action
                ),

                user_confirmed=True,

                agent_confidence=(
                    confidence
                ),

                verification_score=(
                    verification_score
                ),

                # Final consensus is stored here.
                safety_decision=(
                    multi_agent_decision
                ),

                safe_for_auto_resolution=(
                    proof_safe_for_auto_resolution
                ),

                evidence={
                    "attempted_steps": (
                        attempted_steps
                    ),

                    "category": (
                        category
                    ),

                    "classification": (
                        classification
                    ),

                    "safety_verifier": (
                        verification
                    ),

                    "verifier_decision": (
                        verifier_decision
                    ),

                    "skeptic_review": (
                        skeptic_review
                    ),

                    "multi_agent_verification": (
                        multi_agent_verification
                    ),

                    "multi_agent_gate": (
                        multi_agent_gate
                    ),

                    "failure_memory_used": (
                        pipeline[
                            "failure_memory_used"
                        ]
                    ),

                    "repeated_failure_count": (
                        pipeline[
                            "repeated_failure_count"
                        ]
                    ),
                },

                resolution_reason=(
                    proof_reason
                ),
            )
        )

        proof_verified = (
            resolution_proof.proof_status
            == "verified"
        )

        # ----------------------------------------------------
        # MULTI-AGENT CONSENSUS + VERIFIED PROOF REQUIRED
        # ----------------------------------------------------

        can_close_ticket = bool(
            proof_verified
            and all_agents_approved
            and has_resolution_evidence
        )

        if not can_close_ticket:

            if ticket.status not in {
                "resolved",
                "closed",
            }:

                ticket.status = (
                    "in_progress"
                )

                sync_ticket_sla(
                    ticket
                )

                db.commit()
                db.refresh(ticket)

            return {
                "ticket_id": (
                    ticket.id
                ),

                "auto_resolved": False,

                "ticket_status": (
                    ticket.status
                ),

                "action": (
                    "human_review_required"
                ),

                "memory_saved": bool(
                    attempted_steps
                ),

                "successful_steps": (
                    attempted_steps
                ),

                "proof_created": True,

                "proof_verified": (
                    proof_verified
                ),

                "all_agents_approved": (
                    all_agents_approved
                ),

                "skeptic_review": (
                    skeptic_review
                ),

                "multi_agent_verification": (
                    multi_agent_verification
                ),

                "resolution_proof": (
                    serialize_resolution_proof(
                        resolution_proof
                    )
                ),

                "message": (
                    "The reported solution was recorded, "
                    "but autonomous closure was blocked "
                    "because multi-agent consensus and "
                    "verified proof are both required. "
                    "Human review is required."
                ),

                "verification": (
                    verification
                ),
            }

        # ----------------------------------------------------
        # ALL AGENTS APPROVED + PROOF VERIFIED
        # ----------------------------------------------------

        ticket.status = (
            "resolved"
        )

        sync_ticket_sla(
            ticket
        )

        db.commit()
        db.refresh(ticket)

        return {
            "ticket_id": (
                ticket.id
            ),

            "auto_resolved": True,

            "ticket_status": (
                ticket.status
            ),

            "action": (
                "ticket_resolved"
            ),

            "memory_saved": bool(
                attempted_steps
            ),

            "successful_steps": (
                attempted_steps
            ),

            "proof_created": True,

            "proof_verified": True,

            "all_agents_approved": True,

            "skeptic_review": (
                skeptic_review
            ),

            "multi_agent_verification": (
                multi_agent_verification
            ),

            "resolution_proof": (
                serialize_resolution_proof(
                    resolution_proof
                )
            ),

            "message": (
                "The solution was confirmed by the "
                "user, remembered as successful, "
                "approved by the safety verifier, "
                "approved by the skeptic agent, "
                "verified by the Proof-of-Resolution "
                "engine, and the ticket was "
                "automatically resolved."
            ),

            "verification": (
                verification
            ),
        }

    # ========================================================
    # USER CONFIRMED ISSUE NOT SOLVED
    # ========================================================

    for step in attempted_steps:

        remember_failure(
            db=db,
            ticket_id=ticket.id,
            action_text=step,
            category=category,
            confidence=confidence,
            failure_reason=(
                data.failure_reason
                or (
                    "User confirmed that "
                    "the troubleshooting step "
                    "did not resolve the issue."
                )
            ),
        )

    if ticket.status not in {
        "resolved",
        "closed",
    }:

        ticket.status = (
            "in_progress"
        )

        sync_ticket_sla(
            ticket
        )

        db.commit()
        db.refresh(ticket)

    # ========================================================
    # RUN AGENTS AGAIN AFTER FAILURE
    # ========================================================

    new_pipeline = (
        run_memory_aware_agent(
            db=db,
            title=ticket.title,
            description=ticket.description,
            ticket_id=ticket.id,
        )
    )

    new_agent_result = (
        new_pipeline[
            "agent_result"
        ]
    )

    new_verification = (
        new_agent_result.get(
            "verification",
            {},
        )
    )

    new_skeptic_review = (
        new_agent_result.get(
            "skeptic_review",
            {},
        )
    )

    new_multi_agent_verification = (
        new_agent_result.get(
            "multi_agent_verification",
            {},
        )
    )

    new_multi_agent_gate = (
        get_multi_agent_gate(
            new_agent_result
        )
    )

    next_steps = (
        new_pipeline[
            "usable_steps"
        ]
    )

    skipped_steps = (
        new_pipeline[
            "skipped_steps"
        ]
    )

    repeated_failure_count = (
        new_pipeline[
            "repeated_failure_count"
        ]
    )

    memory_escalation = bool(
        new_pipeline[
            "escalation_recommended"
        ]
    )

    multi_agent_escalation = (
        new_multi_agent_gate[
            "next_action"
        ]
        in {
            "human_review",
            "escalate_to_human",
        }
    )

    should_escalate = bool(
        memory_escalation
        or multi_agent_escalation
        or not next_steps
    )

    if should_escalate:

        action = (
            "escalate_to_human"
        )

        next_steps = []

        message = (
            "Previous troubleshooting attempts were "
            "remembered as failed or the multi-agent "
            "verification system requires human "
            "review. Automated troubleshooting "
            "has stopped."
        )

    else:

        action = (
            "try_alternative_resolution"
        )

        message = (
            "That troubleshooting attempt was "
            "remembered as failed. I will not repeat "
            "it on this ticket. The multi-agent "
            "system approved the next safe "
            "alternative troubleshooting steps."
        )

    return {
        "ticket_id": (
            ticket.id
        ),

        "auto_resolved": False,

        "ticket_status": (
            ticket.status
        ),

        "action": (
            action
        ),

        "memory_saved": bool(
            attempted_steps
        ),

        "failed_steps_recorded": (
            attempted_steps
        ),

        "next_steps": (
            next_steps
        ),

        "skipped_failed_steps": (
            skipped_steps
        ),

        "failure_memory_used": (
            new_pipeline[
                "failure_memory_used"
            ]
        ),

        "repeated_failure_count": (
            repeated_failure_count
        ),

        "escalation_recommended": (
            should_escalate
        ),

        "skeptic_review": (
            new_skeptic_review
        ),

        "multi_agent_verification": (
            new_multi_agent_verification
        ),

        "multi_agent_gate": (
            new_multi_agent_gate
        ),

        "proof_created": False,

        "message": (
            message
        ),

        "verification": (
            new_verification
        ),
    }


# ============================================================
# TICKET PROOF SUMMARY
# ============================================================

@router.get(
    "/tickets/{ticket_id}/proof-summary"
)
def ticket_proof_summary(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):

    get_ticket_for_user(
        db=db,
        ticket_id=ticket_id,
        current_user=current_user,
    )

    return get_proof_summary(
        db=db,
        ticket_id=ticket_id,
    )


# ============================================================
# ADMIN MEMORY SUMMARY
# ============================================================

@router.get("/memory/{category}")
def memory_summary(
    category: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):

    if current_user.role != "admin":

        raise HTTPException(
            status_code=403,
            detail=(
                "Only administrators can "
                "view agent memory."
            ),
        )

    return get_memory_summary(
        db=db,
        category=category,
    )