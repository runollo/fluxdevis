"""Routes pour les factures."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.facture import Facture, Echeance, StatutFacture, TypeFacture
from app.models.devis import Devis
from app.models.societe import Societe
from app.services.generation_facture import FactureData, generer_facture
from app.services.facturation_maintenance import devis_maintenance_dus
from app.services.numerotation_facture import prochain_numero, numero_en_cours, format_numero
from app.services import journal as journal_svc
from app.services.export_excel import export_factures_xlsx
from app.services.email import Email, PieceJointe, envoyer_email, email_actif, EmailError
from app.services.parametres import smtp_config
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


class FactureListItem(BaseModel):
    """Facture enrichie pour la liste : porte le client et le projet (devis)."""
    id: int
    numero: str
    type: TypeFacture
    statut: StatutFacture
    date_emission: date
    date_echeance: date
    objet: str
    total_ttc: Decimal
    devis_id: int | None = None
    client: str | None = None
    projet_ref: str | None = None
    projet_nom: str | None = None


@router.get("/", response_model=list[FactureListItem])
async def list_factures(
    statut: StatutFacture | None = None,
    type: TypeFacture | None = None,
    archives: bool = False,
    q: str | None = None,
    client_id: int | None = None,
    devis_id: int | None = None,
    skip: int = 0,
    limit: int = 25,
    db: AsyncSession = Depends(get_db),
):
    """Liste les factures (enrichies du client et du projet). Exclut la corbeille par defaut.

    - archives=true : retourne uniquement les factures archivees.
    - q : recherche sur le numero ou l'objet (insensible a la casse).
    - client_id : ne garde que les factures du client (via le devis rattache).
    - devis_id : ne garde que les factures d'un projet (devis) donne.
    - skip / limit : pagination par decalage.
    """
    query = (
        select(Facture)
        .options(selectinload(Facture.devis))
        .order_by(Facture.date_emission.desc(), Facture.id.desc())
    )
    if archives:
        query = query.where(Facture.archived_at.is_not(None))
    else:
        query = query.where(Facture.archived_at.is_(None))
    if statut:
        query = query.where(Facture.statut == statut)
    if type:
        query = query.where(Facture.type == type)
    if devis_id:
        query = query.where(Facture.devis_id == devis_id)
    if client_id:
        query = query.join(Devis, Facture.devis_id == Devis.id).where(
            Devis.client_id == client_id
        )
    if q:
        motif = f"%{q.strip()}%"
        query = query.where(Facture.numero.ilike(motif) | Facture.objet.ilike(motif))
    query = query.offset(max(skip, 0)).limit(max(min(limit, 200), 1))
    factures = (await db.execute(query)).scalars().all()
    return [
        FactureListItem(
            id=f.id, numero=f.numero, type=f.type, statut=f.statut,
            date_emission=f.date_emission, date_echeance=f.date_echeance,
            objet=f.objet, total_ttc=f.total_ttc, devis_id=f.devis_id,
            client=f.devis.client_raison_sociale if f.devis else None,
            projet_ref=f.devis.reference if f.devis else None,
            projet_nom=f.devis.offre_nom if f.devis else None,
        )
        for f in factures
    ]


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


@router.get("/next-numero", response_model=dict)
async def next_numero(db: AsyncSession = Depends(get_db)):
    """Previsualise le prochain numero legal (F<annee>-NNN) SANS le consommer.

    Lecture seule du compteur : le numero n'est reellement attribue qu'a
    l'emission (POST /{id}/emettre). Sert uniquement a l'affichage. Declaree
    AVANT GET /{facture_id} pour ne pas etre capturee par le convertisseur int.
    """
    year = date.today().year
    n = await numero_en_cours(db, year)
    return {"numero": format_numero(year, n + 1)}


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
        est_shopify=devis.est_shopify if devis else False,
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
    if not await email_actif(db):
        raise HTTPException(
            400,
            "Envoi email non configure : renseignez les parametres SMTP dans Parametres.",
        )

    facture, devis, societe, buf, filename = await _generer_facture_docx(facture_id, db)

    destinataire = devis.client_email if devis else None
    if not destinataire:
        raise HTTPException(
            400,
            "Email client absent du devis : renseignez l'email du client puis regenerez le devis.",
        )

    # Expediteur affiche : parametre SMTP_FROM si defini, sinon construit depuis la
    # societe. Pour le SMTP, l'adresse doit correspondre a la boite authentifiee.
    cfg = await smtp_config(db)
    expediteur = cfg.sender
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
        resultat = await envoyer_email(db, email, expediteur)
    except EmailError as e:
        raise HTTPException(400, str(e))

    return {"ok": True, "id": resultat.get("id"), "destinataire": destinataire}


@router.post("/{facture_id}/emettre", response_model=FactureSummary)
async def emettre_facture(facture_id: int, db: AsyncSession = Depends(get_db)):
    """Emet une facture : attribue le numero legal continu et passe en EMISE.

    Le numero F<annee>-NNN est tire du compteur (sequence chronologique continue)
    UNIQUEMENT ici. Une facture restee en brouillon n'a qu'un numero provisoire et
    peut etre supprimee sans creer de trou dans la numerotation legale.
    L'annee de la sequence est celle de la date d'emission de la facture.
    """
    facture = await db.get(Facture, facture_id)
    if not facture:
        raise HTTPException(404, "Facture non trouvee")
    if facture.statut != StatutFacture.BROUILLON:
        raise HTTPException(400, "Seule une facture en brouillon peut etre emise")

    annee = facture.date_emission.year
    ancien = facture.numero
    facture.numero = await prochain_numero(db, annee)
    facture.statut = StatutFacture.EMISE
    journal_svc.enregistrer(
        db, "facture", facture.id, "emission",
        ancien, facture.numero,
        motif="Emission : attribution du numero legal",
    )
    await db.commit()
    await db.refresh(facture)
    return facture


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


class FactureUpdate(BaseModel):
    numero: str | None = None
    date_emission: date | None = None
    date_echeance: date | None = None
    motif: str | None = None
    confirme: bool = False


class EcheanceDateIn(BaseModel):
    numero: int
    date_echeance: date


class EcheancesUpdate(BaseModel):
    echeances: list[EcheanceDateIn]
    motif: str | None = None
    confirme: bool = False


@router.patch("/{facture_id}", response_model=FactureSummary)
async def modifier_facture(
    facture_id: int, data: FactureUpdate, db: AsyncSession = Depends(get_db)
):
    """Modifie le numero et/ou les dates d'une facture. Tracee dans l'historique.

    Une facture deja emise reste modifiable mais exige une confirmation explicite
    (alerte cote interface) ; chaque changement est journalise.
    """
    facture = await db.get(Facture, facture_id)
    if not facture:
        raise HTTPException(404, "Facture non trouvee")
    if facture.statut != StatutFacture.BROUILLON and not data.confirme:
        raise HTTPException(409, "Facture deja emise : confirmation requise (confirme=true)")

    if data.numero is not None:
        nouveau = data.numero.strip()
        if not nouveau:
            raise HTTPException(400, "Le numero ne peut pas etre vide")
        if nouveau != facture.numero:
            existe = (await db.execute(
                select(func.count()).select_from(Facture).where(
                    Facture.numero == nouveau, Facture.id != facture_id
                )
            )).scalar() or 0
            if existe > 0:
                raise HTTPException(400, f"Le numero '{nouveau}' est deja utilise")
            journal_svc.enregistrer(db, "facture", facture_id, "numero",
                                    facture.numero, nouveau, data.motif)
            facture.numero = nouveau

    if data.date_emission is not None and data.date_emission != facture.date_emission:
        journal_svc.enregistrer(db, "facture", facture_id, "date_emission",
                                facture.date_emission, data.date_emission, data.motif)
        facture.date_emission = data.date_emission
    if data.date_echeance is not None and data.date_echeance != facture.date_echeance:
        journal_svc.enregistrer(db, "facture", facture_id, "date_echeance",
                                facture.date_echeance, data.date_echeance, data.motif)
        facture.date_echeance = data.date_echeance

    await db.commit()
    await db.refresh(facture)
    return facture


@router.patch("/{facture_id}/echeances")
async def modifier_echeances_facture(
    facture_id: int, data: EcheancesUpdate, db: AsyncSession = Depends(get_db)
):
    """Modifie les dates d'echeance ligne par ligne (echeancier editable)."""
    result = await db.execute(
        select(Facture).where(Facture.id == facture_id)
        .options(selectinload(Facture.echeances))
    )
    facture = result.scalar_one_or_none()
    if not facture:
        raise HTTPException(404, "Facture non trouvee")
    if facture.statut != StatutFacture.BROUILLON and not data.confirme:
        raise HTTPException(409, "Facture deja emise : confirmation requise (confirme=true)")

    par_numero = {e.numero: e for e in facture.echeances}
    for maj in data.echeances:
        ech = par_numero.get(maj.numero)
        if ech is None:
            continue
        if ech.date_echeance != maj.date_echeance:
            journal_svc.enregistrer(db, "facture", facture_id, f"echeance[{maj.numero}].date",
                                    ech.date_echeance, maj.date_echeance, data.motif)
            ech.date_echeance = maj.date_echeance

    await db.commit()
    return {"ok": True}


@router.get("/{facture_id}/historique")
async def historique_facture(facture_id: int, db: AsyncSession = Depends(get_db)):
    """Journal des modifications sensibles de la facture."""
    return await journal_svc.historique(db, "facture", facture_id)
