# State Manager

Le `StateManager` scelle et restaure des payloads JSON deterministes.

## Cas DRBG

Le payload scellable du DRBG contient:

- `version`
- `manager_state`
- `sponge_private_state`

Exemple:

```json
{
  "version": 1,
  "manager_state": {
    "active_engine": "multiplexed_sponge",
    "lifecycle_state": "ready"
  },
  "sponge_private_state": {
    "initialized": true,
    "generate_counter": 3
  }
}
```

La restauration refuse un moteur actif incoherent avec la baseline sponge-only.
