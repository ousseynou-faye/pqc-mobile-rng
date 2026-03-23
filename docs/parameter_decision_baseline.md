# Décision de paramètres - baseline officielle

## Statut

Acceptée - version de référence `v1.0` pour l'Étape 2.

## Objet

Cette décision gèle définitivement la manière de présenter les paramètres cryptographiques du prototype mémoire, afin de supprimer la contradiction entre :

- le code effectivement exécuté ;
- les discussions documentaires autour de la NTT ;
- la rédaction du manuscrit.

## 1. Profil du prototype logiciel exécutable

Le profil exécutable officiel est :

```text
module_lwr_proto_software_v1:
  n = 256
  k = 3
  q = 8192
  p = 1024
  secret = {-1, 0, 1}
```

Justification :

- ce profil est effectivement utilisé par `software/pqc_drbg/params.py` ;
- c'est le profil injecté par défaut dans `ModuleLWRCore` ;
- c'est le profil compatible avec le comportement testé actuellement ;
- il n'introduit aucune dépendance à une NTT active.

Conséquence :

- tous les résultats produits par le prototype Python doivent être rapportés avec ce profil.

## 2. Profil d'optimisation mobile future

Le dépôt autorise seulement une décision partielle à ce stade :

```text
module_lwr_mobile_future_ntt_candidate:
  n = 256
  k = 3
  q = 3329
  p = à confirmer
```

Justification :

- `q = 3329` est la valeur documentaire explicitement citée pour une trajectoire future compatible avec une contrainte NTT ;
- aucune implémentation NTT active n'a été trouvée dans le dépôt ;
- aucune valeur de `p` n'est suffisamment établie dans le dépôt pour être injectée honnêtement dans le code courant.

Conséquence :

- cette variante reste documentaire et prospective ;
- elle ne doit pas remplacer le profil exécutable actuel.

## 3. Profil de référence pour le manuscrit

La règle de rédaction est la suivante :

- pour les résultats effectivement obtenus sur le prototype, le manuscrit utilise le profil `n = 256`, `k = 3`, `q = 8192`, `p = 1024` ;
- pour les perspectives d'optimisation mobile, le manuscrit peut discuter `q = 3329` dans une sous-partie explicitement marquée comme future ;
- les deux profils ne doivent jamais être fusionnés comme s'il s'agissait d'un seul paramétrage déjà implémenté.

## 4. Arbitrage final

À partir de cette décision :

- `q = 8192` reste la vérité du prototype logiciel exécutable ;
- `q = 3329` devient une cible documentaire future, pas un paramètre courant du dépôt ;
- `p = 1024` reste la valeur active du code actuel ;
- tout futur `p` lié à la variante mobile doit être confirmé avant toute modification fonctionnelle.

## 5. Texte prêt à copier - Chapitre 4

> Le prototype logiciel actuellement implémenté conserve le profil `Module-LWR` défini par `n = 256`, `k = 3`, `q = 8192` et `p = 1024`. Dans une perspective d'optimisation mobile, une variante future compatible avec une contrainte NTT peut être étudiée autour de `q = 3329`. Cette variante n'est toutefois pas intégrée à la baseline exécutable du dépôt à ce stade ; elle relève d'une trajectoire de travail ultérieure.

## 6. Texte prêt à copier - Chapitre 5

> Tous les résultats expérimentaux rapportés pour le prototype logiciel ont été obtenus avec le profil effectivement exécuté dans le dépôt, à savoir `n = 256`, `k = 3`, `q = 8192` et `p = 1024`. Les discussions relatives à `q = 3329` concernent une variante future orientée optimisation mobile et ne doivent pas être interprétées comme une description du chemin d'exécution actuellement validé.

## 7. Ce qu'il ne faut plus écrire

Les formulations suivantes doivent être évitées sans précision :

- `le prototype courant utilise q = 3329` ;
- `la NTT est déjà active dans le code nominal` ;
- `les résultats actuels ont été obtenus avec le profil mobile futur` ;
- `p a déjà été figé pour la variante NTT` lorsque ce n'est pas documenté dans le dépôt.
