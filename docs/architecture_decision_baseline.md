# Decision d'architecture - Baseline officielle du prototype memoire

## Statut

Acceptee - version de reference `v2.0` du prototype memoire.

## Objet

Cette decision gele l'architecture officielle a utiliser dans :

- le code Python du prototype ;
- la documentation technique ;
- le memoire et la soutenance ;
- les demonstrations et scripts de validation.

## Decisions retenues

### 1. Moteur nominal

Le moteur nominal du prototype est `Multiplexed Sponge`.

Consequences :

- toute generation principale dans le prototype logiciel passe par
  `MultiplexedSpongeAdapter` ;
- la documentation doit parler d'un DRBG post-quantique a coeur
  `Multiplexed Sponge` ;
- le chemin canonique du SDK Python instancie ce moteur par defaut.

### 2. Moteur secondaire

Le moteur secondaire est `Module-LWR`.

Role exact :

- moteur de recherche ;
- moteur de comparaison experimentale ;
- moteur de repli controle uniquement si la politique l'autorise explicitement.

Il ne doit jamais etre presente comme le moteur nominal du prototype memoire.

### 3. Conditionneur officiel

Le conditionneur officiel de la baseline est :

`Toeplitz extractor -> SHAKE-256 -> Seedinit`

### 4. Place de la NTT

La `NTT` reste classee comme :

- optimisation future ;
- piste d'acceleration mobile ou materielle ;
- hors baseline executable actuelle.

### 5. Nature officielle de l'API

La forme officielle de l'API du prototype est une librairie / SDK Python local.

## Formulation officielle a reutiliser

> La version finale du prototype retenue dans ce memoire implemente une
> architecture `SRC -> COND -> DRBG -> STATE`, ou le conditionneur officiel
> repose sur `Toeplitz + SHAKE-256`, le moteur nominal du DRBG est
> `Multiplexed Sponge`, et `Module-LWR` est maintenu comme moteur secondaire de
> recherche, de comparaison et de fallback controle. La NTT n'est pas incluse
> dans la baseline executable actuelle ; elle est classee comme optimisation
> future pour une cible mobile ou materielle.

## Effet attendu

Cette decision fournit une baseline officielle unique, suffisamment claire pour
coder, tester et documenter le depot sans contradiction.
