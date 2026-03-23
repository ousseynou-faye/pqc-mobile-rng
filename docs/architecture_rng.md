# Architecture RNG - Baseline officielle du prototype

## 1. Vue d'ensemble

L'architecture officielle du prototype mémoire est la suivante :

```text
SRC  ->  COND  ->  DRBG  ->  STATE
```

- `SRC` : collecte d'entropie brute.
- `COND` : conditionnement de l'entropie.
- `DRBG` : génération déterministe post-quantique.
- `STATE` : gestion, scellement et restauration de l'état.

Cette structure est la seule architecture de référence pour la version actuelle du prototype.

## 2. Couche SRC

La couche `SRC` agrège plusieurs sources d'entropie non déterministes, principalement :

- le `CPU jitter` ;
- une source secondaire de type capteurs inertiels ou simulation équivalente.

Son rôle n'est pas de produire directement une sortie uniforme, mais de fournir une matière première entropique à la couche suivante.

## 3. Couche COND

Le conditionneur officiel retenu est :

```text
Raw_Data -> Toeplitz Extractor -> SHAKE-256 -> Seedinit
```

### Décision de gel

- `Toeplitz + SHAKE-256` est la seule formulation correcte du conditionneur actuel.
- La formulation `Toeplitz + LWR` ne doit plus être utilisée pour décrire la couche `COND`.
- `LWR` n'est pas un conditionneur ; c'est le coeur du moteur DRBG nominal.

## 4. Couche DRBG

### 4.1 Moteur nominal

Le moteur nominal du DRBG est `Module-LWR`.

Il constitue la version principale du prototype logiciel et doit être présenté comme tel dans tout document final.

### 4.2 Moteur secondaire

Le moteur secondaire est `Multiplexed Sponge`.

Son rôle est limité à :

- la recherche ;
- la comparaison expérimentale ;
- un éventuel mode dégradé contrôlé par politique.

Il ne remplace pas silencieusement le moteur nominal.

### 4.3 Statut d'exécution

Dans la baseline actuelle :

- le mode nominal correspond à la politique `STRICT_LWR_ONLY` ;
- un usage du `Multiplexed Sponge` doit être explicite, contrôlé et visible dans l'état exporté ;
- un passage en mode dégradé de recherche ne doit jamais être présenté comme le comportement normal du prototype.

## 5. Couche STATE

La couche `STATE` protège l'état interne du DRBG.

Dans le prototype actuel, elle est représentée par :

- un gestionnaire d'état logiciel ;
- un mécanisme de scellement / restauration simulé ;
- une logique de détection d'altération et de rollback.

La présence d'un TEE réel reste une cible de déploiement, mais la baseline exécutable actuelle repose sur une simulation logicielle contrôlée.

## 6. Paramètres gelés du moteur nominal

Le profil de référence du prototype est :

```text
module_lwr_baseline_v1:
  n = 256
  k = 3
  q = 8192
  p = 1024
  secret = {-1, 0, 1}
```

Ce profil correspond au code par défaut du dépôt.

## 7. Place de la NTT

La `NTT` n'appartient pas à la baseline exécutable actuelle.

Elle est reclassée comme :

- optimisation future ;
- piste d'accélération logicielle ;
- piste d'accélération matérielle ;
- travail ultérieur pour une cible plus proche d'un déploiement mobile réel.

### Conséquence documentaire

Les anciens schémas mentionnant `RLWE + NTT` doivent être relus comme des cibles futures et non comme la description fidèle du prototype actuellement codé.

## 8. Nature de l'API

La forme officielle de l'API du prototype est une librairie / SDK Python local.

Le point d'intégration officiel observé dans le dépôt est constitué par les appels suivants :

- `instantiate(...)`
- `generate(...)`
- `reseed(...)`
- `export_state()`
- `zeroize()`

L'information de santé et de statut est actuellement portée par `export_state()` et par l'état logique du gestionnaire.

Un service HTTP peut être ajouté plus tard comme démonstrateur, mais il ne constitue pas l'API officielle de la baseline.

## 9. Résumé d'architecture

```text
Sources physiques/simulées
        |
        v
 SRC : CPU jitter + capteurs
        |
        v
 COND : Toeplitz + SHAKE-256
        |
        v
 DRBG : Module-LWR (nominal)
        |        \
        |         \--> Multiplexed Sponge (secondaire / recherche)
        v
 STATE : état, sealing, restore, anti-rollback simulé
```

## 10. Formulation à reprendre dans le manuscrit

> La baseline officielle du prototype mémoire repose sur une architecture en quatre couches `SRC -> COND -> DRBG -> STATE`. Le conditionneur officiel est `Toeplitz + SHAKE-256`, le moteur nominal du DRBG est `Module-LWR`, et le `Multiplexed Sponge` est maintenu comme moteur secondaire de recherche. La NTT n'est pas intégrée à la baseline exécutable actuelle ; elle est classée comme optimisation future.
