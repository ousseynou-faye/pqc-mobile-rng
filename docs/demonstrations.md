# Demonstrations

## Objectif

Les demonstrations doivent rendre visibles les couches du projet et montrer clairement ce qui change entre:

- l'entropie brute
- la sortie conditionnee
- les graines LFSR
- les sequences de recurrence
- le multiplexage
- l'etat sponge
- la sortie DRBG finale

## Scripts disponibles

### `demos/demo_rng_output_formats.py`

Montre uniquement la conversion d'une sortie binaire en:

- bytes
- liste decimale des octets
- hex
- decimal
- binaire
- binaire groupe

Commande:

```bash
python demos/demo_rng_output_formats.py
```

### `demos/demo_multiplexed_sponge.py`

Montre un scenario deterministe focalise sur le moteur:

- derivation `seed_s` / `seed_t`
- echantillon `S_n`
- echantillon `T_n`
- echantillon `phi(l,n)`
- echantillon de sequence multiplexee
- trace simplifiee du sponge

Commande:

```bash
python demos/demo_multiplexed_sponge.py
```

### `demos/demo_full_pipeline.py`

Montre le pipeline complet:

- `SOURCE D'ENTROPIE`
- `CONDITIONNEUR`
- `SEEDINIT`
- `DERIVATION LFSR`
- `SEQUENCE S_n`
- `SEQUENCE T_n`
- `PHI(l,n)`
- `SEQUENCE MULTIPLEXEE`
- `MULTIPLEXED SPONGE`
- `SORTIE FINALE`

Commande:

```bash
python demos/demo_full_pipeline.py
```

## Sections affichees

Le format cible est volontairement pedagogique:

```text
=== SOURCE D'ENTROPIE ===
...
=== CONDITIONNEUR ===
...
=== SEEDINIT ===
...
=== DERIVATION LFSR ===
...
=== SEQUENCE S_n ===
...
=== SEQUENCE T_n ===
...
=== PHI(l,n) ===
...
=== SEQUENCE MULTIPLEXEE ===
...
=== MULTIPLEXED SPONGE ===
...
=== SORTIE FINALE ===
Bytes: ...
Hex: ...
Decimal: ...
Binary: ...
```

## Conseils d'interpretation

- `SOURCE D'ENTROPIE`: permet de voir la matiere brute avant tout traitement
- `CONDITIONNEUR`: montre la reduction Toeplitz et le contexte SHAKE
- `SEEDINIT`: correspond a l'entree reelle de la phase DRBG apres marquage de provenance
- `DERIVATION LFSR`: rend visibles les graines internes derivees du `seed_digest`
- `S_n`, `T_n`, `phi(l,n)`: aident a distinguer les sous-couches mathematiques
- `MULTIPLEXED SPONGE`: montre l'evolution simplifiee de l'etat pendant le squeeze
- `SORTIE FINALE`: donne la meme sortie en plusieurs formats de lecture

## Lien avec l'API

Les demonstrations utilisent les memes briques que la baseline:

- `RNGService`
- `EntropyMixer`
- `derive_sponge_lfsr_seeds()`
- `MultiplexedSequence`
- `build_reference_sponge()`
- `format_output_bytes()`

Il ne s'agit pas de maquettes independantes.
