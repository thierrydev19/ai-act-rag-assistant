# 11 - Checklist CTO de revue avant lancement dev

## 1. Objectif de la checklist

Valider de manière formelle que le projet est suffisamment cadré pour autoriser Cursor à démarrer l’implémentation du MVP sans ambiguïté, sans redéfinition d’architecture et sans dérive de périmètre. Tant que cette checklist n’est pas validée, le développement ne démarre pas.

## 2. Checklist de validation produit

- [ ]  Le produit est bien défini comme **assistant documentaire AI Act traçable**, et non comme chatbot PDF générique.
- [ ]  L’objectif du MVP vitrine est validé.
- [ ]  La cible prioritaire est validée : **dirigeants PME et consultants**.
- [ ]  Le périmètre MVP est borné et compris.
- [ ]  Les cas d’usage vitrine prioritaires sont validés.
- [ ]  Les 10 questions de démonstration prioritaires sont figées.
- [ ]  Les 5 questions de refus / limites sont figées.
- [ ]  Le périmètre verbal de démonstration “couvert / non couvert” est défini.
- [ ]  La posture produit est claire : **réponse sourcée ou refus explicite**.
- [ ]  Aucun objectif SaaS complet n’est implicitement glissé dans le MVP.

## 3. Checklist de validation corpus

- [ ]  Le document source exact est validé : **Regulation (EU) 2024/1689 ... (Artificial Intelligence Act)**.
- [ ]  La langue unique du corpus MVP est validée : **français**.
- [ ]  Une seule version documentaire est retenue pour le MVP.
- [ ]  Le corpus MVP est volontairement limité au **texte officiel AI Act**.
- [ ]  Les contenus explicitement exclus sont confirmés : guides non officiels, blogs, jurisprudence, autres règlements, multi-documents.
- [ ]  Le format d’entrée documentaire est connu et disponible pour implémentation.
- [ ]  Le niveau de granularité documentaire attendu pour les citations est validé.
- [ ]  Le corpus est jugé suffisant pour couvrir les cas de démonstration retenus.
- [ ]  Il n’existe pas de contradiction entre le corpus retenu et les questions de démo prévues.
- [ ]  La règle de stabilité du corpus pendant le MVP est validée : pas de changement de version en cours d’implémentation.

## 4. Checklist de validation architecture

- [ ]  L’architecture RAG en 4 blocs est validée : ingestion, chunking, retrieval avec métadonnées, génération contrainte.
- [ ]  Le MVP est confirmé comme **vitrine + base propre pour évoluer sans refaire**.
- [ ]  La dette technique acceptable est confirmée comme **faible dette, pas de bricolage structurel**.
- [ ]  La remplaçabilité attendue est confirmée comme **modulaire simple**.
- [ ]  Le passage SaaS est explicitement reporté à **après premiers retours prospects**.
- [ ]  Chroma est validé comme vector store MVP.
- [ ]  Aucun composant SaaS prématuré n’est attendu dans le développement initial.
- [ ]  Les frontières des modules sont comprises par le CTO.
- [ ]  La règle de refus explicite est validée.
- [ ]  Le format public de citation est validé.
- [ ]  Les composants remplaçables sont identifiés.
- [ ]  Aucun point d’architecture critique ne reste ambigu pour Cursor.

## 5. Checklist de validation métadonnées

- [ ]  Le principe “les métadonnées sont un invariant, pas un enrichissement secondaire” est validé.
- [ ]  Les métadonnées minimales obligatoires sont figées :
    - [ ]  `document_id`
    - [ ]  `document_title`
    - [ ]  `page_number`
    - [ ]  `article_ref`
    - [ ]  `section_ref` si disponible
    - [ ]  `language`
    - [ ]  `version_date`
    - [ ]  `source_type`
    - [ ]  `chunk_text`
    - [ ]  `chunk_index`
- [ ]  Le titre exact affiché du document dans les citations est validé.
- [ ]  La forme finale de `article_ref` est validée.
- [ ]  La forme finale de `section_ref` est validée.
- [ ]  La règle d’affichage quand article et section sont disponibles est validée.
- [ ]  La règle d’affichage quand seule la page est fiable est validée.
- [ ]  La politique “mieux vaut une métadonnée absente qu’une métadonnée fausse” est validée.
- [ ]  La règle de stabilité des citations entre démonstrations est validée.
- [ ]  Cursor n’aura pas à inventer de métadonnées non fiabilisées.

## 6. Checklist de validation chunking

