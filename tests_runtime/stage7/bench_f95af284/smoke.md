# Benchmark Report

- Type: software_performance
- Date UTC: 2026-03-31T12:29:46.497505+00:00
- Machine: AMD64
- Systeme: Windows

## Methodologie
- Benchmark logiciel Python local.
- Les resultats ne sont pas directement generalisables a un smartphone sans execution sur cible reelle.
- Les mesures memoire sont des estimations via tracemalloc, pas une mesure systeme mobile complete.
- Le nom performance_arm.py ne signifie pas que les chiffres proviennent d'une cible ARM reelle.

## Comparaison
- module_lwr: instantiate mean 122066.7 ns, reseed mean 126500.0 ns, generate(256 B) mean 2702511966.7 ns, throughput mean 95.1 B/s
- multiplexed_sponge: instantiate mean 19510133.3 ns, reseed mean 19182466.7 ns, generate(256 B) mean 177000166.7 ns, throughput mean 1454.5 B/s
