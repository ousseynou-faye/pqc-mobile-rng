# Démonstration globale du projet

## But

Dans ce document, j'explique comment lancer la démonstration complète du projet
`SRC -> COND -> DRBG -> STATE`.

Le point d'entrée principal est :

- `demo/run_full_project_demo.py`

## Objectif

Avec cette démo, je montre de manière structurée :

- l'architecture globale ;
- la collecte d'entropie brute ;
- le conditionnement Toeplitz + SHAKE-256 ;
- le moteur nominal `Module-LWR` ;
- le moteur secondaire `Multiplexed Sponge` ;
- le gestionnaire composite et ses politiques ;
- la machine à états ;
- la couche `STATE` / TEE simulé ;
- les vérifications de sécurité essentielles.

## Commande d'exécution

Depuis la racine `pqc_mobile_rng`, je lance :

```powershell
python demo/run_full_project_demo.py
```

Si je veux utiliser explicitement l'interpréteur du virtualenv local :

```powershell
venv\Scripts\python.exe demo/run_full_project_demo.py
```

## Ce que la démo affiche

La sortie terminal est organisée en sections numérotées.

Je montre notamment :

- les modules associés à chaque couche ;
- les symboles collectés par `CPUJitterSource` et `SensorEntropySource` ;
- les rapports de santé simples et les métadonnées de collecte ;
- les octets bruts exportés par le pool ;
- la chaîne `raw_data -> toeplitz_output -> Seedinit` ;
- la génération nominale `Module-LWR` et l'effet d'un `reseed` ;
- la génération du moteur secondaire `Multiplexed Sponge` ;
- le moteur actif du gestionnaire composite selon la politique ;
- les transitions `UNINITIALIZED -> READY -> NEED_RESEED -> FAIL_STOP -> ZEROIZED` ;
- un blob scellé, sa restauration, puis un checkpoint complet du DRBG ;
- la détection d'une altération d'intégrité ;
- la détection d'un rollback.

## Positionnement des moteurs

Je garde une distinction explicite dans la démo :

- `Module-LWR` est le moteur nominal ;
- `Multiplexed Sponge` est un moteur secondaire de recherche ;
- le fallback sponge n'est montré que comme comportement expérimental contrôlé.

## Robustesse de la démo

J'ai isolé les ajouts dans `demo/` et dans cette documentation.

Je n'ai pas modifié :

- les interfaces publiques de `software/entropy/` ;
- les interfaces publiques de `software/conditioner/` ;
- les interfaces publiques de `software/pqc_drbg/` ;
- les interfaces publiques de `software/state_manager/`.

La démo gère les erreurs par section et les rend visibles dans le terminal au
lieu d'échouer silencieusement.

## Suite logique

Pour vérifier que la démo n'introduit pas de régression, je peux ensuite lancer :

```powershell
python -m pytest tests/test_entropy_layer.py tests/test_conditioner_layer.py tests/test_pqc_drbg_complete.py tests/test_pqc_drbg_state_machine.py tests/test_state_manager.py -q
```
