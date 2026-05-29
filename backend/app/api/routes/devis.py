"""Routes pour les devis."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
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
from app.models.facture import Facture, FactureLigne, Echeance, TypeFacture, StatutFacture
from app.services.reference import generer_reference_facture
from app.services.reference import generer_reference_devis
from app.services.generation_devis import generer_devis, repartition_echeances
from app.services.facturation_maintenance import (
    generer_facture_maintenance, prochaine_periode, montant_recurrent_ht, MaintenanceError,
)

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


class FactureGenereeInfo(BaseModel):
    id: int
    numero: str
    type: str
    total_ttc: Decimal


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


class StatutUpdate(BaseModel):
    statut: StatutDevis


@router.get("/{devis_id}/detail")
async def detail_devis(devis_id: int, db: AsyncSession = Depends(get_db)):
    """Retourne le devis complet : snapshot, options, prestations, articles, factures liees."""
    result = await db.execute(
        select(Devis)
        .where(Devis.id == devis_id)
        .options(
            selectinload(Devis.lignes),
            selectinload(Devis.options),
            selectinload(Devis.articles_offerts),
            selectinload(Devis.factures),
        )
    )
    d = result.scalar_one_or_none()
    if not d:
        raise HTTPException(404, "Devis non trouve")

    recurrent_ht = montant_recurrent_ht(d)
    periode_due = await prochaine_periode(db, d)
    maintenance = {
        "recurrent_ht": str(recurrent_ht),
        "recurrent_ttc": str((recurrent_ht * Decimal("1.20")).quantize(Decimal("0.01"))),
        "a_facturer": periode_due is not None,
        "leasing": d.mode_reglement == ModeReglement.LEASING,
        "periode_due": (
            {
                "debut": periode_due["debut"].isoformat(),
                "fin": periode_due["fin"].isoformat(),
                "montant_ttc": str(periode_due["montant_ttc"]),
            } if periode_due else None
        ),
    }

    return {
        "id": d.id,
        "reference": d.reference,
        "statut": d.statut.value,
        "date_emission": d.date_emission.isoformat(),
        "date_validite": d.date_validite.isoformat(),
        "date_mise_en_ligne": d.date_mise_en_ligne.isoformat() if d.date_mise_en_ligne else None,
        "client_raison_sociale": d.client_raison_sociale,
        "client_adresse": d.client_adresse,
        "client_cp": d.client_cp,
        "client_ville": d.client_ville,
        "client_interlocuteur": d.client_interlocuteur,
        "client_telephone": d.client_telephone,
        "client_siret": d.client_siret,
        "offre_nom": d.offre_nom,
        "offre_type_site": d.offre_type_site,
        "mode_reglement": d.mode_reglement.value,
        "plan_paiement": d.plan_paiement.value if d.plan_paiement else None,
        "prix_vente_final": str(d.prix_vente_final),
        "total_prestations_ht": str(d.total_prestations_ht),
        "total_options_setup_ht": str(d.total_options_setup_ht),
        "total_pack_maintenance_ht": str(d.total_pack_maintenance_ht),
        "total_options_recurrent_ht": str(d.total_options_recurrent_ht),
        "loyer_mensuel": str(d.loyer_mensuel) if d.loyer_mensuel is not None else None,
        "duree_financement_mois": d.duree_financement_mois,
        "commercial": d.commercial,
        "total_ht": str(d.total_ht),
        "total_tva": str(d.total_tva),
        "total_ttc": str(d.total_ttc),
        "maintenance": maintenance,
        "options": [
            {
                "code": o.code, "nom": o.nom, "type_ligne": o.type_ligne,
                "quantite": o.quantite, "prix_setup_ht": str(o.prix_setup_ht),
                "prix_mensuel_ht": str(o.prix_mensuel_ht), "inclus": o.inclus,
            }
            for o in sorted(d.options, key=lambda x: x.ordre)
        ],
        "lignes": [
            {
                "designation": lg.designation, "quantite": lg.quantite,
                "prix_unitaire_vente": str(lg.prix_unitaire_vente),
            }
            for lg in sorted(d.lignes, key=lambda x: x.ordre)
        ],
        "articles_offerts": [
            {"designation": a.designation, "prix_vente": str(a.prix_vente)}
            for a in sorted(d.articles_offerts, key=lambda x: x.ordre)
        ],
        "factures": [
            {
                "id": f.id, "numero": f.numero, "type": f.type.value,
                "statut": f.statut.value, "total_ttc": str(f.total_ttc),
                "date_emission": f.date_emission.isoformat(),
            }
            for f in sorted(d.factures, key=lambda x: x.id)
        ],
    }


@router.patch("/{devis_id}/statut", response_model=DevisSummary)
async def changer_statut_devis(
    devis_id: int, data: StatutUpdate, db: AsyncSession = Depends(get_db)
):
    """Change le statut d'un devis (brouillon, envoye, accepte, refuse, expire)."""
    devis = await db.get(Devis, devis_id)
    if not devis:
        raise HTTPException(404, "Devis non trouve")
    devis.statut = data.statut
    await db.commit()
    await db.refresh(devis)
    return devis


