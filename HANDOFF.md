# HANDOFF — Projet FluxDevis

Document de passation pour reprise par un autre agent.
Date de creation : 2026-05-29 — Derniere mise a jour : 2026-06-10

---

## POINT DE REPRISE (2026-06-10)

Numerotation legale des factures + import de l'historique reel : TERMINE (2026-06-10).
FluxDevis devient la SOURCE UNIQUE de facturation. Cf. section "Numerotation legale
des factures & import historique". En bref :
- Numero legal `F<annee>-NNN` (ex F2026-010), sequence CONTINUE par annee, attribue a
  l'EMISSION (bouton "Emettre"), jamais au brouillon -> pas de trou si un brouillon est
  supprime. Compteur en base (table `compteur_facture`), positionne a 9 pour 2026.
- Historique importe : OMNIPUB (devis FW-RAI-25122012 + facture F2026-001 emise) et
  ASK-VSE (devis 16, ref corrigee FW-RAI-26032511 + factures F2026-005..009). Prochaine
  facture emise = F2026-010.
- Decision Bruno : on poursuit la serie 2026 existante ; nouvelle numerotation a revoir
  au 1er janvier 2027 (frontiere d'annee = moment legal pour changer de serie, et caler
  avec la reforme e-facturation TPE de sept. 2027).

Pieces jointes archivees sur un devis : TERMINE (2026-06-10). Catalogue editable +
propositions budgetaires + maintenance Shopify affinee etaient deja livres ; phase
Shopify (devis + factures) achevee au 2026-06-02. Branche `main`.

Derniere fonctionnalite (2026-06-10) — Pieces jointes / archivage du devis signe :
on peut joindre a un devis le veritable document signe (devis/contrat retourne par le
client) + des scans. Repond au cas ASK VSE (devis reconstitue dans l'appli, l'original
signe etant archive a part). Cf. section "Pieces jointes archivees (documents du devis)".

Derniers commits (les plus recents en haut) :
- `608f4ba` (2026-06-02) fix : simulateur — panneau resultats collant scrollable
  (bloc Enregistrer toujours atteignable). Cf. section "Simulateur — panneau collant".
- `d37e531` (2026-06-02) feat : maintenance Shopify — nouveaux prix mensuels exacts
  (35/49/79/129 EUR via heures en 4 decimales) + textes court/detaille editables par
  pack. Cf. section "Maintenance Shopify — prix et textes".
- `d32216d` (2026-06-02) feat : propositions budgetaires (type de document devis /
  proposition_budgetaire), contenu editable des packs (Option.contenu_pack) et options
  incluses par offre (editeur a cases). Cf. section "Catalogue editable & propositions".
- `ad783de` / anterieurs : phase Shopify (devis + factures). Cf. "Phase Shopify".

