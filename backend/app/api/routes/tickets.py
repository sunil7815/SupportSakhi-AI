import json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.security import get_current_user, require_admin
from app.db.database import get_db
from app.db.models.ticket import Ticket
from app.db.models.user import User
from app.services.activity_service import log_ticket_activity
from app.services.sla_service import (
    calculate_sla_due_at,
    get_sla_details,

    sync_ticket_sla,)


router = APIRouter(
    prefix="/tickets",
    tags=["Tickets"],
)


# ============================================================
# CONSTANTS
# ============================================================

ALLOWED_PRIORITIES = [
    "low",
    "medium",
    "high",
    "urgent",
]

ALLOWED_STATUSES = [
    "open",
    "in_progress",
    "resolved",
    "closed",
]


# ============================================================
# UPDATE TICKET REQUEST BODY
# ============================================================

class TicketUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    priority: str | None = None
    status: str | None = None


# ============================================================
# FORMAT TICKET RESPONSE
# ============================================================

def ticket_response(ticket: Ticket):
    sla_details = get_sla_details(
        priority=ticket.priority,
        sla_due_at=ticket.sla_due_at,
        ticket_status=ticket.status,
    )

    ai_solution = None

    # Convert stored JSON string into real Python list
    if ticket.ai_solution:
        try:
            ai_solution = json.loads(ticket.ai_solution)
        except (json.JSONDecodeError, TypeError):
            ai_solution = ticket.ai_solution

    return {
        "id": ticket.id,
        "title": ticket.title,
        "description": ticket.description,
        "category": ticket.category,
        "status": ticket.status,
        "priority": ticket.priority,
        "user_id": ticket.user_id,
        "assigned_to_id": ticket.assigned_to_id,
        "ai_solution": ai_solution,
        "sla_due_at": ticket.sla_due_at,
        "sla_status": sla_details["sla_status"],
        "sla_hours": sla_details["sla_hours"],
        "sla_remaining_seconds": sla_details["remaining_seconds"],
        "sla_breached_at": ticket.sla_breached_at,
        "created_at": ticket.created_at,
        "updated_at": ticket.updated_at,
    }


# ============================================================
# SEARCH + FILTER HELPER
# ============================================================

def apply_ticket_filters(
    query,
    search: str | None = None,
    ticket_status: str | None = None,
    priority: str | None = None,
    category: str | None = None,
):

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    if search:
        search_value = search.strip()

        if search_value:
            search_pattern = f"%{search_value}%"

            query = query.filter(
                or_(
                    Ticket.title.ilike(search_pattern),
                    Ticket.description.ilike(search_pattern),
                    Ticket.category.ilike(search_pattern),
                )
            )

    # --------------------------------------------------------
    # STATUS FILTER
    # --------------------------------------------------------

    if ticket_status:

        ticket_status = ticket_status.strip().lower()

        if ticket_status not in ALLOWED_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Status must be open, in_progress, "
                    "resolved, or closed"
                ),
            )

        query = query.filter(
            Ticket.status == ticket_status
        )

    # --------------------------------------------------------
    # PRIORITY FILTER
    # --------------------------------------------------------

    if priority:

        priority = priority.strip().lower()

        if priority not in ALLOWED_PRIORITIES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Priority must be low, medium, "
                    "high, or urgent"
                ),
            )

        query = query.filter(
            Ticket.priority == priority
        )

    # --------------------------------------------------------
    # CATEGORY FILTER
    # --------------------------------------------------------

    if category:

        category = category.strip().lower()

        if category:
            query = query.filter(
                Ticket.category == category
            )

    return query


# ============================================================
# PAGINATION HELPER
# ============================================================

def paginate_tickets(
    query,
    page: int,
    page_size: int,
):

    total = query.count()

    if total == 0:
        total_pages = 0
    else:
        total_pages = (
            total + page_size - 1
        ) // page_size

    offset = (page - 1) * page_size

    tickets = (
        query
        .order_by(Ticket.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
        "tickets": [
            ticket_response(ticket)
            for ticket in tickets
        ],
    }


# ============================================================
# CREATE TICKET
# ============================================================

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED
)
def create_ticket(
    title: str,
    description: str = "",
    priority: str = "medium",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    title = title.strip()
    priority = priority.strip().lower()

    # --------------------------------------------------------
    # VALIDATE TITLE
    # --------------------------------------------------------

    if not title:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ticket title cannot be empty",
        )

    # --------------------------------------------------------
    # VALIDATE PRIORITY
    # --------------------------------------------------------

    if priority not in ALLOWED_PRIORITIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Priority must be low, medium, "
                "high, or urgent"
            ),
        )

    # --------------------------------------------------------
    # CREATE TICKET
    # --------------------------------------------------------

    new_ticket = Ticket(
        title=title,
        description=description.strip(),
        category=None,
        status="open",
        priority=priority,
        user_id=current_user.id,
        assigned_to_id=None,
        ai_solution=None,
        sla_due_at=calculate_sla_due_at(priority),
        sla_status="within_sla",
        sla_breached_at=None,
    )

    db.add(new_ticket)

    # Generate ticket ID before activity logging
    db.flush()

    # --------------------------------------------------------
    # ACTIVITY LOG
    # --------------------------------------------------------

    log_ticket_activity(
        db=db,
        ticket_id=new_ticket.id,
        user_id=current_user.id,
        action="ticket_created",
        details=(
            f"Ticket created with priority "
            f"'{priority}'."
        ),
    )

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    db.commit()
    db.refresh(new_ticket)

    return ticket_response(new_ticket)


