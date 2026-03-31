# Demonstration globale du projet

## But

Ce document explique comment lancer la demonstration complete du projet
`SRC -> COND -> DRBG -> STATE`.

Le point d'entree principal est :

- `demo/run_full_project_demo.py`

## Objectif

Avec cette demo, on montre de maniere structuree :

- l'architecture globale ;
- la collecte d'entropie brute ;
- le conditionnement Toeplitz + SHAKE-256 ;
- le moteur nominal `Multiplexed Sponge` ;
- le moteur secondaire `Module-LWR` ;
- le gestionnaire composite et ses politiques ;
- la machine a etats ;
- la couche `STATE` / TEE simule ;
- les verifications de securite essentielles.

## Commande d'execution

Depuis la racine `pqc_mobile_rng` :

```powershell
python demo/run_full_project_demo.py
```

Si l'environnement local utilise le venv du depot :

```powershell
venv\Scripts\python.exe demo/run_full_project_demo.py
```

## Ce que la demo affiche

La sortie terminal est organisee en sections numerotees. Elle montre notamment :

- les modules associes a chaque couche ;
- les symboles collectes par `CPUJitterSource` et `SensorEntropySource` ;
- les rapports de sante simples et les metadonnees de collecte ;
- la chaine `raw_data -> toeplitz_output -> Seedinit` ;
- la generation nominale `Multiplexed Sponge` et l'effet d'un `reseed` ;
- la generation du moteur secondaire `Module-LWR` ;
- le moteur actif du gestionnaire composite selon la politique ;
- les transitions `UNINITIALIZED -> READY -> NEED_RESEED -> FAIL_STOP -> ZEROIZED` ;
- un blob scelle, sa restauration, puis un checkpoint complet du DRBG ;
- la detection d'une alteration d'integrite ;
- la detection d'un rollback.

## Positionnement des moteurs

La demo garde une distinction explicite :

- `Multiplexed Sponge` est le moteur nominal ;
- `Module-LWR` est un moteur secondaire de recherche ;
- le fallback LWR n'est montre que comme comportement experimental controle.

## Robustesse de la demo

Les ajouts restent isoles dans `demo/` et dans cette documentation. La demo
gere les erreurs par section et les rend visibles dans le terminal au lieu
d'echouer silencieusement.

## Suite logique

Pour verifier que la demo n'introduit pas de regression :

```powershell
python -m pytest tests/test_entropy_layer.py tests/test_conditioner_layer.py tests/test_pqc_drbg_complete.py tests/test_pqc_drbg_state_machine.py tests/test_state_manager.py -q
```
