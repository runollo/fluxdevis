"""compteur de numerotation des factures (sequence continue par annee)

Table `compteur_facture` : un compteur par annee, qui ne fait qu'augmenter. Le
numero legal F<annee>-NNN est attribue a l'EMISSION de la facture (pas au
brouillon) en incrementant ce compteur. Garantit une sequence chronologique
continue sans trou (exigence art. 242 nonies A du CGI), independante des
brouillons supprimes.

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-06-10 12:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'a7b8c9d0e1f2'
down_revision: Union[str, None] = 'f6a7b8c9d0e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'compteur_facture',
        sa.Column('annee', sa.Integer(), nullable=False),
        sa.Column('dernier', sa.Integer(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('annee'),
    )


def downgrade() -> None:
    op.drop_table('compteur_facture')
