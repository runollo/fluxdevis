"""Contenu detaille des packs de maintenance (annexe contractuelle).

Source de verite UNIQUE du descriptif des packs de maintenance, utilisee pour :
- enrichir le devis Word (detail de ce qui est inclus dans le pack choisi) ;
- repondre aux questions client ("qu'est-ce qui est inclus dans la maintenance X ?").

Les packs sont CUMULATIFS : chaque niveau "inclut l'ensemble des prestations du pack
inferieur, completees par" ses propres prestations. On ne stocke donc QUE les
prestations PROPRES a chaque niveau ; `contenu_cumule()` resout la chaine d'heritage.

Le `code` correspond a Option.code en base (WF_MAINT_* / SHOPIFY_MAINT_*).

NB : les chaines de texte (accroche, intro, prestations, delai, rappel) sont destinees
a l'AFFICHAGE CLIENT (devis Word) -> elles sont accentuees correctement. Seuls les
commentaires et identifiants suivent la convention projet (sans accents).
"""

# Rappel affiche en tete de la famille Shopify (abonnement a la charge du client).
RAPPEL_SHOPIFY = (
    "L'abonnement Shopify (incluant l'hébergement) et les applications payantes sont "
    "souscrits et réglés directement par le Client."
)

# famille : "Webflow" | "Shopify"
# Chaque entree : famille, famille_label, niveau, socle_obligatoire, accroche, intro,
#   prestations (liste de (titre, detail)), delai_reponse, herite_de.
PACKS_MAINTENANCE: dict[str, dict] = {
    # --- Famille 1 : Sites vitrine Webflow (hebergement inclus) ---
    "WF_MAINT_ESS": {
        "famille": "Webflow",
        "famille_label": "Sites vitrine — Webflow (hébergement inclus)",
        "niveau": "Essentielle",
        "socle_obligatoire": True,
        "accroche": "Le site est surveillé et sécurisé.",
        "intro": "Ce pack constitue le socle minimal requis pour garantir le bon "
                 "fonctionnement du site :",
        "prestations": [
            ("Hébergement inclus",
             "infrastructure, publication, certificat SSL, diffusion (CDN)."),
            ("Supervision et continuité",
             "contrôle régulier de l'accessibilité du site et vérification du bon "
             "fonctionnement des pages et formulaires."),
            ("Sécurité",
             "contrôle des accès, recommandations de sécurité, vérification des "
             "configurations à risque."),
            ("Correctifs techniques",
             "correction des anomalies directement imputables aux éléments mis en "
             "place par le Prestataire."),
            ("Assistance", "prise en charge des demandes par email."),
        ],
        "delai_reponse": "48 heures ouvrées",
        "herite_de": None,
    },
    "WF_MAINT_STD": {
        "famille": "Webflow",
        "famille_label": "Sites vitrine — Webflow (hébergement inclus)",
        "niveau": "Standard",
        "socle_obligatoire": False,
        "accroche": "Le site est surveillé, sécurisé et corrigé sur demande.",
        "intro": None,
        "prestations": [
            ("Interventions correctives sur demande",
             "corrections mineures et ajustements ponctuels du site (textes, liens, "
             "composants, affichage, mise en page) signalés par le Client."),
            ("Support prioritaire",
             "les demandes du Client sont traitées avec un délai de réponse réduit."),
        ],
        "delai_reponse": "24 heures ouvrées",
        "herite_de": "WF_MAINT_ESS",
    },
    "WF_MAINT_PRO": {
        "famille": "Webflow",
        "famille_label": "Sites vitrine — Webflow (hébergement inclus)",
        "niveau": "Pro",
        "socle_obligatoire": False,
        "accroche": "Le site est surveillé, corrigé et amélioré en continu.",
        "intro": None,
        "prestations": [
            ("Évolutions mineures",
             "améliorations ponctuelles du site à l'initiative du Prestataire ou sur "
             "demande du Client (ajout ou modification de sections, ajustement de la "
             "mise en page, mise à jour de composants)."),
            ("Optimisations SEO on-page",
             "le Prestataire identifie et corrige les points bloquants techniques "
             "(balises titres, structure des contenus, maillage interne, performances "
             "d'affichage) afin d'améliorer la visibilité du site dans les moteurs de "
             "recherche."),
        ],
        "delai_reponse": "12 heures ouvrées",
        "herite_de": "WF_MAINT_STD",
    },
    "WF_MAINT_PREM": {
        "famille": "Webflow",
        "famille_label": "Sites vitrine — Webflow (hébergement inclus)",
        "niveau": "Premium",
        "socle_obligatoire": False,
        "accroche": "Le site est surveillé, amélioré et accompagné stratégiquement.",
        "intro": None,
        "prestations": [
            ("Suivi régulier et recommandations",
             "le Prestataire effectue un suivi mensuel du site et formule des "
             "recommandations d'amélioration portant sur l'ergonomie, le parcours "
             "utilisateur, la performance technique et la visibilité. Un point de suivi "
             "mensuel est proposé au Client (email de synthèse ou visioconférence courte)."),
            ("Mise en ligne de contenus",
             "le Prestataire assiste le Client dans la mise en ligne de contenus et de "
             "mises à jour fournis par le Client (textes, visuels, documents)."),
            ("Support prioritaire renforcé",
             "les demandes du Client sont traitées en priorité absolue."),
        ],
        "delai_reponse": "12 heures ouvrées",
        "herite_de": "WF_MAINT_PRO",
    },

    # --- Famille 2 : Sites e-commerce Shopify (hebergement exclu) ---
    "SHOPIFY_MAINT_ESS": {
        "famille": "Shopify",
        "famille_label": "Sites e-commerce — Shopify (hébergement exclu)",
        "niveau": "Essentielle",
        "socle_obligatoire": True,
        "accroche": "La boutique est surveillée et sécurisée.",
        "intro": "Ce pack constitue le socle minimal requis pour garantir le bon "
                 "fonctionnement de la boutique :",
        "prestations": [
            ("Supervision et continuité",
             "contrôle régulier de l'accessibilité du site et vérification du bon "
             "fonctionnement des pages, formulaires et du parcours principal."),
            ("Sécurité",
             "contrôle des accès, recommandations de sécurité, vérification des "
             "configurations à risque."),
            ("Correctifs techniques",
             "correction des anomalies directement imputables aux éléments mis en place "
             "par le Prestataire (configuration, intégrations, paramétrages)."),
            ("Assistance", "prise en charge des demandes par email."),
        ],
        "delai_reponse": "48 heures ouvrées",
        "herite_de": None,
    },
    "SHOPIFY_MAINT_STD": {
        "famille": "Shopify",
        "famille_label": "Sites e-commerce — Shopify (hébergement exclu)",
        "niveau": "Standard",
        "socle_obligatoire": False,
        "accroche": "La boutique est surveillée, sécurisée et corrigée sur demande.",
        "intro": None,
        "prestations": [
            ("Interventions correctives sur demande",
             "corrections mineures et ajustements ponctuels de la boutique (textes, "
             "liens, composants, affichage, mise en page) signalés par le Client."),
            ("Supervision transactionnelle",
             "vérification du bon fonctionnement des fonctionnalités e-commerce "
             "(checkout, paiements, notifications de commande)."),
            ("Support prioritaire",
             "les demandes du Client sont traitées avec un délai de réponse réduit."),
        ],
        "delai_reponse": "24 heures ouvrées",
        "herite_de": "SHOPIFY_MAINT_ESS",
    },
    "SHOPIFY_MAINT_PRO": {
        "famille": "Shopify",
        "famille_label": "Sites e-commerce — Shopify (hébergement exclu)",
        "niveau": "Pro",
        "socle_obligatoire": False,
        "accroche": "La boutique est surveillée, corrigée et améliorée en continu.",
        "intro": None,
        "prestations": [
            ("Évolutions mineures",
             "améliorations ponctuelles de la boutique à l'initiative du Prestataire ou "
             "sur demande du Client (ajout ou modification de sections, ajustement de la "
             "mise en page, mise à jour de composants)."),
            ("Optimisations catalogue",
             "le Prestataire identifie et corrige les incohérences de fiches produits, "
             "les paramétrages perfectibles et les points bloquants simples afin "
             "d'améliorer la qualité de la boutique et le parcours d'achat."),
        ],
        "delai_reponse": "12 heures ouvrées",
        "herite_de": "SHOPIFY_MAINT_STD",
    },
    "SHOPIFY_MAINT_PREM": {
        "famille": "Shopify",
        "famille_label": "Sites e-commerce — Shopify (hébergement exclu)",
        "niveau": "Premium",
        "socle_obligatoire": False,
        "accroche": "La boutique est surveillée, améliorée et accompagnée stratégiquement.",
        "intro": None,
        "prestations": [
            ("Suivi régulier et recommandations",
             "le Prestataire effectue un suivi mensuel de la boutique et formule des "
             "recommandations d'amélioration portant sur l'ergonomie, le parcours "
             "d'achat, la performance technique et la visibilité. Un point de suivi "
             "mensuel est proposé au Client (email de synthèse ou visioconférence courte)."),
            ("Mise en ligne de contenus et produits",
             "le Prestataire assiste le Client dans la mise en ligne de fiches produits, "
             "de contenus et de mises à jour fournis par le Client."),
            ("Support prioritaire renforcé",
             "les demandes du Client sont traitées en priorité absolue."),
        ],
        "delai_reponse": "12 heures ouvrées",
        "herite_de": "SHOPIFY_MAINT_PRO",
    },
}


