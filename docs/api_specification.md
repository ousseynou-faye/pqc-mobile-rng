# API Specification - Baseline officielle du prototype

## 1. Nature de l'API

La forme officielle de l'API du prototype est une librairie Python locale, utilisable comme SDK de démonstration.

Cette API expose le coeur RNG aux couches applicatives sans imposer, dans la baseline actuelle, un service HTTP ni une architecture distribuée.

## 2. Objet de l'API

L'API doit permettre de :

- initialiser le générateur ;
- produire des octets aléatoires ;
- déclencher un reseed ;
- observer le statut logique et la santé exportable ;
- remettre l'état à zéro.

## 3. Composant de référence

Le composant de référence est le gestionnaire composite :

```python
PQCCompositeDRBG
```

Il orchestre :

- `Module-LWR` comme moteur nominal ;
- `Multiplexed Sponge` comme moteur secondaire ;
- la politique de sélection ;
- la machine à états.

## 4. Interface officielle observée dans le dépôt

### 4.1 `instantiate(seed_material: bytes, personalization: bytes = b"") -> None`

Initialise le DRBG.

Préconditions :

- `seed_material` ne doit pas être vide ;
- le système ne doit pas être en `fail_stop`.

Effets :

- crée l'état initial ;
- sélectionne le moteur actif selon la politique ;
- place le système dans un état prêt.

### 4.2 `generate(nbytes: int, additional_input: bytes = b"") -> bytes`

Retourne `nbytes` octets pseudo-aléatoires.

Préconditions :

- le système doit être initialisé ;
- le système ne doit pas être en `need_reseed` ni `fail_stop`.

Effets :

- consulte la santé du moteur actif ;
- produit la sortie ;
- met à jour les compteurs ;
- fait évoluer l'état interne.

### 4.3 `reseed(seed_material: bytes, additional_input: bytes = b"", reason: str = "manual_reseed") -> None`

Rafraîchit l'état avec une nouvelle matière d'initialisation.

Préconditions :

- le système doit déjà être initialisé ;
- le système ne doit pas être `zeroized` sans nouvelle instanciation.

Effets :

- réinjecte une nouvelle seed ;
- remet le compteur de requêtes à zéro ;
- restaure un état prêt à générer.

### 4.4 `export_state() -> dict`

Retourne un export non sensible destiné au diagnostic, au statut logique et à l'observabilité.

Dans l'implémentation actuelle, c'est ce point d'entrée qui porte l'information principale de `health/status`, car il expose notamment :

- `manager_state.lifecycle_state` ;
- `manager_state.flags` ;
- `active_engine_state`.

### 4.5 `zeroize() -> None`

Efface au mieux l'état logiciel maintenu par le prototype.

## 5. États logiques attendus

L'API repose sur une machine à états explicite.

États principaux du code courant :

- `uninitialized`
- `ready`
- `need_reseed`
- `fail_stop`
- `zeroized`

Le mode de recherche dégradé n'est pas un état séparé de la machine ; il est représenté par le drapeau `manager_state.flags.degraded_research`.

## 6. Règles de conception de l'API

### 6.1 Pas d'accès direct aux secrets

L'utilisateur de l'API ne doit pas manipuler directement :

- le vecteur secret interne ;
- les graines privées ;
- l'état interne complet du moteur.

### 6.2 Politique explicite

Toute déviation du mode nominal doit être rendue visible par la politique et par l'état.

### 6.3 Pas de masquage silencieux des fautes critiques

Une erreur de sécurité critique ne doit pas être dissimulée par :

- un fallback automatique opaque ;
- un redémarrage implicite ;
- un changement silencieux de moteur.

## 7. Choix officiellement rejetés pour la baseline

Les éléments suivants ne constituent pas l'API officielle actuelle :

- un service HTTP comme mode principal ;
- une interface Android native complète ;
- une passerelle réseau vers un matériel distant.

Ces possibilités peuvent exister plus tard comme wrappers ou démonstrateurs, mais elles sont hors baseline.

## 8. Exemple minimal d'utilisation

```python
from software.pqc_drbg.drbg_engine import PQCCompositeDRBG

rng = PQCCompositeDRBG()
rng.instantiate(b"seed-demo")
out = rng.generate(32)
status = rng.export_state()
```

## 9. Résumé

L'API officielle de la baseline est une API Python locale, simple et auditée, centrée sur un composant unique `PQCCompositeDRBG`, avec `Module-LWR` comme moteur nominal et `Multiplexed Sponge` comme moteur secondaire de recherche. La surface publique réellement constatée dans le dépôt est `instantiate / generate / reseed / export_state / zeroize`, l'information de santé et de statut étant actuellement portée par `export_state()` plutôt que par un service réseau ou une méthode dédiée supplémentaire.