# ============================================================
# GET MY TICKETS
# SEARCH + FILTER + PAGINATION
# ============================================================

@router.get("/my")
def get_my_tickets(
    search: str | None = None,

    ticket_status: str | None = Query(
        default=None,
        alias="status"
    ),

    priority: str | None = None,

    category: str | None = None,

    page: int = Query(
        default=1,
        ge=1
    ),

    page_size: int = Query(
        default=10,
        ge=1,
        le=100
    ),

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    ),
):

    query = (
        db.query(Ticket)
        .filter(
            Ticket.user_id == current_user.id
        )
    )

    query = apply_ticket_filters(
        query=query,
        search=search,
        ticket_status=ticket_status,
        priority=priority,
        category=category,
    )

    return paginate_tickets(
        query=query,
        page=page,
        page_size=page_size,
    )


# ============================================================
# GET ALL TICKETS
# ADMIN ONLY
# SEARCH + FILTER + PAGINATION
# ============================================================

@router.get("/")
def get_all_tickets(
    search: str | None = None,

    ticket_status: str | None = Query(
        default=None,
        alias="status"
    ),

    priority: str | None = None,

    category: str | None = None,

    page: int = Query(
        default=1,
        ge=1
    ),

    page_size: int = Query(
        default=10,
        ge=1,
        le=100
    ),

    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_admin
    ),
):

    query = db.query(Ticket)

    query = apply_ticket_filters(
        query=query,
        search=search,
        ticket_status=ticket_status,
        priority=priority,
        category=category,
    )

    return paginate_tickets(
        query=query,
        page=page,
        page_size=page_size,
    )


# ============================================================
# GET TICKET BY ID
# OWNER / ASSIGNED USER / ADMIN
# ============================================================

@router.get("/{ticket_id}")
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):

    ticket = (
        db.query(Ticket)
        .filter(Ticket.id == ticket_id)
        .first()
    )

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )

    # --------------------------------------------------------
    # PERMISSION CHECK
    # --------------------------------------------------------

    if (
        ticket.user_id != current_user.id
        and ticket.assigned_to_id != current_user.id
        and current_user.role != "admin"
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You do not have permission "
                "to view this ticket"
            ),
        )

    return ticket_response(ticket)


# ============================================================
# UPDATE TICKET
# OWNER / ASSIGNED USER / ADMIN
# ============================================================

