# Specification API

## Objectif

Cette specification decrit les interfaces utiles pour piloter, observer et tester le RNG logiciel.

## Service canonique

Fichier: `software/api/rng_service.py`

### `build_entropy_seed() -> ConditioningResult`

Construit la graine conditionnee a partir de `SRC` et `COND`.

Expose indirectement:

- `raw_data`
- `toeplitz_seed`
- `toeplitz_output`
- `context_info`
- `seedinit`

### `instantiate_rng(personalization: bytes | None = None, seed_result: ConditioningResult | None = None)`

Initialise le DRBG `Multiplexed Sponge`.

Comportement:

- si `seed_result` est absent, le service reconstruit une seed via `build_entropy_seed()`
- sinon il reutilise explicitement la seed fournie

### `generate_bytes(length: int, additional_input: bytes = b"") -> bytes`

Retourne les octets produits par le DRBG officiel.

Point important:

- c'est la frontiere fonctionnelle qui produit la sortie binaire finale

### `generate_output_bundle(length: int, additional_input: bytes = b"") -> dict`

Nouvelle interface d'observabilite.

Retour:

- `raw_bytes`
- `raw_bytes_repr`
- `raw_byte_values`
- `length_bytes`
- `length_bits`
- `byteorder`
- `hex`
- `binary`
- `binary_grouped`
- `decimal`

### `reseed_rng()`

Reconstruit une seed neuve et reseed le moteur courant.

### `checkpoint_state()` / `restore_state()`

Scelle puis restaure l'etat du DRBG et de son manager.

### `sdk_status()` / `health_status()`

Expose un etat synthetique et non sensible du service.

## Wrappers publics SDK

Fichiers:

- `software/api/rng_init.py`
- `software/api/rng_generate.py`
- `software/api/rng_reseed.py`
- `software/api/rng_health.py`

### `rng_init() -> bool`

Initialise l'instance partagee du service.

### `rng_get_bytes(length: int) -> bytes`

Lecture publique directe de la sortie.

### `rng_generate(length: int) -> bytes`

Alias public de `rng_get_bytes`.

### `rng_get_output_formats(length: int) -> dict`

Nouvelle interface publique de visualisation.

Usage type:

```python
from software.api import rng_get_output_formats, rng_init

rng_init(force_reinit=True)
bundle = rng_get_output_formats(16)
print(bundle["hex"])
print(bundle["decimal"])
```

### `rng_reseed()`, `rng_restore_state()`, `rng_zeroize()`, `rng_health()`

Wrappers de cycle de vie et d'etat.

## Utilitaires de conversion

Fichier: `software/api/output_formats.py`

Fonctions:

- `to_decimal(output_bytes, byteorder="big")`
- `to_hex(output_bytes)`
- `to_binary(output_bytes)`
- `group_bits(binary_string, group_size=8, separator=" ")`
- `format_output_bytes(output_bytes, byteorder="big", bit_group_size=8)`

## Contrat de conversion decimale

La valeur decimale est obtenue par:

```python
int.from_bytes(output_bytes, "big", signed=False)
```

Hypotheses:

- entree: exactement les octets de sortie du RNG
- entier non signe
- ordre des octets: `big-endian`
- pas de signe
- pas de normalisation supplementaire

Consequences:

- deux tableaux d'octets differents peuvent produire la meme valeur numerique si l'un ajoute des zeros de tete
- pour identifier une sortie de facon exacte, il faut comparer les octets ou au minimum `hex` + `length_bytes`

## Gestion des erreurs

Les utilitaires de formatage rejettent:

- entree non `bytes`
- entree vide
- `byteorder` invalide
- `group_size <= 0`

## Limite publique sur la generation

`rng_get_bytes()` et `rng_get_output_formats()` appliquent la meme limite:

- `1 <= length <= 4096`
