# 10 - Prompts Cursor d’implémentation par lot

## 1. Objectif des prompts Cursor

Donner à Cursor une série d’instructions **prêtes à exécuter**, découpées en petits lots contrôlés, pour implémenter le MVP AI Act RAG Assistant sans redéfinir l’architecture, sans élargir le périmètre et sans introduire de complexité SaaS prématurée. L’objectif est d’obtenir une chaîne documentaire fiable, traçable et démontrable, pas un prototype opaque ni une surconstruction technique.

## 2. Règles d’utilisation des prompts

- exécuter **un seul lot à la fois**
- ne jamais fusionner plusieurs lots critiques
- ne pas modifier l’architecture décidée
- ne pas élargir le périmètre produit
- produire du code **strictement borné au lot demandé**
- exécuter les tests et vérifications demandés dans le lot
- ne pas considérer un lot comme DONE sans ses critères de validation
- en cas d’ambiguïté structurelle, **stopper** et remonter le point
- ne pas introduire de composants SaaS non demandés
- ne pas écrire de “solution alternative” sans validation CTO

## 3. Découpage en lots d’implémentation

### Lot 1 — Socle projet MVP

### Lot 2 — Ingestion du texte officiel AI Act

### Lot 3 — Métadonnées documentaires minimales

### Lot 4 — Chunking juridique

### Lot 5 — Embeddings + stockage vectoriel

### Lot 6 — Retrieval sur question utilisateur

### Lot 7 — Génération contrainte + citations + refus

### Lot 8 — Première preuve de bout en bout

### Lot 9 — Interface vitrine scénarisée

### Lot 10 — Fiabilisation démo + grille qualité MVP

## 4. Un prompt Cursor complet par lot

## Prompt Lot 1 — Socle projet MVP

```
Rôle
Tu es le développeur exécutant du projet AI Act RAG Assistant.
Tu implémentes strictement le lot demandé.
Tu ne redéfinis ni l’architecture, ni le périmètre produit.

Objectif
Mettre en place le socle projet MVP propre, simple, modulaire et réutilisable, sans complexité SaaS prématurée.

Périmètre
Créer la structure de base du projet pour séparer clairement :
- ingestion documentaire
- structuration / métadonnées
- chunking
- embeddings / stockage vectoriel
- retrieval
- génération de réponse
- interface vitrine
- logs simples
- tests

Fichiers / modules visés
Si le repo est vide ou partiel, créer une structure simple de ce type :
- app/
- app/ingestion/
- app/document/
- app/chunking/
- app/embeddings/
- app/retrieval/
- app/generation/
- app/ui/
- app/logging/
- tests/

Changements attendus
- structure de modules claire
- responsabilités séparées
- aucun code métier SaaS
- aucune auth
- aucun multi-tenant
- aucune logique multi-corpus
- base de projet lisible pour la suite

Tests attendus
- vérification que la structure projet est cohérente
- vérification qu’aucun module critique n’est mélangé dans un seul fichier monolithique
- vérification que les imports de base ne cassent pas le projet

Critères DONE
- structure de projet créée
- frontières de responsabilité lisibles
- aucun composant hors périmètre MVP
- base exploitable pour le lot 2

Interdits
- ne pas implémenter encore le pipeline complet
- ne pas coder de logique SaaS
- ne pas improviser un framework complexe
- ne pas créer une architecture microservices
- ne pas ajouter des composants non demandés

Livrable attendu
- arborescence créée
- bref résumé des fichiers créés
- liste des points potentiellement ambigus bloquants s’il y en a
```

## Prompt Lot 2 — Ingestion du texte officiel AI Act

