# HANDOFF — Projet FluxDevis

Document de passation pour reprise par un autre agent.
Date : 2026-05-29

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

### Point critique : PAS de JavaScript client
Les **Client Components React ne fonctionnent pas** sur ce setup (hydratation cassee quand on accede depuis un autre PC du reseau). Toutes les pages sont des **Server Components purs** avec formulaires HTML natifs. Les boutons onClick, useState, useEffect ne marchent pas. Utiliser uniquement :
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
`/home/ullop/.claude-max/projects/-home-ullop--openclaw-workspace-projects-tarificateur/memory/`

- `user_identity.md` — Identite de Bruno
- `feedback_autonomy.md` — Preference d'autonomie
- `project_fluxdevis.md` — Etat du projet
