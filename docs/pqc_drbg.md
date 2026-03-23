# DRBG post-quantique - paramètres et statut d'implémentation

## 1. Rôle du DRBG dans l'architecture globale

Dans l'architecture officielle du prototype, la chaîne retenue reste :

```text
SRC -> COND -> DRBG -> STATE
```

Le DRBG reçoit une seed déjà conditionnée par `Toeplitz + SHAKE-256`, produit un flux déterministe post-initialisation et maintient un état interne contrôlé. Le moteur nominal reste `Module-LWR` ; le `Multiplexed Sponge` reste un moteur secondaire de recherche.

## 2. Paramètres cryptographiques du moteur nominal

Le dépôt exécute aujourd'hui un unique profil logiciel nominal pour `Module-LWR`.

### 2.1 Profil exécutable actuel

Le profil réellement utilisé par le code et par les tests est :

```text
module_lwr_proto_software_v1:
  n = 256
  k = 3
  q = 8192
  p = 1024
  secret = {-1, 0, 1}
```

Ce profil est exposé par [`params.py`](C:/Users/DELL/OneDrive/Desktop/Deploiement%20API%20MOBILE%20POST%20QUANTIQUES/pqc_mobile_rng/software/pqc_drbg/params.py#L1) et injecté par défaut dans [`lwr_core.py`](C:/Users/DELL/OneDrive/Desktop/Deploiement%20API%20MOBILE%20POST%20QUANTIQUES/pqc_mobile_rng/software/pqc_drbg/lwr_core.py#L1).

### 2.2 Pourquoi ce profil reste la baseline exécutable

Ce profil est conservé comme baseline exécutable pour trois raisons :

- il correspond exactement au comportement courant du dépôt ;
- il est déjà cohérent avec les tests et avec la démonstration logicielle ;
- il ne dépend d'aucune optimisation NTT active.

En particulier, le ratio `q/p = 8` garde une logique d'arrondi simple dans le prototype actuel.

## 3. Décision définitive sur les profils de paramètres

Pour supprimer les contradictions entre code et manuscrit, trois profils distincts sont désormais figés.

| Profil | n | k | q | p | Statut | Implémenté maintenant ? | Commentaire |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Prototype logiciel exécutable | 256 | 3 | 8192 | 1024 | Baseline active | Oui | Profil réellement exécuté par le dépôt, sans NTT |
| Manuscrit de référence | 256 | 3 | 8192 | 1024 | Référence pour les résultats implémentés | Oui | Les résultats expérimentaux du prototype doivent être reportés avec ce profil |
| Optimisation mobile future | 256 | 3 | 3329 | À confirmer | Variante documentaire future | Non | `q = 3329` n'est pas activé dans le code courant ; `p` n'est pas figé dans le dépôt |

## 4. Place exacte de la NTT

La `NTT` n'appartient pas à la baseline exécutable actuelle.

Dans ce projet, elle doit être comprise comme :

- une contrainte de conception pour une variante future ;
- un motif expliquant pourquoi un manuscrit peut discuter `q = 3329` ;
- une optimisation mobile ou matérielle encore séparée du prototype Python courant.

Conséquence directe : le profil `q = 3329` ne doit jamais être présenté comme déjà déployé dans le prototype logiciel tant qu'aucune implémentation NTT réellement active n'apparaît dans le dépôt et dans les tests.

## 5. Ce qui est implémenté et ce qui ne l'est pas

### 5.1 Implémenté maintenant

Les éléments suivants sont effectivement implémentés :

- un moteur nominal `Module-LWR` ;
- un profil par défaut `n = 256`, `k = 3`, `q = 8192`, `p = 1024` ;
- une génération déterministe post-initialisation ;
- un moteur secondaire `Multiplexed Sponge` pour la recherche ;
- une machine à états explicite ;
- un export d'état non sensible.

### 5.2 Futur ou documentaire

Les éléments suivants ne doivent pas être confondus avec l'état réel du dépôt :

- une variante `q = 3329` exécutée dans le code nominal ;
- une compatibilité NTT effectivement activée ;
- une preuve de choix définitif de `p` pour la variante mobile future ;
- une migration complète du prototype courant vers une nouvelle arithmétique.

## 6. Consigne de rédaction pour le manuscrit

Pour éviter toute contradiction dans le mémoire :

- le Chapitre 5 doit présenter les résultats expérimentaux avec le profil réellement exécuté `n = 256`, `k = 3`, `q = 8192`, `p = 1024` ;
- le Chapitre 4 peut discuter `q = 3329` uniquement comme cible d'optimisation mobile ou variante future liée à une contrainte NTT ;
- le texte doit expliciter que cette variante future n'est pas encore la baseline logicielle du dépôt.

Une formulation sûre est la suivante :

> Le prototype logiciel exécuté dans ce mémoire utilise actuellement le profil `n = 256`, `k = 3`, `q = 8192`, `p = 1024` pour le moteur `Module-LWR`. Une variante future orientée optimisation mobile peut être étudiée avec `q = 3329` dans un cadre compatible NTT, mais cette variante n'est pas encore intégrée au chemin d'exécution nominal du dépôt.

## 7. Impact sur l'interface logicielle

Le gel des paramètres ne modifie pas l'API du composant `PQCCompositeDRBG`.

Le comportement public reste :

- `instantiate(...)`
- `generate(...)`
- `reseed(...)`
- `export_state()`
- `zeroize()`

Le changement de cette étape est documentaire et structurel : il sépare explicitement le profil exécuté aujourd'hui des profils discutés pour la suite.
