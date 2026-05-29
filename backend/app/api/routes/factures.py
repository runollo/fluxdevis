"""Routes pour les factures."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.facture import Facture, StatutFacture, TypeFacture
from app.models.devis import Devis
from app.models.societe import Societe
from app.services.generation_facture import FactureData, generer_facture
from app.services.facturation_maintenance import devis_maintenance_dus
from app.services.export_excel import export_factures_xlsx
from app.services.email_resend import Email, PieceJointe, envoyer_email, email_actif, EmailError
from app.core.config import get_settings
from pydantic import BaseModel
from decimal import Decimal
from datetime import date, datetime, timezone

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
    archives: bool = False,
    q: str | None = None,
    skip: int = 0,
    limit: int = 25,
    db: AsyncSession = Depends(get_db),
):
    """Liste les factures. Par defaut, exclut les factures archivees (corbeille).

    - archives=true : retourne uniquement les factures archivees.
    - q : recherche sur le numero ou l'objet (insensible a la casse).
    - skip / limit : pagination par decalage.
    """
    query = select(Facture).order_by(Facture.date_emission.desc(), Facture.id.desc())
    if archives:
        query = query.where(Facture.archived_at.is_not(None))
    else:
        query = query.where(Facture.archived_at.is_(None))
    if statut:
        query = query.where(Facture.statut == statut)
    if type:
        query = query.where(Facture.type == type)
    if q:
        motif = f"%{q.strip()}%"
        query = query.where(Facture.numero.ilike(motif) | Facture.objet.ilike(motif))
    query = query.offset(max(skip, 0)).limit(max(min(limit, 200), 1))
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/export.xlsx")
async def export_factures(q: str | None = None, db: AsyncSession = Depends(get_db)):
    """Exporte les factures actives (non archivees) au format Excel, en respectant q."""
    query = select(Facture).where(Facture.archived_at.is_(None)).order_by(
        Facture.date_emission.desc(), Facture.id.desc()
    )
    if q:
        motif = f"%{q.strip()}%"
        query = query.where(Facture.numero.ilike(motif) | Facture.objet.ilike(motif))
    factures = (await db.execute(query)).scalars().all()
    buf = export_factures_xlsx(factures)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="factures.xlsx"'},
    )


@router.get("/maintenance/dus")
async def maintenance_dus(db: AsyncSession = Depends(get_db)):
    """Liste les factures de maintenance dues aujourd'hui (pour automatisation Make/cron).

    Ne cree rien : retourne les devis a facturer avec la periode concernee. Une
    automatisation peut ensuite appeler POST /api/devis/{id}/factures-maintenance.
    """
    return await devis_maintenance_dus(db)


@router.get("/{facture_id}", response_model=FactureSummary)
async def get_facture(facture_id: int, db: AsyncSession = Depends(get_db)):
    facture = await db.get(Facture, facture_id)
    if not facture:
        raise HTTPException(404, "Facture non trouvee")
    return facture


_DOCX_CT = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


async def _generer_facture_docx(facture_id: int, db: AsyncSession):
    """Charge une facture et genere son document Word.

    Retourne (facture, devis, societe, buffer_docx, nom_fichier). Mutualise entre
    le telechargement et l'envoi par email.
    """
    result = await db.execute(
        select(Facture)
        .where(Facture.id == facture_id)
        .options(selectinload(Facture.echeances), selectinload(Facture.lignes))
    )
    facture = result.scalar_one_or_none()
    if not facture:
        raise HTTPException(404, "Facture non trouvee")

    devis = await db.get(Devis, facture.devis_id)
    societe = (await db.execute(select(Societe).limit(1))).scalar_one_or_none()

    echeances = sorted(facture.echeances, key=lambda e: e.numero)
    ech_rows = [
        {"label": e.label, "date": e.date_echeance.strftime("%d/%m/%Y"), "ttc": e.montant_ttc}
        for e in echeances
    ]
    idx_echeance = sum(1 for e in echeances if e.payee)

    cp_ville = " ".join(x for x in [devis.client_cp, devis.client_ville] if x) if devis else ""

    periode = None
    if facture.type == TypeFacture.MAINTENANCE and facture.periode_debut and facture.periode_fin:
        periode = f"{facture.periode_debut.strftime('%d/%m/%Y')} au {facture.periode_fin.strftime('%d/%m/%Y')}"

    data = FactureData(
        numero=facture.numero,
        type_facture=facture.type.value,
        date_emission=facture.date_emission,
        date_echeance=facture.date_echeance,
        objet=facture.objet,
        emetteur_nom=societe.nom if societe else "BLUELINK INNOVATIONS",
        emetteur_forme=societe.forme_juridique if societe else "",
        emetteur_marque=societe.marque if societe else "FluXweb",
        emetteur_adresse=societe.adresse if societe else "",
        emetteur_cp_ville=societe.cp_ville if societe else "",
        emetteur_siret=societe.siret if societe else "",
        emetteur_rcs=societe.rcs if societe else "",
        emetteur_tva_num=societe.tva_intracom if societe else "",
        emetteur_email=societe.email if societe else "",
        emetteur_web=societe.site_web if societe else "",
        emetteur_iban=societe.iban if societe else "",
        emetteur_bic=societe.bic if societe else "",
        client_societe=devis.client_raison_sociale if devis else "",
        client_contact=devis.client_interlocuteur if devis else "",
        client_adresse=devis.client_adresse if devis else "",
        client_cp_ville=cp_ville,
        client_siret=devis.client_siret if devis else "",
        designation=facture.objet,
        quantite="1",
        prix_unitaire_ht=facture.total_ht,
        montant_ht=facture.total_ht,
        devis_ref=devis.reference if devis else "",
        periode=periode,
        echeances=ech_rows,
        idx_echeance=idx_echeance,
    )

    buf = generer_facture(data)
    filename = f"Facture_{facture.numero}.docx"
    return facture, devis, societe, buf, filename


@router.get("/{facture_id}/document")
async def telecharger_facture(facture_id: int, db: AsyncSession = Depends(get_db)):
    """Genere et retourne la facture au format Word (.docx)."""
    _, _, _, buf, filename = await _generer_facture_docx(facture_id, db)
    return StreamingResponse(
        buf,
        media_type=_DOCX_CT,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _corps_email_facture(facture: Facture, devis, societe) -> tuple[str, str]:
    """Construit (sujet, html) de l'email selon le type de facture."""
    marque = (societe.marque or societe.nom) if societe else "FluXweb"
    contact = (devis.client_interlocuteur if devis else None) or "Madame, Monsieur"
    if facture.type == TypeFacture.MAINTENANCE:
        sujet = f"Facture de maintenance {facture.numero} - {marque}"
        periode = ""
        if facture.periode_debut and facture.periode_fin:
            periode = (
                f"<p>Periode : du {facture.periode_debut.strftime('%d/%m/%Y')} "
                f"au {facture.periode_fin.strftime('%d/%m/%Y')}.</p>"
            )
        intro = (
            "<p>Veuillez trouver ci-joint votre facture de maintenance "
            "(abonnement reconductible tacitement).</p>"
        )
        intro += periode
    else:
        sujet = f"Facture {facture.numero} - {marque}"
        intro = "<p>Veuillez trouver ci-joint votre facture.</p>"

    html = (
        f"<p>Bonjour {contact},</p>"
        f"{intro}"
        f"<p>Montant : {facture.total_ttc} EUR TTC.</p>"
        f"<p>Cordialement,<br>{marque}</p>"
    )
    return sujet, html


