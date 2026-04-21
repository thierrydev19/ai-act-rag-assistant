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

## Lancement frontend local (lot W2)

- Se placer dans le dossier frontend: `cd web`
- Installer les dépendances: `npm install`
- (Optionnel) définir l'URL API: `set NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000`
- Lancer le frontend: `npm run dev`
- Ouvrir: [http://localhost:3000](http://localhost:3000)