# Benchmark Report

- Type: software_performance
- Date UTC: 2026-03-29T21:02:04.729030+00:00
- Machine: AMD64
- Systeme: Windows

## Methodologie
- Benchmark logiciel Python local.
- Les resultats ne sont pas directement generalisables a un smartphone sans execution sur cible reelle.
- Les mesures memoire sont des estimations via tracemalloc, pas une mesure systeme mobile complete.
- Le nom performance_arm.py ne signifie pas que les chiffres proviennent d'une cible ARM reelle.

## Comparaison
- module_lwr: instantiate mean 163566.7 ns, reseed mean 179866.7 ns, generate(256 B) mean 2827884466.7 ns, throughput mean 93.5 B/s
- multiplexed_sponge: instantiate mean 42620400.0 ns, reseed mean 32925466.7 ns, generate(256 B) mean 227978200.0 ns, throughput mean 1142.0 B/s
