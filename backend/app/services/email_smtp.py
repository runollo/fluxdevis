"""Envoi d'emails via le SMTP de ta propre messagerie pro (ex OVH).

Solution recommandee pour une TPE : l'email part de ta vraie boite
(contact@fluxweb.fr), sans service tiers ni configuration DNS supplementaire.
Les identifiants sont lus depuis la configuration (SMTP_USER, SMTP_PASSWORD)
et restent dans backend/.env.

smtplib est synchrone et bloquant : on l'execute dans un thread via
asyncio.to_thread pour ne pas bloquer la boucle asyncio de FastAPI. On reutilise
les dataclasses Email / PieceJointe et l'exception EmailError du module Resend
pour garder une interface unique.
"""

import asyncio
import smtplib
from email.message import EmailMessage
from email.utils import parseaddr

from app.core.config import get_settings
from app.services.email_resend import Email, EmailError  # interface partagee


def smtp_actif() -> bool:
    """Vrai si le SMTP est configure (serveur + identifiants presents)."""
    s = get_settings()
    return bool(s.SMTP_HOST and s.SMTP_USER and s.SMTP_PASSWORD)


def _envoyer_bloquant(host: str, port: int, starttls: bool, user: str,
                      password: str, message: EmailMessage) -> None:
    """Envoi SMTP synchrone (appele dans un thread)."""
    if starttls:
        with smtplib.SMTP(host, port, timeout=30) as serveur:
            serveur.starttls()
            serveur.login(user, password)
            serveur.send_message(message)
    else:
        with smtplib.SMTP_SSL(host, port, timeout=30) as serveur:
            serveur.login(user, password)
            serveur.send_message(message)


async def envoyer_email_smtp(email: Email, expediteur: str) -> dict:
    """Envoie un email (avec pieces jointes) via le SMTP configure.

    `expediteur` est l'entete From affiche (ex 'FluXweb <contact@fluxweb.fr>').
    Pour OVH, l'adresse de From doit correspondre a SMTP_USER (boite authentifiee).
    """
    s = get_settings()
    if not smtp_actif():
        raise EmailError(
            "Envoi SMTP desactive : renseignez SMTP_USER et SMTP_PASSWORD dans backend/.env."
        )
    if not email.destinataire:
        raise EmailError("Aucune adresse destinataire (email client absent).")

    from_header = expediteur or s.SMTP_FROM or s.SMTP_USER
    msg = EmailMessage()
    msg["From"] = from_header
    msg["To"] = email.destinataire
    msg["Subject"] = email.sujet
    if email.reply_to:
        msg["Reply-To"] = email.reply_to
    # Corps : version texte de repli + HTML.
    msg.set_content("Cet email contient une version HTML (et une piece jointe).")
    msg.add_alternative(email.html, subtype="html")

    for pj in email.pieces_jointes:
        maintype, _, subtype = (pj.content_type or "application/octet-stream").partition("/")
        msg.add_attachment(
            pj.contenu, maintype=maintype or "application",
            subtype=subtype or "octet-stream", filename=pj.nom_fichier,
        )

    try:
        await asyncio.to_thread(
            _envoyer_bloquant, s.SMTP_HOST, s.SMTP_PORT, s.SMTP_STARTTLS,
            s.SMTP_USER, s.SMTP_PASSWORD, msg,
        )
    except smtplib.SMTPAuthenticationError as e:
        raise EmailError(
            f"Authentification SMTP refusee (verifiez SMTP_USER / SMTP_PASSWORD) : {e}"
        ) from e
    except (smtplib.SMTPException, OSError) as e:
        raise EmailError(f"Echec de l'envoi SMTP : {e}") from e

    # Pas d'id renvoye par SMTP : on renvoie l'adresse expediteur effective.
    _, from_addr = parseaddr(from_header)
    return {"id": None, "from": from_addr}
