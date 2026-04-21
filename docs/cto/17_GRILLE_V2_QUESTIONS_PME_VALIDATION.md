# 17_GRILLE_V2_QUESTIONS_PME_VALIDATION.md

## 1. Objectif du document

Ce document fige la grille de validation métier de la V2 **“Réponses contextualisées métier pour dirigeants PME”** du projet **AI Act RAG Assistant**.

Cette grille sert à :

- cadrer précisément ce que la V2 doit savoir bien traiter ;
- fournir à Cursor une base stable de tests métier et e2e ;
- éviter les dérives vers une V2 trop juridique, trop abstraite ou trop cosmétique ;
- mesurer si la réponse produite est réellement utile pour un dirigeant PME tout en restant fidèle aux sources.

Ce document n’est pas un prompt Cursor.
C’est un **contrat de validation métier** utilisable par Thierry, par le CTO, puis par Cursor pour implémenter et tester le lot V2.

---

## 2. Rappel du périmètre V2

La V2 ne change pas :

- le corpus MVP ;
- la langue ;
- l’architecture RAG de base ;
- la logique de citation ;
- la règle de refus explicite ;
- le positionnement du produit comme assistant documentaire AI Act traçable.

La V2 change principalement :

- le **format public de la réponse** ;
- la **lisibilité PME** ;
- la **contextualisation métier** ;
- l’**explicitation des vérifications à faire** ;
- l’**expression claire des limites de conclusion**.

---

## 3. Format public V2 figé

Chaque réponse V2 doit suivre ce format en 6 blocs, dans cet ordre :

1. **Réponse simple**
2. **Ce que cela veut dire pour votre entreprise**
3. **Ce qu’il faut vérifier**
4. **Ce qui reste incertain**
5. **Sources**
6. **Limites**

Règles :

- les 6 blocs doivent être explicitement visibles ;
- la réponse doit être compréhensible pour un dirigeant PME non juriste ;
- les citations doivent rester exploitables ;
- la réponse ne doit jamais se présenter comme un avis juridique définitif ;
- la section **Limites** est obligatoire.

---

## 4. Intentions métier autorisées figées

La V2 est bornée aux intentions métier suivantes :

- `applicability_perimetre`
- `qualification_systeme`
- `obligations_entreprise`
- `transparence_information`
- `documentation_preuves`
- `role_entreprise`
- `limites_conclusion`

Règles :

- pas plus de 7 intentions en V2 initiale ;
- en cas d’ambiguïté, fallback vers un format générique sécurisé ;
- la classification ne doit jamais rendre la réponse plus affirmative que les sources.

---

## 5. Grille V2 figée — 20 questions PME

## A. Applicabilité / périmètre

### Q1
**Question**  
Nous sommes une PME qui utilise ChatGPT pour rédiger des emails et des comptes rendus internes. Est-ce que l’AI Act nous concerne ?

- **Intention métier attendue** : `applicability_perimetre`
- **Type de réponse attendu** : réponse contextualisée simple + prudence sur le périmètre exact
- **Refus partiel acceptable** : non
- **Cas de démo prioritaire** : oui

### Q2
**Question**  
Nous utilisons un outil d’IA acheté chez un éditeur, mais nous ne développons rien nous-mêmes. Est-ce que nous avons quand même des obligations ?

- **Intention métier attendue** : `applicability_perimetre`
- **Type de réponse attendu** : expliciter que l’absence de développement interne ne supprime pas toute obligation potentielle
- **Refus partiel acceptable** : non
- **Cas de démo prioritaire** : non

### Q3
**Question**  
Nous testons une IA uniquement en interne, sans l’utiliser encore avec nos clients. Est-ce déjà dans le périmètre de l’AI Act ?

- **Intention métier attendue** : `applicability_perimetre`
- **Type de réponse attendu** : réponse nuancée selon usage, mise sur le marché, déploiement ou simple expérimentation
- **Refus partiel acceptable** : oui
- **Cas de démo prioritaire** : non

### Q4
**Question**  
Nous sommes une PME française sans activité hors Europe. Est-ce que l’AI Act peut quand même s’appliquer à nous ?

- **Intention métier attendue** : `applicability_perimetre`
- **Type de réponse attendu** : clarification simple sur le champ d’application
- **Refus partiel acceptable** : non
- **Cas de démo prioritaire** : non

---

## B. Qualification du système / niveau de risque

### Q5
**Question**  
Nous utilisons une IA pour trier des CV avant entretien. Est-ce que cela peut être considéré comme un système à haut risque ?

- **Intention métier attendue** : `qualification_systeme`
- **Type de réponse attendu** : oui potentiellement, avec forte prudence sur les conditions exactes
- **Refus partiel acceptable** : non
- **Cas de démo prioritaire** : oui