@router.post("/{facture_id}/envoyer")
async def envoyer_facture_email(facture_id: int, db: AsyncSession = Depends(get_db)):
    """Envoie la facture (Word en piece jointe) au client par email via Resend.

    FONCTIONNALITE PREVUE, NON ACTIVEE (cf. app/services/email_resend.py et
    HANDOFF). Tant que RESEND_API_KEY n'est pas renseignee, renvoie 400 et
    n'envoie rien. A finaliser quand Bruno aura choisi sa solution d'envoi.
    """
    if not email_actif():
        raise HTTPException(
            400, "Envoi email non configure : renseignez RESEND_API_KEY dans backend/.env."
        )

    facture, devis, societe, buf, filename = await _generer_facture_docx(facture_id, db)

    destinataire = devis.client_email if devis else None
    if not destinataire:
        raise HTTPException(
            400,
            "Email client absent du devis : renseignez l'email du client puis regenerez le devis.",
        )

    settings = get_settings()
    expediteur = settings.RESEND_FROM
    if not expediteur and societe and societe.email:
        expediteur = f"{societe.marque or societe.nom} <{societe.email}>"

    sujet, html = _corps_email_facture(facture, devis, societe)
    email = Email(
        destinataire=destinataire,
        sujet=sujet,
        html=html,
        pieces_jointes=[PieceJointe(filename, buf.getvalue(), _DOCX_CT)],
        reply_to=(societe.email if societe else None),
    )

    try:
        resultat = await envoyer_email(email, expediteur)
    except EmailError as e:
        raise HTTPException(400, str(e))

    return {"ok": True, "id": resultat.get("id"), "destinataire": destinataire}


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


