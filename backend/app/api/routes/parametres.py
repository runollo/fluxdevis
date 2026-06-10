"""Routes des parametres applicatifs (page Parametres).

Aujourd'hui : configuration de l'envoi d'emails (SMTP). Extensible ensuite. Le mot
de passe SMTP n'est jamais renvoye en clair (seul un booleen indique s'il est defini).
"""

from datetime import date, timedelta
from types import SimpleNamespace

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services import parametres as svc
from app.services.parametres import smtp_config
from app.services.email import Email, envoyer_email, email_actif, EmailError
from app.services import email_modeles as modeles
from app.models.societe import Societe
from app.models.devis import DOC_DEVIS

router = APIRouter()


class ParametresOut(BaseModel):
    smtp_host: str | None
    smtp_port: int | None
    smtp_starttls: bool | None
    smtp_user: str | None
    smtp_from: str | None
    smtp_password_defini: bool
    smtp_actif: bool
    # Modeles d'emails : valeur EFFECTIVE (stockee ou defaut) pour pre-remplir l'UI.
    email_signature: str
    email_objet_devis: str
    email_corps_devis: str
    email_objet_facture: str
    email_corps_facture: str


async def _serialiser(db: AsyncSession) -> ParametresOut:
    p = await svc.charger(db)
    cfg = await smtp_config(db)
    return ParametresOut(
        smtp_host=p.smtp_host, smtp_port=p.smtp_port, smtp_starttls=p.smtp_starttls,
        smtp_user=p.smtp_user, smtp_from=p.smtp_from,
        smtp_password_defini=bool(p.smtp_password),
        smtp_actif=cfg.actif,
        email_signature=p.email_signature or modeles.DEFAUT_SIGNATURE,
        email_objet_devis=p.email_objet_devis or modeles.DEFAUT_OBJET_DEVIS,
        email_corps_devis=p.email_corps_devis or modeles.DEFAUT_CORPS_DEVIS,
        email_objet_facture=p.email_objet_facture or modeles.DEFAUT_OBJET_FACTURE,
        email_corps_facture=p.email_corps_facture or modeles.DEFAUT_CORPS_FACTURE,
    )


@router.get("/", response_model=ParametresOut)
async def get_parametres(db: AsyncSession = Depends(get_db)):
    """Renvoie les parametres (mot de passe SMTP masque)."""
    return await _serialiser(db)


class ParametresUpdate(BaseModel):
    smtp_host: str | None = None
    smtp_port: int | None = None
    smtp_starttls: bool | None = None
    smtp_user: str | None = None
    smtp_from: str | None = None
    smtp_password: str | None = None  # vide/None = ne pas changer le mot de passe
    email_signature: str | None = None
    email_objet_devis: str | None = None
    email_corps_devis: str | None = None
    email_objet_facture: str | None = None
    email_corps_facture: str | None = None


def _norm(v):
    """Chaine nettoyee, ou None si vide (=> repli sur le .env)."""
    if v is None:
        return None
    v = v.strip() if isinstance(v, str) else v
    return v or None


@router.patch("/", response_model=ParametresOut)
async def update_parametres(data: ParametresUpdate, db: AsyncSession = Depends(get_db)):
    """Mise a jour PARTIELLE : ne touche que les champs reellement fournis, pour que
    la sauvegarde d'une section (SMTP) n'efface pas l'autre (modeles d'emails).
    Le mot de passe n'est change que si fourni non vide. Un champ texte vide -> NULL
    (=> repli sur le defaut / .env)."""
    p = await svc.charger(db)
    fournis = data.model_dump(exclude_unset=True)

    if "smtp_password" in fournis:
        pw = (fournis.pop("smtp_password") or "").strip()
        if pw:
            p.smtp_password = pw

    if "smtp_port" in fournis:
        p.smtp_port = fournis["smtp_port"]
    if "smtp_starttls" in fournis:
        p.smtp_starttls = fournis["smtp_starttls"]
    for champ in (
        "smtp_host", "smtp_user", "smtp_from", "email_signature",
        "email_objet_devis", "email_corps_devis",
        "email_objet_facture", "email_corps_facture",
    ):
        if champ in fournis:
            setattr(p, champ, _norm(fournis[champ]))

    await db.commit()
    return await _serialiser(db)


@router.get("/apercu")
async def apercu_email(type: str = "devis", db: AsyncSession = Depends(get_db)):
    """Apercu (objet + html) d'un email, rendu avec des donnees d'EXEMPLE.

    Reflete les modeles actuellement enregistres. type = devis | facture.
    """
    p = await svc.charger(db)
    societe = (await db.execute(select(Societe).limit(1))).scalar_one_or_none()
    today = date.today()
    if type == "facture":
        facture = SimpleNamespace(
            numero="F2026-010", date_emission=today, date_echeance=today + timedelta(days=30),
            periode_debut=None, periode_fin=None, total_ttc="1 200,00",
        )
        devis = SimpleNamespace(
            client_raison_sociale="EXEMPLE SARL", client_interlocuteur="M. Dupont",
        )
        objet, html = modeles.construire_email_facture(facture, devis, societe, p)
    else:
        devis = SimpleNamespace(
            document_type=DOC_DEVIS, reference="D-EXEM-2606101200",
            date_emission=today, date_validite=today + timedelta(days=30),
            client_raison_sociale="EXEMPLE SARL", client_interlocuteur="M. Dupont",
            total_ttc="3 600,00",
        )
        objet, html = modeles.construire_email_devis(devis, societe, p)
    return {"objet": objet, "html": html}


class TestEmailIn(BaseModel):
    destinataire: str | None = None


@router.post("/test-email")
async def test_email(data: TestEmailIn, db: AsyncSession = Depends(get_db)):
    """Envoie un email de test pour verifier la configuration SMTP."""
    if not await email_actif(db):
        raise HTTPException(
            400, "Envoi non configure : enregistrez d'abord les parametres SMTP."
        )
    societe = (await db.execute(select(Societe).limit(1))).scalar_one_or_none()
    cfg = await smtp_config(db)
    destinataire = (data.destinataire or "").strip() or (societe.email if societe else "") or cfg.user
    if not destinataire:
        raise HTTPException(400, "Indiquez une adresse de test.")

    expediteur = cfg.sender
    if not expediteur and societe and societe.email:
        expediteur = f"{societe.marque or societe.nom} <{societe.email}>"

    email = Email(
        destinataire=destinataire,
        sujet="Test d'envoi - FluxDevis",
        html=(
            "<p>Ceci est un email de test envoye depuis FluxDevis.</p>"
            "<p>Si vous le recevez, votre configuration SMTP fonctionne.</p>"
        ),
        reply_to=(societe.email if societe else None),
    )
    try:
        await envoyer_email(db, email, expediteur)
    except EmailError as e:
        raise HTTPException(400, str(e))
    return {"ok": True, "destinataire": destinataire}
