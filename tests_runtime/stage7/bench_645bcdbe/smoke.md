# Benchmark Report

- Type: software_performance
- Date UTC: 2026-03-25T15:08:39.307605+00:00
- Machine: AMD64
- Systeme: Windows

## Methodologie
- Benchmark logiciel Python local.
- Les resultats ne sont pas directement generalisables a un smartphone sans execution sur cible reelle.
- Les mesures memoire sont des estimations via tracemalloc, pas une mesure systeme mobile complete.
- Le nom performance_arm.py ne signifie pas que les chiffres proviennent d'une cible ARM reelle.

## Comparaison
- module_lwr: instantiate mean 222600.0 ns, reseed mean 257566.7 ns, generate(256 B) mean 2209227400.0 ns, throughput mean 116.4 B/s
- multiplexed_sponge: instantiate mean 30379233.3 ns, reseed mean 29199033.3 ns, generate(256 B) mean 300732333.3 ns, throughput mean 851.3 B/s
