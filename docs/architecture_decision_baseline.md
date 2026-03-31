# Architecture Decision Baseline

## Decision

La baseline executable retient une seule architecture DRBG:

- conditionnement Toeplitz + SHAKE-256
- derivation de deux graines LFSR
- calcul de `phi(l,n)`
- expansion par `Multiplexed Sponge`

## Rationale

- reduction de complexite architecturale
- suppression des chemins alternatifs et des fallbacks implicites
- meilleure coherence entre code, tests, et documentation
- frontiere d'etat plus simple a restaurer et verifier

## Consequences

- `active_engine` doit toujours etre `multiplexed_sponge`
- aucun mode de selection de moteur secondaire n'est supporte
- les benchmarks et campagnes portent sur le moteur officiel de la baseline
