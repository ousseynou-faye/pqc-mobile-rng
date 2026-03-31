# Pipeline COND vers LFSR

## But

Ce document décrit précisément la transition:

`raw_data -> conditionneur -> seedinit -> seed_s/seed_t -> S_n/T_n`

## Pipeline nominal

```text
raw_data
  -> EntropyMixer.condition_raw_data(...)
  -> ConditioningResult.seedinit
  -> encode_conditioner_seed_for_drbg(seedinit)
  -> MultiplexedSpongeAdapter.instantiate(...)
  -> decode_conditioner_seed_for_drbg(...)
  -> seed_digest = SHAKE-256("sponge_init:" || personalization || seedinit)
  -> derive_sponge_lfsr_seeds(seed_digest)
  -> seed_s / seed_t
  -> RecurrenceSequence(S_n) / RecurrenceSequence(T_n)
```

## Production de `seedinit`

La couche `COND`:

1. prend `raw_data`
2. applique Toeplitz
3. applique SHAKE-256
4. retourne `ConditioningResult.seedinit`

Cette valeur est la seule racine de dérivation autorisée pour le DRBG.

## Encodage obligatoire du seed de DRBG

Le module `software/conditioner/drbg_seed_material.py` impose un pont explicite:

- `encode_conditioner_seed_for_drbg(seedinit)`
- `decode_conditioner_seed_for_drbg(seed_material)`

Le rôle de ce pont est d'interdire les seeds arbitraires injectés directement dans le DRBG.

## Dérivation de `seed_s` et `seed_t`

`derive_sponge_lfsr_seeds(...)` produit:

- `seed_s`
- `seed_t`

avec:

- séparation de domaine `SEQ_S` / `SEQ_T`
- réduction dans l'espace des états valides du LFSR
- exclusion de l'état nul

## Initialisation des suites

La baseline initialise:

- `seq_s = RecurrenceSequence(degree=16, seed=seed_s)`
- `seq_t = RecurrenceSequence(degree=16, seed=seed_t)`

Ces deux suites alimentent ensuite la chaîne `phi -> multiplexage -> sponge`.

## Invariant critique

L'invariant à retenir est le suivant:

- sans `ConditioningResult.seedinit`, il n'y a pas de seed material DRBG valide
- sans seed material DRBG valide, `MultiplexedSpongeAdapter.instantiate()` échoue
- donc la sponge ne peut pas fonctionner en contournant le conditionneur
