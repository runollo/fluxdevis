"""Routes pour les devis (placeholder — logique metier a completer en Phase 2)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.devis import Devis, StatutDevis
from pydantic import BaseModel
from decimal import Decimal
from datetime import date

router = APIRouter()


class DevisSummary(BaseModel):
    id: int
    reference: str
    statut: StatutDevis
    date_emission: date
    client_raison_sociale: str
    offre_nom: str
    mode_reglement: str
    total_ttc: Decimal

    model_config = {"from_attributes": True}


@router.get("/", response_model=list[DevisSummary])
async def list_devis(
    statut: StatutDevis | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Devis).order_by(Devis.date_emission.desc())
    if statut:
        query = query.where(Devis.statut == statut)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{devis_id}", response_model=DevisSummary)
async def get_devis(devis_id: int, db: AsyncSession = Depends(get_db)):
    devis = await db.get(Devis, devis_id)
    if not devis:
        raise HTTPException(404, "Devis non trouve")
    return devis


@router.get("/next-reference", response_model=dict)
async def next_reference(db: AsyncSession = Depends(get_db)):
    """Genere la prochaine reference de devis (D2026-XXX)."""
    year = date.today().year
    prefix = f"D{year}-"
    result = await db.execute(
        select(func.count()).where(Devis.reference.like(f"{prefix}%"))
    )
    count = result.scalar() or 0
    return {"reference": f"{prefix}{count + 1:03d}"}
