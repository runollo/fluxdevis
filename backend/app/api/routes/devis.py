"""Routes pour les devis."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from decimal import Decimal
from datetime import date, timedelta, datetime, timezone

from app.core.database import get_db
from app.models.devis import Devis, DevisLigne, DevisOptionLigne, DevisArticleOffert, StatutDevis, ModeReglement, PlanPaiement
from app.models.client import Client
from app.models.offre import Offre
from app.models.societe import Societe
from app.models.facture import Facture, FactureLigne, Echeance, TypeFacture, StatutFacture
from app.services.reference import generer_reference_facture
from app.services.reference import generer_reference_devis
from app.services.generation_devis import generer_devis, repartition_echeances
from app.services.export_excel import export_devis_xlsx
from app.services.facturation_maintenance import (
    generer_facture_maintenance, prochaine_periode, montant_recurrent_ht, MaintenanceError,
)

router = APIRouter()

_PLAN_MAP = {
    "100%": PlanPaiement.CENT,
    "50/50": PlanPaiement.CINQUANTE_CINQUANTE,
    "33/33/33": PlanPaiement.TIERS,
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
    version: int = 1

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
    total_offerts_recurrent_ht: Decimal = Decimal("0")
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
    # Prestations sur mesure (designation, quantite, prix_unitaire_achat, prix_unitaire_vente)
    prestations: list[dict] = []
    # Articles offerts (designation, prix_achat, prix_vente, est_setup)
    articles_offerts: list[dict] = []
    # Textes
    commercial: str | None = None


@router.get("/", response_model=list[DevisSummary])
async def list_devis(
    statut: StatutDevis | None = None,
    archives: bool = False,
    q: str | None = None,
    skip: int = 0,
    limit: int = 25,
    db: AsyncSession = Depends(get_db),
):
    """Liste les devis. Par defaut, exclut les devis archives (corbeille).

    - archives=true : retourne uniquement les devis archives.
    - q : recherche sur la reference, le client ou l'offre (insensible a la casse).
    - skip / limit : pagination par decalage.
    """
    query = select(Devis).order_by(Devis.date_emission.desc(), Devis.id.desc())
    if archives:
        query = query.where(Devis.archived_at.is_not(None))
    else:
        query = query.where(Devis.archived_at.is_(None))
    # Ne montrer que la version active de chaque devis (les anciennes versions
    # restent consultables via le detail, mais pas dans la liste).
    query = query.where(Devis.version_active.is_(True))
    if statut:
        query = query.where(Devis.statut == statut)
    if q:
        motif = f"%{q.strip()}%"
        query = query.where(
            Devis.reference.ilike(motif)
            | Devis.client_raison_sociale.ilike(motif)
            | Devis.offre_nom.ilike(motif)
        )
    query = query.offset(max(skip, 0)).limit(max(min(limit, 200), 1))
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/export.xlsx")
async def export_devis(q: str | None = None, db: AsyncSession = Depends(get_db)):
    """Exporte les devis actifs (non archives) au format Excel, en respectant q."""
    query = select(Devis).where(Devis.archived_at.is_(None)).order_by(
        Devis.date_emission.desc(), Devis.id.desc()
    )
    if q:
        motif = f"%{q.strip()}%"
        query = query.where(
            Devis.reference.ilike(motif)
            | Devis.client_raison_sociale.ilike(motif)
            | Devis.offre_nom.ilike(motif)
        )
    devis = (await db.execute(query)).scalars().all()
    buf = export_devis_xlsx(devis)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="devis.xlsx"'},
    )


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

    # Toutes les versions de la lignee (racine + revisions), pour le bloc "Versions".
    racine = d.racine_id or d.id
    versions_rows = (await db.execute(
        select(Devis)
        .where((Devis.id == racine) | (Devis.racine_id == racine))
        .order_by(Devis.version)
    )).scalars().all()
    versions = [
        {
            "id": v.id, "reference": v.reference, "version": v.version,
            "statut": v.statut.value, "active": v.version_active,
            "date_emission": v.date_emission.isoformat(),
            "total_ttc": str(v.total_ttc),
        }
        for v in versions_rows
    ]

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
        "version": d.version,
        "version_active": d.version_active,
        "versions": versions,
        "date_emission": d.date_emission.isoformat(),
        "date_validite": d.date_validite.isoformat(),
        "date_mise_en_ligne": d.date_mise_en_ligne.isoformat() if d.date_mise_en_ligne else None,
        "client_raison_sociale": d.client_raison_sociale,
        "client_adresse": d.client_adresse,
        "client_cp": d.client_cp,
        "client_ville": d.client_ville,
        "client_interlocuteur": d.client_interlocuteur,
        "client_telephone": d.client_telephone,
        "client_email": d.client_email,
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
            if f.archived_at is None
        ],
    }


@router.get("/{devis_id}/edition")
async def edition_devis(devis_id: int, db: AsyncSession = Depends(get_db)):
    """Retourne l'etat du devis sous une forme directement reexploitable par le
    simulateur (pour rouvrir et modifier le devis). Reconstitue les quantites
    d'options, le pack, les prestations, les remises/mode/plan et les cases
    "Offrir" (par correspondance de designation avec les articles offerts).
    """
    result = await db.execute(
        select(Devis)
        .where(Devis.id == devis_id)
        .options(
            selectinload(Devis.lignes),
            selectinload(Devis.options),
            selectinload(Devis.articles_offerts),
        )
    )
    d = result.scalar_one_or_none()
    if not d:
        raise HTTPException(404, "Devis non trouve")

    offerts_noms = {(a.designation or "").strip() for a in d.articles_offerts}

    options = []
    pack_id = None
    offrir_option_ids = []
    for o in sorted(d.options, key=lambda x: x.ordre):
        if o.type_ligne == "PACK":
            pack_id = o.option_id
        else:
            options.append({"option_id": o.option_id, "quantite": o.quantite, "inclus": o.inclus})
        if (o.nom or "").strip() in offerts_noms:
            offrir_option_ids.append(o.option_id)

    prestations = [
        {
            "nom": lg.designation,
            "qty": str(lg.quantite),
            "achat": str(lg.prix_unitaire_achat),
            "vente": str(lg.prix_unitaire_vente),
            "offrir": (lg.designation or "").strip() in offerts_noms,
        }
        for lg in sorted(d.lignes, key=lambda x: x.ordre)
    ]

    def pct(v):
        return str((v * Decimal("100")).quantize(Decimal("0.01")).normalize())

    return {
        "id": d.id,
        "statut": d.statut.value,
        "offre_id": d.offre_id,
        "client_id": d.client_id,
        "mode": d.mode_reglement.value,
        "plan": d.plan_paiement.value if d.plan_paiement else "100%",
        "remise_setup": pct(d.remise_pct_setup),
        "remise_recurrent": pct(d.remise_pct_recurrent),
        "marge_add": str(d.marge_additionnelle),
        "pack_id": pack_id,
        "options": options,
        "offrir_option_ids": offrir_option_ids,
        "prestations": prestations,
    }


def _reference_version(reference_base: str, version: int) -> str:
    """Construit la reference d'une version : base pour V1, base-V{n} ensuite.

    Tolere une reference deja suffixee (ex: une ancienne -V2) en repartant de la base.
    """
    base = reference_base.split("-V")[0] if "-V" in reference_base else reference_base
    return base if version <= 1 else f"{base}-V{version}"


@router.post("/{devis_id}/reviser", response_model=DevisSummary, status_code=201)
async def reviser_devis(devis_id: int, data: DevisCreateRequest, db: AsyncSession = Depends(get_db)):
    """Enregistre une modification d'un devis existant.

    - Si le devis est en BROUILLON : il est mis a jour sur place (pas de nouvelle
      version ; le brouillon est librement modifiable).
    - Sinon (envoye/accepte/refuse/expire) : une NOUVELLE VERSION est creee
      (V+1), l'ancienne est conservee en lecture seule (version_active=False).
      La nouvelle version repart en BROUILLON.

    Garde-fou : on ne revise jamais une version qui n'est plus active (il faut
    repartir de la version courante).
    """
    ancien = await db.get(Devis, devis_id)
    if not ancien:
        raise HTTPException(404, "Devis non trouve")
    if not ancien.version_active:
        raise HTTPException(400, "Cette version n'est plus active. Revisez la version courante.")
    if ancien.archived_at is not None:
        raise HTTPException(400, "Devis archive : restaurez-le avant de le modifier.")

    client = await db.get(Client, data.client_id)
    if not client:
        raise HTTPException(404, "Client non trouve")
    offre = await db.get(Offre, data.offre_id)
    if not offre:
        raise HTTPException(404, "Offre non trouvee")

    mode = ModeReglement.LEASING if data.mode_reglement == "Leasing" else ModeReglement.COMPTANT
    plan = _PLAN_MAP.get(data.plan_paiement)

    # --- Cas 1 : brouillon -> mise a jour sur place ---
    if ancien.statut == StatutDevis.BROUILLON:
        # Purger les lignes filles existantes, puis les reconstruire a l'identique
        # de ce que le simulateur envoie.
        await db.execute(
            DevisOptionLigne.__table__.delete().where(DevisOptionLigne.devis_id == ancien.id)
        )
        await db.execute(
            DevisLigne.__table__.delete().where(DevisLigne.devis_id == ancien.id)
        )
        await db.execute(
            DevisArticleOffert.__table__.delete().where(DevisArticleOffert.devis_id == ancien.id)
        )
        _appliquer_champs(ancien, data, client, offre, mode, plan)
        await db.flush()
        _remplir_lignes(db, ancien.id, data)
        await db.commit()
        await db.refresh(ancien)
        return ancien

    # --- Cas 2 : devis deja transmis -> nouvelle version ---
    racine_id = ancien.racine_id or ancien.id
    nouvelle_version = ancien.version + 1
    reference = _reference_version(ancien.reference, nouvelle_version)

    nouveau = Devis(
        reference=reference,
        racine_id=racine_id,
        version=nouvelle_version,
        version_active=True,
        statut=StatutDevis.BROUILLON,
        date_emission=date.today(),
        date_validite=date.today() + timedelta(days=30),
        client_id=client.id,
    )
    _appliquer_champs(nouveau, data, client, offre, mode, plan)
    db.add(nouveau)
    ancien.version_active = False
    await db.flush()
    _remplir_lignes(db, nouveau.id, data)
    await db.commit()
    await db.refresh(nouveau)
    return nouveau


def _appliquer_champs(devis: Devis, data: "DevisCreateRequest", client, offre, mode, plan) -> None:
    """Applique les champs d'une requete sur un devis (snapshot client/offre + prix)."""
    devis.client_id = client.id
    devis.client_raison_sociale = client.raison_sociale
    devis.client_adresse = client.adresse
    devis.client_cp = client.code_postal
    devis.client_ville = client.ville
    devis.client_interlocuteur = client.interlocuteur
    devis.client_telephone = client.telephone
    devis.client_email = client.email
    devis.client_siret = client.siret
    devis.offre_id = offre.id
    devis.offre_nom = offre.nom
    devis.offre_type_site = offre.type_site
    devis.offre_prix_catalogue = offre.tarif_vente_conseille
    devis.mode_reglement = mode
    devis.plan_paiement = plan
    devis.prix_vente_final = data.prix_vente_final
    devis.total_prestations_ht = data.total_prestations_ht
    devis.total_options_setup_ht = data.total_options_setup_ht
    devis.total_pack_maintenance_ht = data.total_pack_maintenance_ht
    devis.total_options_recurrent_ht = data.total_options_recurrent_ht
    devis.total_offerts_recurrent_ht = data.total_offerts_recurrent_ht
    devis.remise_pct_setup = data.remise_pct_setup
    devis.remise_pct_recurrent = data.remise_pct_recurrent
    devis.remise_eur_setup = data.remise_eur_setup
    devis.remise_eur_recurrent = data.remise_eur_recurrent
    devis.marge_additionnelle = data.marge_additionnelle
    devis.duree_financement_mois = data.duree_financement_mois
    devis.coefficient_locam = data.coefficient_locam
    devis.pct_maintenance_locam = data.pct_maintenance_locam
    devis.garantie_web = data.garantie_web
    devis.montant_finance = data.montant_finance
    devis.loyer_mensuel = data.loyer_mensuel
    devis.total_ht = data.total_ht
    devis.total_tva = data.total_tva
    devis.total_ttc = data.total_ttc
    devis.commercial = data.commercial


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


