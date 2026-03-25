# Benchmark Report

- Type: software_performance
- Date UTC: 2026-03-25T14:04:06.623964+00:00
- Machine: AMD64
- Systeme: Windows

## Methodologie
- Benchmark logiciel Python local.
- Les resultats ne sont pas directement generalisables a un smartphone sans execution sur cible reelle.
- Les mesures memoire sont des estimations via tracemalloc, pas une mesure systeme mobile complete.
- Le nom performance_arm.py ne signifie pas que les chiffres proviennent d'une cible ARM reelle.

## Comparaison
- module_lwr: instantiate mean 129600.0 ns, reseed mean 133233.3 ns, generate(256 B) mean 2332004400.0 ns, throughput mean 109.8 B/s
- multiplexed_sponge: instantiate mean 18142966.7 ns, reseed mean 21122066.7 ns, generate(256 B) mean 184223966.7 ns, throughput mean 1389.9 B/s
