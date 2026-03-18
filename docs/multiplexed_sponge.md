# Multiplexed Sponge Prototype

## 1. But du prototype

Cette etape fige le prototype Python du "Multiplexed Sponge" utilise dans le
memoire *Deploiement d'un RNG Mobile Post-Quantique*. Le but est de stabiliser
le coeur mathematique du prototype, sans le transformer en API, en DRBG complet
ou en source d'entropie de production.

## 2. Architecture generale

Le prototype combine :

- deux suites de recurrence binaires basees sur des LFSR ;
- une fonction `phi(l, n)` calculee a partir de la suite `s` ;
- une sequence multiplexee definie par `u_n = t_{n + phi(l, n)}` ;
- un etat de sponge avec phases d'absorption et de squeeze ;
- un orchestrateur `MultiplexedSponge` qui assemble ces composants.

## 3. Structure des dossiers

- `software/lfsr/` : LFSR, suites de recurrence et polynomes primitifs.
- `software/sponge/` : `phi`, sequence multiplexee, etat sponge, absorption,
  squeeze et orchestrateur.
- `tests/` : tests de non-regression du prototype.
- `docs/` : documentation technique du memoire.

## 4. Role de chaque fichier

### Dossier `software/lfsr/`

- `primitive_polynomials.py` : catalogue des polynomes primitifs supportes.
- `lfsr_core.py` : coeur LFSR binaire mutable.
- `recurrence_sequences.py` : facade pedagogique au-dessus du LFSR.
- `__init__.py` : exports publics du sous-package.

### Dossier `software/sponge/`

- `phi_function.py` : calcul de `phi(l, n)` sans consommation destructive.
- `multiplexed_sequence.py` : definition operationnelle de `u_n`.
- `permutation.py` : permutation educative et deterministe du prototype.
- `sponge_state.py` : conteneur d'etat du sponge.
- `sponge_absorb.py` : phase d'absorption.
- `sponge_squeeze.py` : phase de squeeze.
- `multiplexed_sponge.py` : orchestrateur de haut niveau.
- `__init__.py` : exports publics du sous-package.

## 5. Definition de `phi(l, n)`

Dans ce prototype, `phi(l, n)` est obtenu par lecture de `l` bits de la suite
`s`, sans consommer cette suite.

- si `offsets is None`, on lit une fenetre contigue de `l` bits a partir de la
  position courante ;
- sinon, on lit les bits aux offsets explicitement demandes ;
- les bits lus sont ensuite assembles en entier selon la convention
  `msb_first`.

## 6. Definition de la sequence multiplexee

La sequence multiplexee reste strictement conforme a la definition :

`u_n = t_{n + phi(l, n)}`

Implementation retenue :

- on calcule `phi(l, n)` a partir de `s` par preview ;
- on lit `t_{n + phi(l, n)}` par `peek` dans `t` ;
- on avance ensuite `s` et `t` d'un seul pas chacun.

Ainsi, les fonctions de preview restent non destructives, et la logique
mathematique est preservee.

## 7. Fonctionnement de l'absorption

Pour chaque bloc d'entree :

1. un bloc de meme taille est genere depuis la sequence multiplexee ;
2. ce bloc sert de masque par XOR ;
3. le resultat est absorbe dans la partie `rate` de l'etat ;
4. une permutation est appliquee.

## 8. Fonctionnement du squeeze

Pour chaque bloc de sortie :

1. on extrait un bloc depuis la partie `rate` de l'etat ;
2. on genere un bloc multiplexe de meme taille ;
3. on combine les deux par XOR ;
4. on permute ensuite l'etat.

## 9. Convention de bits choisie

La convention est maintenant explicite et uniforme.

### MSB / LSB

- `MSB` = bit de poids fort.
- `LSB` = bit de poids faible.

### LFSR