@router.delete("/{devis_id}", status_code=204)
async def archiver_devis(devis_id: int, db: AsyncSession = Depends(get_db)):
    """Archive un devis (corbeille) — aucune destruction physique.

    Garde-fou juridique : refuse si une facture deja emise (ou au-dela) est
    rattachee, car un devis facture est un document contractuel. Les eventuelles
    factures encore en brouillon sont archivees en cascade.
    """
    devis = await db.get(Devis, devis_id)
    if not devis:
        raise HTTPException(404, "Devis non trouve")
    if devis.archived_at is not None:
        raise HTTPException(400, "Devis deja archive")

    factures = (
        await db.execute(
            select(Facture).where(
                Facture.devis_id == devis_id, Facture.archived_at.is_(None)
            )
        )
    ).scalars().all()

    # Seules les factures encore actives (emise/payee/en retard) bloquent : ce
    # sont des documents engageants. Les brouillons et les factures annulees
    # (avoirs deja neutralises) sont archivees en cascade avec le devis.
    neutres = {StatutFacture.BROUILLON, StatutFacture.ANNULEE}
    engageantes = [f for f in factures if f.statut not in neutres]
    if engageantes:
        numeros = ", ".join(f.numero for f in engageantes)
        raise HTTPException(
            400,
            "Impossible d'archiver : des factures emises sont rattachees a ce devis "
            f"({numeros}). Annulez-les d'abord (avoir).",
        )

    now = datetime.now(timezone.utc)
    for f in factures:  # brouillons et annulees uniquement a ce stade
        f.archived_at = now
    devis.archived_at = now
    await db.commit()


