"""Modele de base SQLAlchemy."""

from datetime import datetime, timezone
from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base declarative pour tous les modeles."""
    pass


class TimestampMixin:
    """Mixin ajoutant created_at et updated_at a un modele."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class SoftDeleteMixin:
    """Mixin pour l'archivage (corbeille) plutot que la suppression physique.

    Conformite juridique : un document n'est jamais detruit en base, il est
    seulement masque (archived_at renseigne). Permet la restauration et garde
    une trace complete. La purge physique reelle reste reservee aux donnees de
    test via le script scripts/purge_donnees.py.
    """

    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, nullable=True
    )
