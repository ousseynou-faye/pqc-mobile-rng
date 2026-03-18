# Couche COND — Toeplitz + SHAKE-256

## But de cette étape

Dans cette étape, je transforme l'entropie brute issue de la couche SRC en une graine
plus propre, stable et exploitable par le DRBG.

Je suis la forme générale :

`Seedinit = SHAKE-256(Toeplitz(Raw_Data) || Context_Info)`

## Pourquoi cette étape existe

Le DRBG ne doit jamais recevoir directement une graine brute :
- elle peut être biaise ;
- elle peut contenir des corrélations ;
- elle peut dépendre fortement de la source physique.

Le conditionneur sert donc à :
1. extraire l'entropie utile ;
2. réduire les biais résiduels ;
3. produire une seed de longueur fixe.

## Fichiers

- `toeplitz_extractor.py` :
  implémente l'extracteur de Toeplitz sur GF(2).
- `shake_conditioner.py` :
  applique SHAKE-256 à la sortie de Toeplitz.
- `entropy_mixer.py` :
  orchestre toute la couche COND.

## Convention de bits

J'utilise la convention suivante :
<!-- - les bits sont lus MSB-first par défaut ; -->
- la conversion bytes -> bits et bits -> bytes reste cohérente d'un bout à l'autre ;
- la matrice de Toeplitz est paramétrée par `input_bits + output_bits - 1` bits.

## Point méthodologique important

Dans un cadre théorique idéal, la matrice de Toeplitz doit être choisie indépendamment
de la source brute. Dans ce prototype, je dérive donc la graine de Toeplitz à partir d'un
contexte public configurable, et non à partir de `raw_data` lui-même.

Cela me donne un comportement :
<!-- - déterministe ; -->
- reproductible ;
- pratique pour les tests ;
- propre pour le mémoire.

## Exemple rapide

```python
from software.conditioner import EntropyMixer

mixer = EntropyMixer(
    toeplitz_output_bits=256,
    shake_output_bytes=32,
)

result = mixer.condition_raw_data(
    raw_data=b"demo entropy block",
    metadata={"source": "src", "ready": True},
    personalization=b"memoire-m2",
)

print(result.seedinit.hex())
```

## Intégration avec la couche SRC

Si mon pool d'entropie expose :
<!-- - `export_raw_bytes()`
- `export_metadata()` -->

alors je peux faire directement :

```python
result = mixer.condition_from_pool(pool, personalization=b"memoire-m2")
```

## Limites

Cette implémentation :
<!-- - est un prototype logiciel propre ; -->
- ne constitue pas une certification formelle ;
- ne remplace pas une validation complète du système final.
