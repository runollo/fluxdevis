"""Envoi d'emails via le SMTP de ta propre messagerie pro (ex OVH).

Solution recommandee pour une TPE : l'email part de ta vraie boite
(contact@fluxweb.fr), sans service tiers ni configuration DNS supplementaire.
La config (serveur, identifiants) est resolue en amont (base puis .env) et passee
sous forme de SmtpConfig.

smtplib est synchrone et bloquant : on l'execute dans un thread via
asyncio.to_thread pour ne pas bloquer la boucle asyncio de FastAPI. On reutilise
les dataclasses Email / PieceJointe et l'exception EmailError du module Resend
pour garder une interface unique.
"""

import asyncio
import smtplib
from email.message import EmailMessage
from email.utils import parseaddr

from app.services.email_resend import Email, EmailError  # interface partagee
from app.services.parametres import SmtpConfig


def _envoyer_bloquant(cfg: SmtpConfig, message: EmailMessage) -> None:
    """Envoi SMTP synchrone (appele dans un thread)."""
    if cfg.starttls:
        with smtplib.SMTP(cfg.host, cfg.port, timeout=30) as serveur:
            serveur.starttls()
            serveur.login(cfg.user, cfg.password)
            serveur.send_message(message)
    else:
        with smtplib.SMTP_SSL(cfg.host, cfg.port, timeout=30) as serveur:
            serveur.login(cfg.user, cfg.password)
            serveur.send_message(message)


async def envoyer_email_smtp(email: Email, expediteur: str, cfg: SmtpConfig) -> dict:
    """Envoie un email (avec pieces jointes) via le SMTP fourni.

    From = expediteur (ou cfg.sender, ou cfg.user). Pour OVH, l'adresse de From
    doit correspondre a la boite authentifiee (cfg.user).
    """
    if not cfg.actif:
        raise EmailError(
            "Envoi SMTP desactive : renseignez l'adresse et le mot de passe SMTP "
            "dans Parametres (ou backend/.env)."
        )
    if not email.destinataire:
        raise EmailError("Aucune adresse destinataire (email client absent).")

    from_header = expediteur or cfg.sender or cfg.user
    msg = EmailMessage()
    msg["From"] = from_header
    msg["To"] = email.destinataire
    msg["Subject"] = email.sujet
    if email.reply_to:
        msg["Reply-To"] = email.reply_to
    msg.set_content("Cet email contient une version HTML (et une piece jointe).")
    msg.add_alternative(email.html, subtype="html")

    for pj in email.pieces_jointes:
        maintype, _, subtype = (pj.content_type or "application/octet-stream").partition("/")
        msg.add_attachment(
            pj.contenu, maintype=maintype or "application",
            subtype=subtype or "octet-stream", filename=pj.nom_fichier,
        )

    try:
        await asyncio.to_thread(_envoyer_bloquant, cfg, msg)
    except smtplib.SMTPAuthenticationError as e:
        raise EmailError(
            f"Authentification SMTP refusee (verifiez l'adresse et le mot de passe) : {e}"
        ) from e
    except (smtplib.SMTPException, OSError) as e:
        raise EmailError(f"Echec de l'envoi SMTP : {e}") from e

    _, from_addr = parseaddr(from_header)
    return {"id": None, "from": from_addr}
