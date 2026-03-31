# Tests et validation

## Strategie generale

Le depot contient plusieurs niveaux de validation:

- tests unitaires des briques de base
- tests d'integration du pipeline
- tests d'API publique
- tests de demonstrations
- smoke tests statistiques
- benchmarks et campagnes de comparaison

## Tests directement lies a cette passe

### `tests/test_output_formats.py`

Verifie:

- conversion bytes -> decimal
- conversion bytes -> hex
- conversion bytes -> binaire
- convention `big-endian`
- reproductibilite
- rejet des entrees invalides

### `tests/test_demo_outputs.py`

Verifie:

- execution des demos sans erreur
- presence des sections attendues
- presence des sorties `Hex`, `Decimal`, `Binary`

### `tests/test_public_api.py`

Verifie maintenant aussi:

- `rng_get_output_formats()`
- coherence de `format_output_bytes()`

## Couverture existante utile

### Pipeline et service

- `tests/test_rng_service.py`
- `tests/test_end_to_end_pipeline.py`
- `tests/test_public_api.py`
- `tests/test_api_contract.py`

### Conditioner

- `tests/test_conditioner_layer.py`
- `tests/test_entropy_validation.py`

### Multiplexed Sponge et LFSR

- `tests/test_multiplexed_sponge.py`
- `tests/test_phi_and_multiplexing.py`
- `tests/test_sponge_seed_derivation.py`
- `tests/test_lfsr_core.py`

### Etat et machine a etats

- `tests/test_pqc_drbg_complete.py`
- `tests/test_pqc_drbg_state_machine.py`
- `tests/test_state_manager.py`

### Validation statistique

- `tests/test_statistical_smoke.py`
- `tests/test_analysis_metrics.py`

## Commandes utiles

### Validation ciblee

```bash
pytest tests/test_output_formats.py tests/test_demo_outputs.py tests/test_public_api.py tests/test_rng_service.py tests/test_end_to_end_pipeline.py
```

### Validation plus large

```bash
pytest tests
```

## Limites de validation

- les tests statistiques ne prouvent pas la securite cryptographique
- les demonstrations testees garantissent surtout la lisibilite et l'absence d'erreur d'execution
- la presence d'un format decimal ne change pas les proprietes du DRBG, elle ameliore seulement son observabilite
