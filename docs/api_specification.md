# Specification de l'API

## 1. Objectif / Perimetre

Ce document decrit la surface publique reellement exposee par le depot pour le
RNG post-quantique.

L'API actuelle est un SDK Python local. Elle n'est ni un service HTTP natif, ni
une API mobile finale.

## 2. Vue d'ensemble

Le depot expose deux niveaux d'interface :

- un coeur DRBG dans `software/pqc_drbg/` ;
- un SDK Python plus stable dans `software/api/`.

Le point d'entree recommande pour l'usage applicatif local est `software.api`.

## 3. Structure / Surface publique

Les symboles publics exposes par `software/api/__init__.py` sont :

- `get_rng_service`
- `RNGService`
- `RNGServiceConfig`
- `rng_init`
- `rng_get_bytes`
- `rng_generate`
- `rng_health`
- `rng_reseed`
- `rng_restore_state`
- `rng_zeroize`
- `RNGAPIError`
- `RNGNotInitializedError`
- `RNGInvalidLengthError`
- `RNGStateError`
- `RNGRestoreError`
- `RNGProfileError`

Le coeur DRBG expose aussi `PQCCompositeDRBG`, mais le SDK Python reste la
surface la plus simple pour la soutenance et les usages locaux.

## 4. Interfaces / Composants

### 4.1 Service canonique

`RNGService` dans `software/api/rng_service.py` orchestre la baseline :

```text
SRC -> COND -> DRBG -> STATE
```

Methodes principales :

- `build_entropy_seed()`
- `instantiate_rng(...)`
- `generate_bytes(length, additional_input=b"")`
- `reseed_rng(additional_input=b"")`
- `checkpoint_state(...)`
- `restore_state(...)`
- `zeroize()`
- `sdk_status()`
- `health_status()`

### 4.2 Wrappers publics SDK

#### `rng_init(personalization: bytes | None = None, force_reinit: bool = False, profile: str | None = None) -> bool`

- initialise le service RNG canonique pour le processus courant ;
- supporte les profils `baseline` et `default` ;
- renvoie `True` si le RNG est pret.

#### `rng_get_bytes(length: int) -> bytes`

- renvoie des octets pseudo-aleatoires via le SDK public ;
- impose une taille strictement positive ;
- impose une limite publique de `4096` octets par appel.

#### `rng_generate(length: int) -> bytes`

- alias public de `rng_get_bytes`.

#### `rng_health() -> dict`

- renvoie un statut public non sensible ;
- ne doit pas exposer seed, entropie brute ni etat interne complet.

#### `rng_reseed(additional_input: bytes | None = None) -> bool`

- force un reseed controle du RNG courant.

#### `rng_restore_state(payload_metadata: dict | None = None) -> bool`

- restaure un etat scelle via la couche `STATE`.

#### `rng_zeroize() -> bool`

- efface l'etat memoire maintenu par le SDK pour la session courante.

### 4.3 Fonctions utilitaires exposees mais plus internes

Le depot expose aussi des wrappers fins non necessairement destines a la surface
la plus simple :

- `build_entropy_seed()`
- `instantiate_rng()`
- `generate_bytes()`
- `reseed_rng()`
- `checkpoint_state()`
- `restore_state()`

Ils sont reels dans le depot, mais la documentation de soutenance peut rester
centree sur `rng_init / rng_get_bytes / rng_health / rng_reseed / rng_restore_state / rng_zeroize`.

## 5. Hypotheses

- L'API est utilisee localement dans un processus Python.
- La machine a etats du service canonique pilote l'autorisation de generation et
  de reseed.
- Le SDK ne doit pas exposer de materiau sensible dans sa surface publique.

## 6. Comportements attendus

### 6.1 Initialisation

Avant toute generation publique, il faut appeler :

```python
rng_init(...)
```

ou instancier explicitement `RNGService`.

### 6.2 Generation

`rng_get_bytes(length)` :

- verifie `length` ;
- exige un RNG deja initialise ;
- refuse les tailles au-dela de la limite publique.

### 6.3 Reseed

`rng_reseed()` :

- exige un RNG deja initialise ;
- reconstruit une seed fraiche via la baseline `SRC -> COND -> DRBG`.

### 6.4 Health / status

`rng_health()` expose un etat public, notamment :

- `initialized`
- `instantiated`
- `state_available`
- `reseed_supported`
- `last_operation`
- `profile`
- `health_status`
- `lifecycle_state`

### 6.5 Export / restore

La surface publique supporte la restauration via `rng_restore_state()`.

La creation d'un checkpoint est reelle dans le depot, mais elle passe surtout
par `RNGService.checkpoint_state(...)` ou par le wrapper fin `checkpoint_state(...)`.

### 6.6 Zeroize

`rng_zeroize()` :

- efface l'etat memoire du service courant ;
- remet le SDK dans un etat non initialise.

## 7. Gestion d'erreurs

Erreurs publiques principales :

- `RNGAPIError`
- `RNGNotInitializedError`
- `RNGInvalidLengthError`
- `RNGStateError`
- `RNGRestoreError`
- `RNGProfileError`

Principes :

- les erreurs doivent rester explicites ;
- la surface publique ne doit pas divulguer de secret ;
- les details sensibles du DRBG ne doivent pas etre exposes dans les messages.

## 8. Machine a etats logique

Le coeur du depot repose sur une machine a etats explicite, exposee
indirectement par `export_state()` et `sdk_status()`.

Etats principaux :

- `uninitialized`
- `ready`
- `need_reseed`
- `fail_stop`
- `zeroized`

Le mode de recherche degrade est represente par un drapeau logique et non par un
etat public distinct.

## 9. Exemple minimal d'utilisation

```python
from software.api import rng_health, rng_init, rng_reseed, rng_get_bytes, rng_zeroize

rng_init(force_reinit=True)
data = rng_get_bytes(32)
status = rng_health()
rng_reseed()
rng_zeroize()
```

Exemple avec service canonique :

```python
from software.api import get_rng_service

service = get_rng_service(reset=True)
service.instantiate_rng()
data = service.generate_bytes(32)
status = service.sdk_status()
```

## 10. Limites

- Il ne s'agit pas d'une API mobile finale.
- Il n'existe pas de service HTTP natif dans la baseline.
- La persistance securisee reste une simulation logicielle.
- Certaines fonctions sont des wrappers pratiques pour tests et demo, pas une
  promesse de stabilite ABI a long terme.

## 11. Statut actuel

### Implemente

- SDK Python local
- service canonique `RNGService`
- wrappers publics de base
- health public non sensible
- zeroize et restauration d'etat

### Futur possible

- wrappers mobiles natifs ;
- couche HTTP ou IPC ;
- adaptation Android ou embarquee.

Ces extensions futures ne doivent pas etre presentees comme deja disponibles.
