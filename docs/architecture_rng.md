# Architecture du RNG

## 1. Objectif / Perimetre

Ce document decrit l'architecture de reference du prototype executable du projet
`Deploiement d'un RNG Mobile Post-Quantique`.

La baseline logicielle actuelle est strictement :

```text
SRC -> COND -> DRBG -> STATE
```

Cette architecture est celle qui doit etre utilisee dans le memoire, la
soutenance et la maintenance du depot.

## 2. Vue d'ensemble

Le projet implemente un prototype academique de RNG structure en couches :

- `SRC` collecte une entropie brute issue de sources logicielles ou simulees.
- `COND` transforme cette entropie en une seed d'initialisation exploitable.
- `DRBG` produit la sortie pseudo-aleatoire a partir de cette seed.
- `STATE` protege la persistance, la restauration et la logique de cycle de vie.

Le point d'integration principal pour l'usage applicatif est le SDK Python local
dans `software/api/`.

## 3. Schema global

```text
  Sources physiques / simulees
            |
            v
  SRC : CPU jitter + capteurs inertiels simules
            |
            v
  COND : Toeplitz Extractor -> SHAKE-256 -> Seedinit
            |
            v
  DRBG : Multiplexed Sponge (nominal)
            |
            +--> Module-LWR (secondaire / recherche)
            |
            v
  STATE : machine a etats + sealing/restauration + anti-rollback simule
            |
            v
  SDK Python local : software.api / RNGService
```

## 4. Interfaces / Composants

### 4.1 SRC

La couche `SRC` est implemente dans `software/entropy/` et repose
principalement sur :

- `CPUJitterSource`
- `SensorEntropySource`
- `HealthEstimator`
- `EntropyPool`

Le role de `SRC` est de fournir une matiere premiere entropique. Cette couche
ne garantit pas a elle seule une sortie uniforme.

### 4.2 COND

Le conditionneur officiel est :

```text
Raw_Data -> Toeplitz -> SHAKE-256 -> Seedinit
```

Les composants associes sont dans `software/conditioner/` :

- `ToeplitzExtractor`
- `ShakeConditioner`
- `EntropyMixer`

Le conditionnement officiel du depot est donc `Toeplitz + SHAKE-256`. Il ne
faut pas decrire `LWR` comme un conditionneur.

### 4.3 DRBG

La couche `DRBG` est implemente dans `software/pqc_drbg/`.

Le moteur nominal est :

- `Multiplexed Sponge`, via `MultiplexedSpongeAdapter`

Le moteur secondaire est :

- `Module-LWR`, via `ModuleLWRCore`

Le gestionnaire composite `PQCCompositeDRBG` orchestre :

- la politique de selection des moteurs ;
- la machine a etats ;
- les transitions `READY`, `NEED_RESEED`, `FAIL_STOP`, `ZEROIZED`.

### 4.4 STATE

La couche `STATE` est implantee dans `software/state_manager/`.

Elle fournit :

- un `StateManager` ;
- un `SimulatedTEE` ;
- un mecanisme de sealing et de restauration ;
- une detection d'integrite et de rollback.

Cette couche est une simulation logicielle controlee. Elle ne correspond pas a
un TEE mobile reel deja deploye.

### 4.5 SDK Python

Le SDK Python local est expose par `software/api/`.

Il fournit :

- une surface publique simplifiee via `rng_init`, `rng_get_bytes`,
  `rng_generate`, `rng_reseed`, `rng_restore_state`, `rng_zeroize`,
  `rng_health` ;
- un service canonique `RNGService` qui orchestre `SRC -> COND -> DRBG -> STATE`.

Il ne s'agit pas d'un service HTTP natif ni d'une API mobile finale.

### 4.6 Demonstration

La demonstration de reference se trouve dans `demo/run_full_project_demo.py`.

Elle montre :

- le chemin complet `SRC -> COND -> DRBG -> STATE` ;
- le moteur nominal `Multiplexed Sponge` ;
- le moteur secondaire `Module-LWR` ;
- la machine a etats ;
- le sealing et la restauration d'etat.

## 5. Hypotheses

- La source d'entropie reste une source logicielle ou simulee, pas une
  qualification materielle complete.
- Le conditionnement `Toeplitz + SHAKE-256` est l'unique formulation correcte
  de la baseline actuelle.
- `Multiplexed Sponge` est le moteur nominal de la baseline executable.
- `Module-LWR` est conserve pour la recherche, la comparaison et le fallback controle.
- La couche `STATE` simule un environnement protege, sans pretendre a un TEE
  materiel deja deploye.

## 6. Limites

- La baseline actuelle est un prototype academique, pas un produit mobile fini.
- L'API principale reste un SDK Python local.
- La persistance securisee est simulee.
- Les performances mesurees localement ne sont pas des mesures smartphone
  natives.
- Les validations statistiques et benchmarks sont experimentaux et ne valent pas
  certification normative.

## 7. Statut actuel

### 7.1 Ce qui est implemente et executable

- `SRC` avec collecte, tests de sante et pool d'entropie
- `COND` avec `Toeplitz + SHAKE-256`
- `DRBG` nominal `Multiplexed Sponge`
- moteur secondaire `Module-LWR`
- `STATE` avec machine a etats et TEE simule
- SDK Python local et demonstration complete
- validation statistique et benchmarks logiciels locaux

### 7.2 Ce qui est experimental

- usage du `Multiplexed Sponge` comme moteur secondaire
- comparaison statistique et benchmark LWR vs Sponge
- benchmark energie et latence materielle uniquement via cadres ou imports

### 7.3 Ce qui est futur

- acceleration NTT
- portage materiel plus complet
- execution sur vraie cible ARM/mobile
- instrumentation energie reelle

## 8. Evolutions futures

- Integrer des optimisations de performance, y compris la NTT, sans changer la
  separation `SRC -> COND -> DRBG -> STATE`.
- Porter le prototype vers un environnement mobile ou embarque plus proche d'un
  deploiement reel.
- Durcir la couche `STATE` avec une cible de securisation materielle plus fidele.

## 9. Place exacte de la NTT

La `NTT` n'est pas un composant actif de la baseline executable actuelle.

Dans ce depot, elle doit etre comprise comme :

- une optimisation future ;
- un levier possible d'acceleration logicielle ou materielle ;
- un sujet de travaux ulterieurs.

Elle ne doit pas etre documentee comme deja integree au moteur nominal courant.
