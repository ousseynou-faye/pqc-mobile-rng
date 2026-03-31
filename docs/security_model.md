# Security Model

## Portee

Ce document decrit le modele de securite de la baseline executable du depot:

- source d'entropie locale
- conditionnement Toeplitz + SHAKE-256
- derivation de graines LFSR
- DRBG `Multiplexed Sponge`
- gestion d'etat avec scellement logiciel simule

## Objectifs

Le systeme vise:

- unpredictabilite conditionnee a une entropie suffisante en entree
- separation claire des couches `SRC -> COND -> DRBG -> STATE`
- preservation de l'etat entre executions
- reseed explicite
- forward security pratique via rekeying et overwrite logique de l'etat

## Hypotheses

### Entropie

La securite suppose que `SRC` apporte assez d'incertitude brute pour que `COND` produise un `seedinit` non predictable.

### Conditionnement

Toeplitz + SHAKE-256 est traite comme un compresseur d'entropie et un deriveur deterministe de seed, pas comme une preuve formelle de conformite SP 800-90.

### LFSR et multiplexage

Les LFSR `S_n` et `T_n` ne sont pas utilises seuls comme generateurs finaux. Ils servent de structure interne au schema Multiplexed Sponge:

- `S_n` pilote `phi(l,n)`
- `T_n` fournit la sequence secondaire
- la sponge absorbe et etend l'etat final

### Sponge

La resistance finale repose sur:

- la separation de domaine
- le melange par permutation
- la regeneration d'etat a l'instanciation et au reseed
- l'usage de SHAKE-256 dans la canonicalisation des seeds

## Flux d'entropie

```text
entropie brute
 -> Toeplitz
 -> SHAKE-256
 -> seedinit
 -> derive_sponge_lfsr_seeds()
 -> S_n, T_n
 -> phi(l,n)
 -> Multiplexed Sponge
 -> sortie DRBG
```

## Progres de securite par etape

### Instantiate

- `seed_material` doit etre non vide et provenir explicitement de `seedinit`
- un digest canonique est derive
- l'instance sponge est reconstruite
- l'etat passe a `ready`

### Generate

- refus si `need_reseed`
- refus si `fail_stop`
- `additional_input` declenche un rekey interne
- l'etat de sortie reste coherent avec le compteur de generation

### Reseed

- exige un moteur deja initialise
- derive un nouvel etat a partir du seed frais
- remet a zero les compteurs de requetes et d'octets

### Restore

- la version du payload est verifiee
- l'etat actif doit etre `multiplexed_sponge`
- un etat incoherent declenche une erreur

## Forward Security

Le depot ne revendique pas une preuve formelle. En revanche:

- l'etat est rederive par SHAKE-256 a l'instanciation et au reseed
- `additional_input` peut provoquer un rekey avant squeeze
- `zeroize()` supprime l'instance et efface les materiaux derives en memoire Python

## Failure Model

Le composant entre en `fail_stop` sur:

- faute d'integrite
- moteur actif non sain
- echec de generation quand `fail_stop_on_health_error=True`

Ce mode empeche toute generation supplementaire jusqu'a reset explicite.

## Limites

- Pas de revendication de certification NIST/FIPS/CMVP
- Pas de TEE materiel reel dans la baseline
- Les tests statistiques sont des indicateurs, pas des preuves
- Le contexte "post-quantique" du depot repose sur les objectifs de robustesse architecturale et de separation des couches, pas sur une validation normative complete
