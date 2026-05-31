"""Echeancier configurable (date debut + intervalle) + journal des modifications.

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-31
"""
from alembic import op
import sqlalchemy as sa

revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("devis", sa.Column("date_debut_echeancier", sa.Date(), nullable=True))
    op.add_column(
        "devis",
        sa.Column("intervalle_echeance_jours", sa.Integer(), nullable=False, server_default="30"),
    )

    op.create_table(
        "journal_modifications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("entite", sa.String(length=20), nullable=False),
        sa.Column("entite_id", sa.Integer(), nullable=False),
        sa.Column("champ", sa.String(length=80), nullable=False),
        sa.Column("ancienne_valeur", sa.Text(), nullable=True),
        sa.Column("nouvelle_valeur", sa.Text(), nullable=True),
        sa.Column("motif", sa.Text(), nullable=True),
        sa.Column("auteur", sa.String(length=120), nullable=True),
        sa.Column("cree_le", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_journal_modifications_entite", "journal_modifications", ["entite"]
    )
    op.create_index(
        "ix_journal_modifications_entite_id", "journal_modifications", ["entite_id"]
    )


def downgrade():
    op.drop_index("ix_journal_modifications_entite_id", table_name="journal_modifications")
    op.drop_index("ix_journal_modifications_entite", table_name="journal_modifications")
    op.drop_table("journal_modifications")
    op.drop_column("devis", "intervalle_echeance_jours")
    op.drop_column("devis", "date_debut_echeancier")