def contenu_cumule(code: str) -> dict | None:
    """Retourne le contenu CUMULE d'un pack (resout la chaine d'heritage).

    Renvoie un dict :
      - famille, famille_label, niveau, socle_obligatoire, accroche, delai_reponse ;
      - prestations : liste cumulee (du socle au niveau choisi), avec une cle `niveau`
        sur chaque ligne pour pouvoir grouper a l'affichage si besoin ;
      - rappel : RAPPEL_SHOPIFY pour la famille Shopify, sinon None.
    Renvoie None si le code est inconnu.
    """
    pack = PACKS_MAINTENANCE.get(code)
    if pack is None:
        return None

    # Remonter la chaine d'heritage jusqu'au socle (ordre socle -> niveau choisi).
    chaine: list[dict] = []
    courant: dict | None = pack
    while courant is not None:
        chaine.insert(0, courant)
        parent_code = courant.get("herite_de")
        courant = PACKS_MAINTENANCE.get(parent_code) if parent_code else None

    prestations: list[dict] = []
    for niveau_pack in chaine:
        for titre, detail in niveau_pack["prestations"]:
            prestations.append({
                "titre": titre,
                "detail": detail,
                "niveau": niveau_pack["niveau"],
            })

    return {
        "code": code,
        "famille": pack["famille"],
        "famille_label": pack["famille_label"],
        "niveau": pack["niveau"],
        "socle_obligatoire": pack["socle_obligatoire"],
        "accroche": pack["accroche"],
        "delai_reponse": pack["delai_reponse"],
        "prestations": prestations,
        "rappel": RAPPEL_SHOPIFY if pack["famille"] == "Shopify" else None,
    }
