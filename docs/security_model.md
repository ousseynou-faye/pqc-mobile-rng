# Modele de securite

## 1. Objectif / Perimetre

Ce document decrit le modele de securite du prototype executable actuellement
present dans le depot.

Il distingue explicitement :

- la securite experimentale observee ;
- la securite argumentee par construction ;
- ce qui ne constitue pas une conformite formelle.

## 2. Vue d'ensemble

La baseline consideree est :

```text
SRC -> COND -> DRBG -> STATE
```

avec :

- `COND = Toeplitz + SHAKE-256`
- `DRBG nominal = Module-LWR`
- `Multiplexed Sponge = moteur secondaire de recherche`
- `STATE = persistance et protection simulees`

## 3. Actifs a proteger

- l'entropie brute collectee ;
- la seed conditionnee `Seedinit` ;
- l'etat interne du moteur actif ;
- la coherence de la machine a etats ;
- l'integrite de l'etat scelle et restaure ;
- la sortie pseudo-aleatoire exposee par le SDK.

## 4. Hypotheses

### 4.1 Source d'entropie

Le prototype suppose que la couche `SRC` fournit une matiere premiere :

- non entierement triviale a predire ;
- suffisamment variable a l'echelle de la collecte ;
- surveillee par des tests de sante simples.

Cette hypothese reste empirique. Elle ne constitue pas une qualification
materielle complete de la source.

### 4.2 Conditionnement

Le conditionneur `Toeplitz + SHAKE-256` est utilise pour :

- separer la collecte d'entropie de la generation deterministe ;
- fournir une seed d'initialisation stable au DRBG ;
- attenuer des biais de la matiere brute.

Il ne doit pas etre presente comme une preuve formelle complete de min-entropie.

### 4.3 Moteur nominal

`Module-LWR` est le moteur nominal effectivement execute.

La securite attendue est celle d'un prototype academique defendable, pas celle
d'un composant certifie, homologue ou normalise.

### 4.4 Gestion d'etat

La couche `STATE` suppose :

- une machine a etats explicite ;
- un comportement `FAIL_STOP` sur faute critique ;
- une simulation de sealing, d'integrite et d'anti-rollback.

Cette simulation n'est pas equivalente a un TEE mobile materiel reel.

## 5. Menaces considerees

- source gelee ou pathologique detectee par health checks simples ;
- utilisation du RNG avant initialisation ;
- generation alors qu'un reseed est requis ;
- incoherence d'etat interne ;
- alteration d'un blob scelle ;
- tentative de rollback detectee par la logique de persistance simulee ;
- bascule silencieuse non autorisee de moteur.

## 6. Menaces non couvertes

- compromission complete du systeme d'exploitation ;
- extraction memoire par un adversaire privilegie ;
- qualification complete des capteurs reels sur smartphone ;
- resistance a tous les canaux auxiliaires ;
- securite d'un TEE materiel reel ;
- evaluation normative SP 800-90A, SP 800-90B, SP 800-22, FIPS ou CMVP.

## 7. Role des composants

### 7.1 Source d'entropie

Elle fournit la matiere premiere. Sa qualite est evaluee par des tests
experimentaux prudents, pas par une validation normative complete.

### 7.2 Toeplitz + SHAKE-256

Il s'agit du conditionneur officiel de la baseline. Il prepare `Seedinit` et
separe `SRC` de `DRBG`.

### 7.3 Module-LWR

Il porte la generation deterministe nominale du prototype. C'est le coeur
post-quantique effectivement active par defaut.

### 7.4 Multiplexed Sponge

Il est maintenu comme moteur secondaire de recherche, utile pour comparaison et
experimentation. Il ne doit pas etre decrit comme le comportement normal par
defaut.

### 7.5 STATE / persistance / restauration

La couche `STATE` protege la coherence de cycle de vie et simule des controles
d'integrite et d'anti-rollback.

## 8. Risques lies a l'export et a la restauration d'etat

- un export prive mal manipule reste sensible ;
- la restauration d'etat introduit un risque de replay si elle est retiree du
  cadre de controle prevu ;
- la simulation logicielle ne fournit pas les garanties d'un stockage materiel
  protege ;
- une mauvaise gestion des metadonnees de checkpoint peut invalider la logique
  de restauration attendue.

La documentation publique doit donc rester centree sur les exports non sensibles
et sur la restauration administree.

## 9. Limites de la simulation

- `STATE` repose sur un `SimulatedTEE` ;
- les capteurs peuvent etre simules ;
- l'environnement est Python et local ;
- les benchmarks ARM, energie et latence materielle ne sont pas des preuves de
  deploiement reel.

## 10. Limites du prototype Python

- absence d'isolation forte de type enclave materielle ;
- sensibilite a l'environnement d'execution local ;
- absence de garantie temps reel ;
- surface memoire et runtime Python non equivalentes a un deploiement mobile
  final.

## 11. Securite experimentale, securite argumentee et non-conformite formelle

### 11.1 Securite experimentale observee

- health checks simples ;
- validation statistique experimentale ;
- benchmark logiciel et comparaison de cout ;
- detection experimentale d'integrite et de rollback.

### 11.2 Securite argumentee

- separation des couches `SRC -> COND -> DRBG -> STATE` ;
- conditionneur explicite ;
- moteur nominal fige ;
- machine a etats explicite et politique de fail-stop.

### 11.3 Ce qui n'est pas demontre formellement

- aucune conformite NIST formelle ;
- aucune certification produit ;
- aucune preuve cryptographique derivee des seuls tests statistiques ;
- aucune equivalence a une cible mobile deployee.

## 12. Risques residuels

- surestimation possible de la qualite de la source d'entropie ;
- dependance forte a l'environnement local d'execution ;
- ecart entre prototype Python et deploiement mobile reel ;
- risques associes aux fonctions d'etat si elles etaient exposees sans
  gouvernance adequate ;
- differences potentielles entre comportement logiciel et future cible
  materielle.

## 13. Statut actuel

### Implemente

- baseline complete `SRC -> COND -> DRBG -> STATE`
- health checks et validation experimentale
- machine a etats et fail-stop
- integrite et anti-rollback simules

### Experimental

- comparaison LWR vs Sponge
- benchmarks de cout logiciel
- cadres energie et materiel sans mesures reelles par defaut

### Futur

- execution sur cible ARM reelle
- instrumentation energie reelle
- durcissement materiel
- acceleration NTT

## 14. Evolutions futures

- qualifer une vraie cible mobile ou embarquee ;
- renforcer la protection d'etat avec une cible materielle reelle ;
- etendre l'analyse securitaire au-dela du prototype Python ;
- ajouter des preuves, rapports ou validations externes quand elles seront
  effectivement disponibles.
