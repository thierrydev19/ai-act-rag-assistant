# Lot V3-3 — Mesure des distances et scores de retrieval

Mesures realisees avec :
- Corpus: AI Act FR officiel (UE 2024/1689), 144 pages, 230 chunks
- Embeddings: sentence_transformers_v1 (384 dim)
- Seuils retrieval actuels (calibres pour hashing_v2) :
  - max_acceptable_distance = 1.35
  - relaxed_max_distance = 1.7
  - min_lexical_overlap = 0.08
  - min_combined_score = 0.14

## Synthese

- Questions positives correctement servies : 6/8
- Refus correctement detectes : 4/4

## Tableau detaille

| Cat. | Question | Attendu | Observe | Suffisant | min_dist | best_comb | best_lex | best_sem | UI refus | Intent |
|---|---|---|---|---|---|---|---|---|---|---|
| positive | Quelles obligations de transparence pour les systemes IA ? | positive | sufficient | Y | 0.453 | 0.724 | 0.667 | 0.748 | N | transparence_information |
| positive | Quelles sanctions sont prevues en cas de violation ? | positive | sufficient | Y | 0.405 | 0.743 | 0.667 | 0.775 | N | limites_conclusion |
| positive | Comment le reglement definit un systeme IA ? | positive | sufficient | Y | 0.559 | 0.483 | 0.000 | 0.690 | N | qualification_systeme |
| positive | Quelles obligations existent pour les systemes IA a haut risque ? | positive | sufficient | Y | 0.536 | 0.612 | 0.400 | 0.702 | N | obligations_entreprise |
| positive | Que faut-il verifier avant de mettre un systeme IA sur le marche ? | positive | sufficient | Y | 0.516 | 0.549 | 0.167 | 0.713 | Y | qualification_systeme |
| positive | Que prevoit le texte pour la surveillance des systemes IA ? | positive | sufficient | Y | 0.385 | 0.550 | 0.000 | 0.786 | N | limites_conclusion |
| positive | Que dit l'AI Act sur les voies de recours ? | positive | sufficient | Y | 0.693 | 0.431 | 0.000 | 0.615 | N | limites_conclusion |
| positive | Quels points de conformite sont attendus pour les fournisseurs ? | positive | sufficient | Y | 0.955 | 0.389 | 0.250 | 0.449 | Y | obligations_entreprise |
| limit | Quelles obligations pour les importateurs de systemes IA ? | limit | sufficient | Y | 0.818 | 0.482 | 0.333 | 0.546 | N | obligations_entreprise |
| limit | Que dit le texte sur les obligations des deployeurs ? | limit | sufficient | Y | 0.963 | 0.425 | 0.333 | 0.465 | N | obligations_entreprise |
| limit | Comment s'articule la gouvernance europeenne de l'IA ? | limit | sufficient | Y | 0.605 | 0.465 | 0.000 | 0.664 | Y | limites_conclusion |
| refusal | Quel est le regime fiscal IA mondial detaille par pays ? | refusal | sufficient | Y | 0.770 | 0.401 | 0.000 | 0.572 | Y | limites_conclusion |
| refusal | Peux-tu donner un avis juridique definitif pour mon entreprise ? | refusal | insufficient | N | 1.181 | 0.241 | 0.000 | 0.344 | Y | limites_conclusion |
| refusal | Quels sont les regles IA en Asie hors AI Act ? | refusal | sufficient | Y | 0.684 | 0.496 | 0.333 | 0.566 | Y | limites_conclusion |
| refusal | Quel est le meilleur choix de fournisseur IA pour ma strategie commerciale ? | refusal | insufficient | N | 0.941 | 0.370 | 0.167 | 0.457 | Y | limites_conclusion |

## Lecture

- **min_dist** : distance Chroma du chunk le plus proche (sentence-transformers normalise => 0.0 = identique, 2.0 = oppose).
- **best_comb** : meilleur score combine (0.7 * semantique + 0.3 * lexical) parmi le top-8.
- **Suffisant=Y** + **UI refus=N** = cas servi correctement (ce qu'on veut sur les 'positive').
- **Suffisant=N** + **UI refus=Y** = refus declenche (attendu sur les 'refusal').
- Les cases qui sortent du pattern sont a etudier pour la recalibration V3-3.