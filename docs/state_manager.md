# Couche STATE / TEE simulé

## Introduction

Dans mon architecture globale, je conserve la chaîne suivante :

```text
SRC -> COND -> DRBG -> STATE
```

Je place la couche `STATE` après le `DRBG` parce que le générateur déterministe ne suffit pas à lui seul. Même si mon DRBG est correct d’un point de vue algorithmique, je dois encore protéger **la persistance de son état interne** entre deux exécutions. Si cet état est mal protégé, un attaquant peut restaurer un ancien état, rejouer d’anciennes sorties, cloner un contexte de génération ou injecter une version modifiée de l’état.

Dans cette étape, je mets donc en place une **simulation logicielle sérieuse** d’un composant de type TEE chargé de :

- sceller l’état sensible du DRBG ;
- vérifier l’intégrité du blob persistant ;
- simuler un compteur monotone ;
- détecter les tentatives de rollback ;
- restaurer l’état seulement si les vérifications de sécurité sont satisfaites.

Je ne prétends pas construire ici un vrai TrustZone mobile. Mon objectif est de **valider la logique de sécurité**, de l’expliquer clairement dans le mémoire, puis de préparer un futur portage vers un TEE réel.

## Objectif de sécurité

### Pourquoi je protège l’état du DRBG

Le DRBG produit une suite pseudo-aléatoire à partir d’un état interne secret. Cet état est donc critique : si un attaquant peut le lire, le modifier ou le restaurer dans une ancienne version, il peut compromettre la sécurité du générateur.

Je veux en particulier empêcher quatre familles de risques :

- **fuite d’état** : un attaquant récupère le contenu sensible persisté et tente d’en déduire des sorties ;
- **altération** : un attaquant modifie le blob pour forcer un état invalide ou malveillant ;
- **rollback** : un attaquant restaure un ancien blob alors que le système avait déjà progressé ;
- **clonage d’état** : un attaquant duplique un blob pour rejouer le même contexte de génération sur un autre support.

### Menaces couvertes

Je couvre explicitement les menaces suivantes :

- lecture directe du fichier de blob sans disposer de la clé dérivée locale ;
- modification d’un octet du blob stocké ;
- substitution d’un ancien blob à la place du blob courant ;
- incohérence volontaire entre métadonnées, AAD et contenu chiffré ;
- restauration d’un état dont le compteur logiciel est plus ancien que le compteur matériel simulé.

### Réaction attendue

Quand une vérification échoue, je veux **refuser la restauration**. Dans ce modèle, un état rejeté n’est pas toléré partiellement : je considère qu’il faut invalider l’état restauré et repartir d’un nouvel état fiable, par exemple via une réinstanciation ou un reseed frais.

## Pourquoi un TEE simulé

### Ce que je simule

Je simule les propriétés fonctionnelles essentielles suivantes :

- `seal()` ;
- `unseal()` ;
- clé de base liée au périphérique simulé ;
- authentification du blob ;
- compteur monotone persistant ;
- détection d’anti-rollback ;
- lien fort entre le blob, le périphérique, le namespace et les métadonnées associées.

### Ce que je ne simule pas

Je ne simule pas :

- l’isolation matérielle réelle d’un ARM TrustZone ;
- un stockage RPMB eMMC/UFS authentifié par matériel ;
- la résistance physique à l’extraction de clés ;
- un service de compteur monotone certifié par un composant sécurisé ;
- une validation FIPS, Common Criteria ou équivalente.

### Pourquoi cette simulation est utile dans le mémoire

À ce stade du projet, la simulation me rend trois services importants :

1. Je peux **valider la logique de sécurité** sans dépendre immédiatement d’un terminal mobile précis.
2. Je peux **expliquer proprement le protocole** `CHW / CSW` et la chaîne `seal / unseal` dans le manuscrit.
3. Je peux **préparer une vraie intégration mobile** en séparant déjà les responsabilités : le DRBG génère, la couche `STATE` protège la persistance.

Autrement dit, cette simulation ne remplace pas un TEE réel, mais elle me permet de démontrer que l’architecture défensive est cohérente avant le portage final.

## Architecture du module

J’ai organisé cette couche autour des fichiers suivants :

