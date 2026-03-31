# Benchmark Report

- Type: software_performance
- Date UTC: 2026-03-31T12:33:23.731620+00:00
- Machine: AMD64
- Systeme: Windows

## Methodologie
- Benchmark logiciel Python local.
- Les resultats ne sont pas directement generalisables a un smartphone sans execution sur cible reelle.
- Les mesures memoire sont des estimations via tracemalloc, pas une mesure systeme mobile complete.
- Le nom performance_arm.py ne signifie pas que les chiffres proviennent d'une cible ARM reelle.

## Comparaison
- module_lwr: instantiate mean 191500.0 ns, reseed mean 146900.0 ns, generate(256 B) mean 2250210400.0 ns, throughput mean 113.9 B/s
- multiplexed_sponge: instantiate mean 15916733.3 ns, reseed mean 22089833.3 ns, generate(256 B) mean 182907533.3 ns, throughput mean 1408.9 B/s