```
Rôle
Tu es le développeur exécutant du projet AI Act RAG Assistant.
Tu implémentes strictement le lot demandé.

Objectif
Implémenter l’ingestion du texte officiel AI Act retenu pour le MVP, en français, avec extraction exploitable du texte et des pages.

Périmètre
À partir du document source officiel validé, produire une ingestion simple et fiable qui :
- charge le document
- extrait le texte
- conserve l’identification des pages
- prépare une base documentaire brute exploitable

Fichiers / modules visés
- app/ingestion/
- éventuellement app/document/
- tests/ liés à l’ingestion

Changements attendus
- pipeline d’ingestion simple
- extraction texte exploitable
- identification des pages
- aucun enrichissement encore complexe

Tests attendus
- test sur le document officiel AI Act
- vérification manuelle ou automatisée sur un petit échantillon de pages
- vérification que le texte extrait n’est pas vide
- vérification que les pages sont correctement repérées

Critères DONE
- document chargé correctement
- texte extrait de manière exploitable
- pages identifiables
- base documentaire brute disponible pour structuration

Interdits
- ne pas introduire OCR complexe
- ne pas gérer plusieurs documents
- ne pas ajouter de logique de chunking ici
- ne pas masquer une mauvaise extraction

Livrable attendu
- code du module d’ingestion
- test(s) de validation
- exemple de sortie d’ingestion sur quelques pages
- limites observées s’il y en a
```

## Prompt Lot 3 — Métadonnées documentaires minimales

```
Rôle
Tu es le développeur exécutant du projet AI Act RAG Assistant.
Tu n’improvises pas de schéma alternatif.

Objectif
Associer au texte ingéré les métadonnées minimales obligatoires du MVP pour garantir la traçabilité.

Périmètre
Implémenter le schéma minimal permettant de rattacher chaque unité documentaire exploitable à :
- document_id
- document_title
- page_number
- article_ref
- section_ref si disponible
- language
- version_date
- source_type
- chunk_text ou texte intermédiaire
- chunk_index plus tard si applicable

Fichiers / modules visés
- app/document/
- éventuellement app/ingestion/
- tests/document/

Changements attendus
- représentation structurée des unités documentaires
- métadonnées cohérentes
- traçabilité exploitable en aval

Tests attendus
- vérification sur un échantillon d’articles / pages
- vérification que les champs minimaux sont bien présents
- vérification que page, article et section ne sont pas inventés

Critères DONE
- métadonnées minimales implémentées
- données documentaires traçables
- base compatible avec le chunking

Interdits
- ne pas enrichir avec des métadonnées SaaS
- ne pas ajouter de champs décoratifs non fiables
- ne pas remplir des champs incertains “pour faire joli”

Livrable attendu
- structure documentaire avec métadonnées minimales
- tests ou vérifications
- exemples concrets de sorties structurées
```

## Prompt Lot 4 — Chunking juridique

```
Rôle
Tu es le développeur exécutant du projet AI Act RAG Assistant.
Tu appliques strictement la stratégie de chunking validée.

Objectif
Implémenter le chunking juridique du texte AI Act pour produire des chunks courts à moyens, précis, citables, avec léger overlap.

Périmètre
Appliquer les règles validées :
- chunks courts à moyens
- cible 400 à 800 mots max au départ
- priorité à la précision des citations
- ne pas casser un article sauf s’il devient trop long
- découpage interne par paragraphe, alinéa, liste, sous-section si nécessaire
- overlap léger de 10 à 15 %

Fichiers / modules visés
- app/chunking/
- éventuellement app/document/
- tests/chunking/

Changements attendus
- génération de chunks juridiquement cohérents
- conservation du lien avec document, article, page, chunk_index
- pas de découpage arbitraire purement technique

Tests attendus
- revue sur plusieurs articles courts et longs
- vérification que les articles courts restent entiers si raisonnable
- vérification que les articles longs sont découpés logiquement
- vérification de la présence de chunk_index
- vérification du léger overlap

Critères DONE
- chunks cohérents et citables
- lien source préservé
- découpage conforme à la stratégie validée

Interdits
- ne pas faire un découpage uniquement par taille fixe
- ne pas casser la logique juridique
- ne pas perdre la traçabilité
- ne pas fusionner plusieurs articles sans justification validée

Livrable attendu
- module de chunking
- exemples de chunks produits
- résultats de test / vérification sur cas représentatifs
```

## Prompt Lot 5 — Embeddings + stockage vectoriel

