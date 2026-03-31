# Formats de sortie

## Objectif

Le projet expose maintenant une representation canonique des sorties RNG dans quatre formats:

- `bytes`
- `hex`
- `binaire`
- `decimal`

## Module de reference

Fichier: `software/api/output_formats.py`

## Fonctions disponibles

### `to_decimal(output_bytes, byteorder="big")`

Convertit les octets en entier non signe.

Specification exacte:

- les octets convertis sont exactement ceux emis par le DRBG
- la conversion utilise `int.from_bytes(..., "big", signed=False)`
- la valeur retournee est deterministe

Exemple:

```python
to_decimal(b"\x00\x01\x02") == 258
```

### `to_hex(output_bytes)`

Retourne une chaine hexadecimale continue sans prefixe.

Exemple:

```python
to_hex(b"\x00\x01\x02") == "000102"
```

### `to_binary(output_bytes)`

Retourne une chaine binaire continue sur 8 bits par octet.

Exemple:

```python
to_binary(b"\x00\x01") == "0000000000000001"
```

### `group_bits(binary_string, group_size=8, separator=" ")`

Rend la sortie plus lisible:

```python
group_bits("0000000000000001") == "00000000 00000001"
```

### `format_output_bytes(output_bytes, byteorder="big", bit_group_size=8)`

Produit une vue complete:

- `raw_bytes`
- `raw_bytes_repr`
- `raw_byte_values`
- `length_bytes`
- `length_bits`
- `byteorder`
- `hex`
- `binary`
- `binary_grouped`
- `decimal`

## Endianness et reproductibilite

### Convention officielle

- endianness pour `decimal`: `big-endian`
- pas d'entier signe
- pas de troncature

### Zeros de tete

Les zeros de tete sont bien presents dans le tableau d'octets d'origine, mais la representation decimale d'un entier n'affiche pas ces zeros.

Exemple:

- `b"\x00\x01"` et `b"\x01"` donnent tous deux la valeur numerique `1`
- en revanche, ils ne representent pas la meme sortie binaire

Conclusion:

- pour reproduire exactement une sortie, il faut conserver `raw_bytes` ou au minimum `hex` et `length_bytes`
- pour comparer seulement la valeur numerique, `decimal` suffit

## Cas invalides

Les utilitaires rejettent:

- les valeurs non `bytes`
- les tableaux d'octets vides
- un `byteorder` invalide
- un regroupement de bits avec taille nulle ou negative

## Exemple complet

```python
from software.api import format_output_bytes

bundle = format_output_bytes(b"\x00\x06\xcd\xef\x12\x34\x56\x78")
print(bundle["raw_bytes_repr"])
print(bundle["hex"])
print(bundle["decimal"])
print(bundle["binary_grouped"])
```

## API et demos qui s'appuient dessus

- `RNGService.generate_output_bundle()`
- `rng_get_output_formats()`
- `main.py`
- `demo/run_full_project_demo.py`
- `demos/demo_rng_output_formats.py`
- `demos/demo_full_pipeline.py`