```text
software/
├── pqc_drbg/
│   └── tee_bridge.py
└── state_manager/
    ├── __init__.py
    ├── errors.py
    ├── models.py
    ├── tee_simulator.py
    └── state_manager.py
```

### Rôle de chaque fichier

#### `software/state_manager/errors.py`

Je regroupe ici les exceptions métier de la couche :

- `StateManagerError` pour les erreurs générales ;
- `IntegrityError` quand l’intégrité ou les métadonnées ne correspondent pas ;
- `RollbackDetectedError` quand je détecte un retour arrière ;
- `SealedBlobNotFoundError` quand aucun blob n’est disponible.

#### `software/state_manager/models.py`

Je définis ici mes structures de données simples :

- `SealedBlob` pour représenter le blob persisté ;
- `TeeDeviceStatus` pour exposer un état minimal du TEE simulé.

#### `software/state_manager/tee_simulator.py`

Je mets ici le cœur de la simulation :

- initialisation du périphérique simulé ;
- génération et persistance d’une HUK simulée ;
- compteur monotone matériel simulé ;
- dérivation des clés de scellement et d’authentification ;
- chiffrement du payload ;
- calcul et vérification du tag ;
- détection d’anti-rollback.

#### `software/state_manager/state_manager.py`

Je fournis ici une couche plus ergonomique au-dessus du TEE simulé :

- sérialisation JSON du payload ;
- génération des AAD ;
- scellement et restauration de dictionnaires Python ;
- pont avec le DRBG via `checkpoint_drbg()` et `restore_drbg()`.

#### `software/pqc_drbg/tee_bridge.py`

Je propose ici un point d’entrée léger pour relier le DRBG et la couche `STATE`, sans exposer directement tous les détails internes du TEE simulé.

### Relation avec `software/pqc_drbg/`

La couche `STATE` ne remplace pas le DRBG. Je garde une séparation nette :

- le DRBG sait **exporter** un état scellable ;
- la couche `STATE` sait **protéger** cet état ;
- le DRBG sait ensuite **réimporter** l’état restauré.

Cette séparation est importante pour le mémoire, car elle montre que la sécurité de persistance est traitée comme une responsabilité dédiée, et non comme un détail caché dans le générateur.

## Vue d’ensemble du fonctionnement

Je peux résumer le flux principal ainsi :

```text
Etat DRBG
   |
   v
export_sealable_state()
   |
   v
StateManager.seal_payload()
   |
   v
SimulatedTEE.seal()
   |
   v
blob JSON scellé + compteurs + tag
```

Puis, lors de la restauration :

```text
blob JSON
   |
   v
SimulatedTEE.unseal()
   |
   +--> vérification version
   +--> vérification CHW / CSW
   +--> vérification AAD
   +--> vérification tag
   |
   v
plaintext restauré
   |
   v
import_sealable_state()
```

## Fonctionnement détaillé de `seal()`

### Entrée

La fonction `seal(blob_id, plaintext, aad=b"")` reçoit :

- un identifiant logique de blob ;
- un `plaintext` représentant l’état sensible sérialisé ;
- des `AAD` facultatives, c’est-à-dire des données associées authentifiées mais non chiffrées.

Dans mon implémentation, le `StateManager` construit d’abord un payload JSON compact, puis fabrique les AAD à partir :

- du `blob_id` ;
- du `namespace` ;
- du `device_id` ;
- de métadonnées applicatives.

### Étape 1 : incrément du compteur monotone

Je commence par incrémenter le compteur matériel simulé `CHW`.

```text
CHW = CHW + 1
CSW = CHW
```

Je copie ensuite cette valeur dans le compteur logiciel `CSW` embarqué dans le blob. Ainsi, chaque scellement correspond à un nouvel état logique du système.

### Étape 2 : dérivation des clés

Je dérive ensuite deux clés à partir :

- de la HUK simulée du périphérique ;
- du `namespace` ;
- du `device_id` ;
- du `blob_id` ;
- du `software_counter`.

Je produis :

- `seal_key` pour le chiffrement ;
- `auth_key` pour l’authentification.

Cette dérivation me permet de lier cryptographiquement le blob à son contexte. Un blob n’est donc pas censé être interchangeable librement entre deux périphériques simulés ou deux compteurs différents.

### Étape 3 : chiffrement du plaintext

Je chiffre le `plaintext` avec un mécanisme logiciel simple :

