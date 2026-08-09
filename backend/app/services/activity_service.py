from sqlalchemy.orm import Session

from app.db.models.ticket_activity import TicketActivity


def log_ticket_activity(
    db: Session,
    ticket_id: int,
    user_id: int | None,
    action: str,
    details: str | None = None,
):
    activity = TicketActivity(
        ticket_id=ticket_id,
        user_id=user_id,
        action=action,
        details=details,
    )

    db.add(activity)

    return activity