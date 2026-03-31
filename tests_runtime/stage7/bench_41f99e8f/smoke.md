# Benchmark Report

- Type: software_performance
- Date UTC: 2026-03-29T21:02:58.893308+00:00
- Machine: AMD64
- Systeme: Windows

## Methodologie
- Benchmark logiciel Python local.
- Les resultats ne sont pas directement generalisables a un smartphone sans execution sur cible reelle.
- Les mesures memoire sont des estimations via tracemalloc, pas une mesure systeme mobile complete.
- Le nom performance_arm.py ne signifie pas que les chiffres proviennent d'une cible ARM reelle.

## Comparaison
- module_lwr: instantiate mean 250766.7 ns, reseed mean 402033.3 ns, generate(256 B) mean 2324979800.0 ns, throughput mean 110.5 B/s
- multiplexed_sponge: instantiate mean 16955933.3 ns, reseed mean 15723000.0 ns, generate(256 B) mean 154080433.3 ns, throughput mean 1665.6 B/s
