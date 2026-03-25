# Benchmark Report

- Type: software_performance
- Date UTC: 2026-03-25T14:04:27.328613+00:00
- Machine: AMD64
- Systeme: Windows

## Methodologie
- Benchmark logiciel Python local.
- Les resultats ne sont pas directement generalisables a un smartphone sans execution sur cible reelle.
- Les mesures memoire sont des estimations via tracemalloc, pas une mesure systeme mobile complete.
- Le nom performance_arm.py ne signifie pas que les chiffres proviennent d'une cible ARM reelle.

## Comparaison
- module_lwr: instantiate mean 116600.0 ns, reseed mean 126533.3 ns, generate(256 B) mean 1517936800.0 ns, throughput mean 168.8 B/s
- multiplexed_sponge: instantiate mean 13957333.3 ns, reseed mean 15515700.0 ns, generate(256 B) mean 131886833.3 ns, throughput mean 1942.3 B/s
