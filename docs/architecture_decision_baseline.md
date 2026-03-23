# Décision d'architecture - Baseline officielle du prototype mémoire

## Statut

Acceptée - version de référence `v1.0` du prototype mémoire.

## Objet

Cette décision gèle l'architecture officielle à utiliser dans :

- le code Python du prototype ;
- la documentation technique ;
- le Chapitre 4 du mémoire ;
- le Chapitre 5 du mémoire.

Elle sert à éliminer les contradictions entre schémas de présentation, manuscrit et dépôt logiciel.

## Décisions retenues

### 1. Moteur nominal

Le moteur nominal du prototype est `Module-LWR`.

Conséquences :

- toute génération principale dans le prototype logiciel repose sur `software/pqc_drbg/lwr_core.py` ;
- la documentation doit parler d'un DRBG post-quantique à coeur `Module-LWR` ;
- le vocabulaire `RLWE + NTT` n'est pas utilisé pour décrire la version actuelle codée.

### 2. Moteur secondaire

Le moteur secondaire est le `Multiplexed Sponge`.

Rôle exact :

- moteur de recherche ;
- moteur de comparaison expérimentale ;
- moteur de repli contrôlé uniquement si la politique l'autorise explicitement.

Il ne doit jamais être présenté comme le moteur nominal du prototype mémoire.

### 3. Conditionneur officiel

Le conditionneur officiel de la baseline est :

`Toeplitz extractor -> SHAKE-256 -> Seedinit`

Conséquences :

- la chaîne de conditionnement du manuscrit et du code devient unique ;
- la formulation `Toeplitz + LWR` ne doit plus être utilisée comme description du conditionneur ;
- `LWR` appartient au moteur DRBG, pas à la couche `COND`.

### 4. Place de la NTT

La `NTT` est classée comme :

- optimisation future ;
- piste d'accélération mobile ou matérielle ;
- hors baseline exécutable actuelle.

Conséquences :

- on ne décrit pas la NTT comme une capacité déjà implémentée dans le prototype courant ;
- les schémas ou paragraphes qui évoquent `RLWE + NTT` doivent être reformulés comme cible d'optimisation ou extension future.

### 5. Nature officielle de l'API

La forme officielle de l'API du prototype est une librairie / SDK Python local.

Conséquences :

- l'interface publique de référence observée dans le code est `instantiate / generate / reseed / export_state / zeroize` ;
- l'information de santé et de statut passe actuellement par `export_state()` et par la machine à états ;
- un service HTTP peut exister plus tard comme wrapper de démonstration, mais ce n'est pas la forme officielle de la baseline.

## Paramètres gelés de la baseline logicielle

Profil gelé : `module_lwr_baseline_v1`

- `n = 256`
- `k = 3`
- `q = 8192`
- `p = 1024`
- secret ternaire `{-1, 0, 1}`

## Justification du gel des paramètres

Ce choix est cohérent avec le dépôt logiciel actuel :

- `params.py` expose déjà ce profil par défaut ;
- l'opération d'arrondi reste simple avec un rapport `q/p = 8` ;
- la logique pédagogique du mémoire reste stable.

## Arbitrage sur les documents contradictoires

Quand une diapositive, un schéma ou un ancien brouillon contredit cette baseline, l'ordre d'autorité devient :

1. le code du dépôt ;
2. cette décision d'architecture ;
3. les chapitres révisés ;
4. les présentations simplifiées.

## Formulation officielle à réutiliser dans le mémoire

> La version finale du prototype retenue dans ce mémoire implémente une architecture `SRC -> COND -> DRBG -> STATE`, où le conditionneur officiel repose sur `Toeplitz + SHAKE-256`, le moteur nominal du DRBG est `Module-LWR`, et le `Multiplexed Sponge` est maintenu comme moteur secondaire de recherche et de comparaison. La NTT n'est pas incluse dans la baseline exécutable actuelle ; elle est classée comme optimisation future pour une cible mobile ou matérielle.

## Ce que l'on ne doit plus écrire

À partir de cette décision, il faut éviter les formulations suivantes sans précision :

- `le moteur final est RLWE + NTT` ;
- `le conditionneur est Toeplitz + LWR` ;
- `l'API officielle est un service HTTP` ;
- `la NTT est déjà intégrée au prototype actuel`.

## Effet attendu

Cette décision fournit une baseline officielle unique, suffisamment claire pour :

- coder sans ambiguïté ;
- écrire les chapitres sans contradiction ;
- justifier la différence entre prototype courant et optimisations futures.
