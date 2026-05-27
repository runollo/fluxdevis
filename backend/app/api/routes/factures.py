"""Routes pour les factures (placeholder — logique metier a completer en Phase 2)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.facture import Facture, StatutFacture, TypeFacture
from pydantic import BaseModel
from decimal import Decimal
from datetime import date

router = APIRouter()


class FactureSummary(BaseModel):
    id: int
    numero: str
    type: TypeFacture
    statut: StatutFacture
    date_emission: date
    date_echeance: date
    objet: str
    total_ttc: Decimal

    model_config = {"from_attributes": True}


@router.get("/", response_model=list[FactureSummary])
async def list_factures(
    statut: StatutFacture | None = None,
    type: TypeFacture | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Facture).order_by(Facture.date_emission.desc())
    if statut:
        query = query.where(Facture.statut == statut)
    if type:
        query = query.where(Facture.type == type)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{facture_id}", response_model=FactureSummary)
async def get_facture(facture_id: int, db: AsyncSession = Depends(get_db)):
    facture = await db.get(Facture, facture_id)
    if not facture:
        raise HTTPException(404, "Facture non trouvee")
    return facture


@router.get("/next-numero", response_model=dict)
async def next_numero(db: AsyncSession = Depends(get_db)):
    """Genere le prochain numero de facture (F2026-XXX)."""
    year = date.today().year
    prefix = f"F{year}-"
    result = await db.execute(
        select(func.count()).where(Facture.numero.like(f"{prefix}%"))
    )
    count = result.scalar() or 0
    return {"numero": f"{prefix}{count + 1:03d}"}
