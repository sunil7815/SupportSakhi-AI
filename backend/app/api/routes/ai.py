import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.database import get_db
from app.db.models.ticket import Ticket
from app.db.models.user import User
from app.services.ticket_ai_service import analyze_ticket
from app.services.activity_service import log_ticket_activity


router = APIRouter(
    prefix="/ai",
    tags=["AI"]
)


@router.post("/tickets/{ticket_id}/analyze")
def analyze_ticket_endpoint(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    # ========================================================
    # FIND TICKET
    # ========================================================

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

    # ========================================================
    # PERMISSION CHECK
    # ========================================================

    if (
        ticket.user_id != current_user.id
        and ticket.assigned_to_id != current_user.id
        and current_user.role != "admin"
    ):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to analyze this ticket"
        )

    # ========================================================
    # RUN AI ANALYSIS
    # ========================================================

    result = analyze_ticket(ticket)

    old_priority = ticket.priority
    old_category = ticket.category

    # ========================================================
    # SAVE CATEGORY
    # ========================================================

    ticket.category = result["category"]

    # ========================================================
    # SAVE PRIORITY
    # ========================================================

    suggested_priority = result["suggested_priority"]

    if suggested_priority in [
        "low",
        "medium",
        "high",
        "urgent",
    ]:
        ticket.priority = suggested_priority

    # ========================================================
    # SAVE AI SOLUTION
    # ========================================================

    solution = result.get("solution", [])

    ticket.ai_solution = json.dumps(
        solution,
        ensure_ascii=False
    )

    # ========================================================
    # LOG PRIORITY CHANGE IF AI CHANGED IT
    # ========================================================

    if old_priority != ticket.priority:
        log_ticket_activity(
            db=db,
            ticket_id=ticket.id,
            user_id=current_user.id,
            action="priority_changed",
            details=(
                f"AI changed priority from "
                f"'{old_priority}' to '{ticket.priority}'."
            ),
        )

    # ========================================================
    # LOG AI ANALYSIS
    # ========================================================

    log_ticket_activity(
        db=db,
        ticket_id=ticket.id,
        user_id=current_user.id,
        action="ai_analysis_completed",
        details=(
            f"AI classified ticket as '{ticket.category}'. "
            f"Previous category: '{old_category}'."
        ),
    )

    # ========================================================
    # SAVE EVERYTHING
    # ========================================================

    db.commit()
    db.refresh(ticket)

    return {
        **result,
        "saved_to_database": True,
        "updated_priority": ticket.priority,
        "updated_category": ticket.category,
        "ai_solution_saved": True,
        "activity_logged": True,
    }