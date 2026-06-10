"""Suivi des factures a relancer.

Une facture est "a relancer" si elle n'est ni payee, ni brouillon, ni annulee, ni
archivee, ET que l'une des conditions est atteinte (au plus tot) :
  - son echeance est depassee, OU
  - elle a ete envoyee il y a plus de DELAI_RELANCE_JOURS jours.
"""

from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.facture import Facture, StatutFacture

DELAI_RELANCE_JOURS = 30


def _dernier_envoi(f: Facture):
    return max(f.envois, key=lambda e: e.date_envoi) if f.envois else None


def est_a_relancer(f: Facture, today: date | None = None) -> bool:
    today = today or date.today()
    if f.archived_at is not None:
        return False
    if f.statut not in (StatutFacture.EMISE, StatutFacture.EN_RETARD):
        return False
    if f.date_echeance and f.date_echeance < today:
        return True
    dernier = _dernier_envoi(f)
    if dernier and dernier.date_envoi.date() < today - timedelta(days=DELAI_RELANCE_JOURS):
        return True
    return False


def jours_retard(f: Facture, today: date | None = None) -> int | None:
    """Nombre de jours depuis l'echeance (None si pas encore echue)."""
    today = today or date.today()
    if f.date_echeance and f.date_echeance < today:
        return (today - f.date_echeance).days
    return None


async def factures_a_relancer(db: AsyncSession) -> list[Facture]:
    """Liste des factures a relancer (envois + devis charges), echeance croissante."""
    today = date.today()
    rows = (await db.execute(
        select(Facture)
        .where(
            Facture.archived_at.is_(None),
            Facture.statut.in_([StatutFacture.EMISE, StatutFacture.EN_RETARD]),
        )
        .options(selectinload(Facture.devis), selectinload(Facture.envois))
        .order_by(Facture.date_echeance.asc())
    )).scalars().all()
    return [f for f in rows if est_a_relancer(f, today)]
