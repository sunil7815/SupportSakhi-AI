"""add resolution attempts

Revision ID: 430fcb9f54b9
Revises: 4e7da02a2d22
Create Date: 2026-08-12 07:27:41.435030
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "430fcb9f54b9"

down_revision: Union[
    str,
    Sequence[str],
    None,
] = "4e7da02a2d22"

branch_labels: Union[
    str,
    Sequence[str],
    None,
] = None

depends_on: Union[
    str,
    Sequence[str],
    None,
] = None


def upgrade() -> None:
    op.create_table(
        "resolution_attempts",

        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "ticket_id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "category",
            sa.String(length=100),
            nullable=True,
        ),

        sa.Column(
            "action_key",
            sa.String(length=150),
            nullable=False,
        ),

        sa.Column(
            "action_text",
            sa.Text(),
            nullable=False,
        ),

        sa.Column(
            "outcome",
            sa.String(length=30),
            nullable=False,
        ),

        sa.Column(
            "confidence",
            sa.Float(),
            nullable=True,
        ),

        sa.Column(
            "source",
            sa.String(length=50),
            nullable=False,
        ),

        sa.Column(
            "failure_reason",
            sa.Text(),
            nullable=True,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),

        sa.ForeignKeyConstraint(
            ["ticket_id"],
            ["tickets.id"],
        ),

        sa.PrimaryKeyConstraint(
            "id"
        ),
    )

    op.create_index(
        "ix_resolution_attempts_action_key",
        "resolution_attempts",
        ["action_key"],
        unique=False,
    )

    op.create_index(
        "ix_resolution_attempts_category",
        "resolution_attempts",
        ["category"],
        unique=False,
    )

    op.create_index(
        "ix_resolution_attempts_id",
        "resolution_attempts",
        ["id"],
        unique=False,
    )

    op.create_index(
        "ix_resolution_attempts_outcome",
        "resolution_attempts",
        ["outcome"],
        unique=False,
    )

    op.create_index(
        "ix_resolution_attempts_ticket_id",
        "resolution_attempts",
        ["ticket_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_resolution_attempts_ticket_id",
        table_name="resolution_attempts",
    )

    op.drop_index(
        "ix_resolution_attempts_outcome",
        table_name="resolution_attempts",
    )

    op.drop_index(
        "ix_resolution_attempts_id",
        table_name="resolution_attempts",
    )

    op.drop_index(
        "ix_resolution_attempts_category",
        table_name="resolution_attempts",
    )

    op.drop_index(
        "ix_resolution_attempts_action_key",
        table_name="resolution_attempts",
    )

    op.drop_table(
        "resolution_attempts"
    )