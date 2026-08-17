from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.services.knowledge_service import (
    retrieve_relevant_knowledge,
)


def make_query_db(candidates):
    db = MagicMock()

    query = db.query.return_value

    # First filter:
    # is_active=True + is_approved=True
    query.filter.return_value = query

    query.order_by.return_value = query
    query.limit.return_value = query
    query.all.return_value = candidates

    return db, query


def test_rag_requires_active_and_approved_filters():
    db, query = make_query_db(
        candidates=[]
    )

    result = retrieve_relevant_knowledge(
        db=db,
        query_text="wifi not working",
    )

    assert result == []

    # Initial RAG query must apply both:
    # is_active=True
    # is_approved=True
    initial_filter_call = (
        query.filter.call_args_list[0]
    )

    criteria = [
        str(argument).lower()
        for argument
        in initial_filter_call.args
    ]

    assert any(
        "is_active" in criterion
        and "true" in criterion
        for criterion in criteria
    )

    assert any(
        "is_approved" in criterion
        and "true" in criterion
        for criterion in criteria
    )


def test_rag_returns_relevant_approved_candidate():
    item = SimpleNamespace(
        id=201,
        title="WiFi connection issue",
        problem_text=(
            "Laptop cannot connect to WiFi."
        ),
        solution_text=(
            "Restart the network adapter."
        ),
        category="network",
        keywords=["wifi", "network"],
        confidence=0.90,
        is_approved=True,
        is_active=True,
    )

    db, _ = make_query_db(
        candidates=[item]
    )

    with (
        patch(
            "app.services.knowledge_service."
            "calculate_relevance_score",
            return_value=0.80,
        ),
        patch(
            "app.services.knowledge_service."
            "calculate_quality_score",
            return_value=0.90,
        ),
        patch(
            "app.services.knowledge_service."
            "serialize_knowledge_item",
            return_value={
                "id": 201,
                "title": (
                    "WiFi connection issue"
                ),
                "is_approved": True,
                "is_active": True,
            },
        ),
    ):

        result = retrieve_relevant_knowledge(
            db=db,
            query_text=(
                "My laptop WiFi is not working"
            ),
            category="network",
        )

    assert len(result) == 1

    assert result[0]["id"] == 201

    assert (
        result[0]["is_approved"]
        is True
    )

    assert (
        result[0]["is_active"]
        is True
    )

    assert (
        result[0]["relevance_score"]
        == 0.80
    )

    assert (
        result[0]["quality_score"]
        == 0.90
    )


def test_rag_rejects_candidate_below_minimum_score():
    item = SimpleNamespace(
        id=202,
        title="Unrelated knowledge",
    )

    db, _ = make_query_db(
        candidates=[item]
    )

    with patch(
        "app.services.knowledge_service."
        "calculate_relevance_score",
        return_value=0.10,
    ):

        result = retrieve_relevant_knowledge(
            db=db,
            query_text="wifi problem",
            minimum_score=0.15,
        )

    assert result == []


def test_rag_respects_result_limit():
    candidates = [
        SimpleNamespace(
            id=index
        )
        for index in range(
            1,
            6,
        )
    ]

    db, _ = make_query_db(
        candidates=candidates
    )

    def serialize(item):
        return {
            "id": item.id,
        }

    with (
        patch(
            "app.services.knowledge_service."
            "calculate_relevance_score",
            return_value=0.80,
        ),
        patch(
            "app.services.knowledge_service."
            "calculate_quality_score",
            return_value=0.80,
        ),
        patch(
            "app.services.knowledge_service."
            "serialize_knowledge_item",
            side_effect=serialize,
        ),
    ):

        result = retrieve_relevant_knowledge(
            db=db,
            query_text="wifi",
            limit=2,
        )

    assert len(result) == 2