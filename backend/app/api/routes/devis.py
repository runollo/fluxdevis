"""Routes pour les devis."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from decimal import Decimal
from datetime import date, timedelta

from app.core.database import get_db
from app.models.devis import Devis, DevisOptionLigne, StatutDevis, ModeReglement, PlanPaiement
from app.models.client import Client
from app.models.offre import Offre
from app.models.societe import Societe
from app.services.reference import generer_reference_devis
from app.services.generation_devis import generer_devis

router = APIRouter()

_PLAN_MAP = {
    "100%": PlanPaiement.CENT,
    "50/50": PlanPaiement.CINQUANTE_CINQUANTE,
    "50/25/25": PlanPaiement.CINQUANTE_VINGTCINQ_VINGTCINQ,
    "25/25/25/25": PlanPaiement.VINGTCINQ_X4,
}


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


class DevisCreateRequest(BaseModel):
    client_id: int
    offre_id: int
    mode_reglement: str = "Comptant"
    plan_paiement: str = "100%"
    # Prix
    prix_vente_final: Decimal
    total_prestations_ht: Decimal = Decimal("0")
    total_options_setup_ht: Decimal = Decimal("0")
    total_pack_maintenance_ht: Decimal = Decimal("0")
    total_options_recurrent_ht: Decimal = Decimal("0")
    # Remises
    remise_pct_setup: Decimal = Decimal("0")
    remise_pct_recurrent: Decimal = Decimal("0")
    remise_eur_setup: Decimal = Decimal("0")
    remise_eur_recurrent: Decimal = Decimal("0")
    marge_additionnelle: Decimal = Decimal("0")
    # Leasing
    duree_financement_mois: int | None = None
    coefficient_locam: Decimal | None = None
    pct_maintenance_locam: Decimal | None = None
    garantie_web: Decimal | None = None
    montant_finance: Decimal | None = None
    loyer_mensuel: Decimal | None = None
    # Totaux
    total_ht: Decimal = Decimal("0")
    total_tva: Decimal = Decimal("0")
    total_ttc: Decimal = Decimal("0")
    # Options selectionnees
    options: list[dict] = []
    # Textes
    commercial: str | None = None


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


@router.get("/{devis_id}/document")
async def telecharger_devis(devis_id: int, db: AsyncSession = Depends(get_db)):
    """Genere et retourne le devis au format Word (.docx)."""
    result = await db.execute(
        select(Devis)
        .where(Devis.id == devis_id)
        .options(
            selectinload(Devis.lignes),
            selectinload(Devis.options),
            selectinload(Devis.articles_offerts),
        )
    )
    devis = result.scalar_one_or_none()
    if not devis:
        raise HTTPException(404, "Devis non trouve")

    societe = (await db.execute(select(Societe).limit(1))).scalar_one_or_none()

    buf = generer_devis(devis, societe)
    filename = f"Devis_{devis.reference}.docx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/", response_model=DevisSummary, status_code=201)
async def create_devis(data: DevisCreateRequest, db: AsyncSession = Depends(get_db)):
    """Cree un devis avec snapshot des infos client et offre."""
    client = await db.get(Client, data.client_id)
    if not client:
        raise HTTPException(404, "Client non trouve")

    offre = await db.get(Offre, data.offre_id)
    if not offre:
        raise HTTPException(404, "Offre non trouvee")

    reference = generer_reference_devis(client.raison_sociale)

    mode = ModeReglement.LEASING if data.mode_reglement == "Leasing" else ModeReglement.COMPTANT
    plan = _PLAN_MAP.get(data.plan_paiement)

    devis = Devis(
        reference=reference,
        statut=StatutDevis.BROUILLON,
        date_emission=date.today(),
        date_validite=date.today() + timedelta(days=30),
        # Snapshot client
        client_id=client.id,
        client_raison_sociale=client.raison_sociale,
        client_adresse=client.adresse,
        client_cp=client.code_postal,
        client_ville=client.ville,
        client_interlocuteur=client.interlocuteur,
        client_telephone=client.telephone,
        client_siret=client.siret,
        # Snapshot offre
        offre_id=offre.id,
        offre_nom=offre.nom,
        offre_type_site=offre.type_site,
        offre_prix_catalogue=offre.tarif_vente_conseille,
        # Mode
        mode_reglement=mode,
        plan_paiement=plan,
        # Prix
        prix_vente_final=data.prix_vente_final,
        total_prestations_ht=data.total_prestations_ht,
        total_options_setup_ht=data.total_options_setup_ht,
        total_pack_maintenance_ht=data.total_pack_maintenance_ht,
        total_options_recurrent_ht=data.total_options_recurrent_ht,
        # Remises
        remise_pct_setup=data.remise_pct_setup,
        remise_pct_recurrent=data.remise_pct_recurrent,
        remise_eur_setup=data.remise_eur_setup,
        remise_eur_recurrent=data.remise_eur_recurrent,
        marge_additionnelle=data.marge_additionnelle,
        # Leasing
        duree_financement_mois=data.duree_financement_mois,
        coefficient_locam=data.coefficient_locam,
        pct_maintenance_locam=data.pct_maintenance_locam,
        garantie_web=data.garantie_web,
        montant_finance=data.montant_finance,
        loyer_mensuel=data.loyer_mensuel,
        # Totaux
        total_ht=data.total_ht,
        total_tva=data.total_tva,
        total_ttc=data.total_ttc,
        # Textes
        commercial=data.commercial,
    )
    db.add(devis)
    await db.flush()

    # Sauvegarder les options selectionnees
    for opt_data in data.options:
        opt_ligne = DevisOptionLigne(
            devis_id=devis.id,
            option_id=opt_data.get("option_id", 0),
            code=opt_data.get("code", ""),
            nom=opt_data.get("nom", ""),
            type_ligne=opt_data.get("type_ligne", ""),
            quantite=opt_data.get("quantite", 1),
            prix_setup_ht=Decimal(str(opt_data.get("prix_setup_ht", 0))),
            prix_mensuel_ht=Decimal(str(opt_data.get("prix_mensuel_ht", 0))),
            inclus=opt_data.get("inclus", False),
        )
        db.add(opt_ligne)

    await db.commit()
    await db.refresh(devis)
    return devis
