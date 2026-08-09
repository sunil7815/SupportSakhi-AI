"""add sla fields to tickets

Revision ID: 4e7da02a2d22
Revises:
Create Date: 2026-08-09 09:33:00.888309

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.

revision: str = "4e7da02a2d22"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # SLA deadline
    op.add_column(
        "tickets",
        sa.Column(
            "sla_due_at",
            sa.DateTime(),
            nullable=True,
        ),
    )

    # SLA current status
    op.add_column(
        "tickets",
        sa.Column(
            "sla_status",
            sa.String(length=30),
            nullable=True,
        ),
    )

    # Time when SLA was breached
    op.add_column(
        "tickets",
        sa.Column(
            "sla_breached_at",
            sa.DateTime(),
            nullable=True,
        ),
    )

    # SLA indexes
    op.create_index(
        "ix_tickets_sla_due_at",
        "tickets",
        ["sla_due_at"],
        unique=False,
    )

    op.create_index(
        "ix_tickets_sla_status",
        "tickets",
        ["sla_status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_tickets_sla_status",
        table_name="tickets",
    )

    op.drop_index(
        "ix_tickets_sla_due_at",
        table_name="tickets",
    )

    op.drop_column(
        "tickets",
        "sla_breached_at",
    )

    op.drop_column(
        "tickets",
        "sla_status",
    )

    op.drop_column(
        "tickets",
        "sla_due_at",
    )
