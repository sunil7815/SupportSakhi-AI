"""add resolution proofs

Revision ID: e66b364d3ade
Revises: 430fcb9f54b9
Create Date: 2026-08-14 15:57:30.568874
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e66b364d3ade"

down_revision: Union[
    str,
    Sequence[str],
    None,
] = "430fcb9f54b9"

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
        "resolution_proofs",

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
            "resolution_attempt_id",
            sa.Integer(),
            nullable=True,
        ),

        sa.Column(
            "confirmed_by_user_id",
            sa.Integer(),
            nullable=True,
        ),

        sa.Column(
            "proof_status",
            sa.String(length=30),
            nullable=False,
        ),

        sa.Column(
            "proof_type",
            sa.String(length=30),
            nullable=False,
        ),

        sa.Column(
            "successful_action",
            sa.Text(),
            nullable=True,
        ),

        sa.Column(
            "user_confirmed",
            sa.Boolean(),
            nullable=False,
        ),

        sa.Column(
            "agent_confidence",
            sa.Float(),
            nullable=True,
        ),

        sa.Column(
            "verification_score",
            sa.Float(),
            nullable=True,
        ),

        sa.Column(
            "safety_decision",
            sa.String(length=50),
            nullable=True,
        ),

        sa.Column(
            "safe_for_auto_resolution",
            sa.Boolean(),
            nullable=False,
        ),

        sa.Column(
            "evidence",
            sa.JSON(),
            nullable=True,
        ),

        sa.Column(
            "resolution_reason",
            sa.Text(),
            nullable=True,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),

        sa.Column(
            "verified_at",
            sa.DateTime(),
            nullable=True,
        ),

        sa.ForeignKeyConstraint(
            ["confirmed_by_user_id"],
            ["users.id"],
        ),

        sa.ForeignKeyConstraint(
            ["resolution_attempt_id"],
            ["resolution_attempts.id"],
        ),

        sa.ForeignKeyConstraint(
            ["ticket_id"],
            ["tickets.id"],
        ),

        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_resolution_proofs_confirmed_by_user_id",
        "resolution_proofs",
        ["confirmed_by_user_id"],
        unique=False,
    )

    op.create_index(
        "ix_resolution_proofs_id",
        "resolution_proofs",
        ["id"],
        unique=False,
    )

    op.create_index(
        "ix_resolution_proofs_proof_status",
        "resolution_proofs",
        ["proof_status"],
        unique=False,
    )

    op.create_index(
        "ix_resolution_proofs_resolution_attempt_id",
        "resolution_proofs",
        ["resolution_attempt_id"],
        unique=False,
    )

    op.create_index(
        "ix_resolution_proofs_ticket_id",
        "resolution_proofs",
        ["ticket_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_resolution_proofs_ticket_id",
        table_name="resolution_proofs",
    )

    op.drop_index(
        "ix_resolution_proofs_resolution_attempt_id",
        table_name="resolution_proofs",
    )

    op.drop_index(
        "ix_resolution_proofs_proof_status",
        table_name="resolution_proofs",
    )

    op.drop_index(
        "ix_resolution_proofs_id",
        table_name="resolution_proofs",
    )

    op.drop_index(
        "ix_resolution_proofs_confirmed_by_user_id",
        table_name="resolution_proofs",
    )

    op.drop_table(
        "resolution_proofs"
    )