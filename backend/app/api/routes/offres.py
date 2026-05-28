"""Routes CRUD pour les offres."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.offre import Offre
from app.models.option import Option, OptionInclusion
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


class OptionWithStatut(BaseModel):
    id: int
    code: str
    nom: str
    categorie: str
    type_ligne: str
    vente_setup: Decimal
    vente_mensuel: Decimal
    setup_achat: Decimal
    mensuel_achat: Decimal
    commentaire: str | None
    statut: str  # Inclus, Option payante, Non disponible
    ordre: int

    model_config = {"from_attributes": True}


# Noms des 4 packs maintenance
_PACK_CODES = {"WF_MAINT_ESS", "WF_MAINT_STD", "WF_MAINT_PRO", "WF_MAINT_PREM",
               "SHOPIFY_MAINT_ESS", "SHOPIFY_MAINT_STD", "SHOPIFY_MAINT_PRO", "SHOPIFY_MAINT_PREM"}


@router.get("/{offre_id}/options", response_model=list[OptionWithStatut])
async def get_offre_options(offre_id: int, db: AsyncSession = Depends(get_db)):
    """Retourne toutes les options avec leur statut pour une offre donnee."""
    offre = await db.get(Offre, offre_id)
    if not offre:
        raise HTTPException(404, "Offre non trouvee")

    # Charger les inclusions pour cette offre
    incl_result = await db.execute(
        select(OptionInclusion.option_id).where(OptionInclusion.offre_id == offre_id)
    )
    included_ids = set(incl_result.scalars().all())

    # Charger toutes les options actives
    opts_result = await db.execute(
        select(Option).where(Option.actif).order_by(Option.ordre)
    )
    options = opts_result.scalars().all()

    # Determiner le type de site pour filtrer les packs maintenance
    is_shopify = "shopify" in offre.type_site.lower()

    result = []
    for opt in options:
        # Filtrer les packs maintenance par plateforme
        if opt.code.startswith("WF_MAINT_") and is_shopify:
            continue
        if opt.code.startswith("SHOPIFY_MAINT_") and not is_shopify:
            continue

        # Determiner le statut
        if opt.id in included_ids:
            statut = "Inclus"
        elif opt.type_ligne == "PACK":
            statut = "Disponible"
        else:
            statut = "Option payante"

        result.append(OptionWithStatut(
            id=opt.id,
            code=opt.code,
            nom=opt.nom,
            categorie=opt.categorie,
            type_ligne=opt.type_ligne,
            vente_setup=opt.vente_setup,
            vente_mensuel=opt.vente_mensuel,
            setup_achat=opt.setup_achat,
            mensuel_achat=opt.mensuel_achat,
            commentaire=opt.commentaire,
            statut=statut,
            ordre=opt.ordre,
        ))
    return result