- [ ]  La stratégie de chunking juridique est validée.
- [ ]  La finesse retenue est validée : **chunks courts à moyens et précis**.
- [ ]  La priorité principale est validée : **précision des citations**.
- [ ]  La règle en cas de doute est validée : **ne pas casser un article**, sauf s’il devient vraiment trop long.
- [ ]  La taille cible est validée : **400 à 800 mots max au départ**.
- [ ]  Le découpage par unité juridique logique est validé.
- [ ]  Le découpage interne autorisé est validé :
    - [ ]  paragraphe
    - [ ]  alinéa
    - [ ]  liste
    - [ ]  sous-section
- [ ]  L’overlap léger est validé : **10 à 15 %**.
- [ ]  La source minimale toujours citable est validée :
    - [ ]  document
    - [ ]  article
    - [ ]  page
    - [ ]  chunk_index
- [ ]  La règle de citation si un chunk couvre plusieurs pages est définie ou explicitement reportée avec défaut connu.
- [ ]  La règle de citation si un chunk couvre plusieurs sous-parties d’un même article est définie ou explicitement reportée avec défaut connu.

## 7. Checklist de validation qualité attendue

- [ ]  La grille d’évaluation qualité MVP est validée.
- [ ]  Le juge de la réponse correcte est validé : **toi + moi**, puis tiers métier/juridique plus tard.
- [ ]  L’exigence sur les citations est validée : **page + article/section cohérents à chaque fois**.
- [ ]  La tolérance aux réponses partielles est validée : acceptable si bien sourcée et explicite sur ses limites.
- [ ]  Le temps de réponse acceptable en démo est validé : **moins de 10 s**.
- [ ]  Le seuil minimum de réponses correctes / acceptables est validé : **au moins 80 % sur 15 à 20 questions**.
- [ ]  Le seuil de citation est validé : **100 % des réponses de démo affichent une source exploitable**.
- [ ]  Le seuil de refus est validé : le système refuse proprement sur les cas hors périmètre ou insuffisamment documentés.
- [ ]  Le seuil de stabilité est validé : pas de crash, démo fluide, 3 à 5 cas maîtrisés d’avance.
- [ ]  Le MVP montrable est défini par des critères explicites, pas par impression générale.

## 8. Checklist de validation des prompts Cursor

- [ ]  Les prompts Cursor d’implémentation existent pour tous les lots.
- [ ]  Le découpage en lots est cohérent avec le plan d’implémentation.
- [ ]  Les lots sont suffisamment petits et contrôlés.
- [ ]  L’ordre d’exécution des lots est validé.
- [ ]  Chaque prompt contient :
    - [ ]  objectif
    - [ ]  périmètre
    - [ ]  fichiers/modules visés
    - [ ]  changements attendus
    - [ ]  tests attendus
    - [ ]  critères DONE
    - [ ]  interdits
- [ ]  Les points de revue CTO entre lots sont définis.
- [ ]  Les erreurs classiques à éviter sont explicitées.
- [ ]  Les conditions de stop et de remontée d’ambiguïté sont explicitées.
- [ ]  La règle finale “Cursor implémente, il ne reconçoit pas” est comprise et maintenue.

## 9. Points bloquants qui interdisent de lancer le dev

- [ ]  Le corpus exact n’est pas figé.
- [ ]  La langue ou la version documentaire restent ambiguës.
- [ ]  Le périmètre verbal de démonstration “couvert / non couvert” n’est pas défini.
- [ ]  Le format public de citation n’est pas figé.
- [ ]  La formulation publique du refus n’est pas figée.
- [ ]  Les métadonnées minimales obligatoires ne sont pas figées.
- [ ]  La stratégie de chunking n’est pas validée.
- [ ]  Les critères de qualité “MVP montrable” ne sont pas validés.
- [ ]  Les prompts Cursor ne sont pas prêts.
- [ ]  Un point d’architecture critique reste laissé à l’interprétation de Cursor.
- [ ]  Cursor devrait choisir lui-même entre plusieurs options structurantes.
- [ ]  Le MVP contient encore des attentes SaaS implicites non arbitrées.

### Règle dure

Si un seul point bloquant critique reste ouvert, **le développement ne démarre pas**.

## 10. Règle finale de go / no-go

### GO

Cursor peut démarrer **uniquement si** :

- toutes les checklists 2 à 8 sont validées,
- aucun point bloquant critique de la section 9 n’est ouvert,
- les prompts Cursor sont prêts,
- le lot 1 est clairement borné,
- et le CTO considère que Cursor n’a plus à interpréter l’architecture.

### NO-GO

Cursor ne démarre pas si :

- un invariant majeur n’est pas figé,
- une règle documentaire clé reste floue,
- un critère de qualité reste non défini,
- ou si le MVP risque encore d’être confondu avec une vitrine jetable ou un SaaS prématuré.