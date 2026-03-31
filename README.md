# Deploiement d'un RNG Mobile Post-Quantique

Prototype academique de RNG post-quantique structure autour de la baseline :

```text
SRC -> COND -> DRBG -> STATE
```

Le depot fournit aujourd'hui un prototype executable principalement en Python,
une API de type SDK local, une demonstration complete, une couche de validation
experimentale et une couche de benchmark logiciel.

## Statut du projet

- statut : prototype academique / experimental
- interface principale actuelle : SDK Python local
- moteur nominal : Multiplexed Sponge
- moteur secondaire : Module-LWR
- conditionneur officiel : Toeplitz + SHAKE-256
- NTT : optimisation future, non active dans la baseline executable actuelle

## Architecture resumee

```text
SRC : collecte d'entropie
  -> COND : Toeplitz + SHAKE-256
  -> DRBG : Multiplexed Sponge (nominal) / Module-LWR (secondaire)
  -> STATE : machine a etats + persistance protegee simulee
```

Documentation detaillee :

- [Architecture](docs/architecture_rng.md)
- [API](docs/api_specification.md)
- [Modele de securite](docs/security_model.md)
- [Conception materielle](docs/hardware_design.md)
- [Demonstration complete](docs/full_demo.md)

## Structure du depot

- `software/` : implementation du prototype
- `software/entropy/` : sources d'entropie et health checks
- `software/conditioner/` : Toeplitz + SHAKE-256
- `software/pqc_drbg/` : coeur DRBG et machine a etats
- `software/state_manager/` : sealing, restauration et anti-rollback simules
- `software/api/` : SDK Python local
- `analysis/` : validation statistique et reporting
- `benchmarks/` : benchmarks logiciels, energie et latence materielle
- `hardware/` : RTL, simulation, synthese et cibles FPGA
- `demo/` : demonstration complete
- `tests/` : tests unitaires et d'integration
- `docs/` : documentation technique

## Installation

Depuis la racine `pqc_mobile_rng` :

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Si `pytest` n'est pas deja disponible dans l'environnement, l'installation du
venv local reste recommandee pour reproduire les commandes du depot.

## Lancement principal

Demonstration complete :

```powershell
venv\Scripts\python.exe demo/run_full_project_demo.py
```

Usage SDK minimal :

```python
from software.api import rng_health, rng_init, rng_get_bytes

rng_init(force_reinit=True)
data = rng_get_bytes(32)
status = rng_health()
```

## Tests

Exemple de suite ciblee :

```powershell
venv\Scripts\python.exe -m pytest tests\test_entropy_layer.py tests\test_conditioner_layer.py tests\test_pqc_drbg_complete.py tests\test_public_api.py -q
```

Validation experimentale recente :

```powershell
venv\Scripts\python.exe -m pytest tests\test_entropy_validation.py tests\test_statistical_smoke.py tests\test_benchmarks.py -q
```

## Validation statistique

La couche `analysis/` couvre notamment :

- validation prudente de la source d'entropie ;
- comparaison avant / apres conditionnement ;
- tests statistiques inspires de SP 800-22 ;
- campagnes comparatives LWR vs Sponge ;
- reporting JSON / CSV / Markdown.

Ces resultats sont experimentaux et ne constituent pas une conformite NIST
formelle.

## Benchmarks

La couche `benchmarks/` fournit :

- benchmark logiciel local de `Module-LWR` et `Multiplexed Sponge` ;
- cadre honnete pour energie (`not_measured` si aucune mesure reelle) ;
- cadre honnete pour latence materielle (`not_measured` ou import de rapport).

Smoke benchmark :

```powershell
venv\Scripts\python.exe benchmarks\run_all_benchmarks.py
```

## Documentation disponible

- [docs/architecture_rng.md](docs/architecture_rng.md)
- [docs/api_specification.md](docs/api_specification.md)
- [docs/security_model.md](docs/security_model.md)
- [docs/hardware_design.md](docs/hardware_design.md)
- [docs/full_demo.md](docs/full_demo.md)

## Limites connues

- le projet n'est pas une API mobile finale ;
- la baseline executable reste un SDK Python local ;
- la couche `STATE` repose sur une simulation de TEE ;
- les benchmarks actuels sont d'abord des benchmarks logiciels locaux ;
- les tests statistiques ne sont pas une preuve cryptographique ;
- l'energie reelle et la latence materielle reelle ne sont pas mesurees par
  defaut dans le depot.

## Avertissements methodologiques

- ne pas presenter `Module-LWR` comme moteur nominal ;
- ne pas presenter la NTT comme deja integree a la baseline executable ;
- ne pas presenter les resultats AMD64 locaux comme des resultats smartphone ARM
  sans execution sur cible reelle ;
- ne pas revendiquer une conformite formelle SP 800-90A, SP 800-90B, SP 800-22,
  FIPS ou CMVP.

## Roadmap courte

- renforcer la documentation et la tracabilite experimentale ;
- executer des benchmarks sur vraie cible ARM quand elle est disponible ;
- documenter ou importer des rapports materiels reels ;
- etudier des optimisations futures, y compris la NTT, sans changer la baseline
  de reference tant qu'elles ne sont pas effectivement integrees.
