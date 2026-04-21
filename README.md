# AI Act RAG Assistant

MVP vitrine d’assistant documentaire AI Act fondé sur une architecture RAG traçable.

## Structure
- `docs/` : cadrage, architecture, décisions, prompts Cursor
- `app/` : code applicatif modulaire du MVP
- `app/ingestion/` : contrat d'ingestion documentaire
- `app/document/` : modèles et métadonnées documentaires
- `app/chunking/` : contrat de découpage en chunks
- `app/embeddings/` : contrat embeddings / stockage vectoriel
- `app/retrieval/` : contrat de retrieval
- `app/generation/` : contrat de génération contrainte
- `app/ui/` : point d'entrée interface vitrine
- `app/logging/` : journalisation simple
- `tests/` : tests de structure et de bootstrap

## Règle
Le développement se fait par lots Cursor validés par pilotage CTO.

## Lancement API locale (lot W1)

- Installer les dépendances: `python -m pip install -r requirements.txt`
- Lancer le backend web: `uvicorn app.api.main:app --reload`
- Endpoints minimum:
  - `GET /health`
  - `GET /api/demo-cases`
  - `POST /api/ask`

### Configuration backend (local + Railway)

- `CORS_ALLOW_ORIGINS` : liste d'origines autorisées séparées par des virgules.
  - défaut local: `http://localhost:3000,http://127.0.0.1:3000`
  - exemple Railway: `https://<votre-frontend>.up.railway.app`
- Lancement backend "production-like":
  - PowerShell: `$env:PORT=8000; uvicorn app.api.main:app --host 0.0.0.0 --port $env:PORT`

## Lancement frontend local (lot W2)

- Se placer dans le dossier frontend: `cd web`
- Installer les dépendances: `npm install`
- Copier `web/.env.example` en `.env.local`
- Définir l'URL API: `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000`
- Lancer le frontend: `npm run dev`
- Ouvrir: [http://localhost:3000](http://localhost:3000)

### Frontend "production-like"

- Build: `cd web && npm run build`
- Start: `cd web && npm run start`
- Le frontend reste utilisable si `/api/demo-cases` echoue (fallback local des 4 cas de demo).

## Preparation Railway (W3)

- Service backend (FastAPI):
  - Start command: `uvicorn app.api.main:app --host 0.0.0.0 --port $PORT`
  - Variables minimales:
    - `CORS_ALLOW_ORIGINS=https://<frontend-railway>`
- Service frontend (Next.js):
  - Build command: `npm run build`
  - Start command: `npm run start`
  - Variable:
    - `NEXT_PUBLIC_API_BASE_URL=https://<backend-railway>`