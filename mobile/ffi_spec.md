# Specification FFI mobile

## Objet

Ce document definit le contrat binaire minimal de la trajectoire mobile.
Il ne decrit pas une integration Android ou Linux deja operationnelle.

Dans l'etat actuel du depot:

- l'implementation de reference reste le SDK Python local
- le contrat mobile est materialise uniquement par un bridge de transition Python
- aucune implementation native C, Rust, JNI ou NDK n'est declaree comme validee

Le bridge de reference se trouve dans:

`software/interface_hw/mobile_bridge.py`

## Choix d'architecture

La frontiere mobile retenue est volontairement simple:

- Python reste l'implementation de reference pour l'etude, les tests et les benchmarks
- la future couche native devra prendre en charge le coeur d'execution du DRBG
- la frontiere binaire est placee au niveau du service, pas a l'interieur des sources d'entropie ou du conditionneur

Cette decision permet de:

- conserver intacte la baseline officielle `SRC -> COND -> DRBG -> STATE`
- figer un contrat d'appel exploitable plus tard par un wrapper natif
- eviter de pretendre qu'une pile mobile complete existe deja

## Operations supportees

Codes d'operation:

- `1` : `instantiate`
- `2` : `generate`
- `3` : `reseed`
- `4` : `health`
- `5` : `zeroize`

Codes reserves mais non actives dans la baseline:

- `6` : `export_state`
- `7` : `import_state`

Dans la baseline actuelle, toute tentative d'utilisation de `export_state` ou `import_state` doit renvoyer `UNSUPPORTED`.

## Signatures logiques

### `instantiate`

But:

- instancier le DRBG a partir du chemin canonique deja present dans le projet

Entree:

- `personalization: bytes`

Sortie:

- statut de succes ou d'erreur

### `generate`

But:

- produire un bloc d'octets pseudo-aleatoires

Entree:

- `length: u32`
- `additional_input: bytes`

Sortie:

- octets generes si l'operation reussit

### `reseed`

But:

- demander un reseed explicite du generateur actif

Entree:

- `additional_input: bytes`

Sortie:

- statut de succes ou d'erreur

### `health`

But:

- retourner un etat de sante non sensible

Entree:

- aucune

Sortie:

- metadonnees synthetiques sur l'etat courant

### `zeroize`

But:

- effacer l'etat actif maintenu en memoire

Entree:

- aucune

Sortie:

- statut de succes ou d'erreur

## Modele d'erreur

Codes de statut:

- `0` : `ok`
- `1` : `invalid_argument`
- `2` : `not_initialized`
- `3` : `reseed_required`
- `4` : `health_error`
- `5` : `unsupported`
- `255` : `internal_error`

Conventions:

- les erreurs de transport ou de trame restent traitees au niveau du format de frame
- les erreurs fonctionnelles sont renvoyees dans une reponse avec un code de statut non nul
- `detail_code` est reserve pour une future implementation native et reste a `0` dans le bridge Python actuel

## Regles de memoire et d'ownership

Pour les requetes:

- l'appelant est proprietaire du buffer de requete
- le bridge lit ce buffer mais ne conserve pas de reference durable dessus

Pour les reponses:

- le bridge construit un buffer de reponse complet
- l'appelant devient responsable de sa liberation ou de sa copie dans son environnement d'execution

Pour `zeroize`:

- l'appel efface l'etat actif du DRBG maintenu par le service de reference
- dans le cas Python, cela ne constitue pas une garantie de nettoyage memoire bas niveau comparable a une implementation native specialisee

## Politique sur l'export et l'import d'etat

L'export et l'import d'etat ne font pas partie de la baseline mobile active.

Cette restriction est volontaire pour trois raisons:

- le format d'etat scelle actuel depend de la couche Python existante
- exposer l'etat interne au travers d'une FFI agrandit la surface d'attaque
- une vraie trajectoire mobile doit privilegier un stockage scelle cote plateforme plutot qu'un transfert brut d'etat applicatif

Si cette capacite est activee plus tard, elle devra obligatoirement etre:

- versionnee explicitement
- protegee par scellement ou par un mecanisme materiel equivalent
- inaccessible au code applicatif non privilegie

## Limites assumees

Cette specification ne doit pas etre interpretee comme:

- une preuve d'integration Android
- une preuve d'integration Linux embarquee
- une validation JNI ou NDK
- une preuve de portabilite native deja testee

Elle sert uniquement a definir une frontiere FFI credible, minimale et defendable pour une extension mobile future.
