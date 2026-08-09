from datetime import UTC, datetime, timedelta


SLA_HOURS = {
    "low": 72,
    "medium": 48,
    "high": 24,
    "urgent": 4,
}


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def normalize_datetime(value: datetime | None) -> datetime:
    if value is None:
        return utc_now()

    if value.tzinfo is not None:
        return value.astimezone(UTC).replace(tzinfo=None)

    return value


def get_sla_hours(priority: str) -> int:
    priority = (priority or "medium").strip().lower()
    return SLA_HOURS.get(priority, SLA_HOURS["medium"])


def calculate_sla_due_at(
    priority: str,
    start_time: datetime | None = None,
) -> datetime:
    start_time = normalize_datetime(start_time)

    return start_time + timedelta(
        hours=get_sla_hours(priority)
    )


def calculate_sla_status(
    sla_due_at: datetime | None,
    ticket_status: str = "open",
    priority: str = "medium",
    current_time: datetime | None = None,
) -> str:

    status = (ticket_status or "open").strip().lower()

    if status in {"resolved", "closed"}:
        return "completed"

    if sla_due_at is None:
        return "within_sla"

    current_time = normalize_datetime(current_time)
    sla_due_at = normalize_datetime(sla_due_at)

    if current_time >= sla_due_at:
        return "breached"

    remaining = sla_due_at - current_time

    near_breach_hours = get_sla_hours(priority) * 0.20

    if remaining <= timedelta(hours=near_breach_hours):
        return "near_breach"

    return "within_sla"


def get_sla_details(
    priority: str,
    sla_due_at: datetime | None,
    ticket_status: str,
) -> dict:

    current_time = utc_now()

    sla_status = calculate_sla_status(
        sla_due_at=sla_due_at,
        ticket_status=ticket_status,
        priority=priority,
        current_time=current_time,
    )

    remaining_seconds = None

    if (
        sla_due_at is not None
        and sla_status not in {"completed", "breached"}
    ):
        due_at = normalize_datetime(sla_due_at)

        remaining_seconds = max(
            0,
            int((due_at - current_time).total_seconds()),
        )

    return {
        "sla_hours": get_sla_hours(priority),
        "sla_due_at": sla_due_at,
        "sla_status": sla_status,
        "remaining_seconds": remaining_seconds,
    }


def sync_ticket_sla(
    ticket,
    current_time: datetime | None = None,
) -> bool:

    current_time = normalize_datetime(current_time)
    changed = False

    # Backfill SLA for older tickets.
    if ticket.sla_due_at is None:
        ticket.sla_due_at = calculate_sla_due_at(
            ticket.priority,
            ticket.created_at,
        )
        changed = True

    new_status = calculate_sla_status(
        sla_due_at=ticket.sla_due_at,
        ticket_status=ticket.status,
        priority=ticket.priority,
        current_time=current_time,
    )

    if ticket.sla_status != new_status:
        ticket.sla_status = new_status
        changed = True

    if (
        new_status == "breached"
        and ticket.sla_breached_at is None
    ):
        ticket.sla_breached_at = current_time
        changed = True

    return changed
