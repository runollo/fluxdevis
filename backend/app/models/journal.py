"""Journal des modifications sensibles (numeros, dates, echeancier).

Trace chaque edition manuelle d'un champ sensible d'un devis ou d'une facture,
notamment apres emission. Sert d'historique consultable dans la fiche.
L'auteur reste null tant que l'authentification n'est pas en place (Phase 4).
"""

from datetime import datetime

from sqlalchemy import String, Integer, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class JournalModification(Base):
    """Une ligne = une modification d'un champ d'un devis ou d'une facture."""

    __tablename__ = "journal_modifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    # "devis" ou "facture"
    entite: Mapped[str] = mapped_column(String(20), index=True)
    entite_id: Mapped[int] = mapped_column(Integer, index=True)
    # Champ modifie (ex. "reference", "date_emission", "echeance[2].date")
    champ: Mapped[str] = mapped_column(String(80))
    ancienne_valeur: Mapped[str | None] = mapped_column(Text)
    nouvelle_valeur: Mapped[str | None] = mapped_column(Text)
    motif: Mapped[str | None] = mapped_column(Text)
    auteur: Mapped[str | None] = mapped_column(String(120))
    cree_le: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