- je génère un `nonce` aléatoire ;
- je dérive un flot avec `SHAKE-256` à partir de `seal_key || nonce` ;
- je fais un XOR entre ce flot et le `plaintext`.

Cette construction reste une **simulation pédagogique**. Je ne la présente pas comme un remplaçant d’un AEAD matériel ou standardisé de production. Son rôle est de matérialiser le scellement de façon lisible dans le mémoire.

### Étape 4 : calcul du tag d’intégrité

Je construis ensuite un en-tête authentifié contenant :

- `blob_id` ;
- `hardware_counter` ;
- `software_counter` ;
- `version`.

Je calcule ensuite un tag HMAC sur :

```text
header || aad || nonce || ciphertext
```

Ainsi, je protège à la fois :

- les métadonnées critiques ;
- les AAD ;
- le nonce ;
- le contenu chiffré.

### Étape 5 : création du blob

Je retourne enfin une structure `SealedBlob` qui contient :

- l’identifiant logique du blob ;
- `hardware_counter` ;
- `software_counter` ;
- `nonce_hex` ;
- `ciphertext_hex` ;
- `tag_hex` ;
- `aad_hex` ;
- `version`.

Ce blob est ensuite persisté au format JSON.

## Fonctionnement détaillé de `unseal()`

### Chargement du blob

La restauration commence par le chargement du blob JSON depuis le stockage simulé. Si le fichier n’existe pas, je lève `SealedBlobNotFoundError`.

### Vérification de version

Je contrôle d’abord la version du blob. Cela me permet de garder un point d’extension pour de futurs changements de format. Si la version ne correspond pas à celle attendue, je rejette le blob.

### Vérification du compteur

Je récupère ensuite le compteur matériel courant `CHW` et je le compare au compteur logiciel `CSW` porté par le blob.

Je fais les vérifications suivantes :

- si `CSW < CHW`, je détecte un rollback ;
- si `CSW > CHW`, je détecte une incohérence ;
- si `hardware_counter != software_counter` dans le blob, je détecte aussi une incohérence interne.

Cette logique matérialise directement le protocole décrit dans mon architecture.

### Vérification des AAD

Je compare les AAD stockées dans le blob avec les AAD attendues côté appelant. Si elles diffèrent, je rejette le blob. Cela empêche par exemple de réutiliser un blob dans un contexte applicatif différent.

### Vérification du tag

Je redérive `seal_key` et `auth_key`, puis je recalcule le tag attendu à partir de :

```text
header || aad || nonce || ciphertext
```

Si le tag recalculé ne correspond pas au tag stocké, je lève `IntegrityError`.

### Restauration du plaintext

Si toutes les vérifications réussissent, je déchiffre le `ciphertext` avec le même flot dérivé et je restaure le `plaintext`. Le `StateManager` peut alors désérialiser le JSON et restituer le dictionnaire d’état.

## Protection d’intégrité

### Ce qui est authentifié

Dans mon implémentation, j’authentifie explicitement :

- `blob_id` ;
- `hardware_counter` ;
- `software_counter` ;
- `version` ;
- les `AAD` ;
- le `nonce` ;
- le `ciphertext`.

### Pourquoi c’est indispensable

Le chiffrement seul ne suffit pas. Sans authentification, un attaquant pourrait :

- modifier le contenu chiffré ;
- remplacer un champ de compteur ;
- injecter un nonce différent ;
- modifier les AAD attendues ;
- forcer un état incohérent sans être détecté.

L’intégrité me permet donc de détecter toute altération du blob ou de son contexte.

### Comportement en cas d’échec

Si la vérification échoue, je lève `IntegrityError` et je refuse toute restauration. Je ne tente jamais une restauration partielle ni une correction implicite du blob.

## Compteur monotone et anti-rollback

### Définition de `CHW`

`CHW` représente ici le **compteur matériel simulé**. Dans un vrai système mobile, je viserais un compteur ancré dans un composant sécurisé ou un stockage protégé contre le rollback. Dans cette étape, je le simule par une valeur persistée dans les métadonnées du périphérique.

### Définition de `CSW`

`CSW` représente le **compteur logiciel** recopié dans le blob scellé au moment du scellement.

### Règle de détection

La règle centrale est la suivante :