```
Rôle
Tu es le développeur exécutant du projet AI Act RAG Assistant.

Objectif
Indexer les chunks avec leurs embeddings et leurs métadonnées dans le vector store MVP retenu.

Périmètre
- générer les embeddings des chunks
- stocker embeddings + chunk_text + métadonnées
- garder une structure simple et propre compatible MVP

Fichiers / modules visés
- app/embeddings/
- app/retrieval/ ou module store dédié
- tests/embeddings/
- tests/store/

Changements attendus
- pipeline d’indexation fonctionnel
- conservation du lien fort entre chunk et métadonnées
- stockage interrogeable simplement

Tests attendus
- vérification qu’un chunk indexé peut être récupéré avec ses métadonnées
- test simple de persistance / chargement
- vérification que les embeddings sont bien générés pour les chunks attendus

Critères DONE
- index vectoriel MVP opérationnel
- chunks et métadonnées liés correctement
- base prête pour le retrieval

Interdits
- ne pas changer le vector store décidé pour le MVP
- ne pas ajouter de stratégie multi-store
- ne pas casser le lien entre texte et source

Livrable attendu
- module embeddings + indexation
- tests
- exemple d’un enregistrement indexé récupérable
```

## Prompt Lot 6 — Retrieval sur question utilisateur

```
Rôle
Tu es le développeur exécutant du projet AI Act RAG Assistant.

Objectif
Implémenter la recherche sémantique sur question utilisateur pour retrouver les meilleurs extraits documentaires.

Périmètre
- prendre une question utilisateur
- générer son embedding
- interroger le vector store
- retourner les meilleurs extraits avec métadonnées
- préparer la distinction base suffisante / insuffisante

Fichiers / modules visés
- app/retrieval/
- tests/retrieval/

Changements attendus
- retrieval fonctionnel
- sortie traçable
- extraits lisibles et exploitables pour la génération

Tests attendus
- test sur plusieurs questions de démonstration validées
- vérification humaine de la pertinence des extraits
- vérification que chaque extrait retourné reste correctement citable

Critères DONE
- retrieval fonctionnel sur questions réelles
- extraits pertinents dans une majorité de cas initiaux
- sortie exploitable pour génération et refus

Interdits
- ne pas générer encore la réponse finale ici
- ne pas compenser un retrieval faible par des hypothèses LLM
- ne pas retourner des extraits sans métadonnées exploitables

Livrable attendu
- module de retrieval
- résultats sur plusieurs questions de démonstration
- signalement clair des limites observées
```

## Prompt Lot 7 — Génération contrainte + citations + refus

```
Rôle
Tu es le développeur exécutant du projet AI Act RAG Assistant.

Objectif
Produire une réponse professionnelle fondée uniquement sur les extraits retrouvés, avec citations explicites et refus clair si la base est insuffisante.

Périmètre
- construire un prompt contraint
- injecter uniquement les extraits retrouvés
- imposer le ton professionnel
- imposer les citations
- implémenter la règle de refus explicite

Fichiers / modules visés
- app/generation/
- éventuellement app/retrieval/
- tests/generation/

Changements attendus
- réponse bornée aux sources
- citations publiques explicites
- refus clair si la base ne permet pas de conclure

Tests attendus
- test sur questions documentées
- test sur questions qui doivent conduire à un refus
- vérification que les citations affichées correspondent bien aux extraits utilisés
- vérification que la réponse n’invente pas hors source

Critères DONE
- réponse professionnelle sourcée
- citation page + article/section cohérents quand disponibles
- refus explicite fonctionnel
- comportement borné

Interdits
- ne pas laisser le LLM improviser hors source
- ne pas masquer une insuffisance documentaire
- ne pas produire de citations approximatives
- ne pas transformer la réponse en avis juridique définitif

Livrable attendu
- module de génération
- exemples de réponses
- exemples de refus
- vérifications de cohérence citation/source
```

## Prompt Lot 8 — Première preuve de bout en bout

