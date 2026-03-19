# DRBG post-quantique : coeur composite Module-LWR + Multiplexed Sponge

## Rôle du DRBG dans l'architecture globale

Dans mon architecture globale, je garde la chaîne suivante :

```text
SRC -> COND -> DRBG -> STATE
```

Je place le DRBG après la source d'entropie `SRC` et le conditionneur `COND`.
Dans cette étape, je veux que le DRBG :
- reçoive une seed déjà conditionnée ;
- fournisse une sortie déterministe reproductible ;
- maintienne un état interne contrôlé ;
- applique des règles de sécurité explicites ;
- arrête proprement la génération si un état critique apparaît.

Le DRBG n'est donc pas une source d'entropie brute. Je l'utilise comme
générateur déterministe post-initialisation.

## Pourquoi je retiens Module-LWR comme moteur nominal

Je considère ici **Module-LWR** comme moteur nominal du système.

Je fais ce choix pour trois raisons principales :
- je peux relier son fonctionnement à une structure mathématique claire ;
- je peux expliquer sa transition d'état de façon pédagogique dans le mémoire ;
- je peux conserver une génération déterministe avec une mutation interne explicite.

Le coeur LWR suit la logique suivante :
1. Je dérive deux graines internes depuis `seed_material` :
   - une graine secrète pour le vecteur secret `s` ;
   - une graine publique `seed_a` pour reconstruire la matrice `A`.
2. Je reconstruis ensuite `A`.
3. Je calcule `A * s mod q`.
4. J'applique la réduction de type LWR :
   `floor((p / q) * (A * s)) mod p`.
5. Je recompresse ce résultat avec `SHAKE-256` pour obtenir le nouvel état.

Dans le code, je sépare volontairement :
- la logique mathématique dans `software/pqc_drbg/lattice_math.py` ;
- les paramètres dans `software/pqc_drbg/params.py` ;
- le moteur nominal dans `software/pqc_drbg/lwr_core.py`.

Je garde cette séparation pour mieux expliquer le comportement dans le mémoire
et pour limiter les états incohérents.

## Quel est le rôle exact du Multiplexed Sponge

Je réserve le **Multiplexed Sponge** aux scénarios de recherche, de comparaison
ou de disponibilité technique non critique.

Je ne le traite pas comme un remplaçant silencieux du moteur nominal.
Je l'encapsule dans `software/pqc_drbg/sponge_core.py` via
`MultiplexedSpongeAdapter`.

Dans cette couche :
- je l'adapte au même contrat `instantiate / reseed / generate / export_state / zeroize / health` ;
- je l'initialise à partir d'un digest compact dérivé de la seed ;
- je garde sa nature expérimentale visible dans la politique et dans la machine à états.

Si `additional_input` est fourni pendant `generate`, je le transforme en rekey
explicite du moteur sponge. Je préfère cette approche à une mutation implicite
peu lisible, car elle est plus défendable dans un mémoire.

## Interface commune des moteurs

Je normalise les deux moteurs autour de l'interface `DRBGEngine`
dans `software/pqc_drbg/interfaces.py`.

Je veux que chaque moteur fournisse exactement :
- `instantiate(seed_material, personalization=b"")`
- `reseed(seed_material, additional_input=b"")`
- `generate(nbytes, additional_input=b"")`
- `export_state()`
- `zeroize()`
- `health()`

Je complète ce contrat avec `EngineHealth`, qui permet d'exposer :
- le nom du moteur ;
- son état de santé ;
- une raison textuelle ;
- des détails non sensibles pour le diagnostic.

## Machine à états

Je formalise la machine à états dans `software/pqc_drbg/state.py`.

Je distingue les états suivants :
- `UNINITIALIZED`
- `READY`
- `NEED_RESEED`
- `FAIL_STOP`
- `ZEROIZED`
- `DEGRADED_RESEARCH`

### Sens de chaque état

- `UNINITIALIZED`
  Je n'ai pas encore instancié le DRBG.
- `READY`
  Je peux générer normalement avec le moteur actif.
- `NEED_RESEED`
  Je refuse toute nouvelle génération tant qu'un reseed explicite n'a pas eu lieu.
- `FAIL_STOP`
  Je verrouille le système après une faute critique de santé ou d'intégrité.
- `ZEROIZED`
  Je représente une destruction logique volontaire de l'état interne.
- `DEGRADED_RESEARCH`
  J'indique que je tourne volontairement sur le moteur sponge dans un cadre
  expérimental ou de disponibilité contrôlée.

### Transitions principales

- `UNINITIALIZED -> READY`
  Je réalise cette transition après une initialisation nominale LWR.
- `UNINITIALIZED -> DEGRADED_RESEARCH`
  Je réalise cette transition si la politique force le sponge ou autorise un
  fallback expérimental sur indisponibilité technique du LWR.
- `READY -> NEED_RESEED`
  Je réalise cette transition si la politique impose un reseed.
- `NEED_RESEED -> READY`
  Je réalise cette transition après un reseed explicite réussi.
