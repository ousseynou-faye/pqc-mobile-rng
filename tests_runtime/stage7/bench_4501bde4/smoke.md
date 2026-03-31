# Benchmark Report

- Type: software_performance
- Date UTC: 2026-03-31T12:59:13.218750+00:00
- Machine: AMD64
- Systeme: Windows

## Methodologie
- Benchmark logiciel Python local.
- Les resultats ne sont pas directement generalisables a un smartphone sans execution sur cible reelle.
- Les mesures memoire sont des estimations via tracemalloc, pas une mesure systeme mobile complete.
- Le nom performance_arm.py ne signifie pas que les chiffres proviennent d'une cible ARM reelle.

## Comparaison
- module_lwr: instantiate mean 226333.3 ns, reseed mean 245066.7 ns, generate(256 B) mean 2643513600.0 ns, throughput mean 98.8 B/s
- multiplexed_sponge: instantiate mean 31074766.7 ns, reseed mean 27533533.3 ns, generate(256 B) mean 231441400.0 ns, throughput mean 1113.6 B/s