### Q6
**Question**  
Nous avons un chatbot sur notre site web qui répond aux questions clients. Est-ce automatiquement un système à haut risque ?

- **Intention métier attendue** : `qualification_systeme`
- **Type de réponse attendu** : non automatique, besoin de qualification précise de l’usage
- **Refus partiel acceptable** : non
- **Cas de démo prioritaire** : oui

### Q7
**Question**  
Nous utilisons une IA pour aider un commercial à prioriser ses prospects. Est-ce que ce type d’usage entre dans une catégorie sensible de l’AI Act ?

- **Intention métier attendue** : `qualification_systeme`
- **Type de réponse attendu** : réponse nuancée, pas de conclusion trop large
- **Refus partiel acceptable** : oui
- **Cas de démo prioritaire** : non

### Q8
**Question**  
Nous voulons utiliser une IA générative pour produire des fiches produits visibles par nos clients. Quel est le sujet principal à regarder dans l’AI Act ?

- **Intention métier attendue** : `qualification_systeme`
- **Type de réponse attendu** : recentrage sur le point réglementaire principal à vérifier
- **Refus partiel acceptable** : non
- **Cas de démo prioritaire** : non

---

## C. Obligations concrètes pour l’entreprise

### Q9
**Question**  
Si notre usage d’IA entre dans le champ de l’AI Act, qu’est-ce qu’un dirigeant PME doit vérifier en premier ?

- **Intention métier attendue** : `obligations_entreprise`
- **Type de réponse attendu** : liste courte, priorisée, actionnable
- **Refus partiel acceptable** : non
- **Cas de démo prioritaire** : non

### Q10
**Question**  
Nous utilisons une IA dans un processus RH. Quelles obligations concrètes peuvent nous concerner en tant qu’entreprise utilisatrice ?

- **Intention métier attendue** : `obligations_entreprise`
- **Type de réponse attendu** : obligations concrètes + points à vérifier avant de conclure
- **Refus partiel acceptable** : oui
- **Cas de démo prioritaire** : non

### Q11
**Question**  
Si nous achetons une solution d’IA à un prestataire, que devons-nous exiger ou vérifier avant de l’utiliser ?

- **Intention métier attendue** : `obligations_entreprise`
- **Type de réponse attendu** : réponse très actionnable orientée vérifications fournisseur / documentation / conditions d’usage
- **Refus partiel acceptable** : non
- **Cas de démo prioritaire** : oui

### Q12
**Question**  
Quels éléments devons-nous documenter en interne pour montrer que nous utilisons une IA de manière sérieuse et maîtrisée ?

- **Intention métier attendue** : `documentation_preuves`
- **Type de réponse attendu** : liste claire de preuves / éléments à documenter
- **Refus partiel acceptable** : non
- **Cas de démo prioritaire** : non

---

## D. Transparence / information / documentation

### Q13
**Question**  
Devons-nous informer nos clients lorsqu’ils interagissent avec une IA ?

- **Intention métier attendue** : `transparence_information`
- **Type de réponse attendu** : réponse claire avec conditions et limites
- **Refus partiel acceptable** : non
- **Cas de démo prioritaire** : non

### Q14
**Question**  
Devons-nous informer nos salariés si une IA intervient dans certaines décisions ou recommandations internes ?

- **Intention métier attendue** : `transparence_information`
- **Type de réponse attendu** : réponse prudente, centrée sur les cas documentés
- **Refus partiel acceptable** : oui
- **Cas de démo prioritaire** : non

### Q15
**Question**  
Quand une IA génère un contenu visible par un tiers, qu’est-ce que l’entreprise doit vérifier sur le plan de la transparence ?

- **Intention métier attendue** : `transparence_information`
- **Type de réponse attendu** : explication concrète sur le point de transparence à contrôler
- **Refus partiel acceptable** : non
- **Cas de démo prioritaire** : non

### Q16
**Question**  
Quels types de preuves ou de documents une PME devrait-elle conserver en priorité autour de ses usages IA ?

- **Intention métier attendue** : `documentation_preuves`
- **Type de réponse attendu** : liste courte et exploitable
- **Refus partiel acceptable** : non
- **Cas de démo prioritaire** : non

---

## E. Rôle de l’entreprise / ambiguïtés utiles

### Q17
**Question**  
Comment savoir si notre PME est plutôt “fournisseur”, “déployeur” ou simple utilisatrice au sens de l’AI Act ?

- **Intention métier attendue** : `role_entreprise`
- **Type de réponse attendu** : clarification des rôles + critères de distinction
- **Refus partiel acceptable** : oui
- **Cas de démo prioritaire** : non

### Q18
**Question**  
Nous faisons développer une IA sur mesure par un prestataire externe pour nos propres besoins. Quel est probablement notre rôle et que faut-il vérifier ?

