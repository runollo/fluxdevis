"""Versioning des devis : racine_id, version, version_active + reference 30 car.

Revision ID: a1b2c3d4e5f6
Revises: 2d30cbf3e4b7
Create Date: 2026-05-30
"""
from alembic import op
import sqlalchemy as sa

revision = "a1b2c3d4e5f6"
down_revision = "2d30cbf3e4b7"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("devis", "reference", type_=sa.String(30))
    op.add_column("devis", sa.Column("racine_id", sa.Integer(), nullable=True))
    op.add_column("devis", sa.Column("version", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("devis", sa.Column("version_active", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.create_foreign_key("fk_devis_racine", "devis", "devis", ["racine_id"], ["id"])


def downgrade():
    op.drop_constraint("fk_devis_racine", "devis", type_="foreignkey")
    op.drop_column("devis", "version_active")
    op.drop_column("devis", "version")
    op.drop_column("devis", "racine_id")
    op.alter_column("devis", "reference", type_=sa.String(20))
