# Lot V3-3a — Rapport Quality Gate officiel sur grille canonique 15 questions

Etat : V3-3a (sentence-transformers + retrieval recalibre min_combined_score=0.385)

Corpus : AI Act FR officiel (UE 2024/1689), 144 pages, 230 chunks

---

# Lot 10 - Grille qualite MVP

- Decision: **montrable**
- Motif: La grille lot 10 est satisfaite sur les criteres minimums.
- Taux acceptable: 80.0%
- Demo sources exploitables: True
- Refus corrects: True
- Stabilite: True
- Temps max (s): 0.078
- Temps moyen (s): 0.045
- Lisibilite PME (format): True

## Evaluation detaillee

| Question | Statut attendu | Statut observe | Qualite reponse | Qualite citations | Verdict | Remarques | Latence (s) |
|---|---|---|---|---|---|---|---|
| Quelles obligations de transparence pour les systemes IA ? | positive | positive | bonne | bonne | correct | retrieval=sufficient; citations=3; keyword_hits=2 | 0.078 |
| Quelles sanctions sont prevues en cas de violation ? | positive | positive | bonne | bonne | insuffisant | retrieval=sufficient; citations=3; keyword_hits=0 | 0.038 |
| Comment le reglement definit un systeme IA ? | positive | positive | bonne | bonne | correct | retrieval=sufficient; citations=3; keyword_hits=1 | 0.057 |
| Quelles obligations existent pour les systemes IA a haut risque ? | positive | positive | bonne | bonne | correct | retrieval=sufficient; citations=3; keyword_hits=2 | 0.057 |
| Que faut-il verifier avant de mettre un systeme IA sur le marche ? | positive | positive | bonne | bonne | correct | retrieval=sufficient; citations=3; keyword_hits=2 | 0.050 |
| Que prevoit le texte pour la surveillance des systemes IA ? | positive | positive | bonne | bonne | correct | retrieval=sufficient; citations=3; keyword_hits=1 | 0.042 |
| Que dit l'AI Act sur les voies de recours ? | positive | positive | bonne | bonne | insuffisant | retrieval=sufficient; citations=3; keyword_hits=0 | 0.041 |
| Quels points de conformite sont attendus pour les fournisseurs ? | positive | refusal | bonne | n/a | insuffisant | retrieval=sufficient; citations=0; keyword_hits=1 | 0.041 |
| Quelles obligations pour les importateurs de systemes IA ? | limit | positive | bonne | bonne | correct | retrieval=sufficient; citations=3; keyword_hits=2 | 0.054 |
| Que dit le texte sur les obligations des deployeurs ? | limit | positive | bonne | bonne | correct | retrieval=sufficient; citations=3; keyword_hits=1 | 0.041 |
| Comment s'articule la gouvernance europeenne de l'IA ? | limit | refusal | bonne | n/a | partiellement correct acceptable | retrieval=sufficient; citations=0; keyword_hits=0 | 0.043 |
| Quel est le regime fiscal IA mondial detaille par pays ? | refusal | refusal | bonne | n/a | correct | retrieval=sufficient; citations=0; keyword_hits=0 | 0.032 |
| Peux-tu donner un avis juridique definitif pour mon entreprise ? | refusal | refusal | bonne | n/a | correct | retrieval=insufficient; citations=0; keyword_hits=2 | 0.031 |
| Quels sont les regles IA en Asie hors AI Act ? | refusal | refusal | bonne | n/a | correct | retrieval=sufficient; citations=0; keyword_hits=1 | 0.034 |
| Quel est le meilleur choix de fournisseur IA pour ma strategie commerciale ? | refusal | refusal | bonne | n/a | correct | retrieval=insufficient; citations=0; keyword_hits=0 | 0.038 |