# Benchmark Report

- Type: software_performance
- Date UTC: 2026-03-31T12:21:50.282623+00:00
- Machine: AMD64
- Systeme: Windows

## Methodologie
- Benchmark logiciel Python local.
- Les resultats ne sont pas directement generalisables a un smartphone sans execution sur cible reelle.
- Les mesures memoire sont des estimations via tracemalloc, pas une mesure systeme mobile complete.
- Le nom performance_arm.py ne signifie pas que les chiffres proviennent d'une cible ARM reelle.

## Comparaison
- module_lwr: instantiate mean 240566.7 ns, reseed mean 175733.3 ns, generate(256 B) mean 3546780600.0 ns, throughput mean 75.2 B/s
- multiplexed_sponge: instantiate mean 41679366.7 ns, reseed mean 47182400.0 ns, generate(256 B) mean 369281100.0 ns, throughput mean 698.4 B/s