```text
Si CSW < CHW, alors je détecte un rollback.
```

Intuitivement, cela signifie que le système a déjà progressé vers un état plus récent, mais qu’on essaie maintenant de lui faire accepter une ancienne version du blob.

### Exemple intuitif

```text
Scellement 1 : CHW = 1, CSW = 1, blob_A
Scellement 2 : CHW = 2, CSW = 2, blob_B

Si un attaquant réinjecte blob_A alors que CHW vaut déjà 2,
j'obtiens CSW = 1 < CHW = 2  -> rollback détecté
```

### Comportement en cas de rollback

Quand ce cas se produit, je lève `RollbackDetectedError` et je considère l’état comme invalide. Dans le cadre du mémoire, la bonne réaction conceptuelle est alors :

- ne pas restaurer l’état ;
- considérer qu’un ancien état a été réintroduit ;
- repartir d’un nouvel état légitime, par exemple après réinstanciation ou reseed frais.

## Intégration avec le DRBG

### Idée générale

Je ne scelle pas directement un objet Python opaque. Je demande au DRBG de fournir un **état scellable explicite**.

### Rôle de `export_sealable_state()`

Cette méthode, côté DRBG composite, me permet d’extraire :

- l’état du gestionnaire ;
- l’état privé du moteur `Module-LWR` ;
- l’état privé du moteur sponge si présent ;
- une version de format.

Je transforme ainsi l’état runtime du DRBG en structure sérialisable et maîtrisée.

### Rôle de `import_sealable_state()`

Cette méthode réalise l’opération inverse :

- elle recharge les compteurs et drapeaux du gestionnaire ;
- elle réinjecte l’état privé du moteur `LWR` ;
- elle réinjecte éventuellement l’état privé du sponge.

### Rôle de `checkpoint_drbg()`

Dans `StateManager`, `checkpoint_drbg()` :

1. demande au DRBG d’exporter son état scellable ;
2. sérialise ce payload ;
3. génère les AAD ;
4. appelle la couche TEE simulée pour sceller et stocker le tout.

### Rôle de `restore_drbg()`

`restore_drbg()` :

1. recharge et déscelle le blob ;
2. vérifie l’intégrité et l’anti-rollback ;
3. désérialise le payload ;
4. demande au DRBG de réimporter cet état.

### Schéma de l’intégration

```text
PQCCompositeDRBG
   |
   +--> export_sealable_state()
   |
StateManager
   |
   +--> seal_payload()
   +--> unseal_payload()
   |
SimulatedTEE
   |
   +--> seal()
   +--> unseal()
```

## Exemple pratique

### Exemple simple de scellement / restauration

```python
from software.state_manager import SimulatedTEE, StateManager

tee = SimulatedTEE(root_dir="state_data", device_id="pixel-demo", namespace="pqc-rng")
manager = StateManager(tee=tee, blob_id="drbg_state")

payload = {
    "counter": 3,
    "active_engine": "module_lwr",
}

manager.seal_payload(payload, payload_metadata={"purpose": "demo"})
restored = manager.unseal_payload(payload_metadata={"purpose": "demo"})

print(restored)
```

### Exemple avec le DRBG composite

```python
from software.state_manager import SimulatedTEE, StateManager
from software.pqc_drbg.drbg_engine import PQCCompositeDRBG

tee = SimulatedTEE(root_dir="state_data", device_id="pixel-demo", namespace="pqc-rng")
manager = StateManager(tee=tee, blob_id="drbg_state")

drbg = PQCCompositeDRBG()
drbg.instantiate(b"seed-demo-state")
_ = drbg.generate(32)

manager.checkpoint_drbg(
    drbg,
    payload_metadata={"profile": "memoire", "purpose": "checkpoint"},
)

restored_drbg = PQCCompositeDRBG()
payload = manager.restore_drbg(
    restored_drbg,
    payload_metadata={"profile": "memoire", "purpose": "checkpoint"},
)

print(payload["manager_state"]["active_engine"])
print(restored_drbg.export_state()["manager_state"]["lifecycle_state"])
```

## Tests

### Quels tests existent

Le fichier `tests/test_state_manager.py` couvre actuellement quatre scénarios principaux :