```
Rôle
Tu es le développeur exécutant du projet AI Act RAG Assistant.

Objectif
Valider la première preuve de fonctionnement utile : une question posée, une réponse obtenue, une source vérifiable affichée.

Périmètre
Assembler les briques existantes pour obtenir un flux complet :
question -> retrieval -> génération -> citations -> vérification simple

Fichiers / modules visés
- assemblage des modules déjà créés
- tests/e2e/ ou équivalent simple

Changements attendus
- première exécution de bout en bout
- sortie vérifiable humainement
- base de confiance pour continuer

Tests attendus
- exécution complète sur au moins une question de démonstration
- vérification humaine de la citation
- vérification que la réponse correspond bien aux extraits récupérés

Critères DONE
- une première question/réponse sourcée de bout en bout fonctionne
- la source est vérifiable
- le flux ne casse pas

Interdits
- ne pas considérer “pipeline construit” comme suffisant
- ne pas maquiller les résultats
- ne pas sauter les vérifications humaines

Livrable attendu
- scénario de preuve de bout en bout
- résultat observé
- limites résiduelles avant interface vitrine
```

## Prompt Lot 9 — Interface vitrine scénarisée

```
Rôle
Tu es le développeur exécutant du projet AI Act RAG Assistant.

Objectif
Construire l’interface vitrine simple et scénarisée qui expose la valeur du MVP sans le transformer en produit SaaS complet.

Périmètre
- interface simple
- saisie de question
- affichage de réponse
- affichage de citations
- affichage du refus si nécessaire
- préparation de 3 à 5 cas de démonstration maîtrisés

Fichiers / modules visés
- app/ui/
- éventuellement app/generation/ ou orchestration légère
- tests/ui/ si applicable

Changements attendus
- parcours de démonstration fluide
- affichage lisible pour dirigeants PME et consultants
- mise en avant de la preuve documentaire

Tests attendus
- test du parcours complet
- test sur plusieurs cas préparés
- vérification de lisibilité et stabilité
- vérification que l’interface ne masque pas les limites réelles

Critères DONE
- interface vitrine utilisable
- question / réponse / citations / refus visibles proprement
- cas de démonstration préparés

Interdits
- ne pas construire un front SaaS complet
- ne pas ajouter auth, comptes, backoffice
- ne pas privilégier l’esthétique au détriment de la preuve documentaire
- ne pas contourner les limites du système via l’UI

Livrable attendu
- interface vitrine fonctionnelle
- liste des cas de démonstration préparés
- points UX éventuellement à revoir
```

## Prompt Lot 10 — Fiabilisation démo + grille qualité MVP

```
Rôle
Tu es le développeur exécutant du projet AI Act RAG Assistant.

Objectif
Fiabiliser le MVP et le confronter à la grille qualité définie pour déterminer s’il est montrable.

Périmètre
- exécuter les questions de démonstration
- exécuter les cas de refus
- vérifier citations, stabilité, temps de réponse
- corriger les défauts critiques bloquants
- documenter les écarts restants

Fichiers / modules visés
- tous les modules concernés par corrections ciblées
- tests/
- éventuellement document de synthèse de résultats

Changements attendus
- amélioration ciblée
- stabilisation de la démo
- mesure du niveau de qualité MVP

Tests attendus
- jeu de 15 à 20 questions
- vérification du taux de réponses correctes / partiellement correctes acceptables
- vérification 100 % des citations de démo
- vérification refus
- vérification temps de réponse < 10 s en démo
- vérification absence de crash

Critères DONE
- seuil MVP montrable atteint
- démo stable
- 3 à 5 cas maîtrisés à l’avance
- rapport clair sur ce qui est OK et ce qui reste limité

Interdits
- ne pas déclarer le MVP montrable sans passer la grille
- ne pas cacher les cas faibles
- ne pas corriger en introduisant de la complexité SaaS
- ne pas modifier l’architecture sans validation CTO

Livrable attendu
- résultats de validation
- liste des corrections réalisées
- décision argumentée : montrable / non montrable
```

