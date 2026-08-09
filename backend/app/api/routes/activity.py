from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.database import get_db
from app.db.models.ticket import Ticket
from app.db.models.ticket_activity import TicketActivity
from app.db.models.user import User


router = APIRouter(
    prefix="/tickets",
    tags=["Ticket Activity"]
)


def check_ticket_access(
    ticket: Ticket,
    current_user: User
):
    if (
        ticket.user_id != current_user.id
        and ticket.assigned_to_id != current_user.id
        and current_user.role != "admin"
    ):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to access this ticket"
        )


@router.get("/{ticket_id}/activity")
def get_ticket_activity(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    ticket = (
        db.query(Ticket)
        .filter(Ticket.id == ticket_id)
        .first()
    )

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    check_ticket_access(ticket, current_user)

    activities = (
        db.query(TicketActivity)
        .filter(TicketActivity.ticket_id == ticket_id)
        .order_by(TicketActivity.created_at.asc())
        .all()
    )

    return {
        "ticket_id": ticket_id,
        "total_activities": len(activities),
        "activities": [
            {
                "id": activity.id,
                "user_id": activity.user_id,
                "action": activity.action,
                "details": activity.details,
                "created_at": activity.created_at,
            }
            for activity in activities
        ]
    }