# Modèle de sécurité du prototype

## 1. Portée du document

Ce document décrit le modèle de sécurité réaliste de la baseline exécutable du prototype mémoire. Il distingue explicitement :

- ce qui est effectivement implémenté dans le dépôt ;
- ce qui relève encore d'une extension future ;
- les risques introduits lorsqu'on mélange ces deux niveaux de maturité.

La baseline officielle considérée ici est :

- `SRC -> COND -> DRBG -> STATE` ;
- `COND = Toeplitz + SHAKE-256` ;
- `DRBG nominal = Module-LWR` ;
- `Multiplexed Sponge = moteur secondaire de recherche` ;
- `NTT = optimisation future, hors baseline exécutable actuelle`.

## 2. Actifs protégés

Le prototype cherche à protéger en priorité :

- la qualité entropique de la matière première collectée ;
- la seed conditionnée injectée dans le DRBG ;
- l'état interne du moteur actif ;
- la continuité logique de la machine à états ;
- l'intégrité de l'état exporté ou restauré dans le scénario de sealing simulé.

## 3. Hypothèses de sécurité de la baseline actuelle

### 3.1 Sources d'entropie

La baseline suppose que la couche `SRC` fournit une matière première :

- non entièrement prédictible ;
- suffisamment variée sur la durée ;
- surveillée par des contrôles logiciels de santé et de cohérence.

Cette hypothèse reste empirique dans le prototype : elle est raisonnable pour une démonstration académique, mais elle ne vaut pas certification matérielle.

### 3.2 Conditionnement

La baseline suppose que le conditionneur `Toeplitz + SHAKE-256` :

- réduit les biais résiduels de la source brute ;
- produit une seed d'initialisation stable pour le DRBG ;
- sépare correctement la collecte d'entropie de la génération déterministe.

Le rôle sécuritaire du conditionneur est donc de transformer une entropie brute imparfaite en une entrée plus exploitable pour le moteur nominal, sans prétendre remplacer une preuve complète de min-entropie.

### 3.3 Moteur nominal Module-LWR

Le moteur nominal repose sur les hypothèses suivantes :

- la structure `Module-LWR` du dépôt constitue la base post-quantique effective du prototype ;
- les paramètres gelés (`n=256`, `k=3`, `q=8192`, `p=1024`) sont utilisés comme profil de référence ;
- le secret court ternaire `{-1, 0, 1}` reste conforme au code courant ;
- la sécurité visée est celle d'un prototype de mémoire, pas celle d'un module certifié ou industrialisé.

Cette documentation ne doit donc pas sur-vendre le moteur comme une primitive finalisée ou normalisée.

### 3.4 Gestion d'état

La baseline suppose que la couche `STATE` :

- maintient une machine à états explicite ;
- force un comportement `FAIL_STOP` sur faute critique ;
- interdit les transitions silencieuses ambiguës ;
- simule le sealing et la restauration sans prétendre fournir un TEE matériel réel.

La protection de l'état est donc logicielle et démonstrative, pas équivalente à une enclave matérielle ou à un stockage sécurisé natif de smartphone.

## 4. Séparation stricte entre baseline actuelle et travaux futurs

### 4.1 Ce qui appartient à la baseline exécutable actuelle

Les éléments suivants appartiennent au prototype réellement exécutable :

- collecte d'entropie logicielle ;
- conditionnement `Toeplitz + SHAKE-256` ;
- génération nominale `Module-LWR` ;
- moteur secondaire `Multiplexed Sponge` à usage de recherche ;
- machine à états explicite avec `ready`, `need_reseed`, `fail_stop` et `zeroized` ;
- export d'état non sensible et état scellable simulé.

### 4.2 Ce qui n'appartient pas encore à la baseline exécutable

Les éléments suivants sont explicitement hors baseline actuelle :

- une implémentation `RLWE + NTT` présentée comme moteur effectif ;
- une optimisation NTT intégrée au chemin nominal d'exécution ;
- un TEE matériel réel ;
- une API réseau ou un service HTTP comme forme principale du système ;
- une garantie de sécurité équivalente à un produit mobile déployé en production.

## 5. Risques si l'on mélange baseline et extensions futures

Le mélange entre composants réels et cibles futures crée plusieurs risques documentaires et techniques :

- on peut attribuer au prototype une sécurité qu'il n'implémente pas réellement ;
- on peut faire croire que `RLWE + NTT` est déjà codé alors que le dépôt exécute un coeur `Module-LWR` ;
- on peut brouiller la séparation conceptuelle entre `COND` et `DRBG` en parlant de `Toeplitz + LWR` comme conditionneur ;
- on peut décrire une API HTTP inexistante comme interface officielle ;
- on peut rendre les chapitres expérimentaux incohérents avec les tests réellement exécutés.

Dans un mémoire, cette confusion fragilise la démonstration, car elle empêche de savoir quelle partie a été effectivement validée.

## 6. Limites assumées du prototype actuel

Les limites suivantes doivent être énoncées sans ambiguïté :

- la sécurité des sources d'entropie n'est pas certifiée par une campagne matérielle complète ;
- la résistance pratique dépend d'un environnement logiciel contrôlé ;
- le sealing d'état repose sur une simulation et non sur un mécanisme matériel sécurisé ;
- le moteur secondaire `Multiplexed Sponge` n'a pas le statut de moteur nominal ;
- la baseline n'intègre pas encore les optimisations algorithmiques ou matérielles visées pour un déploiement mobile complet.

## 7. Position de la NTT dans le modèle de sécurité

La `NTT` ne doit pas être utilisée comme argument de sécurité de la baseline actuelle.

Dans ce projet, elle doit être interprétée comme :

- un levier d'optimisation de performance ;
- un support possible d'accélération matérielle ;
- un sujet de travaux futurs.

Elle ne modifie donc pas le périmètre de sécurité du prototype exécutable tel qu'il est validé dans cette étape.

## 8. Conclusion

Le prototype actuel fournit une baseline cohérente pour le mémoire : un RNG structuré en couches, conditionné par `Toeplitz + SHAKE-256`, piloté nominalement par `Module-LWR`, et protégé par une gestion d'état explicite. Sa valeur scientifique réside dans la cohérence de l'architecture et dans la traçabilité des choix techniques, non dans la prétention à représenter dès maintenant une implémentation mobile industrialisée.
