from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.db.models.resolution_proof import (
    ResolutionProof,
)


VALID_PROOF_STATUSES = {
    "pending",
    "verified",
    "rejected",
    "human_review",
}


def create_resolution_proof(
    db: Session,
    ticket_id: int,
    confirmed_by_user_id: int | None,
    successful_action: str | None,
    user_confirmed: bool,
    agent_confidence: float | None,
    verification_score: float | None,
    safety_decision: str | None,
    safe_for_auto_resolution: bool,
    resolution_attempt_id: int | None = None,
    evidence: dict[str, Any] | None = None,
    resolution_reason: str | None = None,
) -> ResolutionProof:

    proof_status = determine_proof_status(
        user_confirmed=user_confirmed,
        safety_decision=safety_decision,
        safe_for_auto_resolution=(
            safe_for_auto_resolution
        ),
        verification_score=verification_score,
    )

    verified_at = None

    if proof_status == "verified":
        verified_at = datetime.now(
            UTC
        ).replace(tzinfo=None)

    proof = ResolutionProof(
        ticket_id=ticket_id,
        resolution_attempt_id=(
            resolution_attempt_id
        ),
        confirmed_by_user_id=(
            confirmed_by_user_id
        ),
        proof_status=proof_status,
        proof_type="user_confirmation",
        successful_action=successful_action,
        user_confirmed=user_confirmed,
        agent_confidence=agent_confidence,
        verification_score=verification_score,
        safety_decision=safety_decision,
        safe_for_auto_resolution=(
            safe_for_auto_resolution
        ),
        evidence=evidence or {},
        resolution_reason=resolution_reason,
        verified_at=verified_at,
    )

    db.add(proof)
    db.commit()
    db.refresh(proof)

    return proof


def determine_proof_status(
    user_confirmed: bool,
    safety_decision: str | None,
    safe_for_auto_resolution: bool,
    verification_score: float | None,
) -> str:

    score = verification_score or 0.0

    if not user_confirmed:
        return "rejected"

    if (
        safety_decision
        in {
            "rejected",
            "review_required",
        }
    ):
        return "human_review"

    if not safe_for_auto_resolution:
        return "human_review"

    if score < 0.75:
        return "human_review"

    return "verified"


def get_ticket_proofs(
    db: Session,
    ticket_id: int,
    limit: int = 50,
) -> list[ResolutionProof]:

    return (
        db.query(ResolutionProof)
        .filter(
            ResolutionProof.ticket_id
            == ticket_id
        )
        .order_by(
            ResolutionProof.created_at.desc()
        )
        .limit(limit)
        .all()
    )


def get_latest_verified_proof(
    db: Session,
    ticket_id: int,
) -> ResolutionProof | None:

    return (
        db.query(ResolutionProof)
        .filter(
            ResolutionProof.ticket_id
            == ticket_id,
            ResolutionProof.proof_status
            == "verified",
        )
        .order_by(
            ResolutionProof.created_at.desc()
        )
        .first()
    )


def get_proof_summary(
    db: Session,
    ticket_id: int,
) -> dict[str, Any]:

    proofs = get_ticket_proofs(
        db=db,
        ticket_id=ticket_id,
    )

    verified = [
        proof
        for proof in proofs
        if proof.proof_status
        == "verified"
    ]

    human_review = [
        proof
        for proof in proofs
        if proof.proof_status
        == "human_review"
    ]

    rejected = [
        proof
        for proof in proofs
        if proof.proof_status
        == "rejected"
    ]

    latest = (
        proofs[0]
        if proofs
        else None
    )

    return {
        "ticket_id": ticket_id,
        "total_proofs": len(proofs),
        "verified_proofs": len(
            verified
        ),
        "human_review_proofs": len(
            human_review
        ),
        "rejected_proofs": len(
            rejected
        ),
        "latest_proof_status": (
            latest.proof_status
            if latest
            else None
        ),
        "latest_verification_score": (
            latest.verification_score
            if latest
            else None
        ),
        "latest_successful_action": (
            latest.successful_action
            if latest
            else None
        ),
    }