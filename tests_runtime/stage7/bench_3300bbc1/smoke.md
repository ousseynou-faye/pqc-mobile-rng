# Benchmark Report

- Type: software_performance
- Date UTC: 2026-03-30T16:02:41.415132+00:00
- Machine: AMD64
- Systeme: Windows

## Methodologie
- Benchmark logiciel Python local.
- Les resultats ne sont pas directement generalisables a un smartphone sans execution sur cible reelle.
- Les mesures memoire sont des estimations via tracemalloc, pas une mesure systeme mobile complete.
- Le nom performance_arm.py ne signifie pas que les chiffres proviennent d'une cible ARM reelle.

## Comparaison
- module_lwr: instantiate mean 111266.7 ns, reseed mean 115600.0 ns, generate(256 B) mean 1576863433.3 ns, throughput mean 163.5 B/s
- multiplexed_sponge: instantiate mean 13308166.7 ns, reseed mean 12191633.3 ns, generate(256 B) mean 123298733.3 ns, throughput mean 2085.6 B/s
