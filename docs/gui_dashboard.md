# Interface graphique locale

## Objectif

Cette interface est un tableau de bord scientifique local.
Elle sert a:
- visualiser le pipeline `SRC -> COND -> DRBG -> STATE`
- tester les fonctions principales du prototype
- presenter clairement le projet pendant le memoire ou la soutenance

Elle n'est pas:
- une application mobile finale
- une preuve d'integration Android ou Linux embarquee
- une preuve de conformite cryptographique

## Lancement

Depuis la racine `pqc_mobile_rng`:

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
streamlit run ui/Home.py
```

## Navigation recommandee

Pour une demonstration claire, suivez cet ordre:

1. `Accueil`
2. `Architecture`
3. `SRC`
4. `COND`
5. `DRBG`
6. `STATE`
7. `Validation`
8. `Benchmarks`
9. `Documentation`

## Modes d'affichage

L'interface propose deux niveaux de lecture:
- `pedagogique` pour une vue epuree et facile a expliquer
- `technique` pour afficher plus de details, de journaux et de contextes

## Sorties RNG

La page `DRBG` permet maintenant de lire les sorties sous plusieurs formes:
- apercu hexadecimal
- apercu binaire tronque
- tableau decimal des octets
- histogramme simple des valeurs generees
- resume statistique local

La vue decimale est utile pour:
- montrer la variabilite des octets
- commenter la distribution locale
- presenter les sorties de maniere plus intuitive devant un jury

## Regles d'affichage et de securite

L'interface applique plusieurs garde-fous:
- les apercus binaires sont tronques
- les blobs d'etat sont resumes
- les seeds completes ne sont pas exposees par defaut
- les etats internes prives restent masques
- `multiplexed_sponge` est clairement marque comme moteur secondaire de recherche

## Conseils de demonstration

- commencez par rappeler que le moteur nominal est `Module-LWR`
- utilisez `SRC` puis `COND` pour montrer la construction de `Seedinit`
- utilisez `DRBG` pour comparer les vues hex, binaire et decimale
- utilisez `STATE` pour expliquer checkpoint, restore et zeroize
- utilisez `Validation` et `Benchmarks` uniquement comme indicateurs experimentaux locaux

## Avertissements methodologiques

- les benchmarks affiches sont des benchmarks locaux Python
- sans cible ARM reelle, aucune conclusion mobile de performance ne doit etre tiree
- les tests statistiques affiches sont experimentaux
- la couche `STATE` repose sur une simulation de TEE dans le prototype actuel
- l'interface ne doit jamais etre presentee comme une preuve cryptographique ou comme un deploiement mobile final
