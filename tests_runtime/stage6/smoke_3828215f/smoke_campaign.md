# Validation experimentale

- Contexte: comparative_drbg_campaign
- Mode: smoke
- Date UTC: 2026-03-31T12:22:21.064235+00:00

## Portee

### Implemente
- Validation experimentale de la source d'entropie, du conditionnement et des sorties DRBG.
- Health checks simples et estimation prudente de min-entropie par Most Common Value.
- Campagnes statistiques comparatives sur Module-LWR et Multiplexed Sponge.

### Inspire par NIST
- Architecture SRC -> COND -> DRBG inspiree des bonnes pratiques de separation des couches.
- Health checks inspires de SP 800-90B pour repetition count et adaptive proportion.
- Tests statistiques inspires de SP 800-22 utilises comme indicateurs experimentaux.

### Non conformite formelle
- Ce rapport ne revendique aucune conformite formelle a SP 800-90A, SP 800-90B, SP 800-22, FIPS ou CMVP.
- Les tests statistiques presentes ici ne constituent pas une preuve cryptographique.
- Module-LWR et Multiplexed Sponge ne sont pas presentes comme des DRBG NIST approuves.

## Comparaison
- multiplexed_sponge: taux moyen de succes 1.000, biais moyen -0.003906, complexite lineaire normalisee moyenne 0.499512
- module_lwr: taux moyen de succes 1.000, biais moyen 0.000000, complexite lineaire normalisee moyenne 0.500000
