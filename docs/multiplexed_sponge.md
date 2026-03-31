# Multiplexed Sponge

## Role dans le projet

`Multiplexed Sponge` est l'unique moteur DRBG actif de la baseline. Il n'est pas une source d'entropie. Il consomme une seed conditionnee, derive des structures internes deterministes, puis etend cette seed en sortie pseudo-aleatoire.

## Modules impliques

- `software/pqc_drbg/sponge_core.py`
- `software/sponge/multiplexed_sponge.py`
- `software/sponge/multiplexed_sequence.py`
- `software/sponge/phi_function.py`
- `software/sponge/seed_derivation.py`
- `software/sponge/sponge_state.py`
- `software/sponge/sponge_absorb.py`
- `software/sponge/sponge_squeeze.py`

## Sequence d'initialisation

1. Le conditionneur produit `seedinit`.
2. Le DRBG calcule:

```text
seed_digest = SHAKE-256("sponge_init:" || personalization || seedinit)
```

3. `derive_sponge_lfsr_seeds()` derive deux graines non nulles:

- `seed_s` pour `S_n`
- `seed_t` pour `T_n`

4. `build_reference_sponge()` construit:

- `RecurrenceSequence(seq_s)`
- `RecurrenceSequence(seq_t)`
- `MultiplexedSponge(l=4, rate=128, capacity=128)`

5. Un materiau initial derive par SHAKE est absorbe dans le sponge.

## Sequences internes

### `S_n`

Sequence de recurrence binaire issue d'un LFSR. Elle alimente la fonction `phi(l,n)`.

### `T_n`

Deuxieme sequence de recurrence binaire. Elle sert de sequence source pour le multiplexage final.

### `phi(l,n)`

Prototype implemente dans `software/sponge/phi_function.py`.

Convention actuelle:

- `l=4` dans la baseline de reference
- `phi` lit une fenetre de bits de `S_n`
- `phi.compute()` n'avance pas `S_n`

### Sequence multiplexee

La relation implementee est:

```text
u_n = t_{n + phi(l,n)}
```

Implementation:

- lecture non destructive de `T_n` a l'offset voulu
- puis avance d'un cran de `S_n` et `T_n`

## Absorption

Pendant l'absorption:

1. un bloc d'entree est pris
2. un bloc multiplexe de meme taille est produit
3. les deux blocs sont XORes
4. le resultat est absorbe dans la partie `rate`
5. une permutation est appliquee

## Squeeze

Pendant le squeeze:

1. un bloc est lu dans la partie `rate` de l'etat
2. un bloc multiplexe est produit
3. les deux blocs sont XORes
4. le resultat est retourne
5. l'etat est permute pour la suite

## Etat observable

L'export prive du moteur peut contenir:

- `seed_digest_hex`
- `generate_counter`
- `sponge_state`
- etat courant des sequences `seq_s` et `seq_t`

## Trace simplifiee

La demonstration `demos/demo_full_pipeline.py` et `demos/demo_multiplexed_sponge.py` montrent une trace simplifiee:

- `state_avant`
- bloc de sortie extrait
- `state_apres`

Cette trace est pedagogique. Elle ne remplace pas une instrumentation formelle de type debug hardware.

## Limites et hypotheses

- le sponge implemente ici reste un prototype de recherche logicielle
- la permutation et les tailles ne pretendent pas definir un standard industriel
- la documentation du depot doit donc etre lue comme description d'architecture, pas comme specification normative externe
