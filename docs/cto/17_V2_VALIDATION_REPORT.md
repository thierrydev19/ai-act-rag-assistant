# Rapport final validation V2

- Reference officielle: docs/cto/17_GRILLE_V2_QUESTIONS_PME_VALIDATION.md
- Questions evaluees: 20
- Taux reussite (score 1 ou 2): 100.0%
- Score moyen: 1.55/2
- Demos prioritaires (Q1,Q5,Q6,Q11,Q20): True
- Sources exploitables sur demos: True
- Refus honnetes maitrises: True
- Decision finale V2: **cloturee**
- Motif: Seuils V2 atteints: taux >=80%, demos prioritaires maitrisees, refus propre.

## Detail par question

| QID | Intent attendu | Intent observe | Refus | Score | Sources | Notes |
|---|---|---|---|---|---|---|
| Q1 | applicability_perimetre | applicability_perimetre | False | 2 | True | Reponse contextualisee, sourcee et prudente. |
| Q2 | applicability_perimetre | obligations_entreprise | False | 1 | True | Reponse partielle acceptable mais alignement intent perfectible. |
| Q3 | applicability_perimetre | applicability_perimetre | False | 2 | True | Reponse contextualisee, sourcee et prudente. |
| Q4 | applicability_perimetre | limites_conclusion | False | 1 | True | Reponse partielle acceptable mais alignement intent perfectible. |
| Q5 | qualification_systeme | limites_conclusion | False | 1 | True | Reponse partielle acceptable mais alignement intent perfectible. |
| Q6 | qualification_systeme | limites_conclusion | False | 1 | True | Reponse partielle acceptable mais alignement intent perfectible. |
| Q7 | qualification_systeme | limites_conclusion | False | 1 | True | Reponse partielle acceptable mais alignement intent perfectible. |
| Q8 | qualification_systeme | limites_conclusion | False | 1 | True | Reponse partielle acceptable mais alignement intent perfectible. |
| Q9 | obligations_entreprise | obligations_entreprise | False | 2 | True | Reponse contextualisee, sourcee et prudente. |
| Q10 | obligations_entreprise | applicability_perimetre | False | 1 | True | Reponse partielle acceptable mais alignement intent perfectible. |
| Q11 | obligations_entreprise | limites_conclusion | False | 1 | True | Reponse partielle acceptable mais alignement intent perfectible. |
| Q12 | documentation_preuves | limites_conclusion | False | 1 | True | Reponse partielle acceptable mais alignement intent perfectible. |
| Q13 | transparence_information | transparence_information | False | 2 | True | Reponse contextualisee, sourcee et prudente. |
| Q14 | transparence_information | transparence_information | False | 2 | True | Reponse contextualisee, sourcee et prudente. |
| Q15 | transparence_information | transparence_information | False | 2 | True | Reponse contextualisee, sourcee et prudente. |
| Q16 | documentation_preuves | documentation_preuves | False | 2 | True | Reponse contextualisee, sourcee et prudente. |
| Q17 | role_entreprise | role_entreprise | False | 2 | True | Reponse contextualisee, sourcee et prudente. |
| Q18 | role_entreprise | role_entreprise | False | 2 | True | Reponse contextualisee, sourcee et prudente. |
| Q19 | role_entreprise | role_entreprise | False | 2 | True | Reponse contextualisee, sourcee et prudente. |
| Q20 | limites_conclusion | limites_conclusion | True | 2 | False | Refus attendu. |

## Lot question_mode - reponses prioritaires

### Q1 (score 2/2, mode=applicability_gate)

**Question:** Nous sommes une PME qui utilise ChatGPT pour rediger des emails et des comptes rendus internes. Est-ce que l'AI Act nous concerne ?

**Reponse simple:** Pas automatiquement : le champ d'application depend de votre usage concret, de votre role et du contexte d'exploitation.

**Sources:** AI Act - page 113-114; AI Act - page 26

### Q5 (score 1/2, mode=yes_no_non_automatic)

**Question:** Nous utilisons une IA pour trier des CV avant entretien. Est-ce que cela peut etre considere comme un systeme a haut risque ?

**Reponse simple:** Non, pas automatiquement. Il faut d'abord qualifier l'usage exact, le role de votre entreprise et verifier si une categorie regulatoire sensible s'applique.

**Sources:** AI Act - page 26; AI Act - page 19

### Q6 (score 1/2, mode=yes_no_non_automatic)

**Question:** Nous avons un chatbot sur notre site web qui repond aux questions clients. Est-ce automatiquement un systeme a haut risque ?

**Reponse simple:** Non, pas automatiquement. Il faut d'abord qualifier l'usage exact, le role de votre entreprise et verifier si une categorie regulatoire sensible s'applique.

**Sources:** AI Act - page 24-25; AI Act - page 68

### Q9 (score 2/2, mode=obligation_prioritization)

**Question:** Si notre usage d'IA entre dans le champ de l'AI Act, qu'est-ce qu'un dirigeant PME doit verifier en premier ?

**Reponse simple:** En premier, clarifiez role, qualification du systeme et niveau de risque ; ensuite seulement les familles d'obligations a verifier.

**Sources:** AI Act - Article 2 - page 45; AI Act - page 24-25

### Q17 (score 2/2, mode=role_determination)

**Question:** Comment savoir si notre PME est plutot fournisseur, deployeur ou simple utilisatrice au sens de l'AI Act ?

**Reponse simple:** Votre role probable (fournisseur, deployeur ou autre) depend de qui met le systeme sur le marche et de qui l'exploite ; les sources aident a cadrer cette distinction.

**Sources:** AI Act - page 47-48; AI Act - page 134-135

### Q20 (score 2/2, mode=forbidden_compliance_conclusion)

**Question:** Pouvez-vous me dire si mon entreprise est conforme a l'AI Act aujourd'hui, oui ou non ?

**Reponse simple:** Je ne peux pas conclure de maniere fiable a partir du corpus charge pour cette question.

