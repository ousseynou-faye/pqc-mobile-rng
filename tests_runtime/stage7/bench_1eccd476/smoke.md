# Benchmark Report

- Type: software_performance
- Date UTC: 2026-03-31T12:22:36.716255+00:00
- Machine: AMD64
- Systeme: Windows

## Methodologie
- Benchmark logiciel Python local.
- Les resultats ne sont pas directement generalisables a un smartphone sans execution sur cible reelle.
- Les mesures memoire sont des estimations via tracemalloc, pas une mesure systeme mobile complete.
- Le nom performance_arm.py ne signifie pas que les chiffres proviennent d'une cible ARM reelle.

## Comparaison
- module_lwr: instantiate mean 392733.3 ns, reseed mean 384133.3 ns, generate(256 B) mean 4165540166.7 ns, throughput mean 61.6 B/s
- multiplexed_sponge: instantiate mean 59427466.7 ns, reseed mean 36683533.3 ns, generate(256 B) mean 366854466.7 ns, throughput mean 701.3 B/s
