from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.security import get_current_user, require_admin
from app.db.database import get_db
from app.db.models.ticket import Ticket
from app.db.models.user import User


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


# ============================================================
# HELPER - BUILD DASHBOARD STATISTICS
# ============================================================

def build_dashboard_stats(
    db: Session,
    user_id: int | None = None,
):

    query = db.query(Ticket)

    if user_id is not None:
        query = query.filter(
            Ticket.user_id == user_id
        )

    # ========================================================
    # TOTAL
    # ========================================================

    total_tickets = query.count()

    # ========================================================
    # STATUS COUNTS
    # ========================================================

    open_tickets = (
        query.filter(
            Ticket.status == "open"
        ).count()
    )

    in_progress_tickets = (
        query.filter(
            Ticket.status == "in_progress"
        ).count()
    )

    resolved_tickets = (
        query.filter(
            Ticket.status == "resolved"
        ).count()
    )

    closed_tickets = (
        query.filter(
            Ticket.status == "closed"
        ).count()
    )

    # ========================================================
    # PRIORITY COUNTS
    # ========================================================

    low_priority = (
        query.filter(
            Ticket.priority == "low"
        ).count()
    )

    medium_priority = (
        query.filter(
            Ticket.priority == "medium"
        ).count()
    )

    high_priority = (
        query.filter(
            Ticket.priority == "high"
        ).count()
    )

    urgent_priority = (
        query.filter(
            Ticket.priority == "urgent"
        ).count()
    )

    # ========================================================
    # ASSIGNMENT COUNTS
    # ========================================================

    assigned_tickets = (
        query.filter(
            Ticket.assigned_to_id.isnot(None)
        ).count()
    )

    unassigned_tickets = (
        query.filter(
            Ticket.assigned_to_id.is_(None)
        ).count()
    )

    # ========================================================
    # CATEGORY COUNTS
    # ========================================================

    category_query = (
        db.query(
            Ticket.category,
            func.count(Ticket.id)
        )
    )

    if user_id is not None:
        category_query = category_query.filter(
            Ticket.user_id == user_id
        )

    category_rows = (
        category_query
        .filter(Ticket.category.isnot(None))
        .group_by(Ticket.category)
        .all()
    )

    category_counts = {
        category: count
        for category, count in category_rows
    }

    # ========================================================
    # RETURN
    # ========================================================

    return {
        "total_tickets": total_tickets,

        "status": {
            "open": open_tickets,
            "in_progress": in_progress_tickets,
            "resolved": resolved_tickets,
            "closed": closed_tickets,
        },

        "priority": {
            "low": low_priority,
            "medium": medium_priority,
            "high": high_priority,
            "urgent": urgent_priority,
        },

        "assignment": {
            "assigned": assigned_tickets,
            "unassigned": unassigned_tickets,
        },

        "categories": category_counts,
    }


# ============================================================
# MY DASHBOARD
# ============================================================

@router.get("/my")
def my_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    statistics = build_dashboard_stats(
        db=db,
        user_id=current_user.id,
    )

    return {
        "dashboard": "user",
        "user_id": current_user.id,
        **statistics,
    }


# ============================================================
# ADMIN DASHBOARD
# ============================================================

@router.get("/admin")
def admin_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):

    statistics = build_dashboard_stats(
        db=db
    )

    total_users = (
        db.query(User)
        .count()
    )

    active_users = (
        db.query(User)
        .filter(User.is_active.is_(True))
        .count()
    )

    inactive_users = (
        db.query(User)
        .filter(User.is_active.is_(False))
        .count()
    )

    return {
        "dashboard": "admin",

        "users": {
            "total": total_users,
            "active": active_users,
            "inactive": inactive_users,
        },

        **statistics,
    }