@router.put("/{ticket_id}")
def update_ticket(
    ticket_id: int,
    ticket_data: TicketUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):

    # --------------------------------------------------------
    # FIND TICKET
    # --------------------------------------------------------

    ticket = (
        db.query(Ticket)
        .filter(Ticket.id == ticket_id)
        .first()
    )

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )

    # --------------------------------------------------------
    # PERMISSION CHECK
    # --------------------------------------------------------

    if (
        ticket.user_id != current_user.id
        and ticket.assigned_to_id != current_user.id
        and current_user.role != "admin"
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You do not have permission "
                "to update this ticket"
            ),
        )

    # ========================================================
    # PRIORITY UPDATE
    # ========================================================

    if ticket_data.priority is not None:

        new_priority = (
            ticket_data.priority
            .strip()
            .lower()
        )

        if new_priority not in ALLOWED_PRIORITIES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Priority must be low, medium, "
                    "high, or urgent"
                ),
            )

        old_priority = ticket.priority

        if old_priority != new_priority:

            ticket.priority = new_priority



            # Recalculate SLA from original ticket creation time.

            ticket.sla_due_at = calculate_sla_due_at(

                new_priority,

                ticket.created_at,

            )
            log_ticket_activity(
                db=db,
                ticket_id=ticket.id,
                user_id=current_user.id,
                action="priority_changed",
                details=(
                    f"Priority changed from "
                    f"'{old_priority}' "
                    f"to '{new_priority}'."
                ),
            )

    # ========================================================
    # STATUS UPDATE
    # ========================================================

    if ticket_data.status is not None:

        new_status = (
            ticket_data.status
            .strip()
            .lower()
        )

        if new_status not in ALLOWED_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Status must be open, "
                    "in_progress, resolved, or closed"
                ),
            )

        old_status = ticket.status

        if old_status != new_status:

            ticket.status = new_status

            log_ticket_activity(
                db=db,
                ticket_id=ticket.id,
                user_id=current_user.id,
                action="status_changed",
                details=(
                    f"Status changed from "
                    f"'{old_status}' "
                    f"to '{new_status}'."
                ),
            )

    # ========================================================
    # TITLE UPDATE
    # ========================================================

    if ticket_data.title is not None:

        new_title = ticket_data.title.strip()

        if not new_title:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ticket title cannot be empty",
            )

        if ticket.title != new_title:

            ticket.title = new_title

            log_ticket_activity(
                db=db,
                ticket_id=ticket.id,
                user_id=current_user.id,
                action="title_updated",
                details="Ticket title was updated.",
            )

    # ========================================================
    # DESCRIPTION UPDATE
    # ========================================================

    if ticket_data.description is not None:

        new_description = (
            ticket_data.description.strip()
        )

        if ticket.description != new_description:

            ticket.description = new_description

            log_ticket_activity(
                db=db,
                ticket_id=ticket.id,
                user_id=current_user.id,
                action="description_updated",
                details=(
                    "Ticket description was updated."
                ),
            )

    # --------------------------------------------------------
    # SLA SYNC
    # --------------------------------------------------------

    previous_sla_status = ticket.sla_status

    sla_changed = sync_ticket_sla(ticket)

    if (
        sla_changed
        and previous_sla_status != "breached"
        and ticket.sla_status == "breached"
    ):
        log_ticket_activity(
            db=db,
            ticket_id=ticket.id,
            user_id=current_user.id,
            action="sla_breached",
            details="Ticket SLA has been breached.",
        )

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    db.commit()
    db.refresh(ticket)

    return ticket_response(ticket)


# ============================================================
# ASSIGN TICKET
# ADMIN ONLY
# ============================================================

@router.put(
    "/{ticket_id}/assign/{user_id}"
)
def assign_ticket(
    ticket_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_admin
    ),
):

    # --------------------------------------------------------
    # FIND TICKET
    # --------------------------------------------------------

    ticket = (
        db.query(Ticket)
        .filter(Ticket.id == ticket_id)
        .first()
    )

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )

    # --------------------------------------------------------
    # FIND USER
    # --------------------------------------------------------

    assigned_user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not assigned_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assigned user not found",
        )

    # --------------------------------------------------------
    # ACTIVE USER CHECK
    # --------------------------------------------------------

    if not assigned_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Cannot assign ticket "
                "to inactive user"
            ),
        )

    old_assigned_to_id = (
        ticket.assigned_to_id
    )

    ticket.assigned_to_id = (
        assigned_user.id
    )

    # --------------------------------------------------------
    # ACTIVITY LOG
    # --------------------------------------------------------

    if (
        old_assigned_to_id
        != assigned_user.id
    ):

        log_ticket_activity(
            db=db,
            ticket_id=ticket.id,
            user_id=current_user.id,
            action="ticket_assigned",
            details=(
                f"Ticket assigned to user ID "
                f"{assigned_user.id}."
            ),
        )

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    db.commit()
    db.refresh(ticket)

    return {
        "message": "Ticket assigned successfully",
        "ticket": ticket_response(ticket),
    }


# ============================================================
# DELETE TICKET
# OWNER OR ADMIN
# ============================================================

@router.delete("/{ticket_id}")
def delete_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):

    # --------------------------------------------------------
    # FIND TICKET
    # --------------------------------------------------------

    ticket = (
        db.query(Ticket)
        .filter(Ticket.id == ticket_id)
        .first()
    )

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )

    # --------------------------------------------------------
    # PERMISSION CHECK
    # --------------------------------------------------------

    if (
        ticket.user_id != current_user.id
        and current_user.role != "admin"
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You do not have permission "
                "to delete this ticket"
            ),
        )

    deleted_ticket_id = ticket.id

    # --------------------------------------------------------
    # DELETE
    # --------------------------------------------------------

    db.delete(ticket)
    db.commit()

    return {
        "message": "Ticket deleted successfully",
        "ticket_id": deleted_ticket_id,
    }