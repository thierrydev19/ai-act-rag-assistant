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