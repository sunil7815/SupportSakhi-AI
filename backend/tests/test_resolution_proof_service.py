from app.services.resolution_proof_service import (
    determine_proof_status,
)


def test_verified_proof():
    result = determine_proof_status(
        user_confirmed=True,
        safety_decision="approved",
        safe_for_auto_resolution=True,
        verification_score=0.81,
    )

    assert result == "verified"


def test_reject_when_user_did_not_confirm():
    result = determine_proof_status(
        user_confirmed=False,
        safety_decision="approved",
        safe_for_auto_resolution=True,
        verification_score=0.90,
    )

    assert result == "rejected"


def test_human_review_when_safety_rejected():
    result = determine_proof_status(
        user_confirmed=True,
        safety_decision="rejected",
        safe_for_auto_resolution=True,
        verification_score=0.90,
    )

    assert result == "human_review"


def test_human_review_when_review_required():
    result = determine_proof_status(
        user_confirmed=True,
        safety_decision="review_required",
        safe_for_auto_resolution=True,
        verification_score=0.90,
    )

    assert result == "human_review"


def test_human_review_when_auto_resolution_not_safe():
    result = determine_proof_status(
        user_confirmed=True,
        safety_decision="approved",
        safe_for_auto_resolution=False,
        verification_score=0.90,
    )

    assert result == "human_review"


def test_human_review_when_score_below_threshold():
    result = determine_proof_status(
        user_confirmed=True,
        safety_decision="approved",
        safe_for_auto_resolution=True,
        verification_score=0.74,
    )

    assert result == "human_review"


def test_exact_threshold_is_verified():
    result = determine_proof_status(
        user_confirmed=True,
        safety_decision="approved",
        safe_for_auto_resolution=True,
        verification_score=0.75,
    )

    assert result == "verified"


def test_none_score_requires_human_review():
    result = determine_proof_status(
        user_confirmed=True,
        safety_decision="approved",
        safe_for_auto_resolution=True,
        verification_score=None,
    )

    assert result == "human_review"