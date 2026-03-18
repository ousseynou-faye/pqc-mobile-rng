# Metriques experimentales du Multiplexed Sponge

## 1. But de cette etape

Dans cette etape, je ne cherche pas a prouver formellement la securite
cryptographique ou post-quantique du prototype. Mon objectif est plus modeste
et plus experimental : je veux mesurer plusieurs proprietes mathematiques et
statistiques de la sequence binaire produite par le prototype Multiplexed
Sponge.

J'ajoute donc une couche d'analyse separee du coeur du prototype, afin de :

- conserver la stabilite du code deja valide ;
- produire des mesures reutilisables dans le memoire ;
- documenter clairement les limites de ces observations.

## 2. Metriques implementees

J'ai organise cette couche dans le dossier `analysis/` avec les modules
suivants :

- `generators.py` : generation et validation d'echantillons binaires ;
- `bit_metrics.py` : distribution empirique des 0 et des 1 ;
- `run_metrics.py` : extraction et resume des runs ;
- `period_metrics.py` : estimation d'une periode observee ;
- `linear_complexity.py` : approximation de la complexite lineaire par
  Berlekamp-Massey ;
- `golomb_checks.py` : quelques indicateurs simples inspires des proprietes de
  Golomb ;
- `report.py` : construction d'un rapport consolide.

## 3. Signification des metriques

### 3.1 Periode observee

J'estime ici le plus petit decalage qui reproduit exactement la fenetre
observee sur sa partie comparable.

Important :

- il s'agit d'une periode observee sur un echantillon fini ;
- ce n'est pas necessairement la periode theorique complete ;
- si l'echantillon est trop court, la mesure peut etre trompeuse.

### 3.2 Distribution 0/1

Je mesure le nombre de 0, le nombre de 1, ainsi que leurs frequences
empiriques. Cette mesure me permet de regarder rapidement l'equilibre binaire
de l'echantillon.

### 3.3 Runs

Je recense les suites consecutives de bits identiques, par exemple `111` ou
`00`. Je resume ensuite :

- le nombre total de runs ;
- la plus grande longueur de run ;
- la longueur moyenne ;
- la repartition des runs par longueur ;
- la repartition des runs selon le bit porte (0 ou 1).

### 3.4 Complexite lineaire

J'utilise l'algorithme de Berlekamp-Massey sur une sequence binaire finie pour
obtenir une approximation de la complexite lineaire de l'echantillon.

Je rappelle ici une limite essentielle :

- le resultat depend de la longueur analysee ;
- il ne suffit pas a caracteriser a lui seul la robustesse cryptographique du
  generateur.

### 3.5 Indicateurs inspires de Golomb

Je calcule quelques indicateurs simples :

- ecart d'equilibre entre le nombre de 0 et de 1 ;
- ecart entre le nombre de runs de 0 et de runs de 1 ;
- plus long run observe ;
- comparaison empirique entre le nombre de runs de longueur `k` et une valeur
  attendue approximative de type geometrique.

Je reste volontairement prudent : ces indicateurs ne constituent pas une
verification formelle des postulats de Golomb.

## 4. Interpretation des resultats

J'interprete ces metriques comme des indicateurs experimentaux :

- un bon equilibre 0/1 est souhaitable ;
- des runs tres desequilibres ou anormalement longs peuvent signaler un biais ;
- une complexite lineaire tres faible sur un echantillon long serait un signal
  negatif ;
- une petite periode observee sur une grande fenetre peut suggerer une
  structure repetitive trop visible.

En revanche, aucune de ces mesures ne permet a elle seule de conclure a la
securite du prototype.

## 5. Limites methodologiques

- les mesures dependent fortement de la taille de l'echantillon ;
- une bonne apparence statistique ne prouve pas la securite cryptographique ;
- la periode observee peut sous-estimer ou surestimer le comportement global ;
- la complexite lineaire mesuree sur une fenetre finie reste une approximation ;
- les indicateurs de Golomb implantes ici sont simples et pedagogiques.

## 6. Comment lancer les fonctions ou le rapport

Depuis la racine `pqc_mobile_rng`, je peux utiliser les fonctions directement.

### Exemple avec une suite de recurrence

```python
from analysis.generators import bits_from_object
from analysis.report import build_bit_sequence_report
from software.lfsr.recurrence_sequences import RecurrenceSequence

sequence = RecurrenceSequence(degree=8, seed=0xA5)
bits = bits_from_object(sequence, 64)
report = build_bit_sequence_report(bits, max_period=32)

print(report["bit_balance"])
print(report["observed_period"])
```

### Exemple avec le Multiplexed Sponge

```python
from analysis.report import build_sponge_report
from software.lfsr.recurrence_sequences import RecurrenceSequence
from software.sponge.multiplexed_sponge import MultiplexedSponge

seq_s = RecurrenceSequence(degree=8, seed=0xA5)
seq_t = RecurrenceSequence(degree=9, seed=0x101)
sponge = MultiplexedSponge(seq_s=seq_s, seq_t=seq_t, l=4, rate=32, capacity=32)

report = build_sponge_report(
    sponge,
    n_bits=64,
    absorb_blocks=[0x12, 0x34],
    block_size=8,
    max_period=32,
)

print(report["bit_balance"])
print(report["linear_complexity"])
```

## 7. Exemple de sortie

Exemple de structure de rapport :

```python
{
    "sample_length": 64,
    "bit_balance": {
        "count_0": 31,
        "count_1": 33,
        "frequency_0": 0.484375,
        "frequency_1": 0.515625,
        "bias": 0.015625,
    },
    "runs": {
        "total_runs": 29,
        "longest_run": 4,
    },
    "observed_period": {
        "observed_period": None,
        "checked_prefix_length": 63,
    },
    "linear_complexity": {
        "linear_complexity": 31,
        "normalized_linear_complexity": 0.484375,
    },
}
```

## 8. Positionnement scientifique de cette etape

Dans le cadre du memoire, je peux presenter cette couche comme une base de
validation experimentale du prototype. Elle me permet de montrer que :

- je ne me limite pas a une simple implementation fonctionnelle ;
- j'observe aussi plusieurs proprietes mathematiques de la sortie ;
- je distingue clairement ce qui releve d'une mesure empirique et ce qui
  releverait d'une preuve de securite.
