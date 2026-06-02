"""Routes CRUD pour les options."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.option import Option
from app.data.packs_maintenance import (
    PACKS_MAINTENANCE, contenu_cumule, _prestations_propres, _champ_pack,
)
from app.services.generation_devis import charger_overrides_packs
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
    q: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Option).where(Option.actif).order_by(Option.ordre)
    if categorie:
        query = query.where(Option.categorie == categorie)
    if type_ligne:
        query = query.where(Option.type_ligne == type_ligne)
    if q:
        motif = f"%{q.strip()}%"
        query = query.where(
            Option.nom.ilike(motif)
            | Option.code.ilike(motif)
            | Option.categorie.ilike(motif)
        )
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


# --- Contenu editable des packs de maintenance --------------------------------
# Le descriptif d'un pack (accroche, intro, delai, prestations) est cumulatif :
# chaque niveau herite du precedent. On edite UNIQUEMENT ce qui est propre au
# niveau ; l'herite (cumul du parent) est fourni en lecture seule pour le contexte.
# Defaut = app.data.packs_maintenance ; l'edition est persistee dans
# Option.contenu_pack (override).

class PrestationItem(BaseModel):
    titre: str
    detail: str = ""


class ContenuPackUpdate(BaseModel):
    accroche: str | None = None
    intro: str | None = None
    delai_reponse: str | None = None
    prestations: list[PrestationItem] | None = None


async def _pack_ou_404(option_id: int, db: AsyncSession) -> Option:
    option = await db.get(Option, option_id)
    if not option:
        raise HTTPException(404, "Option non trouvee")
    if (option.type_ligne or "").upper() != "PACK":
        raise HTTPException(400, "Cette option n'est pas un pack de maintenance.")
    if PACKS_MAINTENANCE.get((option.code or "").strip()) is None:
        raise HTTPException(404, "Pack inconnu dans le referentiel packs_maintenance.")
    return option


def _contenu_pack_payload(option: Option, overrides: dict) -> dict:
    """Construit la reponse contenu-pack : niveau propre (editable) + herite (lecture seule)."""
    code = (option.code or "").strip()
    pack = PACKS_MAINTENANCE[code]

    propre_prest = _prestations_propres(code, pack, overrides)
    contenu = {
        "accroche": _champ_pack(code, pack, overrides, "accroche") or "",
        "intro": _champ_pack(code, pack, overrides, "intro") or "",
        "delai_reponse": _champ_pack(code, pack, overrides, "delai_reponse") or "",
        "prestations": [{"titre": t, "detail": d} for t, d in propre_prest],
    }

    herite: list[dict] = []
    parent_code = pack.get("herite_de")
    if parent_code:
        pc = contenu_cumule(parent_code, overrides)
        if pc:
            herite = [
                {"titre": p["titre"], "detail": p["detail"], "niveau": p["niveau"]}
                for p in pc["prestations"]
            ]

    return {
        "option_id": option.id,
        "code": code,
        "nom": option.nom,
        "niveau": pack["niveau"],
        "famille": pack["famille"],
        "famille_label": pack["famille_label"],
        "socle_obligatoire": pack["socle_obligatoire"],
        "personnalise": code in overrides,  # True si un override base existe
        "herite": herite,
        "contenu": contenu,
    }


@router.get("/{option_id}/contenu-pack")
async def get_contenu_pack(option_id: int, db: AsyncSession = Depends(get_db)):
    """Contenu editable d'un pack : le descriptif propre au niveau (override base si
    present, sinon valeurs par defaut du fichier) + les prestations heritees du parent."""
    option = await _pack_ou_404(option_id, db)
    overrides = await charger_overrides_packs(db)
    return _contenu_pack_payload(option, overrides)


@router.patch("/{option_id}/contenu-pack")
async def update_contenu_pack(
    option_id: int, data: ContenuPackUpdate, db: AsyncSession = Depends(get_db)
):
    """Enregistre le descriptif PROPRE au niveau dans Option.contenu_pack (override)."""
    option = await _pack_ou_404(option_id, db)
    option.contenu_pack = {
        "accroche": (data.accroche or "").strip(),
        "intro": (data.intro or "").strip(),
        "delai_reponse": (data.delai_reponse or "").strip(),
        "prestations": [
            {"titre": p.titre.strip(), "detail": (p.detail or "").strip()}
            for p in (data.prestations or [])
            if p.titre.strip()
        ],
    }
    await db.commit()
    await db.refresh(option)
    overrides = await charger_overrides_packs(db)
    return _contenu_pack_payload(option, overrides)


@router.delete("/{option_id}/contenu-pack")
async def reset_contenu_pack(option_id: int, db: AsyncSession = Depends(get_db)):
    """Reinitialise le pack sur le contenu par defaut (supprime l'override base)."""
    option = await _pack_ou_404(option_id, db)
    option.contenu_pack = None
    await db.commit()
    await db.refresh(option)
    overrides = await charger_overrides_packs(db)
    return _contenu_pack_payload(option, overrides)
