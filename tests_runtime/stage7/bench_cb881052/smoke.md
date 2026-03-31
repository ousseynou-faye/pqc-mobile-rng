# Benchmark Report

- Type: software_performance
- Date UTC: 2026-03-31T12:27:47.039018+00:00
- Machine: AMD64
- Systeme: Windows

## Methodologie
- Benchmark logiciel Python local.
- Les resultats ne sont pas directement generalisables a un smartphone sans execution sur cible reelle.
- Les mesures memoire sont des estimations via tracemalloc, pas une mesure systeme mobile complete.
- Le nom performance_arm.py ne signifie pas que les chiffres proviennent d'une cible ARM reelle.

## Comparaison
- module_lwr: instantiate mean 223300.0 ns, reseed mean 155433.3 ns, generate(256 B) mean 2641503433.3 ns, throughput mean 97.0 B/s
- multiplexed_sponge: instantiate mean 21128900.0 ns, reseed mean 21884933.3 ns, generate(256 B) mean 214109166.7 ns, throughput mean 1203.4 B/s
