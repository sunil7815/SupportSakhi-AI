from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.services.self_learning_service import (
    create_resolution_knowledge_draft,
)


def make_db(existing=None):
    db = MagicMock()

    query = db.query.return_value
    filtered = query.filter.return_value
    filtered.first.return_value = existing

    return db


def test_no_successful_steps_does_not_create_draft():
    db = make_db()

    with patch(
        "app.services.self_learning_service.create_knowledge_item"
    ) as create_mock:

        result = create_resolution_knowledge_draft(
            db=db,
            ticket_id=101,
            title="WiFi issue",
            problem_text="WiFi is not working.",
            successful_steps=[],
            category="network",
            confidence=0.90,
        )

    assert result is None
    create_mock.assert_not_called()


def test_existing_active_draft_is_reused():
    existing = SimpleNamespace(
        id=10,
        source_ticket_id=102,
        source_type="self_learning",
        is_active=True,
        is_approved=False,
    )

    db = make_db(
        existing=existing
    )

    with patch(
        "app.services.self_learning_service.create_knowledge_item"
    ) as create_mock:

        result = create_resolution_knowledge_draft(
            db=db,
            ticket_id=102,
            title="Network issue",
            problem_text="Network disconnects.",
            successful_steps=[
                "Restart the network adapter."
            ],
            category="network",
            confidence=0.85,
        )

    assert result is existing
    create_mock.assert_not_called()


def test_new_draft_is_pending_self_learning_item():
    db = make_db(
        existing=None
    )

    created_item = SimpleNamespace(
        id=11,
        is_approved=False,
        is_active=True,
    )

    with patch(
        "app.services.self_learning_service.create_knowledge_item",
        return_value=created_item,
    ) as create_mock:

        result = create_resolution_knowledge_draft(
            db=db,
            ticket_id=103,
            title="WiFi connection stopped",
            problem_text=(
                "Laptop cannot connect to WiFi."
            ),
            successful_steps=[
                "Check Wi-Fi connectivity.",
                "Restart the network adapter.",
            ],
            category="network",
            confidence=0.92,
        )

    assert result is created_item

    create_mock.assert_called_once()

    kwargs = (
        create_mock.call_args.kwargs
    )

    assert kwargs["source_type"] == (
        "self_learning"
    )

    assert kwargs["source_ticket_id"] == 103

    assert kwargs["source_reference"] == (
        "Auto-resolved ticket #103"
    )

    assert kwargs["is_approved"] is False

    assert kwargs["confidence"] == 0.92

    assert kwargs["solution_text"] == (
        "1. Check Wi-Fi connectivity.\n"
        "2. Restart the network adapter."
    )


def test_confidence_is_clamped_to_valid_range():
    db = make_db(
        existing=None
    )

    created_item = SimpleNamespace(
        id=12,
        is_approved=False,
        is_active=True,
    )

    with patch(
        "app.services.self_learning_service.create_knowledge_item",
        return_value=created_item,
    ) as create_mock:

        create_resolution_knowledge_draft(
            db=db,
            ticket_id=104,
            title="WiFi issue",
            problem_text="WiFi issue",
            successful_steps=[
                "Reconnect WiFi."
            ],
            category="network",
            confidence=5.0,
        )

    kwargs = (
        create_mock.call_args.kwargs
    )

    assert kwargs["confidence"] == 1.0


def test_invalid_confidence_uses_default():
    db = make_db(
        existing=None
    )

    created_item = SimpleNamespace(
        id=13,
        is_approved=False,
        is_active=True,
    )

    with patch(
        "app.services.self_learning_service.create_knowledge_item",
        return_value=created_item,
    ) as create_mock:

        create_resolution_knowledge_draft(
            db=db,
            ticket_id=105,
            title="WiFi issue",
            problem_text="WiFi issue",
            successful_steps=[
                "Reconnect WiFi."
            ],
            category="network",
            confidence="invalid",
        )

    kwargs = (
        create_mock.call_args.kwargs
    )

    assert kwargs["confidence"] == 0.5