class MiseEnLigneUpdate(BaseModel):
    date_mise_en_ligne: date | None = None


@router.patch("/{devis_id}/mise-en-ligne", response_model=DevisSummary)
async def definir_mise_en_ligne(
    devis_id: int, data: MiseEnLigneUpdate, db: AsyncSession = Depends(get_db)
):
    """Definit (ou efface) la date de mise en ligne du site, qui declenche la maintenance."""
    devis = await db.get(Devis, devis_id)
    if not devis:
        raise HTTPException(404, "Devis non trouve")
    devis.date_mise_en_ligne = data.date_mise_en_ligne
    await db.commit()
    await db.refresh(devis)
    return devis


@router.post("/{devis_id}/factures-maintenance", response_model=FactureGenereeInfo, status_code=201)
async def generer_facture_maintenance_endpoint(
    devis_id: int, db: AsyncSession = Depends(get_db)
):
    """Genere la facture de maintenance de la prochaine periode due (mois glissant)."""
    devis = await db.get(Devis, devis_id)
    if not devis:
        raise HTTPException(404, "Devis non trouve")
    try:
        facture = await generer_facture_maintenance(db, devis)
    except MaintenanceError as e:
        raise HTTPException(400, str(e))
    return FactureGenereeInfo(
        id=facture.id, numero=facture.numero,
        type=facture.type.value, total_ttc=facture.total_ttc,
    )


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


_TVA = Decimal("0.20")


def _ht_from_ttc(ttc: Decimal) -> Decimal:
    return (ttc / (Decimal("1") + _TVA)).quantize(Decimal("0.01"))


@router.post("/{devis_id}/factures", response_model=list[FactureGenereeInfo], status_code=201)
async def generer_factures_devis(devis_id: int, db: AsyncSession = Depends(get_db)):
    """Genere les factures d'acompte d'un devis selon son plan de paiement.

    Une facture par echeance du plan (100%, 50/50, 50/25/25, 25/25/25/25).
    La derniere echeance est de type SOLDE, les precedentes ACOMPTE.
    """
    devis = await db.get(Devis, devis_id)
    if not devis:
        raise HTTPException(404, "Devis non trouve")

    # Idempotence : ne pas regenerer si des factures existent deja
    existantes = await db.execute(
        select(func.count()).select_from(Facture).where(Facture.devis_id == devis_id)
    )
    if (existantes.scalar() or 0) > 0:
        raise HTTPException(400, "Des factures existent deja pour ce devis")

    plan = devis.plan_paiement.value if devis.plan_paiement else "100%"
    parts = repartition_echeances(plan, devis.total_ttc)
    nb = len(parts)

    # Echeancier complet (commun a toutes les factures, pour affichage Word)
    plan_rows = [
        {"label": label, "date": devis.date_emission.strftime("%d/%m/%Y"), "ttc": ttc}
        for label, ttc in parts
    ]

    creees: list[Facture] = []
    for idx, (label, ttc) in enumerate(parts):
        ht = _ht_from_ttc(ttc)
        tva = ttc - ht
        is_solde = idx == nb - 1
        type_f = TypeFacture.SOLDE if (is_solde and nb > 1) else TypeFacture.ACOMPTE
        type_label = "Solde" if type_f == TypeFacture.SOLDE else f"Acompte {idx + 1}/{nb}"

        numero = generer_reference_facture(devis.client_raison_sociale, num_facture=idx + 1)
        objet = f"{type_label} sur devis {devis.reference} — {devis.offre_nom}"

        # Collections passees au constructeur pour eviter un lazy-load (contexte async)
        ligne = FactureLigne(
            ordre=0, designation=objet, quantite=1,
            prix_unitaire_ht=ht, taux_tva=_TVA, montant_ht=ht,
        )
        echeances_facture = [
            Echeance(
                numero=e_idx + 1,
                label=row["label"],
                date_echeance=devis.date_emission,
                montant_ht=_ht_from_ttc(row["ttc"]),
                montant_ttc=row["ttc"],
                payee=e_idx < idx,
            )
            for e_idx, row in enumerate(plan_rows)
        ]

        facture = Facture(
            numero=numero,
            type=type_f,
            statut=StatutFacture.BROUILLON,
            devis_id=devis.id,
            date_emission=date.today(),
            date_echeance=date.today(),
            objet=objet,
            total_ht=ht,
            total_tva=tva,
            total_ttc=ttc,
            lignes=[ligne],
            echeances=echeances_facture,
        )
        db.add(facture)
        creees.append(facture)

    await db.commit()
    for f in creees:
        await db.refresh(f)
    return [
        FactureGenereeInfo(id=f.id, numero=f.numero, type=f.type.value, total_ttc=f.total_ttc)
        for f in creees
    ]


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
