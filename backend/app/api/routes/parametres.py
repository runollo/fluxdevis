"""Routes des parametres applicatifs (page Parametres).

Aujourd'hui : configuration de l'envoi d'emails (SMTP). Extensible ensuite. Le mot
de passe SMTP n'est jamais renvoye en clair (seul un booleen indique s'il est defini).
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services import parametres as svc
from app.services.parametres import smtp_config
from app.services.email import Email, envoyer_email, email_actif, EmailError
from app.models.societe import Societe

router = APIRouter()


class ParametresOut(BaseModel):
    smtp_host: str | None
    smtp_port: int | None
    smtp_starttls: bool | None
    smtp_user: str | None
    smtp_from: str | None
    smtp_password_defini: bool
    smtp_actif: bool


async def _serialiser(db: AsyncSession) -> ParametresOut:
    p = await svc.charger(db)
    cfg = await smtp_config(db)
    return ParametresOut(
        smtp_host=p.smtp_host, smtp_port=p.smtp_port, smtp_starttls=p.smtp_starttls,
        smtp_user=p.smtp_user, smtp_from=p.smtp_from,
        smtp_password_defini=bool(p.smtp_password),
        smtp_actif=cfg.actif,
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


def _norm(v):
    """Chaine nettoyee, ou None si vide (=> repli sur le .env)."""
    if v is None:
        return None
    v = v.strip() if isinstance(v, str) else v
    return v or None


@router.patch("/", response_model=ParametresOut)
async def update_parametres(data: ParametresUpdate, db: AsyncSession = Depends(get_db)):
    """Met a jour les parametres SMTP. Le mot de passe n'est change que si fourni."""
    p = await svc.charger(db)
    p.smtp_host = _norm(data.smtp_host)
    p.smtp_port = data.smtp_port
    p.smtp_starttls = data.smtp_starttls
    p.smtp_user = _norm(data.smtp_user)
    p.smtp_from = _norm(data.smtp_from)
    if data.smtp_password is not None and data.smtp_password.strip():
        p.smtp_password = data.smtp_password
    await db.commit()
    return await _serialiser(db)


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
