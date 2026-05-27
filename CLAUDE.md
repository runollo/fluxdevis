# CLAUDE.md — FluxDevis

Application web de gestion des devis et factures pour l'agence web **FluXweb** (BLUELINK INNOVATIONS).

Toujours repondre et commenter en **francais**. Ne jamais utiliser d'emojis dans le code.

---

## Stack technique

| Couche | Technologie |
|---|---|
| Backend | FastAPI + SQLAlchemy 2.0 (async) |
| BDD | PostgreSQL 16 |
| Migrations | Alembic |
| Frontend | Next.js (a venir — Phase 3) |
| Generation docs | python-docx (Word), openpyxl (Excel) |
| Auth | JWT + bcrypt (a venir — Phase 4) |

---

## Commandes principales

```bash
# Lancer la stack (PostgreSQL + backend)
docker compose up -d

# Lancer le backend en dev (sans Docker)
cd backend
uvicorn main:app --reload

# Importer les donnees du tarificateur existant
python scripts/import_donnees.py

# Creer une migration Alembic
cd backend
alembic revision --autogenerate -m "description"

# Appliquer les migrations
cd backend
alembic upgrade head
```

---

## Structure du projet

```
fluxdevis/
  backend/
    app/
      models/       — Modeles SQLAlchemy (Societe, Client, Offre, Option, Devis, Facture)
      services/     — Logique metier (simulation, generation Word)
      api/routes/   — Endpoints REST (CRUD offres, options, clients, devis, factures)
      core/         — Config, database, auth
      templates/    — Templates Word pour generation documents
    alembic/        — Migrations BDD
    main.py         — Point d'entree FastAPI
  frontend/         — Next.js (Phase 3)
  scripts/          — Scripts utilitaires (import donnees)
  docker-compose.yml
```

---

## Modele de donnees

6 entites principales :
- **Societe** : emetteur des documents (BLUELINK INNOVATIONS)
- **Client** : prospects et clients (ex contact.xlsx)
- **Offre** : catalogue des offres web (10 offres Webflow/Shopify)
- **Option** : options et packs maintenance (52 options, 15 categories)
- **Devis** : devis avec snapshot des prix figes + lignes + options + articles offerts
- **Facture** : acomptes et maintenance avec echeances et statut de paiement

Les prix sont **figes** dans les devis et factures au moment de l'emission.
Les modifications du catalogue n'affectent pas les documents deja emis.

---

## Origine

Ce projet remplace le tarificateur Excel existant (../tarificateur/).
Le script `scripts/import_donnees.py` importe les donnees de `donnees_catalogue.xlsx` et `contact.xlsx`.
