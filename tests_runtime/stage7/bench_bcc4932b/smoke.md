# Benchmark Report

- Type: software_performance
- Date UTC: 2026-03-29T21:04:38.526111+00:00
- Machine: AMD64
- Systeme: Windows

## Methodologie
- Benchmark logiciel Python local.
- Les resultats ne sont pas directement generalisables a un smartphone sans execution sur cible reelle.
- Les mesures memoire sont des estimations via tracemalloc, pas une mesure systeme mobile complete.
- Le nom performance_arm.py ne signifie pas que les chiffres proviennent d'une cible ARM reelle.

## Comparaison
- module_lwr: instantiate mean 193966.7 ns, reseed mean 196300.0 ns, generate(256 B) mean 464236580100.0 ns, throughput mean 58.9 B/s
- multiplexed_sponge: instantiate mean 16442200.0 ns, reseed mean 14427633.3 ns, generate(256 B) mean 136151566.7 ns, throughput mean 1889.7 B/s
