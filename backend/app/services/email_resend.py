"""Envoi d'emails transactionnels via Resend (https://resend.com).

==============================================================================
STATUT : FONCTIONNALITE PREVUE, NON ACTIVEE (a reprendre ulterieurement).
Au 2026-05-29, il n'y a PAS de compte Resend ni de cle API. Tant que
RESEND_API_KEY est vide dans backend/.env, l'envoi est desactive (email_actif()
renvoie False et envoyer_email leve EmailError) : aucun email ne part.
Bruno doit d'abord decider comment il gere l'envoi (compte Resend + domaine
verifie, ou autre solution). Checklist de reprise dans HANDOFF.md, section
"Envoi email / automatisation maintenance".
==============================================================================

Utilise l'API HTTP Resend (pas de SDK) pour rester leger. La cle API et
l'expediteur sont lus depuis la configuration (RESEND_API_KEY, RESEND_FROM).
Les pieces jointes (ex : facture Word) sont transmises en base64.
"""

import base64
from dataclasses import dataclass, field

import httpx

from app.core.config import get_settings

_RESEND_URL = "https://api.resend.com/emails"


class EmailError(Exception):
    """Erreur d'envoi d'email (configuration manquante ou refus de l'API)."""


@dataclass
class PieceJointe:
    nom_fichier: str
    contenu: bytes
    content_type: str = "application/octet-stream"


@dataclass
class Email:
    destinataire: str
    sujet: str
    html: str
    pieces_jointes: list[PieceJointe] = field(default_factory=list)
    reply_to: str | None = None


def email_actif() -> bool:
    """Indique si l'envoi d'email est configure (cle API presente)."""
    return bool(get_settings().RESEND_API_KEY)


async def envoyer_email(email: Email, expediteur: str) -> dict:
    """Envoie un email via Resend. Leve EmailError si non configure ou refuse.

    `expediteur` doit utiliser un domaine verifie cote Resend (ex
    'FluXweb <factures@mondomaine.fr>').
    """
    settings = get_settings()
    if not settings.RESEND_API_KEY:
        raise EmailError(
            "Envoi desactive : renseignez RESEND_API_KEY dans backend/.env."
        )
    if not email.destinataire:
        raise EmailError("Aucune adresse destinataire (email client absent).")
    if not expediteur:
        raise EmailError(
            "Aucun expediteur : definissez RESEND_FROM ou l'email de la societe."
        )

    payload: dict = {
        "from": expediteur,
        "to": [email.destinataire],
        "subject": email.sujet,
        "html": email.html,
    }
    if email.reply_to:
        payload["reply_to"] = email.reply_to
    if email.pieces_jointes:
        payload["attachments"] = [
            {
                "filename": pj.nom_fichier,
                "content": base64.b64encode(pj.contenu).decode("ascii"),
                "content_type": pj.content_type,
            }
            for pj in email.pieces_jointes
        ]

    headers = {
        "Authorization": f"Bearer {settings.RESEND_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(_RESEND_URL, json=payload, headers=headers)
    except httpx.HTTPError as e:
        raise EmailError(f"Echec reseau vers Resend : {e}") from e

    if resp.status_code >= 400:
        raise EmailError(f"Resend a refuse l'envoi ({resp.status_code}) : {resp.text}")

    return resp.json()
