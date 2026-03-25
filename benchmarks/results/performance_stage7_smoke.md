# Benchmark Report

- Type: software_performance
- Date UTC: 2026-03-25T14:04:05.469143+00:00
- Machine: AMD64
- Systeme: Windows

## Methodologie
- Benchmark logiciel Python local.
- Les resultats ne sont pas directement generalisables a un smartphone sans execution sur cible reelle.
- Les mesures memoire sont des estimations via tracemalloc, pas une mesure systeme mobile complete.
- Le nom performance_arm.py ne signifie pas que les chiffres proviennent d'une cible ARM reelle.

## Comparaison
- module_lwr: instantiate mean 184366.7 ns, reseed mean 212900.0 ns, generate(256 B) mean 1739933700.0 ns, throughput mean 147.5 B/s
- multiplexed_sponge: instantiate mean 20351833.3 ns, reseed mean 15986100.0 ns, generate(256 B) mean 177732266.7 ns, throughput mean 1448.6 B/s