@router.delete("/{facture_id}", status_code=204)
async def archiver_facture(facture_id: int, db: AsyncSession = Depends(get_db)):
    """Archive une facture (corbeille).

    Garde-fou juridique : SEULE une facture en brouillon (jamais emise) peut
    etre archivee. Une facture emise/payee/en retard ne se supprime pas — elle
    doit etre annulee par un avoir (POST /{id}/annuler), ce qui preserve la
    numerotation sequentielle imposee par l'administration fiscale.
    """
    facture = await db.get(Facture, facture_id)
    if not facture:
        raise HTTPException(404, "Facture non trouvee")
    if facture.archived_at is not None:
        raise HTTPException(400, "Facture deja archivee")
    if facture.statut != StatutFacture.BROUILLON:
        raise HTTPException(
            400,
            "Une facture emise ne peut pas etre supprimee (numerotation legale). "
            "Utilisez l'annulation (avoir) a la place.",
        )
    facture.archived_at = datetime.now(timezone.utc)
    await db.commit()


@router.post("/{facture_id}/annuler", response_model=FactureSummary)
async def annuler_facture(facture_id: int, db: AsyncSession = Depends(get_db)):
    """Annule une facture emise (equivalent avoir) : statut ANNULEE.

    La facture reste en base avec son numero — conformite : la numerotation
    sequentielle ne doit jamais comporter de trou. Une facture deja annulee ou
    deja en brouillon n'a pas a etre annulee.
    """
    facture = await db.get(Facture, facture_id)
    if not facture:
        raise HTTPException(404, "Facture non trouvee")
    if facture.statut == StatutFacture.ANNULEE:
        raise HTTPException(400, "Facture deja annulee")
    if facture.statut == StatutFacture.BROUILLON:
        raise HTTPException(
            400,
            "Une facture en brouillon n'a pas a etre annulee : supprimez-la (corbeille).",
        )
    facture.statut = StatutFacture.ANNULEE
    await db.commit()
    await db.refresh(facture)
    return facture


@router.post("/{facture_id}/restaurer", response_model=FactureSummary)
async def restaurer_facture(facture_id: int, db: AsyncSession = Depends(get_db)):
    """Restaure une facture archivee (la sort de la corbeille)."""
    facture = await db.get(Facture, facture_id)
    if not facture:
        raise HTTPException(404, "Facture non trouvee")
    facture.archived_at = None
    await db.commit()
    await db.refresh(facture)
    return facture


@router.delete("/{facture_id}/definitif", status_code=204)
async def supprimer_facture_definitif(facture_id: int, db: AsyncSession = Depends(get_db)):
    """Suppression DEFINITIVE d'une facture (destruction physique) depuis la corbeille.

    Garde-fous : la facture doit deja etre archivee ET en brouillon. Une facture
    emise/payee/en retard/annulee ne peut JAMAIS etre detruite (conservation legale
    de 10 ans, numerotation sequentielle sans trou).
    """
    result = await db.execute(
        select(Facture)
        .where(Facture.id == facture_id)
        .options(selectinload(Facture.lignes), selectinload(Facture.echeances))
    )
    facture = result.scalar_one_or_none()
    if not facture:
        raise HTTPException(404, "Facture non trouvee")
    if facture.archived_at is None:
        raise HTTPException(400, "Mettez d'abord la facture dans la corbeille.")
    if facture.statut != StatutFacture.BROUILLON:
        raise HTTPException(
            400,
            "Suppression definitive interdite : une facture emise ou annulee doit "
            "etre conservee (obligation legale).",
        )
    await db.delete(facture)
    await db.commit()
