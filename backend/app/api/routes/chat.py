from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.database import get_db
from app.db.models.user import User
from app.db.models.ticket import Ticket


router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


@router.get("/health")
def chat_health():
    return {
        "status": "healthy",
        "service": "SupportSakhi AI Chat",
    }


@router.get("/context")
def chat_context(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tickets = (
        db.query(Ticket)
        .filter(Ticket.user_id == current_user.id)
        .all()
    )

    return {
        "user": {
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email,
            "role": current_user.role,
        },
        "ticket_count": len(tickets),
        "tickets": tickets,
    }