- l'etat est un entier sur `degree` bits ;
- le bit de sortie de `step()` est le MSB courant ;
- le registre est decale vers la droite ;
- le bit de retroaction est reinjecte sur le MSB.

### RecurrenceSequence

- `next_bit()` suit exactement la convention du LFSR ;
- `generate_block(..., msb_first=True)` place le premier bit genere en MSB ;
- `generate_block(..., msb_first=False)` place le premier bit genere en LSB ;
- les methodes `peek_*` ne modifient jamais l'etat.

### PhiFunction

- les bits selectionnes dans `s` sont assembles avec `msb_first=True` par
  defaut ;
- si `msb_first=False`, seul l'assemblage change, pas la selection des bits.

### MultiplexedSequence

- la definition `u_n = t_{n + phi(l, n)}` est preservee ;
- `next_block(..., msb_first=True)` assemble les bits multiplexes en mettant le
  premier bit en MSB ;
- `generate_bytes()` forme chaque octet a partir de 8 bits successifs selon le
  parametre `msb_first`.

### SpongeAbsorb

- le bloc multiplexe utilise pour filtrer l'entree est assemble en MSB-first.

### SpongeSqueeze

- la partie `rate` est la partie basse de l'etat entier ;
- les blocs extraits pour la sortie sont pris dans cette partie basse ;
- le bloc multiplexe applique au squeeze est assemble en MSB-first.

### Assemblage des octets

- dans `LFSR.generate_bytes()`, le comportement historique est conserve :
  `lsb_first=True` signifie que le premier bit genere devient le bit 0 de
  l'octet ;
- dans les composants du sponge, les blocs et octets sont documentes via le
  parametre `msb_first`.

## 10. Limites du prototype

- la permutation fournie est educative ; elle n'est pas une primitive finale
  de production ;
- le prototype ne constitue pas encore un DRBG complet ;
- il ne gere pas encore l'initialisation entropique, le reseed securise, ni les
  interfaces mobile/TEE ;
- l'objectif ici est la stabilisation mathematique et logicielle de l'etape 1.

## 11. Comment lancer les tests

Depuis la racine `pqc_mobile_rng` :

```powershell
venv\Scripts\pytest.exe tests\test_lfsr_core.py tests\test_phi_and_multiplexing.py tests\test_multiplexed_sponge.py
```

Ou plus largement :

```powershell
venv\Scripts\pytest.exe tests
```

## 12. Exemples d'execution

### Exemple 1 : LFSR seul

```python
from software.lfsr.recurrence_sequences import RecurrenceSequence

seq = RecurrenceSequence(degree=8, seed=0xA5)
bits = seq.peek_bits(8)
block = seq.peek_block(8, msb_first=True)

print(bits)   # [1, 0, 1, 0, 0, 1, 0, 1]
print(block)  # 165
```

### Exemple 2 : calcul de `phi(l, n)`

```python
from software.lfsr.recurrence_sequences import RecurrenceSequence
from software.sponge.phi_function import PhiFunction

s = RecurrenceSequence(degree=8, seed=0xA5)
phi = PhiFunction(sequence_s=s, l=4, msb_first=True)

print(phi.compute())  # 10
print(s.get_state())  # 165, etat inchangé
```

### Exemple 3 : cycle complet Multiplexed Sponge

```python
from software.lfsr.recurrence_sequences import RecurrenceSequence
from software.sponge.multiplexed_sponge import MultiplexedSponge

seq_s = RecurrenceSequence(degree=8, seed=0xA5)
seq_t = RecurrenceSequence(degree=9, seed=0x101)

sponge = MultiplexedSponge(seq_s=seq_s, seq_t=seq_t, l=4, rate=32, capacity=32)

mixed = sponge.absorb_blocks([0x12, 0x34], block_size=8)
out = sponge.squeeze_bytes(4)

print(mixed)
print(out.hex())
```

Les valeurs exactes de `mixed` et `out.hex()` sont deterministes a parametres
identiques.
