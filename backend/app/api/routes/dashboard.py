"""Route de statistiques pour le tableau de bord."""

from decimal import Decimal
from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.models.offre import Offre
from app.models.option import Option
from app.models.client import Client
from app.models.devis import Devis, StatutDevis
from app.models.facture import Facture, StatutFacture

router = APIRouter()


class DevisRecent(BaseModel):
    id: int
    reference: str
    client_raison_sociale: str
    statut: str
    total_ttc: Decimal
    date_emission: date


class FactureRecente(BaseModel):
    id: int
    numero: str
    objet: str
    statut: str
    total_ttc: Decimal
    date_emission: date


class DashboardStats(BaseModel):
    offres_actives: int
    options_actives: int
    clients: int
    devis_total: int
    devis_acceptes: int
    factures_total: int
    factures_impayees: int
    montant_devis_ttc: Decimal
    montant_factures_ttc: Decimal
    derniers_devis: list[DevisRecent]
    dernieres_factures: list[FactureRecente]


async def _count(db: AsyncSession, model, *conditions) -> int:
    query = select(func.count()).select_from(model)
    for cond in conditions:
        query = query.where(cond)
    return (await db.execute(query)).scalar() or 0


async def _somme(db: AsyncSession, colonne, *conditions) -> Decimal:
    query = select(func.coalesce(func.sum(colonne), 0))
    for cond in conditions:
        query = query.where(cond)
    return Decimal(str((await db.execute(query)).scalar() or 0))


@router.get("/", response_model=DashboardStats)
async def get_dashboard(db: AsyncSession = Depends(get_db)):
    """Retourne les compteurs et les derniers documents pour le tableau de bord."""
    offres_actives = await _count(db, Offre, Offre.actif.is_(True))
    options_actives = await _count(db, Option, Option.actif.is_(True))
    clients = await _count(db, Client, Client.actif.is_(True))
    devis_total = await _count(db, Devis)
    devis_acceptes = await _count(db, Devis, Devis.statut == StatutDevis.ACCEPTE)
    factures_total = await _count(db, Facture)
    factures_impayees = await _count(
        db, Facture, Facture.statut.in_([StatutFacture.EMISE, StatutFacture.EN_RETARD])
    )

    montant_devis = await _somme(db, Devis.total_ttc)
    montant_factures = await _somme(db, Facture.total_ttc)

    derniers_devis = (await db.execute(
        select(Devis).order_by(Devis.date_emission.desc(), Devis.id.desc()).limit(5)
    )).scalars().all()

    dernieres_factures = (await db.execute(
        select(Facture).order_by(Facture.date_emission.desc(), Facture.id.desc()).limit(5)
    )).scalars().all()

    return DashboardStats(
        offres_actives=offres_actives,
        options_actives=options_actives,
        clients=clients,
        devis_total=devis_total,
        devis_acceptes=devis_acceptes,
        factures_total=factures_total,
        factures_impayees=factures_impayees,
        montant_devis_ttc=montant_devis,
        montant_factures_ttc=montant_factures,
        derniers_devis=[
            DevisRecent(
                id=d.id, reference=d.reference,
                client_raison_sociale=d.client_raison_sociale,
                statut=d.statut.value, total_ttc=d.total_ttc,
                date_emission=d.date_emission,
            ) for d in derniers_devis
        ],
        dernieres_factures=[
            FactureRecente(
                id=f.id, numero=f.numero, objet=f.objet,
                statut=f.statut.value, total_ttc=f.total_ttc,
                date_emission=f.date_emission,
            ) for f in dernieres_factures
        ],
    )
