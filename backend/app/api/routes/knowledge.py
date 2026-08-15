from __future__ import annotations

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.database import get_db
from app.db.models.knowledge_item import KnowledgeItem
from app.db.models.user import User

from app.services.knowledge_service import (
    approve_knowledge_item,
    create_knowledge_item,
    deactivate_knowledge_item,
    retrieve_relevant_knowledge,
    serialize_knowledge_item,
)


router = APIRouter(
    prefix="/knowledge",
    tags=["Knowledge Base"],
)


# ============================================================
# REQUEST MODEL
# ============================================================

class KnowledgeCreateRequest(BaseModel):
    title: str = Field(
        min_length=3,
        max_length=255,
    )

    problem_text: str = Field(
        min_length=3,
        max_length=5000,
    )

    solution_text: str = Field(
        min_length=3,
        max_length=5000,
    )

    category: str | None = Field(
        default=None,
        max_length=100,
    )

    keywords: list[str] = Field(
        default_factory=list,
        max_length=30,
    )

    source_type: str = Field(
        default="manual",
        max_length=50,
    )

    source_ticket_id: int | None = None

    source_reference: str | None = Field(
        default=None,
        max_length=255,
    )

    confidence: float = Field(
        default=0.50,
        ge=0.0,
        le=1.0,
    )

    is_approved: bool = False


# ============================================================
# ADMIN CHECK
# ============================================================

def require_admin(
    current_user: User,
) -> None:

    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Administrator access is required.",
        )


# ============================================================
# CREATE KNOWLEDGE
# ============================================================

@router.post(
    "/",
    status_code=201,
)
def create_knowledge(
    data: KnowledgeCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):

    require_admin(
        current_user
    )

    item = create_knowledge_item(
        db=db,
        title=data.title,
        problem_text=data.problem_text,
        solution_text=data.solution_text,
        category=data.category,
        keywords=data.keywords,
        source_type=data.source_type,
        source_ticket_id=data.source_ticket_id,
        source_reference=data.source_reference,
        confidence=data.confidence,
        is_approved=data.is_approved,
    )

    return serialize_knowledge_item(
        item
    )


# ============================================================
# SEARCH KNOWLEDGE
# ============================================================

@router.get("/search")
def search_knowledge(
    q: str = Query(
        min_length=2,
        max_length=1000,
    ),
    category: str | None = Query(
        default=None,
        max_length=100,
    ),
    limit: int = Query(
        default=5,
        ge=1,
        le=20,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):

    results = retrieve_relevant_knowledge(
        db=db,
        query_text=q,
        category=category,
        limit=limit,
    )

    return {
        "query": q,
        "category": category,
        "result_count": len(results),
        "results": results,
    }


# ============================================================
# LIST KNOWLEDGE
# ============================================================

@router.get("/")
def list_knowledge(
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):

    require_admin(
        current_user
    )

    query = db.query(
        KnowledgeItem
    )

    if not include_inactive:
        query = query.filter(
            KnowledgeItem.is_active.is_(True)
        )

    items = (
        query
        .order_by(
            KnowledgeItem.created_at.desc()
        )
        .limit(200)
        .all()
    )

    return {
        "count": len(items),
        "items": [
            serialize_knowledge_item(item)
            for item in items
        ],
    }


# ============================================================
# APPROVE KNOWLEDGE
# ============================================================

@router.put(
    "/{knowledge_item_id}/approve"
)
def approve_knowledge(
    knowledge_item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):

    require_admin(
        current_user
    )

    item = approve_knowledge_item(
        db=db,
        knowledge_item_id=knowledge_item_id,
    )

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Knowledge item not found.",
        )

    return {
        "message": "Knowledge item approved.",
        "knowledge_item": (
            serialize_knowledge_item(item)
        ),
    }


# ============================================================
# DEACTIVATE KNOWLEDGE
# ============================================================

@router.put(
    "/{knowledge_item_id}/deactivate"
)
def deactivate_knowledge(
    knowledge_item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):

    require_admin(
        current_user
    )

    item = deactivate_knowledge_item(
        db=db,
        knowledge_item_id=knowledge_item_id,
    )

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Knowledge item not found.",
        )

    return {
        "message": "Knowledge item deactivated.",
        "knowledge_item": (
            serialize_knowledge_item(item)
        ),
    }