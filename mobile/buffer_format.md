# Format binaire des buffers

## Objectif

Ce document definit le format des buffers echanges sur la frontiere mobile.
Le format retenu est volontairement simple pour rester exploitable plus tard depuis:
- C
- Rust
- JNI
- Python

## Proprietes generales

Le format est:
- binaire
- little-endian
- prefixe par longueur
- sans padding implicite en dehors de l'en-tete documente

Types utilises:
- `u8` : 1 octet
- `u16` : 2 octets
- `u32` : 4 octets

## En-tete commun de trame

Chaque trame commence par l'en-tete suivant:

| champ | type | taille | signification |
| --- | --- | --- | --- |
| `magic` | `bytes[4]` | 4 | signature ASCII fixe `PMBR` |
| `version` | `u8` | 1 | version du protocole, actuellement `1` |
| `code` | `u8` | 1 | opcode pour une requete, code de statut pour une reponse |
| `flags` | `u16` | 2 | reserve, valeur actuelle `0` |
| `request_id` | `u32` | 4 | identifiant de correlation fourni par l'appelant |
| `payload_len` | `u32` | 4 | longueur du payload en octets |
| `detail_code` | `u32` | 4 | reserve, valeur actuelle `0` |

Taille totale de l'en-tete:
- 20 octets

## Payloads de requete

### Requete `instantiate`

Payload:
- `u16 personalization_len`
- `bytes personalization`

### Requete `generate`

Payload:
- `u32 requested_len`
- `u16 additional_input_len`
- `bytes additional_input`

### Requete `reseed`

Payload:
- `u16 additional_input_len`
- `bytes additional_input`

### Requete `health`

Payload:
- vide

### Requete `zeroize`

Payload:
- vide

## Payloads de reponse

### Reponse `instantiate`

Payload:
- vide en cas de succes

### Reponse `generate`

Payload:
- octets pseudo-aleatoires generes

### Reponse `reseed`

Payload:
- vide en cas de succes

### Reponse `zeroize`

Payload:
- vide en cas de succes

### Reponse `health`

Payload:
- `u8 initialized`
- `u8 state_available`
- `u8 health_code`
- `u8 lifecycle_code`
- `u32 capability_flags`

Interpretation:
- `initialized` vaut `1` si le service est initialise, sinon `0`
- `state_available` vaut `1` si un etat scelle est detecte, sinon `0`

## Codes de capacite

Dans `capability_flags`:
- bit `0` : instance active presente
- bit `1` : reseed supporte

## Codes de sante

- `0` : `ok`
- `1` : `warning`
- `2` : `error`
- `255` : `unknown`

## Codes de cycle de vie

- `0` : `absent_or_unknown`
- `1` : `ready`
- `2` : `need_reseed`
- `3` : `fail_stop`
- `4` : `zeroized`
- `255` : `other`

## Reponses en erreur

Pour toute reponse avec un statut non nul:
- le payload est vide dans la baseline actuelle
- `detail_code` reste reserve pour une evolution future
- l'appelant doit mapper le code de statut vers une exception ou un enum dans sa couche d'integration

## Regles de compatibilite

Une implementation conforme doit:
- rejeter une valeur `magic` inconnue
- rejeter une `version` non supportee
- rejeter une trame tronquee
- rejeter un payload dont la longueur effective ne correspond pas a `payload_len`
- rejeter toute trame dont `flags` n'est pas nul, afin de conserver une evolution de protocole propre
