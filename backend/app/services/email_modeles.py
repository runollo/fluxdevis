"""Construction des emails (objet + corps HTML) a partir de modeles editables.

Les modeles et la signature sont stockes dans les Parametres (editables depuis
la page Parametres). Des variables entre accolades sont remplacees par les
donnees du devis/de la facture. Si un modele est vide, on utilise le defaut.

Variables :
- communes : {client}, {interlocuteur}, {montant_ttc}, {marque}
- devis    : {reference}, {date}, {date_validite}, {type_document}
- facture  : {numero}, {date}, {date_echeance}, {periode}
"""

from app.models.devis import DOC_PROPOSITION

# Modeles par defaut (texte simple ; les sauts de ligne deviennent des <br>).
DEFAUT_OBJET_DEVIS = "Votre {type_document} {reference} - {marque}"
DEFAUT_CORPS_DEVIS = (
    "Bonjour {interlocuteur},\n\n"
    "Veuillez trouver ci-joint votre {type_document} {reference} du {date}, "
    "d'un montant de {montant_ttc} EUR TTC (valable jusqu'au {date_validite}).\n\n"
    "Nous restons a votre disposition pour toute question."
)
DEFAUT_OBJET_FACTURE = "Facture {numero} - {marque}"
DEFAUT_CORPS_FACTURE = (
    "Bonjour {interlocuteur},\n\n"
    "Veuillez trouver ci-joint votre facture {numero} du {date}, "
    "d'un montant de {montant_ttc} EUR TTC (echeance le {date_echeance}).\n\n"
    "Nous vous remercions de votre confiance."
)
DEFAUT_SIGNATURE = "Cordialement,\n{marque}"


def _appliquer(modele: str, variables: dict) -> str:
    """Remplace chaque {cle} par sa valeur (laisse intact tout token inconnu)."""
    out = modele or ""
    for cle, val in variables.items():
        out = out.replace("{" + cle + "}", str(val))
    return out


def _texte_vers_html(txt: str) -> str:
    """Convertit un texte (avec sauts de ligne) en HTML simple."""
    return (txt or "").replace("\r\n", "\n").replace("\n", "<br>")


def _assembler(corps: str, signature: str, variables: dict) -> str:
    """Corps + signature (chacun avec substitution) en un fragment HTML."""
    html = _texte_vers_html(_appliquer(corps, variables))
    sig = _appliquer(signature or "", variables).strip()
    if sig:
        html += "<br><br>" + _texte_vers_html(sig)
    return f'<div style="font-family:Arial,sans-serif;font-size:14px;color:#222">{html}</div>'


def _variables_communes(client, interlocuteur, montant_ttc, marque) -> dict:
    return {
        "client": client or "",
        "interlocuteur": interlocuteur or "Madame, Monsieur",
        "montant_ttc": f"{montant_ttc}",
        "marque": marque,
    }


def construire_email_devis(devis, societe, params) -> tuple[str, str]:
    """Retourne (objet, html) de l'email d'un devis, selon les modeles de params."""
    marque = (societe.marque or societe.nom) if societe else "FluXweb"
    type_doc = "proposition budgetaire" if devis.document_type == DOC_PROPOSITION else "devis"
    variables = _variables_communes(
        devis.client_raison_sociale, devis.client_interlocuteur, devis.total_ttc, marque
    )
    variables.update({
        "reference": devis.reference,
        "date": devis.date_emission.strftime("%d/%m/%Y") if devis.date_emission else "",
        "date_validite": devis.date_validite.strftime("%d/%m/%Y") if devis.date_validite else "",
        "type_document": type_doc,
    })
    objet = _appliquer(
        (params and params.email_objet_devis) or DEFAUT_OBJET_DEVIS, variables
    )
    html = _assembler(
        (params and params.email_corps_devis) or DEFAUT_CORPS_DEVIS,
        (params and params.email_signature) or DEFAUT_SIGNATURE,
        variables,
    )
    return objet, html


def construire_email_facture(facture, devis, societe, params) -> tuple[str, str]:
    """Retourne (objet, html) de l'email d'une facture, selon les modeles de params."""
    marque = (societe.marque or societe.nom) if societe else "FluXweb"
    interlocuteur = devis.client_interlocuteur if devis else None
    client = devis.client_raison_sociale if devis else ""
    periode = ""
    if facture.periode_debut and facture.periode_fin:
        periode = (
            f"du {facture.periode_debut.strftime('%d/%m/%Y')} "
            f"au {facture.periode_fin.strftime('%d/%m/%Y')}"
        )
    variables = _variables_communes(client, interlocuteur, facture.total_ttc, marque)
    variables.update({
        "numero": facture.numero,
        "date": facture.date_emission.strftime("%d/%m/%Y") if facture.date_emission else "",
        "date_echeance": facture.date_echeance.strftime("%d/%m/%Y") if facture.date_echeance else "",
        "periode": periode,
    })
    objet = _appliquer(
        (params and params.email_objet_facture) or DEFAUT_OBJET_FACTURE, variables
    )
    html = _assembler(
        (params and params.email_corps_facture) or DEFAUT_CORPS_FACTURE,
        (params and params.email_signature) or DEFAUT_SIGNATURE,
        variables,
    )
    return objet, html