- `READY -> FAIL_STOP`
  Je réalise cette transition si la santé du moteur actif échoue et que la
  politique demande un arrêt strict.
- `READY -> ZEROIZED`
  Je réalise cette transition après `zeroize()`.

Je refuse les transitions ambiguës au moyen d'erreurs dédiées.

## Politiques de sélection du moteur

Je définis les politiques dans `software/pqc_drbg/policy.py`.

Je distingue trois modes :
- `STRICT_LWR_ONLY`
- `ALLOW_EXPERIMENTAL_SPONGE_FALLBACK`
- `FORCE_SPONGE_RESEARCH`

### `STRICT_LWR_ONLY`

Je considère ce mode comme le mode nominal.
Je n'autorise pas le sponge comme moteur actif.

### `ALLOW_EXPERIMENTAL_SPONGE_FALLBACK`

Je n'autorise ici le sponge que pour un cas précis :
- une indisponibilité technique du moteur LWR au moment de l'instanciation.

Je n'autorise pas ce mode à masquer :
- un échec de santé du moteur actif ;
- une faute d'intégrité ;
- un besoin de reseed ;
- un `FAIL_STOP`.

Autrement dit, je peux tolérer une dégradation contrôlée de disponibilité,
mais je refuse de cacher un problème de sécurité.

### `FORCE_SPONGE_RESEARCH`

Je réserve ce mode aux expériences, aux comparaisons et à l'analyse académique.
Dans ce cas, je rends visible l'état `DEGRADED_RESEARCH`.

## Quand le système entre en FAIL_STOP

Je verrouille le système en `FAIL_STOP` si la santé logique du moteur actif
échoue pendant la phase de génération et que la politique
`fail_stop_on_health_error` est active.

Concrètement, je n'accepte pas qu'un problème critique soit masqué par :
- un fallback silencieux ;
- une régénération opportuniste ;
- une bascule automatique vers le sponge.

Une fois en `FAIL_STOP` :
- je bloque `generate` ;
- je bloque `reseed` ;
- je bloque `instantiate`.

Je demande alors une réinitialisation explicite du système. Dans l'implémentation
actuelle, cette remise à zéro explicite passe par `zeroize()` puis par une
nouvelle instanciation dans un nouveau cycle logiciel.

## Gestion des erreurs

Je sépare plusieurs familles d'erreurs dans `software/pqc_drbg/errors.py` :
- `DRBGError`
- `InvalidDRBGStateError`
- `InvalidStateTransitionError`
- `HealthCheckError`
- `ReseedRequiredError`
- `EngineUnavailableError`
- `FailStopError`

Je garde cette séparation pour distinguer clairement :
- les erreurs de logique d'état ;
- les erreurs de santé ;
- les erreurs de politique ;
- les erreurs d'indisponibilité ;
- les arrêts critiques.

## Sécurité logicielle appliquée dans cette étape

Dans le cadre Python du prototype, j'améliore les points suivants :
- validation stricte des seeds et des tailles de sortie ;
- validation des paramètres `LWRParams` ;
- séparation entre état sensible et export d'observabilité ;
- `zeroize()` sur chaque moteur et sur l'orchestrateur ;
- refus des transitions ambiguës ;
- refus des fallbacks silencieux après faute critique ;
- exposition explicite du mode dégradé de recherche.

Je reste cependant dans un prototype Python pédagogique. Je ne prétends pas
obtenir ici une garantie d'effacement mémoire forte au niveau bas.

## Comment lancer les tests

Depuis la racine `pqc_mobile_rng`, je lance :

```powershell
venv\Scripts\pytest.exe tests/test_pqc_drbg.py -q
```

Pour vérifier toute la non-régression du projet, je peux lancer :

```powershell
venv\Scripts\pytest.exe -q
```

## Ce que couvrent maintenant les tests DRBG

Je couvre explicitement :
- le déterminisme du moteur LWR ;
- l'effet d'un reseed sur le flux LWR ;
- la sélection nominale du moteur LWR ;
- le mode sponge forcé pour la recherche ;
- le fallback sponge limité à l'indisponibilité d'instanciation ;
- l'état `NEED_RESEED` ;
- l'état `FAIL_STOP` ;
- l'état `ZEROIZED` ;
- l'export d'état non sensible ;
- la cohérence déterministe du moteur sponge ;
- l'effet explicite de `additional_input` sur le sponge.

## Limites actuelles

Je laisse volontairement plusieurs limites ouvertes pour ne pas déstabiliser le projet :
- je reste sur un prototype Python, pas sur une implémentation optimisée ou certifiable ;
- je n'introduis pas ici de TEE, de scellement d'état ou d'anti-rollback ;
- je ne traite pas encore l'effacement mémoire fort au niveau runtime ;
- je ne change pas la structure générale `SRC -> COND -> DRBG -> STATE` ;
- je ne remplace pas le prototype sponge par une construction standardisée ;
- je ne transforme pas cette couche en API HTTP, SDK mobile ou composant système complet.

Cette version est donc plus robuste, plus explicable et mieux testée, mais elle
reste un coeur expérimental destiné à un mémoire et à un durcissement progressif.
