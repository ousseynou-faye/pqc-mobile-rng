# Benchmark Report

- Type: software_performance
- Date UTC: 2026-03-29T21:01:12.905772+00:00
- Machine: AMD64
- Systeme: Windows

## Methodologie
- Benchmark logiciel Python local.
- Les resultats ne sont pas directement generalisables a un smartphone sans execution sur cible reelle.
- Les mesures memoire sont des estimations via tracemalloc, pas une mesure systeme mobile complete.
- Le nom performance_arm.py ne signifie pas que les chiffres proviennent d'une cible ARM reelle.

## Comparaison
- module_lwr: instantiate mean 145733.3 ns, reseed mean 154400.0 ns, generate(256 B) mean 2542327700.0 ns, throughput mean 102.5 B/s
- multiplexed_sponge: instantiate mean 26702533.3 ns, reseed mean 35167033.3 ns, generate(256 B) mean 181384733.3 ns, throughput mean 1424.3 B/s
