"""modeles d'emails (corps/objet devis & facture) + signature sur parametres

Ajoute a la table `parametres` les modeles d'emails editables et la signature.
NULL/vide => modele par defaut (cf. app/services/email_modeles.py).

Revision ID: c9d0e1f2a3b4
Revises: b8c9d0e1f2a3
Create Date: 2026-06-10 14:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'c9d0e1f2a3b4'
down_revision: Union[str, None] = 'b8c9d0e1f2a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('parametres', sa.Column('email_signature', sa.Text(), nullable=True))
    op.add_column('parametres', sa.Column('email_objet_devis', sa.Text(), nullable=True))
    op.add_column('parametres', sa.Column('email_corps_devis', sa.Text(), nullable=True))
    op.add_column('parametres', sa.Column('email_objet_facture', sa.Text(), nullable=True))
    op.add_column('parametres', sa.Column('email_corps_facture', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('parametres', 'email_corps_facture')
    op.drop_column('parametres', 'email_objet_facture')
    op.drop_column('parametres', 'email_corps_devis')
    op.drop_column('parametres', 'email_objet_devis')
    op.drop_column('parametres', 'email_signature')
