"""document_type et params_doc sur devis

Ajoute le type de document (devis / proposition_budgetaire) et un conteneur
JSON de parametres specifiques au document (forfait references Shopify,
parametres de maintenance, bloc frais externes, etc.).

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-06-02 09:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'devis',
        sa.Column('document_type', sa.String(length=30), nullable=False,
                  server_default='devis'),
    )
    op.add_column(
        'devis',
        sa.Column('params_doc', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('devis', 'params_doc')
    op.drop_column('devis', 'document_type')
