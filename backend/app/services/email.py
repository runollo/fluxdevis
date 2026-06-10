"""Point d'entree unique pour l'envoi d'emails.

Choisit le moteur selon la configuration : le SMTP de ta messagerie pro est
prioritaire (recommande), Resend sert de repli s'il est seul configure. Les
routes importent UNIQUEMENT ce module (Email, PieceJointe, EmailError,
email_actif, envoyer_email) sans se soucier du moteur sous-jacent.
"""

from app.services.email_resend import (
    Email, PieceJointe, EmailError,
    email_actif as _resend_actif,
    envoyer_email as _envoyer_resend,
)
from app.services.email_smtp import smtp_actif, envoyer_email_smtp

__all__ = ["Email", "PieceJointe", "EmailError", "email_actif", "envoyer_email"]


def email_actif() -> bool:
    """Vrai si AU MOINS un moteur d'envoi est configure (SMTP ou Resend)."""
    return smtp_actif() or _resend_actif()


async def envoyer_email(email: Email, expediteur: str) -> dict:
    """Envoie l'email via le moteur disponible (SMTP prioritaire, puis Resend)."""
    if smtp_actif():
        return await envoyer_email_smtp(email, expediteur)
    if _resend_actif():
        return await _envoyer_resend(email, expediteur)
    raise EmailError(
        "Envoi non configure : renseignez SMTP_USER + SMTP_PASSWORD (recommande) "
        "ou RESEND_API_KEY dans backend/.env."
    )