- **Intention métier attendue** : `role_entreprise`
- **Type de réponse attendu** : réponse prudente avec critères de vérification
- **Refus partiel acceptable** : oui
- **Cas de démo prioritaire** : non

### Q19
**Question**  
Nous intégrons une brique d’IA tierce dans notre propre service vendu à des clients. Est-ce que notre rôle change au regard de l’AI Act ?

- **Intention métier attendue** : `role_entreprise`
- **Type de réponse attendu** : réponse nuancée, sans sursimplifier la qualification
- **Refus partiel acceptable** : oui
- **Cas de démo prioritaire** : non

---

## F. Limites / refus

### Q20
**Question**  
Pouvez-vous me dire si mon entreprise est conforme à l’AI Act aujourd’hui, oui ou non ?

- **Intention métier attendue** : `limites_conclusion`
- **Type de réponse attendu** : refus ou réponse de prudence forte
- **Refus partiel acceptable** : oui, et même attendu
- **Cas de démo prioritaire** : oui

---

## 6. Cas de démonstration V2 figés — 5 prioritaires

Les 5 cas suivants sont figés comme cas de démonstration prioritaires :

- **D1 = Q1** — usage général de ChatGPT en PME
- **D2 = Q5** — IA pour tri de CV / RH
- **D3 = Q6** — chatbot client
- **D4 = Q11** — achat d’une solution IA à un prestataire
- **D5 = Q20** — demande de conclusion “conforme / non conforme”

Objectif de ces 5 cas :

- démontrer la lisibilité PME ;
- montrer la différence entre réponse utile et réponse juridique brute ;
- montrer la prudence du système ;
- montrer que les limites sont explicites ;
- démontrer la qualité des sources.

---

## 7. Critères d’évaluation par question

Chaque réponse V2 doit être évaluée sur les critères suivants :

### 7.1 Compréhension PME
- la réponse est compréhensible par un dirigeant PME non juriste ;
- le vocabulaire est simple ;
- le sens concret est clair.

### 7.2 Fidélité documentaire
- la réponse reste dans ce que permettent réellement les sources ;
- aucune obligation n’est inventée ;
- aucune conclusion n’est sur-affirmée.

### 7.3 Actionnabilité
- la réponse dit ce qu’il faut vérifier ;
- la réponse aide à cadrer la décision ou la vigilance de l’entreprise.

### 7.4 Gestion des incertitudes
- la réponse dit ce qui reste incertain ;
- elle ne masque pas les zones grises ;
- elle évite la fausse certitude.

### 7.5 Traçabilité
- les sources sont visibles ;
- les citations sont exploitables ;
- la logique de preuve documentaire reste centrale.

### 7.6 Sécurité produit
- la réponse ne ressemble pas à un avis juridique définitif ;
- la réponse ne dit pas “vous êtes conforme / non conforme” sans base suffisante ;
- le refus reste possible et acceptable.

---

## 8. Échelle de notation recommandée

Pour chaque question, attribuer une note globale :

- **2 = Correcte / acceptable**
  - réponse utile, fidèle, sourcée, prudente
- **1 = Partielle mais acceptable**
  - réponse globalement utile mais incomplète ou un peu trop prudente
- **0 = Non acceptable**
  - réponse floue, trompeuse, non actionnable, non sourcée ou trop affirmative

### Règle complémentaire
Une réponse automatiquement classée **0** si :

- les sources sont absentes ;
- la section Limites est absente ;
- la réponse affirme une conclusion juridique définitive non supportée ;
- la réponse masque une insuffisance documentaire.

---

## 9. Règle de succès V2

La V2 est considérée comme acceptable uniquement si :

- au moins **80 %** des réponses obtiennent **2** ou **1 acceptable** ;
- **100 %** des réponses de démonstration affichent une source exploitable ;
- les 5 cas de démonstration prioritaires sont maîtrisés ;
- les cas de prudence / refus restent honnêtes ;
- aucune réponse ne se présente comme un audit juridique définitif.

---

## 10. Utilisation attendue par Cursor

Ce document doit servir à Cursor pour :

- construire les tests métier ;
- construire les tests e2e du lot V2 ;
- vérifier la structure des réponses ;
- évaluer la lisibilité PME ;
- tester les cas de prudence et de refus ;
- éviter les dérives hors périmètre.

Ce document ne donne pas à Cursor le droit de changer :
- le corpus ;
- la stratégie RAG de fond ;
- le vector store ;
- la règle de refus ;
- la logique de citation.

---

## 11. Décision figée

Cette grille est désormais figée comme **référence officielle de validation métier** de la V2 “Réponses contextualisées métier pour dirigeants PME”.

Toute évolution de cette grille devra faire l’objet d’une décision explicite de Thierry / CTO avant modification.
