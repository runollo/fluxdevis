"""Routes CRUD pour les options."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.option import Option
from pydantic import BaseModel
from decimal import Decimal

router = APIRouter()


class OptionRead(BaseModel):
    id: int
    code: str
    nom: str
    categorie: str
    type_ligne: str
    heures_setup: Decimal
    heures_mensuel: Decimal
    prix_heure: Decimal
    taux_marge: Decimal
    setup_achat: Decimal
    mensuel_achat: Decimal
    vente_setup: Decimal
    vente_mensuel: Decimal
    prix_hebergement: Decimal
    commentaire: str | None
    selection_regle: str
    quantite_defaut: int
    unite: str
    actif: bool
    ordre: int

    model_config = {"from_attributes": True}


class OptionCreate(BaseModel):
    code: str
    nom: str
    categorie: str
    type_ligne: str
    heures_setup: Decimal = Decimal("0")
    heures_mensuel: Decimal = Decimal("0")
    prix_heure: Decimal = Decimal("27")
    taux_marge: Decimal = Decimal("0.30")
    prix_hebergement: Decimal = Decimal("0")
    commentaire: str | None = None
    selection_regle: str = "OPTIONNEL"
    quantite_defaut: int = 0
    unite: str = "unite"
    ordre: int = 0


class OptionUpdate(BaseModel):
    nom: str | None = None
    categorie: str | None = None
    type_ligne: str | None = None
    heures_setup: Decimal | None = None
    heures_mensuel: Decimal | None = None
    prix_heure: Decimal | None = None
    taux_marge: Decimal | None = None
    prix_hebergement: Decimal | None = None
    commentaire: str | None = None
    selection_regle: str | None = None
    quantite_defaut: int | None = None
    unite: str | None = None
    actif: bool | None = None
    ordre: int | None = None


@router.get("/", response_model=list[OptionRead])
async def list_options(
    categorie: str | None = None,
    type_ligne: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Option).where(Option.actif).order_by(Option.ordre)
    if categorie:
        query = query.where(Option.categorie == categorie)
    if type_ligne:
        query = query.where(Option.type_ligne == type_ligne)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{option_id}", response_model=OptionRead)
async def get_option(option_id: int, db: AsyncSession = Depends(get_db)):
    option = await db.get(Option, option_id)
    if not option:
        raise HTTPException(404, "Option non trouvee")
    return option


@router.post("/", response_model=OptionRead, status_code=201)
async def create_option(data: OptionCreate, db: AsyncSession = Depends(get_db)):
    option = Option(**data.model_dump())
    option.recalculer_prix()
    db.add(option)
    await db.commit()
    await db.refresh(option)
    return option


@router.patch("/{option_id}", response_model=OptionRead)
async def update_option(option_id: int, data: OptionUpdate, db: AsyncSession = Depends(get_db)):
    option = await db.get(Option, option_id)
    if not option:
        raise HTTPException(404, "Option non trouvee")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(option, field, value)
    option.recalculer_prix()
    await db.commit()
    await db.refresh(option)
    return option
