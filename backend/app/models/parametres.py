"""Parametres applicatifs editables depuis l'UI (singleton, ligne id=1).

Centralise les reglages que Bruno peut changer sans toucher au code ni au .env :
aujourd'hui l'envoi d'emails (SMTP), demain d'autres (preferences, automatisations...).
Une valeur NULL/vide signifie "utiliser le defaut du .env" (repli). Le mot de passe
SMTP est stocke en base ; il n'est jamais renvoye en clair par l'API (masque).
"""

from sqlalchemy import String, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Parametres(Base, TimestampMixin):
    """Reglages applicatifs (une seule ligne, id=1)."""

    __tablename__ = "parametres"

    id: Mapped[int] = mapped_column(primary_key=True)  # toujours 1

    # Envoi d'emails (SMTP de la messagerie pro). NULL = repli sur .env.
    smtp_host: Mapped[str | None] = mapped_column(String(200), nullable=True)
    smtp_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    smtp_starttls: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    smtp_user: Mapped[str | None] = mapped_column(String(200), nullable=True)
    smtp_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    smtp_from: Mapped[str | None] = mapped_column(String(255), nullable=True)
