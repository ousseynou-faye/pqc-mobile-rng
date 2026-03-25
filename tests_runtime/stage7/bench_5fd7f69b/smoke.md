# Benchmark Report

- Type: software_performance
- Date UTC: 2026-03-25T14:13:12.343320+00:00
- Machine: AMD64
- Systeme: Windows

## Methodologie
- Benchmark logiciel Python local.
- Les resultats ne sont pas directement generalisables a un smartphone sans execution sur cible reelle.
- Les mesures memoire sont des estimations via tracemalloc, pas une mesure systeme mobile complete.
- Le nom performance_arm.py ne signifie pas que les chiffres proviennent d'une cible ARM reelle.

## Comparaison
- module_lwr: instantiate mean 115866.7 ns, reseed mean 123466.7 ns, generate(256 B) mean 1753674666.7 ns, throughput mean 146.1 B/s
- multiplexed_sponge: instantiate mean 15030533.3 ns, reseed mean 14609900.0 ns, generate(256 B) mean 130946600.0 ns, throughput mean 1956.0 B/s
