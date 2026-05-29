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
  (100% -> 1 facture ; 50/50 ; 50/25/25 ; 25/25/25/25). Derniere = SOLDE, sinon ACOMPTE.
  Idempotent (400 si des factures existent deja). Repartition via
  `repartition_echeances()` dans `generation_devis.py` (mutualisee avec l'echeancier devis).
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

### Phase D — Ameliorations UI
- Recherche/filtres catalogue
- Pagination
- Detail d'un devis (page individuelle)
- Changement de statut devis (brouillon → envoye → accepte)
- Export Excel

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
