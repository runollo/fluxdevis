"""Point d'entree unique pour l'envoi d'emails.

Choisit le moteur selon la configuration : le SMTP de ta messagerie pro est
prioritaire (recommande), Resend sert de repli s'il est seul configure. La config
SMTP est resolue depuis la base (page Parametres) puis le .env. Les routes importent
UNIQUEMENT ce module et lui passent la session db.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.email_resend import (
    Email, PieceJointe, EmailError,
    email_actif as _resend_actif,
    envoyer_email as _envoyer_resend,
)
from app.services.email_smtp import envoyer_email_smtp
from app.services.parametres import smtp_config

__all__ = ["Email", "PieceJointe", "EmailError", "email_actif", "envoyer_email"]


async def email_actif(db: AsyncSession) -> bool:
    """Vrai si AU MOINS un moteur d'envoi est configure (SMTP ou Resend)."""
    cfg = await smtp_config(db)
    return cfg.actif or _resend_actif()


async def envoyer_email(db: AsyncSession, email: Email, expediteur: str) -> dict:
    """Envoie l'email via le moteur disponible (SMTP prioritaire, puis Resend)."""
    cfg = await smtp_config(db)
    if cfg.actif:
        return await envoyer_email_smtp(email, expediteur, cfg)
    if _resend_actif():
        return await _envoyer_resend(email, expediteur)
    raise EmailError(
        "Envoi non configure : renseignez l'adresse et le mot de passe SMTP dans "
        "Parametres (ou backend/.env)."
    )