## 5. Pour chaque prompt : objectif, périmètre, fichiers/modules visés, changements attendus, tests attendus, critères DONE, interdits

Chaque prompt ci-dessus contient explicitement :

- l’objectif
- le périmètre
- les fichiers/modules visés
- les changements attendus
- les tests attendus
- les critères DONE
- les interdits

Aucun lot ne doit être exécuté sans respecter ces 7 rubriques.

## 6. Ordre recommandé d’exécution

1. Lot 1 — Socle projet MVP
2. Lot 2 — Ingestion du texte officiel AI Act
3. Lot 3 — Métadonnées documentaires minimales
4. Lot 4 — Chunking juridique
5. Lot 5 — Embeddings + stockage vectoriel
6. Lot 6 — Retrieval sur question utilisateur
7. Lot 7 — Génération contrainte + citations + refus
8. Lot 8 — Première preuve de bout en bout
9. Lot 9 — Interface vitrine scénarisée
10. Lot 10 — Fiabilisation démo + grille qualité MVP

### Règle CTO

Ne pas inverser Lot 9 avec les lots documentaires. L’interface vient après la preuve de bout en bout.

## 7. Points de revue CTO entre les lots

### Après Lot 1

- la structure projet est-elle propre et non monolithique ?

### Après Lot 2

- l’extraction du texte et des pages est-elle exploitable ?

### Après Lot 3

- la traçabilité minimale est-elle réellement fiable ?

### Après Lot 4

- les chunks sont-ils juridiquement cohérents et citables ?

### Après Lot 5

- le lien chunk / embedding / métadonnées est-il intact ?

### Après Lot 6

- les extraits retrouvés sont-ils vraiment pertinents ?

### Après Lot 7

- les réponses sont-elles bornées, sourcées et refusent-elles correctement ?

### Après Lot 8

- dispose-t-on d’une première preuve utile et vérifiable ?

### Après Lot 9

- la vitrine met-elle en valeur la preuve documentaire sans masquer les limites ?

### Après Lot 10

- le MVP atteint-il réellement le seuil “montrable” ?

## 8. Erreurs classiques que Cursor ne doit pas commettre

- regrouper plusieurs lots critiques pour aller plus vite
- commencer par l’interface au lieu de la chaîne documentaire
- écrire une logique monolithique difficile à faire évoluer
- introduire des composants SaaS non demandés
- perdre le lien entre chunk et métadonnées
- faire un chunking purement technique
- compenser un retrieval faible par un LLM plus bavard
- produire des citations approximatives
- contourner la règle de refus
- déclarer DONE sans test ni vérification
- “améliorer” l’architecture sans validation
- ajouter plusieurs corpus, plusieurs LLMs ou une orchestration complexe

## 9. Conditions pour stopper l’implémentation et remonter une ambiguïté

Cursor doit stopper et remonter le point si :

- une décision d’architecture n’est pas compatible avec le repo existant
- le document source réellement disponible contredit les hypothèses validées
- les métadonnées minimales ne peuvent pas être dérivées proprement
- le chunking validé est impossible à appliquer tel quel sur la structure extraite
- le vector store ou le moteur d’embeddings retenu n’est pas exploitable dans le contexte réel
- une citation fiable ne peut pas être produite avec les données actuelles
- la règle de refus nécessite un arbitrage non encore figé
- un lot impose de changer le périmètre MVP
- un composant existant du repo pousse vers une architecture différente
- un test critique échoue et bloque le lot suivant

### Règle

En cas d’ambiguïté structurelle : **stop, expliquer, proposer 1 option par défaut, attendre validation**.

## 10. Règle finale : Cursor implémente, il ne reconçoit pas

Cursor doit :

- implémenter exactement le lot demandé
- respecter l’architecture, les invariants et la checklist DONE
- produire les tests et vérifications attendus
- signaler les ambiguïtés réelles

Cursor ne doit pas :

- redéfinir l’architecture
- élargir le périmètre
- simplifier la logique documentaire sans validation
- improviser une trajectoire SaaS
- remplacer une décision actée par une préférence technique personnelle