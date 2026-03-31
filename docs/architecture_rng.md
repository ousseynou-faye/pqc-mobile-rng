# Architecture RNG

## Vue d'ensemble

Le depot implemente un pipeline logiciel complet:

`SRC -> COND -> DRBG -> STATE`

Le point d'entree canonique est `software/api/rng_service.py`. Cette classe orchestre toutes les briques reelles du projet sans introduire de logique parallele cachee.

## Couches et responsabilites

### 1. SRC

Modules principaux:

- `software/entropy/cpu_jitter.py`
- `software/entropy/sensor_entropy.py`
- `software/entropy/entropy_pool.py`
- `software/entropy/health_estimator.py`
- `software/entropy/models.py`

Responsabilites:

- collecter des symboles bruts
- estimer une entropie conservative
- appliquer des checks sanitaires
- constituer un `EntropyPool`

Sortie notable:

- `raw_data = pool.export_raw_bytes()`

### 2. COND

Modules principaux:

- `software/conditioner/entropy_mixer.py`
- `software/conditioner/toeplitz_extractor.py`
- `software/conditioner/shake_conditioner.py`
- `software/conditioner/drbg_seed_material.py`

Responsabilites:

- fabriquer un contexte stable de conditionnement
- deriver une graine publique pour Toeplitz
- extraire une sortie Toeplitz
- calculer `seedinit` via SHAKE-256
- encoder explicitement le passage vers le DRBG

Sortie notable:

- `ConditioningResult.seedinit`

### 3. DRBG

Modules principaux:

- `software/pqc_drbg/drbg_engine.py`
- `software/pqc_drbg/sponge_core.py`
- `software/sponge/seed_derivation.py`
- `software/sponge/multiplexed_sponge.py`
- `software/sponge/multiplexed_sequence.py`
- `software/sponge/phi_function.py`
- `software/sponge/sponge_state.py`
- `software/sponge/sponge_absorb.py`
- `software/sponge/sponge_squeeze.py`
- `software/lfsr/recurrence_sequences.py`
- `software/lfsr/lfsr_core.py`

Responsabilites:

- valider la machine a etats DRBG
- transformer `seedinit` en `seed_digest`
- deriver les graines LFSR `seed_s` et `seed_t`
- produire `S_n`, `T_n` et `phi(l,n)`
- generer la sequence multiplexee
- absorber puis compresser via le sponge
- emettre la sortie finale en octets

Point exact de production de la sortie:

- `RNGService.generate_bytes()`
- `PQCCompositeDRBG.generate()`
- `MultiplexedSpongeAdapter.generate()`
- `instance.squeeze_bytes(nbytes)`

### 4. STATE

Modules principaux:

- `software/state_manager/state_manager.py`
- `software/state_manager/tee_simulator.py`
- `software/state_manager/models.py`
- `software/pqc_drbg/state.py`

Responsabilites:

- gerer les etats `uninitialized`, `ready`, `need_reseed`, `fail_stop`, `zeroized`
- exporter un etat scellable
- restaurer l'etat prive du moteur sponge
- simuler la frontiere TEE

## Flux de donnees

1. `CPUJitterSource` et `SensorEntropySource` produisent des blocs bruts.
2. `EntropyPool` filtre et agrege les chunks acceptes.
3. `EntropyMixer` transforme les octets bruts en `toeplitz_output`, puis en `seedinit`.
4. `encode_conditioner_seed_for_drbg()` marque explicitement la provenance conditionnee.
5. `MultiplexedSpongeAdapter.instantiate()` derive un `seed_digest`.
6. `build_reference_sponge()` derive `seed_s` et `seed_t`, initialise le sponge, absorbe un materiau initial.
7. `generate()` appelle `squeeze_bytes()` et retourne la sortie finale.
8. `StateManager` peut sceller puis restaurer l'etat complet.

## Flux de la graine

```text
raw_data
  -> toeplitz_output
  -> seedinit
  -> encode_conditioner_seed_for_drbg(seedinit)
  -> seed_digest = SHAKE-256("sponge_init:" || personalization || seedinit)
  -> derive_sponge_lfsr_seeds(seed_digest)
  -> seed_s / seed_t
```

## Flux de l'etat interne

Etat DRBG manager:

- gere par `software/pqc_drbg/state.py`
- compte les requetes et impose le reseed
- distingue la sante logique du moteur et l'etat de cycle de vie

Etat prive moteur:

- `seed_digest`
- `generate_counter`
- `sponge_state`
- etats courants des deux sequences LFSR

## Interfaces publiques

### Service canonique

- `build_entropy_seed()`
- `instantiate_rng()`
- `generate_bytes()`
- `generate_output_bundle()`
- `reseed_rng()`
- `checkpoint_state()`
- `restore_state()`
- `zeroize()`
- `sdk_status()`

### API publique

Wrappers dans `software/api/`:

- `rng_init()`
- `rng_get_bytes()`
- `rng_generate()`
- `rng_get_output_formats()`
- `rng_reseed()`
- `rng_restore_state()`
- `rng_zeroize()`
- `rng_health()`

## Observabilite disponible

Avant cette passe, l'observabilite etait surtout presente cote UI et surtout par octet. La passe actuelle ajoute:

- conversion canonique bytes -> hex
- conversion canonique bytes -> binaire
- conversion canonique bytes -> decimal
- demonstrations par couche
- traces simplifiees d'etat sponge

## Limites

- le depot contient aussi des couches UI, benchmark, mobile et hardware, mais la baseline executable du RNG reste purement Python
- certains repertoires de runtime et de benchmark sont des artefacts de test, pas des briques fonctionnelles du pipeline
