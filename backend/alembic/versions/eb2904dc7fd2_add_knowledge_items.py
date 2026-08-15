"""add knowledge items

Revision ID: eb2904dc7fd2
Revises: e66b364d3ade
Create Date: 2026-08-14 17:04:48.441857
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "eb2904dc7fd2"

down_revision: Union[
    str,
    Sequence[str],
    None,
] = "e66b364d3ade"

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
        "knowledge_items",

        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "title",
            sa.String(length=255),
            nullable=False,
        ),

        sa.Column(
            "category",
            sa.String(length=100),
            nullable=True,
        ),

        sa.Column(
            "problem_text",
            sa.Text(),
            nullable=False,
        ),

        sa.Column(
            "solution_text",
            sa.Text(),
            nullable=False,
        ),

        sa.Column(
            "keywords",
            sa.JSON(),
            nullable=True,
        ),

        sa.Column(
            "source_type",
            sa.String(length=50),
            nullable=False,
        ),

        sa.Column(
            "source_ticket_id",
            sa.Integer(),
            nullable=True,
        ),

        sa.Column(
            "source_reference",
            sa.String(length=255),
            nullable=True,
        ),

        sa.Column(
            "confidence",
            sa.Float(),
            nullable=False,
        ),

        sa.Column(
            "success_count",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "failure_count",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "is_approved",
            sa.Boolean(),
            nullable=False,
        ),

        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
        ),

        sa.ForeignKeyConstraint(
            ["source_ticket_id"],
            ["tickets.id"],
        ),

        sa.PrimaryKeyConstraint(
            "id"
        ),
    )

    op.create_index(
        "ix_knowledge_items_category",
        "knowledge_items",
        ["category"],
        unique=False,
    )

    op.create_index(
        "ix_knowledge_items_confidence",
        "knowledge_items",
        ["confidence"],
        unique=False,
    )

    op.create_index(
        "ix_knowledge_items_id",
        "knowledge_items",
        ["id"],
        unique=False,
    )

    op.create_index(
        "ix_knowledge_items_is_active",
        "knowledge_items",
        ["is_active"],
        unique=False,
    )

    op.create_index(
        "ix_knowledge_items_is_approved",
        "knowledge_items",
        ["is_approved"],
        unique=False,
    )

    op.create_index(
        "ix_knowledge_items_source_ticket_id",
        "knowledge_items",
        ["source_ticket_id"],
        unique=False,
    )

    op.create_index(
        "ix_knowledge_items_source_type",
        "knowledge_items",
        ["source_type"],
        unique=False,
    )

    op.create_index(
        "ix_knowledge_items_title",
        "knowledge_items",
        ["title"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_knowledge_items_title",
        table_name="knowledge_items",
    )

    op.drop_index(
        "ix_knowledge_items_source_type",
        table_name="knowledge_items",
    )

    op.drop_index(
        "ix_knowledge_items_source_ticket_id",
        table_name="knowledge_items",
    )

    op.drop_index(
        "ix_knowledge_items_is_approved",
        table_name="knowledge_items",
    )

    op.drop_index(
        "ix_knowledge_items_is_active",
        table_name="knowledge_items",
    )

    op.drop_index(
        "ix_knowledge_items_id",
        table_name="knowledge_items",
    )

    op.drop_index(
        "ix_knowledge_items_confidence",
        table_name="knowledge_items",
    )

    op.drop_index(
        "ix_knowledge_items_category",
        table_name="knowledge_items",
    )

    op.drop_table(
        "knowledge_items"
    )