RESTE / OPTIONNEL (pas de dependance, a faire quand utile) :
1. Envoi email : CODE EN PLACE (SMTP de la messagerie pro) pour DEVIS et FACTURES,
   configurable depuis la PAGE PARAMETRES (plus besoin d'editer .env). Activation par
   Bruno : page Parametres -> renseigner adresse + mot de passe SMTP -> Enregistrer ->
   bouton "Envoyer un email de test". Cf. "Page Parametres" et "Envoi email (SMTP)".
   (Eventuel +) sortie PDF au lieu de Word pour la piece jointe.
2. UI annexe maintenance grand public : l'editeur de contenu de pack existe deja dans
   /catalogue/option ; reste eventuellement une vue de consultation cote client. Confort.
3. Auth multi-utilisateur (Phase E) : differee (Bruno seul utilisateur).

---

## Contexte

**Client** : Bruno LLOPIS, gerant de BLUELINK INNOVATIONS (SASU), marque commerciale **FluXweb**.
Agence web specialisee dans la creation de sites Webflow et Shopify.
Email Git : runollo@users.noreply.github.com

**Preference utilisateur** : Bruno prefere qu'on avance sans demander a chaque etape. Il donne carte blanche sur les choix techniques. Repondre en francais, jamais d'emojis dans le code.

---

## L'ancien systeme (tarificateur Excel)

Emplacement : `/home/ullop/.openclaw/workspace/projects/tarificateur/`
Repo GitHub : https://github.com/runollo/tarificateur

### Ce qu'il faisait
- Generait des classeurs Excel `.xlsm` avec macros VBA pour simuler des prix de vente
- Generait des documents Word (devis, contrats, factures d'acompte et maintenance)
- Donnees metier dans `donnees_catalogue.xlsx` (10 offres, 52 options, 15 categories)
- Contacts dans `contact.xlsx`

### Problemes identifies (rapport d'analyse exhaustif fait en debut de session)
- Macros VBA cassees (adresses de cellules incorrectes depuis le Ticket 3)
- Mots de passe en clair dans le code
- Code duplique (3 fichiers de facturation quasi-identiques)
- Pas de multi-utilisateur, pas d'historique, pas de traçabilite
- Donnees eparpillees (Excel, scripts Python, VBA)
- Windows-only (pywin32 requis pour l'injection VBA)

### Architecture de l'ancien systeme
```
gen_modele.py → sheets/*.py → Modeles_generes/*.xlsm
build_factures_acompte.py → Factures_acompte/*.docx
build_factures_maintenance.py → Factures_maintenance/*.docx
build_template_webflow_comptant.py → Modeles contrats/*.docx
```

Fichier de documentation complet : `/home/ullop/.openclaw/workspace/projects/tarificateur/CLAUDE.md`

---

## Le nouveau systeme (FluxDevis)

Emplacement : `/home/ullop/.openclaw/workspace/projects/fluxdevis/`
Repo GitHub : https://github.com/runollo/fluxdevis
Branche : `main`

### Stack technique
| Couche | Technologie |
|---|---|
| Backend | FastAPI + SQLAlchemy 2.0 (async) + Python 3.14 |
| BDD | PostgreSQL 16 (user: fluxdevis, db: fluxdevis, port 5432) |
| Migrations | Alembic |
| Frontend | Next.js 16 + TypeScript + Tailwind CSS |
| Generation docs | python-docx (Word) |
| Virtualenv | `backend/.venv/` |

### MAJ 2026-05-31 : les Client Components fonctionnent (via allowedDevOrigins)
CORRECTION de la note ci-dessous : le probleme d'hydratation sur le LAN venait de
l'absence de `allowedDevOrigins` dans `next.config`. Depuis qu'il contient
`allowedDevOrigins: ["192.168.1.30"]`, les Client Components React marchent depuis le
reseau (le simulateur a ete refondu en temps reel). On PEUT donc utiliser onClick/
useState si besoin. Cela dit, le reste de l'app reste volontairement en **Server
Components + Server Actions** (pattern simple, robuste, SEO/no-JS friendly) — toute
nouvelle page devrait suivre ce pattern par defaut sauf besoin reel d'interactivite.

### (Ancienne note, conservee pour contexte) Server Components purs
Historiquement les Client Components semblaient casses sur le LAN. Le pattern par defaut
reste donc :
- `<form action={serverAction}>` pour les soumissions
- `<Link href="...">` pour la navigation
- `<select defaultValue>` avec `method="GET"` pour les choix
- Query params pour preserver l'etat entre les pages

### Architecture
```
fluxdevis/
  backend/
    app/
      models/         — 6 entites SQLAlchemy (Societe, Client, Offre, Option, Devis, Facture)
      services/
        simulation.py — Moteur de calcul (Decimal, leasing/comptant, marges, zone Q)
        reference.py  — Generation references D-XXXX-AAMMJJHHMM
        generation_facture.py — Generateur factures Word
        word_helpers.py — Palette et helpers Word mutualises
      api/routes/     — Endpoints REST
        offres.py     — CRUD + GET /offres/{id}/options (avec statut calcule)
        options.py    — CRUD + filtre categorie
        clients.py    — CRUD (18 champs complets)
        devis.py      — Liste + POST creation avec snapshot
        factures.py   — Liste + next-numero
        simulation.py — POST calcul simulation
        generation.py — POST generation facture Word
      core/
        config.py     — pydantic-settings, .env
        database.py   — Async + Sync engines
    alembic/          — Migrations
    main.py           — Point d'entree FastAPI, CORS allow_origins=["*"]
  frontend/
    src/app/
      page.tsx              — Dashboard
      catalogue/page.tsx    — Offres + Options (onglets via query param)
      catalogue/offre/      — Formulaire edition offre
      catalogue/option/     — Formulaire edition option
      clients/page.tsx      — Liste clients
      clients/edit/page.tsx — Fiche client complete (18 champs)
      simulateur/page.tsx   — Simulateur complet (Server Component pur)
      devis/page.tsx        — Liste des devis sauvegardes
      api/[...path]/route.ts — Proxy API (Next.js → backend 127.0.0.1:8000)
    src/components/
      Sidebar.tsx     — Bottom nav mobile + sidebar desktop
    src/lib/
      api.ts          — serverFetch, serverPost, serverPatch, clientFetch
      actions.ts      — Server Actions (saveOffre, saveOption, saveClient, runSimulation, saveDevis)
  scripts/
    import_donnees.py — Import donnees_catalogue.xlsx + contact.xlsx → BDD
  docker-compose.yml
```

### Modele de donnees (PostgreSQL)
```
societes        — Emetteur (BLUELINK INNOVATIONS, IBAN, SIRET, etc.)
offres          — 10 offres (Webflow/Shopify, prix achat/vente, pages, heures)
options         — 44 options (27 champs, 15 categories, 3 types: SETUP/RECURRENT/PACK)
option_inclusions — M:N offre↔option (quelle option est incluse dans quelle offre)
clients         — Fiche complete (raison sociale, forme juridique, SIRET, TVA intracom,
                  adresse, CP, ville, pays, civilite, interlocuteur, fonction, tel, mobile, email)
devis           — Snapshot fige (client+offre+prix au moment de l'emission)
devis_lignes    — Prestations sur mesure
devis_option_lignes — Options selectionnees avec prix figes
devis_articles_offerts — Articles offerts
factures        — Acompte + maintenance + echeances
```

### Reference devis
Format : `D-XXXX-AAMMJJHHMM` (ex: `D-ASKV-2605281430`)
- D = Devis, F = Facture
- XXXX = 4 lettres du client (1 mot=4 lettres, 2 mots=3+1, 3+ mots=2+1+1)
- Supprime formes juridiques (SAS, SARL...) et articles (Le, La, Les)
- Timestamp a la minute (aucun doublon possible)
- Le numero sequentiel interne reste en BDD mais n'apparait pas sur le document
- MAJ 2026-05-31 : la reference (devis ET facture) est desormais SURCHARGEABLE
  manuellement (cas legacy / ancienne nomenclature) via `PATCH /api/devis/{id}/reference`
  et `PATCH /api/factures/{id}` (controle d'unicite). Voir la section session 2026-05-31.

### Donnees importees
- 1 societe (BLUELINK INNOVATIONS)
- 10 offres (4 Webflow + 6 Shopify)
- 44 options (avec inclusions M:N)
- 4 clients (depuis contact.xlsx)

---

## Phases realisees

### Phase 1 — Fondations (terminee)
- Structure projet, 6 modeles SQLAlchemy, routes CRUD
- Configuration Alembic, Docker Compose, script import
- Commit initial

### Phase 2 — Services metier (terminee)
- Service simulation : logique complete portee depuis simu_live.py (Decimal, leasing/comptant, remises, marges, zone Q, plan paiement)
- Service generation facture Word (acompte + maintenance)
- Helpers Word mutualises (palette, formatage, tables)

### Phase 3 — Frontend Next.js (terminee)
- Dashboard, Catalogue (offres+options), Clients (CRUD), Simulateur
- Bottom nav mobile, sidebar desktop
- Responsive (cards mobile, tableaux desktop)
- Correction dark mode, contraste

### Corrections majeures (nombreuses iterations)
- Proxy API : rewrites → API route handler catch-all (redirect 307 FastAPI)
- Client Components → Server Components purs (hydratation React cassee sur LAN)
- Formulaire simulateur : Server Action POST avec toutes les selections encodees dans l'URL
- Selection options : endpoint GET /offres/{id}/options avec statut (Inclus/Option payante)

### Sauvegarde devis (terminee)
- Service reference (D-XXXX-AAMMJJHHMM)
- Endpoint POST /devis/ avec snapshot client+offre
- Bouton "Enregistrer ce devis" dans les resultats du simulateur
- Page /devis avec liste et badges statut

---

## Phases a venir

### Phase A — Generation devis Word (terminee 2026-05-29)
- Service `generation_devis.py` : devis Word professionnel (offre, prestations,
  options payantes + incluses, maintenance mensuelle, articles offerts, totaux,
  echeancier selon plan, bloc leasing, zone signature "Bon pour accord")
- Endpoint `GET /api/devis/{id}/document` (StreamingResponse docx)
- Proxy Next.js transmet desormais `Content-Disposition` (nom de fichier preserve)
- Page /devis : bouton "Telecharger le devis (Word)" (a href, zero JS client)

### Phase B — Generation factures (terminee 2026-05-29)
- Endpoint `POST /api/devis/{id}/factures` : cree une facture par echeance du plan
  (100% -> 1 facture ; 50/50 ; 33/33/33 ; 50/25/25 ; 25/25/25/25). Derniere = SOLDE, sinon ACOMPTE.
  Idempotent (400 si des factures existent deja). Repartition via
  `repartition_echeances()` dans `generation_devis.py` (mutualisee avec l'echeancier devis).

### Plans de paiement et arrondi au centime (2026-05-29)
- Plans disponibles : 100%, 50/50, 33/33/33, 50/25/25, 25/25/25/25 (enum `PlanPaiement`
  + valeur PG `TIERS` ajoutee via `ALTER TYPE planpaiement ADD VALUE`).
- Helper unique `app/services/echeances.py:repartir_au_centime(total, fractions)` : repartit
  un montant selon des fractions EXACTES (Fraction, pas des pourcentages flottants), arrondit
  chaque part au centime, et porte l'ecart d'arrondi sur le PREMIER versement pour que la somme
  retombe EXACTEMENT sur le total. Ex 3612,92 en 33/33/33 -> 1204,30 / 1204,31 / 1204,31
  (et non 1204,31 x3 = 3612,93). Utilise par `repartition_echeances` (echeancier devis +
  factures, TTC) ET par `simulation.py` (prelevements).
- Simulateur : les prelevements ("Plan de paiement (TTC)") sont desormais calcules sur le
  TOTAL SETUP TTC (`total_setup_ttc`), meme base que l'echeancier du devis/facture, via le
  meme helper. Le simulateur affiche donc exactement les memes montants que le devis (ex
  1204,30 / 1204,31 / 1204,31). Le bloc "Totaux TTC" de `simulation.py` est calcule avant
  les prelevements pour servir de base.
- Endpoint `GET /api/factures/{id}/document` : facture Word (reutilise `generation_facture.py`),
  echeancier avec versements payes barres et echeance courante en surbrillance.
- Frontend : nouvelle page `/factures` (liste + telechargement), bouton "Generer les factures"
  sur /devis (Server Action `genererFactures`), lien Factures dans la Sidebar.

### Phase C — Dashboard dynamique (terminee 2026-05-29)
- Endpoint `GET /api/dashboard/` : compteurs (offres/options/clients actifs,
  devis total + acceptes, factures total + impayees), montants TTC cumules,
  5 derniers devis et 5 dernieres factures
- Dashboard (page.tsx) : Server Component qui consomme l'endpoint, cartes
  cliquables vers chaque section, listes "Derniers devis" et "Dernieres factures"
  avec badges de statut. Fallback si backend injoignable.

### Phase D — Ameliorations UI (terminee 2026-05-29)
Fait (2026-05-29) :
- Detail d'un devis : page `/devis/detail?id=X` (snapshot complet, options/prestations,
  articles offerts, totaux, factures liees avec telechargement). Endpoint
  `GET /api/devis/{id}/detail`. Reference cliquable depuis la liste /devis.
- Changement de statut devis (brouillon/envoye/accepte/refuse/expire) :
  endpoint `PATCH /api/devis/{id}/statut`, formulaire select+bouton sur le detail
  (Server Action `changerStatut`). Le bouton "Generer les factures" n'apparait que
  si aucune facture n'existe encore.
- SUPPRESSION / CORBEILLE conforme au droit (voir section dediee ci-dessous).
- Recherche `q` + pagination (skip/limit) sur /devis et /factures ; recherche `q`
  sur catalogue (offres + options) et clients. Frontend : barre de recherche
  (form method=GET) + pagination Precedent/Suivant (sans total, page suivante active
  si la page est pleine). `PAR_PAGE = 25`.
- Export Excel : service `app/services/export_excel.py` (openpyxl). Endpoints
  `GET /api/devis/export.xlsx` et `GET /api/factures/export.xlsx` (respectent `q`,
  excluent les archives). Boutons "Export Excel" sur /devis et /factures. Les routes
  `export.xlsx` sont declarees AVANT `/{id}` pour ne pas etre capturees par le
  convertisseur int.

### Suppression et corbeille (soft-delete) — cadre juridique
Principe : aucune destruction physique via l'UI. Colonne `archived_at` (mixin
`SoftDeleteMixin` dans `app/models/base.py`) sur `devis` et `factures`, ajoutee par
ALTER TABLE sur la base existante (le modele la porte pour les bases neuves).
- Devis : `DELETE /api/devis/{id}` archive (corbeille). Garde-fou : refuse si une
  facture ENCORE ACTIVE (emise/payee/en_retard) est rattachee -> il faut d'abord
  l'annuler (avoir). Les factures brouillon ET annulees sont archivees en cascade.
  `POST /api/devis/{id}/restaurer` restaure.
- Facture : `DELETE /api/factures/{id}` archive UNIQUEMENT si statut brouillon (jamais
  emise). Une facture emise ne se supprime pas (numerotation legale sans trou) :
  `POST /api/factures/{id}/annuler` la passe en ANNULEE (equivalent avoir), le numero
  est conserve. `POST /api/factures/{id}/restaurer` restaure.
- Listes (`/devis/`, `/factures/`) : excluent les archives par defaut ; `?archives=true`
  retourne la corbeille. Dashboard et `devis_maintenance_dus` excluent aussi les archives.
- Idempotence factures : la regeneration ne compte que les factures NON archivees
  (on peut donc regenerer apres une mise a la corbeille).
- Frontend : boutons Supprimer/Annuler/Restaurer + vues corbeille (`?archives=1`) sur
  /devis, /factures et /devis/detail. Server Actions dans `src/lib/actions.ts` :
  `archiverDevis`, `restaurerDevis`, `archiverFacture`, `annulerFacture`,
  `restaurerFacture` (+ `serverDelete` dans `src/lib/api.ts`). Les messages du garde-fou
  sont affiches via le query param `suppr_msg`.

### Garde-fous de suppression a 3 niveaux (2026-05-29)
Toutes les actions destructives passent par une PAGE DE CONFIRMATION (pas de JS client,
donc pas de pop-up) : `/devis/confirmer` et `/factures/confirmer` (Server Components).
- Niveau 1 (leger, reversible) : mise en corbeille d'un devis ou d'une facture brouillon
  -> page de confirmation, 1 clic "Confirmer la mise en corbeille".
- Niveau 2 (fort, acte comptable) : annulation par avoir d'une facture emise -> page +
  saisie obligatoire du mot `SUPPRIMER` (verifie cote Server Action `annulerFacture`).
- Niveau 3 (critique, IRREVERSIBLE) : suppression DEFINITIVE depuis la corbeille -> page +
  saisie `SUPPRIMER` + case "irreversible" cochee. Endpoints `DELETE /api/devis/{id}/definitif`
  et `DELETE /api/factures/{id}/definitif` (hard-delete). Garde-fous backend : l'item doit
  etre archive ; facture supprimable definitivement seulement si brouillon (jamais emise/
  payee/annulee = conservation legale) ; devis supprimable seulement si aucune facture
  conservee legalement n'y est rattachee (sinon 400). Server Actions `supprimerDevisDefinitif`
  / `supprimerFactureDefinitif` revalident le mot + la case avant l'appel.
- Le mot de confirmation est `SUPPRIMER` (choix de Bruno). Erreurs : `err=mot` (saisie
  incorrecte) ou `err=<message API>` (garde-fou backend) affichees sur la page.

### Purge des donnees de test (hors UI)
`scripts/purge_donnees.py` : TRUNCATE devis + factures (CASCADE, RESTART IDENTITY).
Reserve au DEV/TEST pour repartir d'une base propre. Conserve catalogue, clients et
societe. Demande confirmation ("oui") ; `--force` pour cron/CI.
Usage : `python scripts/purge_donnees.py` depuis la racine du projet.

### Phase F — Facturation du recurrent / maintenance (terminee 2026-05-29)
Flux INDEPENDANT du setup : la maintenance demarre a la mise en ligne du site,
pas selon le plan de paiement du setup. Mois glissant (anniversaire), sans prorata.
- Champ `devis.date_mise_en_ligne` (ajoute via ALTER TABLE ; le modele le porte donc
  create_all l'inclut sur une base neuve). Endpoint `PATCH /api/devis/{id}/mise-en-ligne`.
- Service reutilisable `app/services/facturation_maintenance.py` :
  `ajouter_mois`, `periode_pour_index`, `montant_recurrent_ht`, `prochaine_periode`,
  `generer_facture_maintenance` (cree la facture de la prochaine periode due),
  `devis_maintenance_dus` (liste ce qui est a facturer aujourd'hui).
  Garde-fou : ne facture jamais une periode future (start > today) -> erreur.
- `POST /api/devis/{id}/factures-maintenance` : genere la facture maintenance de la
  prochaine periode (type MAINTENANCE, periode_debut/fin, mention "reconductible").
- Leasing EXCLU : maintenance geree par le leaser, a developper au 1er contrat leasing.
- Frontend : section "Maintenance (recurrent)" sur /devis/detail (montant mensuel TTC,
  formulaire date de mise en ligne, periode a facturer + bouton generer). Server Actions
  `definirMiseEnLigne` et `genererFactureMaintenance`. Type affiche sur les factures.
- AUTOMATISATION FUTURE (prevue mais non codee) : `GET /api/factures/maintenance/dus`
  expose les maintenances dues. Un scenario Make (HTTP) ou un cron interne peut le poller
  puis appeler POST .../factures-maintenance.
- EMAIL CLIENT DANS LE SNAPSHOT (fait 2026-05-29) : colonne `devis.client_email`
  (modele Devis + ALTER TABLE + backfill des devis existants depuis le client lie).
  Capturee a la creation du devis (`create_devis`), exposee dans `GET /api/devis/{id}/detail`
  (section Client du frontend) ET dans `GET /api/factures/maintenance/dus` (cle
  `client_email`).
### Envoi email (Resend) — CODE PREVU, NON ACTIVE — A REPRENDRE
IMPORTANT : cette phase n'est PAS terminee. Le code de plomberie est en place mais
volontairement DORMANT. Au 2026-05-29 : pas de compte Resend, pas de cle API, aucun
email ne peut partir. Bruno n'a pas encore decide comment il gere l'envoi — ne rien
activer ni configurer sans son accord explicite.

Etat du code (deja ecrit, inactif) :
- Service `app/services/email_resend.py` (API HTTP Resend via httpx, piece jointe
  base64, `EmailError`). `email_actif()` renvoie False tant que la cle est absente.
- Endpoint `POST /api/factures/{id}/envoyer` : genere le Word (helper
  `_generer_facture_docx`, partage avec le telechargement) et l'enverrait au
  `client_email` du devis. Renvoie 400 "non configure" tant que la cle manque.
- Frontend : bouton "Envoyer" sur /factures et /devis/detail (Server Action
  `envoyerFacture`), bandeau succes `?envoye=1`. Si on clique aujourd'hui : message
  d'erreur "non configure", aucun envoi.
- Config : `RESEND_API_KEY` et `RESEND_FROM` dans `backend/.env` (laisses VIDES).
  From par defaut = `marque <email>` de la societe si `RESEND_FROM` vide.
- Tous les fichiers concernes portent un commentaire "FONCTIONNALITE PREVUE, NON ACTIVEE".

Checklist de reprise (quand Bruno aura tranche sa solution d'envoi) :
1. Decider de la solution (Resend ? autre fournisseur ? envoi manuel ?).
2. Si Resend : creer le compte, verifier un domaine d'envoi (DNS), generer la cle.
3. Renseigner `RESEND_API_KEY` et `RESEND_FROM` dans `backend/.env`.
4. Tester un envoi reel (facture acompte puis maintenance) vers une adresse de test.
5. Optionnel : masquer les boutons "Envoyer" tant que l'envoi n'est pas actif
   (exposer un flag d'activation cote API) pour ne pas montrer une action qui echoue.
6. Coder le DECLENCHEUR automatique de la maintenance : cron interne ou scenario
   Make qui poll `GET /api/factures/maintenance/dus`, cree la facture via
   `POST /api/devis/{id}/factures-maintenance`, puis `POST /api/factures/{id}/envoyer`.
7. Eventuellement : choisir PDF plutot que Word pour la piece jointe (format non
   modifiable cote client).

### Articles offerts — saisie + garde-fou recurrent (terminee 2026-05-29)
Le backend savait deja DEDUIRE et AFFICHER les articles offerts (modele
`DevisArticleOffert`, moteur `simulation.py` avec flag `est_setup`, section "Articles
offerts" du devis Word, detail). Il MANQUAIT toute la SAISIE : cette phase la pose.

Principe de saisie (au lieu des 5 lignes figees + menu de 42 articles de l'ancien Excel) :
une case **"Offrir"** apparait sur chaque element DEJA selectionne (option, pack,
prestation). On n'offre donc que ce qui est dans le devis. Comme la page est en Server
Component pur (etat dans l'URL), la case n'apparait qu'apres un premier Simuler :
selectionner -> Simuler -> cocher "Offrir" -> Simuler -> Enregistrer.

On peut tout offrir :
- Setup (option OPTION_SETUP, one-shot) et prestations sur mesure -> `est_setup=true` (ambre).
- Recurrent (PACK ou OPTION_RECURRENT, mensuel) -> `est_setup=false` (rouge), EXCEPTIONNEL.

Garde-fou recurrent (3 niveaux, sans pop-up JS car pas de Client Component) :
1. case "Offrir" du recurrent en rouge + libelle "(recur.)" ;
2. banniere d'alerte rouge dans les resultats apres Simuler (liste + montant/mois deduit) ;
3. a l'enregistrement, case "Je confirme offrir du RECURRENT" OBLIGATOIRE (`required` HTML,
   bloque la soumission) + backstop serveur dans `saveDevis`.

Coherence comptable du recurrent offert (point critique) : un pack offert en mensuel doit
reduire la facturation de maintenance, pas seulement l'affichage. Nouveau champ scalaire
**`devis.total_offerts_recurrent_ht`** (migration Alembic `2d30cbf3e4b7`, `server_default='0'`).
Il est DEDUIT :
- dans `facturation_maintenance.py:montant_recurrent_ht()` (factures de maintenance) ;
- dans `generation_devis.py` (mensuel affiche sur le devis Word).
Choix d'un champ scalaire (et non un flag sur `DevisArticleOffert`) car `devis_maintenance_dus`
ne charge pas la relation `articles_offerts` -> on evite tout lazy-load en contexte async.
Le setup offert, lui, est deja net dans les totaux stockes (via `prix_setup_affiche`).
Verifie end-to-end : pack 100/mois dont 49 offert -> facture maintenance 51 HT / 61,20 TTC.

Fichiers touches :
- backend : `models/devis.py` (champ), `api/routes/devis.py` (`DevisCreateRequest.articles_offerts`
  + `total_offerts_recurrent_ht`, persistance dans `create_devis`), `services/facturation_maintenance.py`,
  `services/generation_devis.py`, `alembic/versions/2d30cbf3e4b7_*.py`.
- frontend : `src/lib/actions.ts` (`runSimulation` construit `articles_offerts` + persiste les
  cases dans l'URL ; `saveDevis` transmet `articles_offerts` + `total_offerts_recurrent_ht` +
  garde-fou), `src/app/simulateur/page.tsx` (cases "Offrir", banniere, recap, case de confirmation).

Note de presentation : une option offerte apparait a la fois comme ligne d'option (a son prix)
ET dans "Articles offerts" avec mention "Offert" -> volontaire (montrer la valeur puis le geste).
Le total reste net du cadeau.

NB demarrage : `uvicorn` n'est PAS sur le PATH global, il est dans le venv
(`backend/.venv/bin/uvicorn`). Alembic doit etre lance avec `PYTHONPATH=.` depuis `backend/`
(`PYTHONPATH=. ./.venv/bin/alembic upgrade head`), sinon `ModuleNotFoundError: No module named 'app'`.

### Page Parametres (reglages editables depuis l'UI) (fait 2026-06-10) TERMINEE
Demande Bruno : un endroit "Parametres" pour renseigner les parametres d'envoi (et
futurs reglages) sans toucher au code/.env.
- Modele singleton `Parametres` (table `parametres`, ligne id=1, migration `b8c9d0e1f2a3`) :
  smtp_host/port/starttls/user/password/from (NULL = repli .env). Enregistre dans
  `models/__init__.py`.
- Service `app/services/parametres.py` : `charger(db)` (get-or-create), `smtp_config(db)`
  -> `SmtpConfig` (fusion base prioritaire + .env repli ; `.actif` = host+user+password).
  L'envoi email lit desormais cette config (email.py / email_smtp.py db-aware ; les routes
  `factures.envoyer` et `devis.envoyer` passent `db`).
- API `app/api/routes/parametres.py` (prefix /api/parametres) : `GET /` (mot de passe
  MASQUE -> `smtp_password_defini` bool + `smtp_actif`), `PATCH /` (mot de passe change
  seulement si fourni non vide ; champ vide -> NULL = repli .env), `POST /test-email`
  (envoi de test). Monte dans main.py.
- Frontend : page `/parametres` (Server Component) — section "Envoi d'emails (SMTP)"
  pre-remplie (defauts OVH), badge Actif/Non configure, + section "Tester l'envoi" (bouton
  desactive tant que non actif). Actions `saveParametres` / `envoyerEmailTest`. Lien
  "Parametres" dans la sidebar desktop (pied) + engrenage dans le header mobile.
Verifie end-to-end (GET masque, PATCH conserve le mdp, save via UI, reset, tsc OK).
ACTIVE PAR BRUNO (2026-06-10) : SMTP OVH configure et envoi de test OK.

### Pieces jointes et telechargement en PDF (fait 2026-06-10) CODE PRET (install LibreOffice requise)
Decision Bruno : envoyer du PDF (non modifiable), et preparer la conformite facture
electronique. Choix du moteur : LibreOffice headless (fidelite parfaite au rendu Word
actuel, vs reecriture ReportLab). Bruno a accepte l'install systeme.
- Service `app/services/pdf.py` : `docx_vers_pdf(bytes) -> bytes` via
  `soffice --headless --convert-to pdf` (profil UserInstallation dedie par appel ->
  pas de conflit de verrou ; sous-process via asyncio). `libreoffice_dispo()`,
  `PdfError`. Si LibreOffice absent -> PdfError -> HTTP 503 explicite.
- `GET /api/devis/{id}/document` et `/api/factures/{id}/document` : renvoient le PDF par
  defaut ; `?format=docx` garde le Word (modifiable). Les emails (devis + factures)
  joignent desormais le PDF.
- Frontend : libelles "Telecharger le devis (PDF)" + petit lien "version Word (modifiable)"
  (devis/detail), "Telecharger (PDF)" (factures). Le proxy Next gere deja le binaire.
- A FAIRE PAR BRUNO (bloquant pour le PDF) :
    sudo apt install --no-install-recommends libreoffice-core libreoffice-writer
  Puis tester un telechargement/envoi PDF. Tant que non installe : Word OK, PDF -> 503.
- ROADMAP conformite (cf. echange 2026-06-10) : Phase 2 = generer Factur-X (PDF/A-3 +
  XML EN 16931, le XML est le vrai travail nouveau, lib `factur-x`) ; Phase 3 (avant
  sept. 2027) = transmission via une PDP (canal obligatoire, PAS l'email ; a cadrer avec
  l'expert-comptable, souvent fourni par son ecosysteme). Le PDF email reste utile en
  interim et pour le B2C/etranger (hors e-invoicing, e-reporting).
Verifie : tsc OK, docx toujours dispo, 503 propre sans LibreOffice. (Conversion PDF reelle
a tester apres install.)

### Apercu email + choix du destinataire a l'envoi (fait 2026-06-10) TERMINEE
- APERCU : `GET /api/parametres/apercu?type=devis|facture` rend l'email (objet + html)
  avec des donnees d'EXEMPLE (SimpleNamespace) -> reflete les modeles enregistres.
  Section "Apercu" sur la page Parametres (rendu via dangerouslySetInnerHTML, contenu
  interne de confiance). Statique : se met a jour apres "Enregistrer les modeles".
- CHOIX DU DESTINATAIRE : les endpoints `POST /devis/{id}/envoyer` et
  `POST /factures/{id}/envoyer` acceptent `{mode}` ("client" defaut / "expediteur").
  mode=expediteur -> envoie a SOI-MEME (adresse `adresse_expediteur(db)` dans email.py :
  SMTP_FROM/SMTP_USER/societe), sujet prefixe "[A transferer]", pour transferer ensuite
  depuis Outlook (ajout de pieces/destinataires). Resout aussi la trace "Envoyes" : le
  transfert depuis Outlook atterrit dans les Envoyes (l'envoi SMTP direct, lui, ne laisse
  pas de copie dans Outlook > Envoyes — comportement normal SMTP vs IMAP).
- Frontend : actions `envoyerDevis`/`envoyerFacture` portent `mode` ; 2 boutons sur
  /devis/detail (devis + chaque facture) et /factures (liste mobile + desktop) ; bandeaux
  de succes distincts (au client / a moi).
- PAS ENCORE FAIT (option proposee a Bruno pour la trace) : copie Cci automatique a
  l'expediteur, et/ou copie dans le dossier Envoyes via IMAP APPEND (fragile : nom du
  dossier OVH "Sent"/"Envoyes" a confirmer, identifiants IMAP). A decider avec lui.
Verifie (apercu devis+facture OK avec la vraie signature, boutons presents, tsc OK ;
envoi reel non declenche pour ne pas spammer).

### Modeles d'emails editables (objet/corps devis & facture + signature) (fait 2026-06-10) TERMINEE
Demande : corps d'email pre-rempli selon devis/facture, avec n° et dates, + signature.
- Colonnes ajoutees sur `Parametres` (migration `c9d0e1f2a3b4`) : `email_signature`,
  `email_objet_devis`, `email_corps_devis`, `email_objet_facture`, `email_corps_facture`.
- Service `app/services/email_modeles.py` : modeles par DEFAUT + substitution de variables
  `{cle}` (remplacement simple, token inconnu laisse tel quel) + assemblage HTML (sauts de
  ligne -> <br>, signature ajoutee). `construire_email_devis` / `construire_email_facture`.
  Variables : communes `{client}`/`{interlocuteur}`/`{montant_ttc}`/`{marque}` ; devis
  `{reference}`/`{date}`/`{date_validite}`/`{type_document}` ; facture
  `{numero}`/`{date}`/`{date_echeance}`/`{periode}`.
- Routes `devis.envoyer` et `factures.envoyer` utilisent ces builders (l'ancien
  `_corps_email_facture` hardcode est supprime).
- API `/api/parametres` : GET renvoie les modeles EFFECTIFS (stocke ou defaut) pour
  pre-remplir l'UI ; PATCH est PARTIEL (`model_dump(exclude_unset=True)`) -> enregistrer
  une section n'efface pas l'autre (SMTP vs modeles). Champ vide -> NULL = retour au defaut.
- Frontend : section "Modeles d'emails" sur `/parametres` (signature + objet/corps devis +
  objet/corps facture + aide listant les variables). Action `saveModelesEmail`.
Verifie end-to-end (rendu devis/facture avec variables substituees, save modeles sans
ecraser le SMTP de Bruno, tsc OK).

### Envoi email (SMTP de la messagerie pro) — devis + factures (fait 2026-06-10) CODE PRET
Decision Bruno : pas de service tiers type Resend ; envoi via le SMTP de sa propre
messagerie pro (OVH), depuis contact@fluxweb.fr. Resend reste dispo en repli.
- Config (`core/config.py` + `backend/.env`) : `SMTP_HOST` (defaut `ssl0.ovh.net`),
  `SMTP_PORT` (587), `SMTP_STARTTLS` (true), `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`.
- Service `app/services/email_smtp.py` : envoi via `smtplib` (EmailMessage multipart
  texte+HTML + pieces jointes) execute dans un thread (`asyncio.to_thread`) pour ne pas
  bloquer asyncio. Reutilise `Email`/`PieceJointe`/`EmailError` de `email_resend.py`.
- Dispatcher `app/services/email.py` : interface unique (`email_actif`, `envoyer_email`)
  qui choisit SMTP en priorite, sinon Resend, sinon `EmailError`. Les routes importent CE
  module (plus `email_resend` directement).
- Factures : `POST /api/factures/{id}/envoyer` (existait, bascule sur le dispatcher).
- Devis : NOUVEAU `POST /api/devis/{id}/envoyer` (genere le devis Word via le helper
  `_generer_devis_docx` partage avec le telechargement, l'envoie au `client_email`).
- Frontend : action `envoyerDevis` + bouton "Envoyer au client (<email>)" sur
  `/devis/detail` (masque si pas d'email client), bandeau succes `?devis_envoye=1`. Le
  bouton "Envoyer" des factures (liste + detail) marche desormais aussi.
- ACTIVATION (reste a faire par Bruno) : mettre SMTP_USER=contact@fluxweb.fr + le mot de
  passe de la boite dans backend/.env, relancer le backend, tester un envoi reel (vers une
  adresse de test). Sans identifiants : `email_actif()` = False, l'UI renvoie un 400 clair.
  NB OVH : le From doit correspondre a la boite authentifiee (SMTP_USER).
Verifie : import OK, 400 propre quand non configure, bouton affiche, tsc OK. (Envoi reel
non teste faute d'identifiants.)

### Filtres de la page Factures : client / projet / statut (fait 2026-06-10) TERMINEE
Modele : un CLIENT a plusieurs PROJETS, ou un projet = un DEVIS (l'extension d'un site
l'an prochain = un nouveau devis sous le meme client). La page Factures expose desormais
le client et le projet, et se filtre.
- Backend : `GET /api/factures/` renvoie `FactureListItem` (enrichi : `client`,
  `projet_ref`, `projet_nom`, `devis_id`, via `selectinload(Facture.devis)`) et accepte
  `client_id` (jointure `Devis.client_id`) + `devis_id`, en plus de statut/type/q/archives.
  `GET /api/devis/` accepte `client_id` (pour peupler le menu Projet d'un client).
- Frontend (`/factures`, Server Component) : barre de filtres (form GET) recherche + Client
  + Projet (n'apparait qu'une fois un client choisi) + Statut (libelles metier : brouillon /
  a encaisser / en retard / payee / annulee) + Type ; colonnes Client et Projet (ref devis
  cliquable -> detail) en desktop et mobile ; pagination conserve les filtres.
- Edge connu (acceptable, pur Server Component) : changer de client en gardant un projet
  d'un autre client renvoie une liste vide -> remettre "Tous les projets".
Verifie end-to-end (filtres combines client+statut+type+devis, navigateur OK, tsc OK).

### Numerotation legale des factures & import historique (fait 2026-06-10) TERMINEE
Contexte : FluxDevis devient la source unique de facturation. L'ancien tarificateur
emettait deja des factures reelles `F2026-001..009` (Omnipub 001-004 dont seule 001
envoyee, ASK-VSE 005-009). Il fallait (a) une numerotation conforme et (b) importer
l'existant pour enchainer proprement.

Conformite (art. 242 nonies A CGI) — numero attribue A L'EMISSION :
- Table `compteur_facture(annee, dernier)` (migration `a7b8c9d0e1f2`, modele
  `CompteurFacture`). Compteur continu par annee qui ne fait qu'augmenter.
- Service `app/services/numerotation_facture.py` : `prochain_numero(db, annee)` (UPSERT
  atomique `INSERT ... ON CONFLICT DO UPDATE ... RETURNING` -> aucun doublon concurrent),
  `numero_en_cours` (lecture seule), `format_numero` (`F<annee>-NNN`, 3 chiffres min).
- Les factures sont creees en BROUILLON avec un numero PROVISOIRE (l'ancien format
  horodate `F-XXXX-...`, via `generer_reference_facture`) ; le numero legal n'est tire
  qu'a l'emission. Un brouillon supprime ne consomme donc aucun numero (pas de trou).
- Endpoint `POST /api/factures/{id}/emettre` : brouillon -> EMISE + `prochain_numero`
  (annee = date_emission). Tracee au journal. `GET /api/factures/next-numero` previsualise
  SANS consommer (DEPLACE avant `GET /{facture_id}` sinon capture par le convertisseur int).
- Frontend : action `emettreFacture` ; bouton vert "Emettre (n° legal)" sur les factures
  brouillon de `/devis/detail` ET de la liste `/factures` (mobile + desktop) ; le numero
  provisoire est grise avec mention "(provisoire)".

Import historique : `scripts/import_historique.py` (idempotent). Cree OMNIPUB (devis
`FW-RAI-25122012`, 15/12/2025, plan 25/25/25/25, 6206 TTC + facture `F2026-001` emise) ;
corrige le devis 16 (ref `FW-RAI-26032511`, mise en ligne 26/05/2026) et remplace ses
factures de test par les vraies `F2026-005`(payee)/`006`(payee)/`007`(emise, solde)/
`008`+`009`(maintenance emises) ; positionne le compteur 2026 a 9 -> prochaine = `F2026-010`.
NB Omnipub : seule la facture 001 a ete reellement emise (les 3 autres versements seront
emis plus tard via FluxDevis) ; le devis Omnipub est cree avec le total global (detail des
prestations non disponible dans l'ancien systeme, offre_id=2 par defaut, a affiner).
Verifie end-to-end (import OK, emission attribue F2026-010 puis remise a 9, tsc OK).
A FAIRE EVENTUELLEMENT : affiner le devis Omnipub (detail des prestations) ; eventuellement
passer date_emission a "aujourd'hui" au moment de l'emission (aujourd'hui conservee telle
quelle, editable via modifier_facture).

### Pieces jointes archivees (documents du devis) (fait 2026-06-10) TERMINEE
Besoin : rattacher a un devis le VRAI document qui fait foi (devis/contrat signe
retourne par le client), plus des scans. Cas declencheur ASK VSE : un devis emis avec
l'ancien systeme, accepte et signe, a ete RECONSTITUE a l'identique dans l'appli (memes
articles, meme prix) ; le devis applicatif n'est qu'informatif, l'original signe est
archive sur le PC. Il fallait pouvoir joindre cet original et le distinguer.

Choix de conception (valides avec Bruno) :
- STOCKAGE EN BASE (bytea), pas sur le disque : une seule sauvegarde (le dump
  PostgreSQL) contient toutes les archives, rien a synchroniser a part.
- soft-delete (corbeille) comme le reste de l'app ; categorie + TAG libre + COMMENTAIRE
  libre par piece (demande de Bruno).

Backend :
- modele `app/models/devis_document.py` : table `devis_documents` (devis_id FK CASCADE,
  categorie, tag, commentaire, nom_fichier, mime_type, taille, contenu=LargeBinary,
  TimestampMixin + SoftDeleteMixin). Categories (constante `CATEGORIES_DOCUMENT`,
  valeurs sans accents = source de verite ; libelles accentues cote frontend dans
  `CATEGORIES_DOC`) : documents ENVOYES (devis_envoye, proposition_envoyee,
  facture_envoyee, contrat_envoye, avenant_envoye) ET SIGNES/retournes (devis_signe,
  contrat_signe, avenant_signe, bon_commande) + annexe / autre. Pour en ajouter :
  completer les DEUX listes (backend tuple + frontend array), pas de migration (colonne
  String, validee au niveau applicatif). Enregistre dans `models/__init__.py`.
- `Devis` : 2 champs `reference_externe` + `date_signature` (tracent l'original externe
  quand le devis applicatif est une reconstitution) + relation `documents`.
- migration `f6a7b8c9d0e1` (table + 2 colonnes). Appliquee.
- endpoints (devis router) : `POST /api/devis/{id}/documents` (multipart UploadFile,
  Form categorie/tag/commentaire, max 25 Mo), `PATCH /api/devis/{id}/document-officiel`
  (reference_externe + date_signature). Le detail (`GET /api/devis/{id}/detail`) renvoie
  desormais `documents[]` (metadonnees, sans le binaire) + `reference_externe`/`date_signature`.
- nouveau routeur `app/api/routes/documents.py` (prefix `/api/documents`) :
  `GET /{id}/download` (Response binaire, Content-Disposition RFC5987 accents OK),
  `PATCH /{id}` (categorie/tag/commentaire), `DELETE /{id}` (soft-delete). Monte dans main.py.
- NB upload : `python-multipart` est deja installe dans le venv.

Frontend :
- `api.ts` : helper `serverPostForm` (POST multipart SANS Content-Type fixe). L'upload
  passe par une Server Action (serveur Next -> backend en direct), PAS par le proxy
  `/api/[...path]` qui lit le body en `text()` et casserait le binaire. Le telechargement
  (GET) passe par le proxy, qui gere deja arrayBuffer + Content-Disposition.
- `actions.ts` : `uploaderDocument`, `modifierDocument`, `supprimerDocument`,
  `definirDocumentOfficiel`.
- `/devis/detail` : section "Documents archives" (ancre #documents) — bandeau ambre si
  document officiel externe renseigne, formulaire reference/date de signature (details),
  liste des pieces (lien telechargement, badge categorie, tag, taille/date, commentaire,
  edition inline, suppression), formulaire d'ajout (fichier + categorie + tag + commentaire).
Verifie end-to-end (upload/officiel/detail/download direct+proxy/patch/delete soft, tsc OK).

Corbeille + confirmation (ajoute le 2026-06-10, meme phase) :
- `POST /api/documents/{id}/restaurer` (annule le soft-delete) ; le detail renvoie aussi
  `documents_archives[]` (les pieces a la corbeille).
- frontend : action `restaurerDocument` ; bloc repliable "Corbeille (n)" avec bouton
  Restaurer sous la liste des pieces actives ; la suppression passe par une confirmation
  inline (`<details>` -> "Confirmer", sans JS) au lieu d'un clic direct.
Verifie end-to-end (upload -> corbeille -> restauration, tsc OK).
A FAIRE EVENTUELLEMENT : categorie/tag des pieces exploitables ailleurs si besoin ;
purge physique des pieces (aujourd'hui le soft-delete suffit, recuperable en base).

### Catalogue editable & propositions budgetaires (fait 2026-06-02, `d32216d`) TERMINEE
Trois evolutions liees, developpees en couches sur des fichiers partages
(`generation_devis.py`, `actions.ts`, `api.ts`) -> un seul commit.

Propositions budgetaires :
- `Devis.document_type` : `devis` ou `proposition_budgetaire` (prefixe de reference
  D- / PB- dans `services/reference.py`). Bascule rapide sur un BROUILLON via
  `PATCH /api/devis/{id}/document-type` + selecteur dans le simulateur.
- Une proposition budgetaire est NON CONTRACTUELLE : pas de signature, pas d'IBAN, pas
  d'echeancier, mentions adaptees. Conteneur `params_doc` (JSON) sur le devis pour les
  parametres de document. Blocs Shopify enrichis (socle, forfait references produits,
  abonnement a charge du client, frais externes, maintenance courte).
- Migration `c3d4e5f6a7b8` (document_type, params_doc).

Contenu editable des packs de maintenance :
- Colonne `Option.contenu_pack` (override JSON) avec FALLBACK sur `packs_maintenance.py`.
  `contenu_cumule(code)` resout l'heritage en appliquant les overrides maillon par maillon.
- API `GET/PATCH/DELETE /api/options/{id}/contenu-pack` + editeur `PackContenuEditor.tsx`
  dans /catalogue/option (parties heritees en lecture seule + prestations propres editables).
- Migration `d4e5f6a7b8c9` (contenu_pack).

Options incluses par offre :
- API `PUT /api/offres/{id}/inclusions` (remplacement complet, garde-fou ids valides).
- Editeur `OffreInclusionsEditor.tsx` (cases a cocher groupees par categorie) dans /catalogue/offre.

N'impacte que le catalogue et les FUTURS documents ; les devis emis gardent prix et
inclusions figes.

### Maintenance Shopify — prix et textes (fait 2026-06-02, `d37e531`) TERMINEE
Prix mensuels HT EXACTS (35 / 49 / 79 / 129 EUR) obtenus en n'ajustant QUE les heures :
- Migration `e5f6a7b8c9d0` : heures en `Numeric(8,4)` (4 decimales). Prix/heure (27) et
  marge (0,20) INCHANGES. Heures Shopify ajustees en base (catalogue editable).

Descriptif Shopify court + detaille, editable par niveau :
- `texte_court` (devis simple / proposition budgetaire) et `texte_detaille`
  (contrat / annexe) ajoutes aux packs Shopify dans `packs_maintenance.py` ;
  `contenu_cumule` les expose (override base possible).
- Generation : `_add_maintenance_shopify` affiche le texte court + un temps inclus derive
  des heures du pack ; annexe `_add_detail_maintenance_shopify` (texte detaille) affichee
  pour un devis CONTRACTUEL (pas en proposition budgetaire).
- Editeur /catalogue/option adapte par FAMILLE (Shopify = textes ; Webflow = prestations
  cumulees, inchange). Aucune mention "hebergement inclus" cote Shopify ; Webflow non impacte.

### Simulateur — panneau resultats collant (fait 2026-06-02, `608f4ba`) TERMINEE
Le panneau de droite (Resultats + Enregistrer) etait sticky ; un recap plus haut que
l'ecran faisait passer le bloc Enregistrer hors d'atteinte au scroll. Desormais plafonne
a la hauteur de la fenetre avec defilement interne
(`lg:max-h-[calc(100vh-2rem)] overflow-y-auto`). Mobile inchange.
NB : le simulateur a un Client Component `SimulateurClient.tsx` (le pattern par defaut du
reste de l'app demeure Server Components — cf. note 2026-05-31).

### Phase Shopify — abonnement a la charge du client (devis 2026-06-01, factures 2026-06-02) TERMINEE
Decision metier (Bruno) : dans un contrat Shopify, l'abonnement Shopify (plateforme,
hebergement, infra, paiement) est souscrit et regle DIRECTEMENT par le client, EN SON
NOM, et n'est NI inclus NI facture par FluXweb (la boutique genere du CA -> trop risque
de porter l'abonnement au nom de FluXweb). A distinguer de Webflow ou FluXweb porte
l'hebergement (31 EUR/mois inclus dans le `prix_hebergement` des packs `WF_MAINT_*`).
Cote tarif c'est deja correct : les packs `SHOPIFY_MAINT_*` ont `prix_hebergement = 0`.

Fait cote DEVIS (`backend/app/services/generation_devis.py`) :
- helper `_is_shopify(devis)` (sur `offre_type_site`) ;
- nouvel encart `_add_abonnement_shopify()` "ABONNEMENT SHOPIFY (a votre charge)" affiche
  pour tout devis Shopify, INDEPENDAMMENT du mensuel maintenance (insere apres
  `_add_abonnement`, avant le recap financier). Texte SANS montant (tarifs Shopify
  variables, hors maitrise FluXweb), mentions juridiques en gras ("en votre nom",
  "ni inclus ni facture par <marque>") ;
- socle commun adapte : pour Shopify, la ligne "Hebergement — Inclus..." devient
  "Hebergement & infrastructure — Assures par la plateforme Shopify (voir encart)" ;
- recap financier : sous-titre "maintenance & hebergement" -> "maintenance & exploitation"
  pour Shopify.
Verifie end-to-end (devis Shopify id 17 OK, non-regression Webflow id 16 OK).

Fait cote FACTURES (2026-06-02) — parite Webflow/Shopify achevee :
- detection Shopify deplacee en SOURCE UNIQUE sur le modele : `Devis.est_shopify`
  (property sur `offre_type_site`). `generation_devis._is_shopify` delegue desormais
  a cette property ; partagee avec la facturation.
- objet de la facture de maintenance (`facturation_maintenance.generer_facture_maintenance`)
  aligne sur le recap du devis : "Maintenance & exploitation — <offre> — periode..."
  pour Shopify, "Maintenance & hebergement — ..." pour Webflow (au lieu du neutre
  "Maintenance <offre> — periode...").
- document Word (`generation_facture.py`) : `FactureData.est_shopify` ajoute ; pour une
  facture de maintenance Shopify, mention de bas de page rappelant que l'abonnement
  plateforme (hebergement, infra, paiement) est souscrit/regle par le client en son nom,
  ni inclus ni facture par FluXweb. Champ propage par `routes/factures.py` (depuis le
  devis) et `routes/generation.py` (endpoint ad hoc, defaut False).
- factures d'acompte/solde : objet "Acompte i/n sur devis <ref> — <offre>" deja neutre
  (creation one-shot), aucune mention d'hebergement -> rien a changer.
Verifie : generation Word des 2 variantes OK, property/_is_shopify OK, imports OK.

### Annexe contenu des packs de maintenance (fait 2026-06-01)
Source de verite UNIQUE du descriptif des packs : `backend/app/data/packs_maintenance.py`
(nouveau module `app/data/`). Contient les 8 packs (WF_MAINT_* + SHOPIFY_MAINT_*) avec,
par niveau : famille, accroche, prestations PROPRES, delai de reponse, `herite_de`. Les
packs sont CUMULATIFS (Essentielle -> Standard -> Pro -> Premium) ; `contenu_cumule(code)`
resout la chaine d'heritage et renvoie la liste cumulee des prestations + le `rappel`
Shopify (abonnement a la charge du client). Les CHAINES de texte sont accentuees (affichage
client) ; commentaires/identifiants sans accents (convention projet).
Exploitation : le devis Word affiche un bloc "CE QUE COMPREND VOTRE MAINTENANCE (NIVEAU)"
(accroche + prestations cumulees titre+descriptif + delai), via `_add_detail_maintenance()`
dans `generation_devis.py` (insere apres l'abonnement mensuel, mappe sur `opt.code` du
snapshot du devis). S'affiche des qu'un pack est present, independamment du montant.
Verifie sur devis 17 (Shopify Premium) et 16 (Webflow Standard).
A reutiliser pour : repondre aux questions client, et eventuellement une page UI catalogue.

### Phase E — Auth multi-utilisateur (differee)
- Bruno est le seul utilisateur pour l'instant
- A implementer si besoin plus tard (admin, commercial, apporteur)

---

## Comment demarrer

### Prerequis
- PostgreSQL actif avec base `fluxdevis` (user: fluxdevis, password: fluxdevis)
- Python 3.14 avec `python3.14-venv` installe
- Node.js 22+

### Lancer le backend
```bash
cd /home/ullop/.openclaw/workspace/projects/fluxdevis/backend
source .venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Lancer le frontend
```bash
cd /home/ullop/.openclaw/workspace/projects/fluxdevis/frontend
export PATH="/home/ullop/.npm-global/bin:$PATH"
npm run dev -- -p 3001
```

### URLs
- Frontend : http://localhost:3001 (ou http://192.168.1.30:3001 depuis le reseau)
- API Swagger : http://localhost:8000/api/docs
- Le port 3000 est utilise par SalesQuest (autre projet)

### Reimporter les donnees (si besoin)
```bash
cd /home/ullop/.openclaw/workspace/projects/fluxdevis
source backend/.venv/bin/activate
python scripts/import_donnees.py
```

---

## Fichiers de memoire

Les memoires persistantes sont dans :
`/home/ullop/.claude-max/projects/-home-ullop--openclaw-workspace-projects-fluxdevis/memory/`

- `MEMORY.md` — Index des memoires (charge a chaque session)
- `user_identity.md` — Identite de Bruno
- `feedback_autonomy.md` — Preference d'autonomie
- `project_fluxdevis.md` — Etat du projet
- `project_env_runtime.md` — Env runtime (PostgreSQL systeme, venv/uvicorn:8000, Alembic)
- `project_js_client_reseau.md` — Client Components OK via allowedDevOrigins
