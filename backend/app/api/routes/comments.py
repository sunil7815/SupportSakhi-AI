from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.database import get_db
from app.db.models.ticket import Ticket
from app.db.models.ticket_comment import TicketComment
from app.db.models.user import User
from app.services.activity_service import log_ticket_activity


router = APIRouter(
    prefix="/tickets",
    tags=["Ticket Comments"]
)


class CommentCreate(BaseModel):
    comment: str


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


# ============================================================
# ADD COMMENT
# ============================================================

@router.post("/{ticket_id}/comments")
def add_comment(
    ticket_id: int,
    data: CommentCreate,
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

    comment_text = data.comment.strip()

    if not comment_text:
        raise HTTPException(
            status_code=400,
            detail="Comment cannot be empty"
        )

    new_comment = TicketComment(
        ticket_id=ticket.id,
        user_id=current_user.id,
        comment=comment_text
    )

    db.add(new_comment)

    # Save activity history
    log_ticket_activity(
        db=db,
        ticket_id=ticket.id,
        user_id=current_user.id,
        action="comment_added",
        details="A comment was added to the ticket."
    )

    db.commit()
    db.refresh(new_comment)

    return {
        "message": "Comment added successfully",
        "comment": {
            "id": new_comment.id,
            "ticket_id": new_comment.ticket_id,
            "user_id": new_comment.user_id,
            "comment": new_comment.comment,
            "created_at": new_comment.created_at,
        }
    }


# ============================================================
# GET ALL COMMENTS
# ============================================================

@router.get("/{ticket_id}/comments")
def get_comments(
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

    comments = (
        db.query(TicketComment)
        .filter(TicketComment.ticket_id == ticket_id)
        .order_by(TicketComment.created_at.asc())
        .all()
    )

    return {
        "ticket_id": ticket_id,
        "total_comments": len(comments),
        "comments": [
            {
                "id": comment.id,
                "user_id": comment.user_id,
                "comment": comment.comment,
                "created_at": comment.created_at,
            }
            for comment in comments
        ]
    }