@router.post("/{devis_id}/restaurer", response_model=DevisSummary)
async def restaurer_devis(devis_id: int, db: AsyncSession = Depends(get_db)):
    """Restaure un devis archive (le sort de la corbeille)."""
    devis = await db.get(Devis, devis_id)
    if not devis:
        raise HTTPException(404, "Devis non trouve")
    devis.archived_at = None
    await db.commit()
    await db.refresh(devis)
    return devis


@router.delete("/{devis_id}/definitif", status_code=204)
async def supprimer_devis_definitif(devis_id: int, db: AsyncSession = Depends(get_db)):
    """Suppression DEFINITIVE d'un devis (destruction physique) depuis la corbeille.

    Garde-fous : le devis doit deja etre archive ; refus si une facture conservee
    legalement (emise/payee/en retard/annulee) y est rattachee. Les seules factures
    encore liees a ce stade (brouillons) sont detruites avec le devis.
    """
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
    if devis.archived_at is None:
        raise HTTPException(400, "Mettez d'abord le devis dans la corbeille.")

    factures = (
        await db.execute(
            select(Facture)
            .where(Facture.devis_id == devis_id)
            .options(selectinload(Facture.lignes), selectinload(Facture.echeances))
        )
    ).scalars().all()
    conservees = [f for f in factures if f.statut != StatutFacture.BROUILLON]
    if conservees:
        numeros = ", ".join(f.numero for f in conservees)
        raise HTTPException(
            400,
            "Suppression definitive impossible : des factures sont conservees "
            f"legalement ({numeros}). Elles doivent rester en base.",
        )

    for f in factures:  # uniquement des brouillons
        await db.delete(f)
    await db.delete(devis)
    await db.commit()


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

    # Idempotence : ne pas regenerer si des factures actives existent deja
    # (les factures archivees ne comptent pas — permet de regenerer apres corbeille)
    existantes = await db.execute(
        select(func.count()).select_from(Facture).where(
            Facture.devis_id == devis_id, Facture.archived_at.is_(None)
        )
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
        client_email=client.email,
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
        total_offerts_recurrent_ht=data.total_offerts_recurrent_ht,
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

    _remplir_lignes(db, devis.id, data)

    await db.commit()
    await db.refresh(devis)
    return devis


def _remplir_lignes(db: AsyncSession, devis_id: int, data: "DevisCreateRequest") -> None:
    """Cree les lignes filles d'un devis (options, prestations, articles offerts)
    a partir d'une requete. Mutualise entre creation et revision (nouvelle version).
    """
    # Options selectionnees
    for opt_data in data.options:
        db.add(DevisOptionLigne(
            devis_id=devis_id,
            option_id=opt_data.get("option_id", 0),
            code=opt_data.get("code", ""),
            nom=opt_data.get("nom", ""),
            type_ligne=opt_data.get("type_ligne", ""),
            quantite=opt_data.get("quantite", 1),
            prix_setup_ht=Decimal(str(opt_data.get("prix_setup_ht", 0))),
            prix_mensuel_ht=Decimal(str(opt_data.get("prix_mensuel_ht", 0))),
            inclus=opt_data.get("inclus", False),
        ))

    # Prestations sur mesure (etaient perdues auparavant : seul le total etait stocke)
    for idx, p_data in enumerate(data.prestations):
        designation = (p_data.get("designation") or "").strip()
        if not designation:
            continue
        db.add(DevisLigne(
            devis_id=devis_id,
            ordre=idx,
            designation=designation,
            quantite=int(p_data.get("quantite", 1) or 1),
            prix_unitaire_achat=Decimal(str(p_data.get("prix_unitaire_achat", 0))),
            prix_unitaire_vente=Decimal(str(p_data.get("prix_unitaire_vente", 0))),
        ))

    # Articles offerts (options/prestations offertes)
    for idx, art_data in enumerate(data.articles_offerts):
        designation = (art_data.get("designation") or "").strip()
        if not designation:
            continue
        db.add(DevisArticleOffert(
            devis_id=devis_id,
            ordre=idx,
            designation=designation,
            prix_achat=Decimal(str(art_data.get("prix_achat", 0))),
            prix_vente=Decimal(str(art_data.get("prix_vente", 0))),
        ))