- `test_seal_unseal_round_trip` : je vérifie qu’un payload scellé peut être restauré sans perte ;
- `test_integrity_tampering_is_detected` : je vérifie qu’une modification du blob est détectée ;
- `test_rollback_is_detected` : je vérifie qu’un ancien blob est rejeté ;
- `test_checkpoint_and_restore_drbg` : je vérifie que l’intégration avec le DRBG composite fonctionne.

### Ce que ces tests prouvent

Ces tests me permettent de montrer que :

- la chaîne `seal -> save -> load -> unseal` est cohérente ;
- le tag protège bien l’intégrité du blob ;
- la règle `CSW < CHW` détecte le rollback ;
- le pont entre `STATE` et `DRBG` est opérationnel.

### Comment les lancer

Si `pytest` est disponible dans l’environnement, je peux lancer :

```bash
python -m pytest tests/test_state_manager.py
```

Je peux aussi lancer un ensemble plus large incluant le DRBG :

```bash
python -m pytest tests/test_state_manager.py tests/test_pqc_drbg_complete.py
```

Si `pytest` n’est pas encore installé dans l’interpréteur courant, il faut d’abord l’ajouter à l’environnement de travail.

## Limites

### Ce qui est bien simulé

Cette étape simule correctement, au niveau fonctionnel :

- le scellement d’un état sensible ;
- la restauration contrôlée ;
- l’intégrité du blob ;
- le lien au contexte via les AAD ;
- la logique de compteur monotone ;
- la détection d’un rollback.

### Ce qui n’est pas un vrai TEE

Je ne dois pas survendre cette implémentation. Elle ne fournit pas :

- d’isolation matérielle forte ;
- de clé réellement inaccessible au monde normal ;
- de stockage anti-rollback matériel ;
- de service sécurisé indépendant du système d’exploitation hôte ;
- de garanties contre l’extraction locale si la machine entière est compromise.

### Limites cryptographiques assumées

Je fais aussi une distinction importante : le chiffrement mis en œuvre ici sert une **simulation pédagogique cohérente**, mais ce n’est pas un schéma de production mobile certifié. Dans une intégration réelle, je privilégierais un mécanisme standardisé fourni par le TEE ou par une bibliothèque validée.

### Limites d’intégration

Dans cette étape :

- je persiste les blobs dans le système de fichiers ;
- je simule la HUK et le compteur monotone par des fichiers JSON ;
- je dépends de l’intégrité de l’environnement d’exécution local.

Autrement dit, la logique de sécurité est correcte à l’échelle du prototype, mais l’enveloppe d’exécution reste logicielle.

## Ce qu’il faudra faire sur un vrai TEE mobile

Pour un portage réel, je devrai remplacer la simulation par des services fournis par la plateforme mobile :

- une clé liée au matériel ou au TEE ;
- une primitive de `seal / unseal` réellement isolée ;
- un stockage protégé contre le rollback, par exemple via RPMB ou équivalent ;
- une politique d’accès qui empêche le monde normal de lire l’état secret ;
- une gestion robuste des erreurs, de l’effacement et du cycle de vie de l’état ;
- idéalement, une journalisation de sécurité minimale et contrôlée.

Je devrai aussi préciser :

- où le compteur monotone réel est stocké ;
- comment il est synchronisé avec le blob ;
- quelle politique de récupération s’applique après détection d’un rollback ;
- quelles primitives cryptographiques natives de la plateforme sont utilisées.

## Conclusion

Avec cette étape, je complète l’architecture `SRC -> COND -> DRBG -> STATE` par une vraie couche dédiée à la **protection de la persistance du DRBG**. Cela me permet d’aller au-delà d’un simple générateur déterministe : je traite explicitement la question du stockage sécurisé de l’état, de l’intégrité, de l’anti-rollback et du lien avec un futur TEE mobile.

Pour le mémoire, cette étape est importante parce qu’elle montre que je ne réduis pas la sécurité du générateur à son seul cœur mathématique. Je prends aussi en compte le problème très concret de la **survie de l’état entre deux redémarrages**, qui est précisément l’un des points sensibles d’un RNG mobile défensif.

En résumé, je considère cette couche comme une **validation fonctionnelle de l’architecture de sécurité** : elle n’est pas encore un TEE réel, mais elle rend démontrable, testable et explicable la logique que je devrai ensuite porter vers un environnement mobile sécurisé.
