# pqc_mobile_rng

Prototype logiciel local d'un pipeline RNG post-quantique articule en quatre couches:

`SRC -> COND -> DRBG -> STATE`

La baseline executable actuelle utilise uniquement `Multiplexed Sponge` comme moteur DRBG. Le depot inclut maintenant une observabilite explicite des sorties en `bytes`, `hex`, `binaire` et `decimal`.

## Presentation generale

Le projet assemble:

- `SRC`: collecte d'entropie locale via jitter CPU et source capteur simulee
- `COND`: reduction et stabilisation de l'entropie brute via Toeplitz puis SHAKE-256
- `DRBG`: derivation LFSR, sequences `S_n` et `T_n`, calcul `phi(l,n)`, multiplexage et expansion `Multiplexed Sponge`
- `STATE`: machine a etats, checkpoint, restauration et zeroization

## Architecture fonctionnelle

```text
[Sources d'entropie]
        |
        v
[Pool / Donnees brutes]
        |
        v
[Conditionneur]
        |
        v
[seedinit]
        |
        v
[Derivation des graines LFSR]
      /   \
     v     v
 [S_n]   [T_n]
    |       |
    +--> [phi(l,n)]
             |
             v
 [u_n = t_{n + phi(l,n)}]
             |
             v
 [Multiplexed Sponge]
             |
             v
 [Sortie DRBG]
     |    |      |
     v    v      v
 [Bytes][Hex][Decimal]
             |
             v
          [STATE]
```

## Points d'entree utiles

- service canonique: `software/api/rng_service.py`
- wrappers publics SDK: `software/api/`
- demonstration simple JSON: `main.py`
- demonstration complete historique: `demo/run_full_project_demo.py`
- demonstrations pedagogiques detaillees: `demos/`

## Conversion des sorties

Le module canonique est `software/api/output_formats.py`.

Fonctions disponibles:

- `to_decimal(output_bytes)`
- `to_hex(output_bytes)`
- `to_binary(output_bytes)`
- `format_output_bytes(output_bytes)`

Convention officielle pour le decimal:

- les octets convertis sont exactement ceux emis par le DRBG
- interpretation en entier non signe
- endianness: `big-endian`
- les zeros de tete restent presents dans le tableau d'octets d'origine, mais la representation decimale d'un entier ne conserve pas visuellement ces zeros
- pour reproduire strictement une sortie, il faut conserver a la fois la longueur et les octets eux-memes

## Demonstrations

Scripts ajoutes:

- `python demos/demo_rng_output_formats.py`
- `python demos/demo_multiplexed_sponge.py`
- `python demos/demo_full_pipeline.py`

Le script complet affiche distinctement:

- source d'entropie
- conditionneur
- `seedinit`
- derivation LFSR
- echantillons `S_n`, `T_n`, `phi(l,n)` et sequence multiplexee
- trace simplifiee de l'etat sponge
- sortie finale en bytes, hex, decimal, binaire

## Documentation

Documentation principale en francais:

- `docs/architecture_rng.md`
- `docs/api_specification.md`
- `docs/multiplexed_sponge.md`
- `docs/output_formats.md`
- `docs/demonstrations.md`
- `docs/tests_validation.md`

## Tests

Exemples:

- `pytest tests/test_output_formats.py`
- `pytest tests/test_demo_outputs.py`
- `pytest tests/test_public_api.py`
- `pytest tests/test_end_to_end_pipeline.py`

## Limites actuelles

- aucune revendication de conformite NIST/FIPS
- sources d'entropie et capteur encore orientes prototype local
- pas de TEE materiel reel dans cette baseline
- valeur decimale utile pour l'inspection, pas pour une evaluation cryptographique a elle seule
