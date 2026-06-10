"""historique des envois de facture (facture_envois)

Trace chaque envoi email d'une facture (date, mode client/expediteur, destinataire)
pour l'historique et l'alerte au renvoi.

Revision ID: e1f2a3b4c5d6
Revises: d0e1f2a3b4c5
Create Date: 2026-06-10 16:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'e1f2a3b4c5d6'
down_revision: Union[str, None] = 'd0e1f2a3b4c5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'facture_envois',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('facture_id', sa.Integer(), nullable=False),
        sa.Column('date_envoi', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('mode', sa.String(length=20), nullable=False),
        sa.Column('destinataire', sa.String(length=200), nullable=False),
        sa.ForeignKeyConstraint(['facture_id'], ['factures.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_facture_envois_facture_id'), 'facture_envois', ['facture_id'])


def downgrade() -> None:
    op.drop_index(op.f('ix_facture_envois_facture_id'), table_name='facture_envois')
    op.drop_table('facture_envois')
