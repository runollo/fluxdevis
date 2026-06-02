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
    # Pour Shopify, le descriptif affiche au client repose sur deux textes
    # auto-portants : `texte_court` (devis simple / proposition budgetaire) et
    # `texte_detaille` (contrat / annexe). Les `prestations` (modele Webflow
    # cumulatif) ne sont pas utilisees a l'affichage pour Shopify.
    "SHOPIFY_MAINT_ESS": {
        "famille": "Shopify",
        "famille_label": "Sites e-commerce — Shopify (hébergement exclu)",
        "niveau": "Essentielle",
        "socle_obligatoire": True,
        "accroche": "La boutique est surveillée et sécurisée.",
        "intro": "Ce pack constitue le socle minimal requis pour garantir le bon "
                 "fonctionnement de la boutique :",
        "texte_court": (
            "Socle minimal de surveillance de la boutique Shopify : contrôle de "
            "l'accessibilité, sécurité de base, correctifs techniques imputables à la "
            "configuration réalisée et assistance par email. Abonnement Shopify et "
            "applications payantes non inclus."
        ),
        "texte_detaille": (
            "La formule Essentielle constitue le socle minimal de maintenance de la "
            "boutique Shopify. Elle comprend le contrôle régulier de l'accessibilité du "
            "site, la vérification du bon fonctionnement des pages principales, du "
            "formulaire de contact et du parcours principal. Elle inclut également le "
            "contrôle des accès, les recommandations de sécurité, la vérification des "
            "configurations à risque et la correction des anomalies directement "
            "imputables aux éléments mis en place par le Prestataire. L'assistance est "
            "assurée par email. Le délai de réponse est de 48 heures ouvrées. Cette "
            "formule ne comprend pas les modifications courantes de contenus, les "
            "évolutions graphiques, les optimisations catalogue, la mise en ligne de "
            "produits ou les développements spécifiques."
        ),
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
        "texte_court": (
            "Maintenance de suivi pour boutique Shopify : supervision, sécurité, "
            "correctifs techniques, interventions correctives mineures, contrôle du "
            "parcours d'achat et assistance prioritaire par email. Abonnement Shopify et "
            "applications payantes non inclus."
        ),
        "texte_detaille": (
            "La formule Standard inclut l'ensemble des prestations de la formule "
            "Essentielle, complétées par des interventions correctives mineures sur "
            "demande du Client. Ces interventions peuvent porter sur des ajustements "
            "ponctuels de textes, liens, composants, affichage, mise en page ou éléments "
            "simples de navigation. Elle comprend également une supervision "
            "transactionnelle du parcours e-commerce : vérification du checkout, des "
            "paiements, des notifications de commande et des principales fonctionnalités "
            "liées à la vente en ligne. Le support est prioritaire par rapport à la "
            "formule Essentielle. Le délai de réponse est de 24 heures ouvrées. Cette "
            "formule ne comprend pas les évolutions fonctionnelles, les refontes de "
            "sections, les optimisations catalogue approfondies, la rédaction de contenus "
            "ou la mise en ligne régulière de nouveaux produits."
        ),
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
        "texte_court": (
            "Maintenance avancée pour boutique Shopify : supervision, sécurité, "
            "correctifs, ajustements mineurs, contrôle e-commerce, évolutions simples et "
            "optimisations ponctuelles du catalogue. Abonnement Shopify et applications "
            "payantes non inclus."
        ),
        "texte_detaille": (
            "La formule Pro inclut l'ensemble des prestations de la formule Standard, "
            "complétées par des évolutions mineures et des optimisations simples de la "
            "boutique. Elle peut comprendre l'ajout ou la modification légère de sections "
            "existantes, l'ajustement de la mise en page, l'amélioration de blocs de "
            "contenu, la correction d'incohérences visibles dans le catalogue, "
            "l'optimisation ponctuelle de fiches produits, la vérification des collections "
            "et les ajustements simples du parcours d'achat. Le délai de réponse est de "
            "12 heures ouvrées. Cette formule est adaptée aux boutiques Shopify "
            "nécessitant un suivi régulier sans accompagnement stratégique mensuel. Elle "
            "ne comprend pas la rédaction de fiches produits, la création d'articles de "
            "blog, les campagnes marketing, les développements spécifiques, les refontes "
            "complètes de pages ou la mise en ligne régulière de contenus en volume."
        ),
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
        "texte_court": (
            "Maintenance renforcée pour boutique Shopify : suivi complet, optimisations, "
            "recommandations mensuelles, accompagnement prioritaire et assistance à la "
            "mise en ligne de contenus ou produits fournis par le Client. Abonnement "
            "Shopify et applications payantes non inclus."
        ),
        "texte_detaille": (
            "La formule Premium inclut l'ensemble des prestations de la formule Pro, "
            "complétées par un accompagnement renforcé de la boutique. Elle comprend un "
            "suivi mensuel avec recommandations portant sur l'ergonomie, le parcours "
            "d'achat, le catalogue, la performance technique et la visibilité. Un point "
            "mensuel peut être proposé sous forme d'email de synthèse ou de "
            "visioconférence courte. Elle inclut également une assistance à la mise en "
            "ligne de contenus ou de produits fournis par le Client, dans la limite du "
            "temps inclus. Le support est traité en priorité renforcée. Le délai de "
            "réponse est de 12 heures ouvrées. Cette formule ne comprend pas la rédaction "
            "complète de contenus, la production graphique avancée, les campagnes "
            "publicitaires, l'email marketing récurrent, les développements spécifiques "
            "ou les évolutions majeures, qui feront l'objet d'un devis complémentaire."
        ),
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


def _prestations_propres(code: str, pack: dict, overrides: dict) -> list[tuple[str, str]]:
    """Prestations PROPRES a un niveau : override base si present, sinon fichier.

    L'override (Option.contenu_pack) stocke des dicts {titre, detail} ; le fichier
    stocke des tuples (titre, detail). On normalise vers une liste de tuples.
    """
    ov = overrides.get(code) or {}
    liste = ov.get("prestations")
    if liste is not None:
        return [
            ((p.get("titre") or "").strip(), (p.get("detail") or "").strip())
            for p in liste
            if (p.get("titre") or "").strip()
        ]
    return list(pack["prestations"])


def _champ_pack(code: str, pack: dict, overrides: dict, cle: str):
    """Valeur d'un champ texte (accroche/intro/delai_reponse) : override sinon fichier."""
    ov = overrides.get(code) or {}
    val = ov.get(cle)
    if val is not None and str(val).strip() != "":
        return val
    return pack.get(cle)


def contenu_cumule(code: str, overrides: dict | None = None) -> dict | None:
    """Retourne le contenu CUMULE d'un pack (resout la chaine d'heritage).

    `overrides` : dict {code_pack: contenu_pack} issu de la base (Option.contenu_pack),
    permettant de surcharger, maillon par maillon, le descriptif du fichier
    `packs_maintenance` (accroche, intro, delai_reponse, prestations propres). Absent
    ou None => contenu du fichier (fallback).

    Renvoie un dict :
      - famille, famille_label, niveau, socle_obligatoire, accroche, intro, delai_reponse ;
      - prestations : liste cumulee (du socle au niveau choisi), avec une cle `niveau`
        sur chaque ligne pour pouvoir grouper a l'affichage si besoin ;
      - rappel : RAPPEL_SHOPIFY pour la famille Shopify, sinon None.
    Renvoie None si le code est inconnu.
    """
    pack = PACKS_MAINTENANCE.get(code)
    if pack is None:
        return None
    overrides = overrides or {}

    # Remonter la chaine d'heritage jusqu'au socle (ordre socle -> niveau choisi),
    # en conservant le code de chaque maillon pour resoudre ses overrides.
    chaine: list[tuple[str, dict]] = []
    code_courant: str | None = code
    courant: dict | None = pack
    while courant is not None:
        chaine.insert(0, (code_courant, courant))
        parent_code = courant.get("herite_de")
        code_courant = parent_code
        courant = PACKS_MAINTENANCE.get(parent_code) if parent_code else None

    prestations: list[dict] = []
    for code_m, pack_m in chaine:
        for titre, detail in _prestations_propres(code_m, pack_m, overrides):
            prestations.append({
                "titre": titre,
                "detail": detail,
                "niveau": pack_m["niveau"],
            })

    return {
        "code": code,
        "famille": pack["famille"],
        "famille_label": pack["famille_label"],
        "niveau": pack["niveau"],
        "socle_obligatoire": pack["socle_obligatoire"],
        "accroche": _champ_pack(code, pack, overrides, "accroche"),
        "intro": _champ_pack(code, pack, overrides, "intro"),
        "delai_reponse": _champ_pack(code, pack, overrides, "delai_reponse"),
        "prestations": prestations,
        # Textes auto-portants utilises pour la famille Shopify (court = devis/PB,
        # detaille = contrat/annexe). None pour Webflow (qui utilise les prestations).
        "texte_court": _champ_pack(code, pack, overrides, "texte_court"),
        "texte_detaille": _champ_pack(code, pack, overrides, "texte_detaille"),
        "rappel": RAPPEL_SHOPIFY if pack["famille"] == "Shopify" else None,
    }
