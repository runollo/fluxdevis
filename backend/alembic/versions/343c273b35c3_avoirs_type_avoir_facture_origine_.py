"""avoirs: type AVOIR, facture_origine, compteur_avoir

Revision ID: 343c273b35c3
Revises: 74c54aff7c28
Create Date: 2026-06-11 14:59:17.892604
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '343c273b35c3'
down_revision: Union[str, None] = '74c54aff7c28'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ajout de la valeur 'AVOIR' a l'enum typefacture (non detecte par autogenerate).
    # SQLAlchemy stocke le NOM du membre enum (majuscules).
    op.execute("ALTER TYPE typefacture ADD VALUE IF NOT EXISTS 'AVOIR'")

    op.create_table('compteur_avoir',
    sa.Column('annee', sa.Integer(), nullable=False),
    sa.Column('dernier', sa.Integer(), server_default='0', nullable=False),
    sa.PrimaryKeyConstraint('annee')
    )
    op.add_column('factures', sa.Column('facture_origine_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_factures_facture_origine', 'factures', 'factures',
        ['facture_origine_id'], ['id'],
    )


def downgrade() -> None:
    op.drop_constraint('fk_factures_facture_origine', 'factures', type_='foreignkey')
    op.drop_column('factures', 'facture_origine_id')
    op.drop_table('compteur_avoir')
    # Remarque : PostgreSQL ne permet pas de retirer une valeur d'un enum ;
    # la valeur 'AVOIR' reste presente dans typefacture (sans effet).
