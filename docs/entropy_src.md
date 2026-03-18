# Couche SRC — Source d'entropie

## But

Dans cette étape, je mets en place la couche **SRC** de mon architecture :

`SRC -> COND -> DRBG -> STATE`

Mon objectif n'est pas encore de produire une sortie uniforme finale.
Je cherche d'abord à **collecter**, **contrôler** et **accumuler** de l'entropie brute.

## Sources retenues

### 1. CPU jitter
Je l'utilise comme source primaire.
Je mesure des variations fines de temps d'exécution sur une boucle dense.

### 2. Capteurs inertiels
Je les utilise comme source secondaire de diversification.
Je ne conserve que les bits faibles (LSB) des lectures.

## Fichiers

- `cpu_jitter.py` : collecte primaire par jitter CPU.
- `sensor_entropy.py` : collecte secondaire inertielle, avec simulation ou adaptateur.
- `entropy_pool.py` : accumulation des blocs et décision de passage au conditionneur.
- `health_estimator.py` : tests de santé simples + borne prudente de min-entropie.
- `models.py` : structures de données partagées.

## Limites

- Je ne prétends pas ici atteindre une conformité complète à NIST SP 800-90B.
- Les estimations restent prudentes et expérimentales.
- La simulation inertielle ne remplace pas un capteur réel.
- Le conditionnement cryptographique sera traité dans l'étape suivante.

## Exemple minimal

```python
from software.entropy import CPUJitterSource, SensorEntropySource, EntropyPool

cpu = CPUJitterSource(sample_count=256, inner_loops=128, lsb_count=2)
sensor = SensorEntropySource(frame_count=128, lsb_count=2)

pool = EntropyPool(target_min_entropy_bits=256.0, target_min_symbols=512)

pool.add_chunk(cpu.collect())
pool.add_chunk(sensor.collect())

snapshot = pool.snapshot()
print(snapshot)
print(pool.export_raw_bytes()[:32].hex())
```
