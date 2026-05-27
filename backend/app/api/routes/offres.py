"""Routes CRUD pour les offres."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.offre import Offre
from pydantic import BaseModel
from decimal import Decimal

router = APIRouter()


class OffreRead(BaseModel):
    id: int
    nom: str
    type_site: str
    type_offre: str
    tarif_achat: Decimal
    taux_marge: Decimal
    tarif_vente_conseille: Decimal
    pages: int
    heures: int
    commission_apporteur: Decimal
    actif: bool
    ordre: int

    model_config = {"from_attributes": True}


class OffreCreate(BaseModel):
    nom: str
    type_site: str
    type_offre: str
    tarif_achat: Decimal
    taux_marge: Decimal
    tarif_vente_conseille: Decimal
    pages: int
    heures: int
    commission_apporteur: Decimal = Decimal("0")
    ordre: int = 0


class OffreUpdate(BaseModel):
    nom: str | None = None
    type_site: str | None = None
    type_offre: str | None = None
    tarif_achat: Decimal | None = None
    taux_marge: Decimal | None = None
    tarif_vente_conseille: Decimal | None = None
    pages: int | None = None
    heures: int | None = None
    commission_apporteur: Decimal | None = None
    actif: bool | None = None
    ordre: int | None = None


@router.get("/", response_model=list[OffreRead])
async def list_offres(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Offre).where(Offre.actif).order_by(Offre.ordre))
    return result.scalars().all()


@router.get("/{offre_id}", response_model=OffreRead)
async def get_offre(offre_id: int, db: AsyncSession = Depends(get_db)):
    offre = await db.get(Offre, offre_id)
    if not offre:
        raise HTTPException(404, "Offre non trouvee")
    return offre


@router.post("/", response_model=OffreRead, status_code=201)
async def create_offre(data: OffreCreate, db: AsyncSession = Depends(get_db)):
    offre = Offre(**data.model_dump())
    db.add(offre)
    await db.commit()
    await db.refresh(offre)
    return offre


@router.patch("/{offre_id}", response_model=OffreRead)
async def update_offre(offre_id: int, data: OffreUpdate, db: AsyncSession = Depends(get_db)):
    offre = await db.get(Offre, offre_id)
    if not offre:
        raise HTTPException(404, "Offre non trouvee")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(offre, field, value)
    await db.commit()
    await db.refresh(offre)
    return offre


@router.delete("/{offre_id}", status_code=204)
async def delete_offre(offre_id: int, db: AsyncSession = Depends(get_db)):
    offre = await db.get(Offre, offre_id)
    if not offre:
        raise HTTPException(404, "Offre non trouvee")
    offre.actif = False
    await db.commit()
