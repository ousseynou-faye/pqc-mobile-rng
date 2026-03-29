# Trajectoire mobile

## Etat reel du depot

Le depot n'est pas "mobile ready" a ce stade.
La baseline executable reste le SDK Python local et son chemin canonique:

`SRC -> COND -> DRBG -> STATE`

Ce qui existe reellement aujourd'hui:

- un SDK Python avec une API publique stable
- une orchestration canonique dans `software/api/rng_service.py`
- une couche de persistance d'etat simulee
- des benchmarks et des validations statistiques locales

Ce qui n'existe pas encore:

- pas d'integration Android effective
- pas de driver Linux ou Android pour un terminal mobile reel
- pas de wrapper JNI ou NDK valide sur appareil
- pas de FFI native stable en C ou Rust dans ce depot
- pas de mesures de performance realisees sur une vraie cible ARM mobile dans cette etape

## Choix retenu pour l'etape 10

La trajectoire retenue est prudente:

- Python reste l'implementation de reference
- une couche de transition mobile est ajoutee sous forme de specifications et de bridge Python
- aucun fichier ne pretend fournir une pile mobile deployable aujourd'hui

## Frontiere technique retenue

La separation choisie est la suivante:

- Python conserve le role de reference academique, d'orchestrateur et de surface de validation
- la future migration mobile visera le coeur d'execution du DRBG et la frontiere binaire autour de `instantiate`, `generate`, `reseed`, `health` et `zeroize`
- `export_state` et `import_state` restent desactives dans la baseline mobile pour des raisons de securite et de couplage au modele Python actuel

## Fichiers ajoutes pour cette trajectoire

- `mobile/ffi_spec.md`
- `mobile/buffer_format.md`
- `mobile/reseed_policy.md`
- `mobile/arm_profiling.md`
- `software/interface_hw/mobile_bridge.py`
- `benchmarks/mobile_profile.py`

## Regle d'interpretation

Ces ajouts doivent etre lus correctement:

- le bridge Python est un contrat de transition, pas un wrapper mobile natif
- le script de profilage decrit un protocole et exporte des metadonnees d'environnement
- toute integration JNI, NDK, driver, Secure Element ou TEE reel reste future et hors du perimetre executable actuel
