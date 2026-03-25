# Conception materielle

## 1. Objectif / Perimetre

Ce document decrit la place du materiel dans le projet et distingue ce qui est
present dans le depot, ce qui est simule et ce qui reste une cible future.

Il ne faut pas lire ce document comme la preuve d'un deploiement materiel reel
deja effectif.

## 2. Vue d'ensemble

Le projet reste aujourd'hui executable principalement comme prototype logiciel
Python. En parallele, le depot contient un dossier `hardware/` qui prepare une
trajectoire de conception materielle.

Structure observee :

- `hardware/rtl/`
- `hardware/simulation/`
- `hardware/synthesis/`
- `hardware/fpga/`

## 3. Schema / Architecture bloc

```text
 Prototype Python
    |
    +--> reference executable pour SRC -> COND -> DRBG -> STATE
    |
    +--> inspiration / reference fonctionnelle pour hardware/
             |
             +--> RTL : blocs VHDL cibles
             +--> simulation : testbenches
             +--> synthesis : scripts et contraintes
             +--> fpga : emplacement pour projet/bitstream
```

## 4. Interfaces / Composants

### 4.1 Ce qui existe aujourd'hui dans le depot

Le dossier `hardware/rtl/` contient notamment :

- `entropy_source.vhd`
- `lfsr_core.vhd`
- `lwr_core.vhd`
- `multiplexed_sponge.vhd`
- `phi_function.vhd`
- `rng_controller.vhd`
- `rng_top.vhd`

Le dossier `hardware/simulation/` contient des testbenches :

- `tb_lfsr.vhd`
- `tb_sponge.vhd`
- `testbench_rng.vhd`

Le dossier `hardware/synthesis/` contient :

- `constraints.xdc`
- `synthesis_script.tcl`

Le dossier `hardware/fpga/` contient des emplacements de projet et bitstream,
mais pas une preuve documentaire d'un deploiement materiel finalise.

### 4.2 Lien avec le logiciel Python

Le logiciel Python reste la reference executable du projet.

Le materiel doit etre compris comme :

- une cible de conception ;
- un support de simulation ;
- une trajectoire d'acceleration ou d'integration future.

Le depot ne montre pas aujourd'hui une chaine complete de deploiement mobile
materiel reliee a l'API Python en production.

## 5. Hypotheses

- les blocs materiels visent a reprendre des fonctions presentes cote logiciel ;
- le logiciel Python reste la source de verite fonctionnelle actuelle ;
- les mesures de latence ou d'energie materielle doivent venir de simulations ou
  rapports externes explicites, pas d'une extrapolation libre.

## 6. Contraintes visees

Les contraintes materiellement pertinentes pour ce projet sont :

- ressources logiques ;
- latence de generation ;
- empreinte memoire ;
- integration avec une logique de persistance et de securisation d'etat ;
- adequation a une cible mobile ou embarquee future.

Ces contraintes sont documentables conceptuellement, mais elles ne doivent pas
etre presentees comme deja closes par une campagne materielle complete.

## 7. Lien avec l'etat, l'anti-rollback et la securisation

Le depot relie deja conceptuellement la generation pseudo-aleatoire et la
protection d'etat :

- machine a etats explicite ;
- scellement et restauration ;
- anti-rollback simule.

Sur une cible materielle future, ces fonctions devraient idealement etre
reliees a :

- un stockage protege ;
- un compteur monotone materiel ;
- une logique d'integrite plus forte.

Aujourd'hui, ce comportement reste simule cote Python.

## 8. Limites

- pas de preuve de deploiement FPGA final ou smartphone materiel ;
- pas de chaine de build materielle integree au flux Python courant ;
- pas de mesure materielle reelle obligatoire dans le depot ;
- pas de latence materielle reelle documentee par defaut ;
- pas de mesure energetique materielle reelle documentee par defaut.

## 9. Statut actuel

### Implemente dans le depot

- fichiers RTL VHDL ;
- testbenches de simulation ;
- scripts de synthese et contraintes ;
- cadre documentaire et benchmark pour importer des rapports externes.

### Simule

- comportement de la couche `STATE` cote securisation ;
- partie des scenarios de demonstration ;
- latence materielle lorsqu'aucun rapport externe n'est fourni.

### Non demontre comme deploye

- bitstream final utilise sur carte cible ;
- execution sur smartphone ou SoC mobile reel ;
- mesures physiques de consommation ou de latence reelle.

## 10. Evolutions futures

- relier plus explicitement les blocs RTL a des rapports de simulation versionnes ;
- ajouter des rapports de synthese ou FPGA effectivement obtenus ;
- confronter la reference Python a une implementation embarquee reelle ;
- instrumenter energie et latence sur cible concrete ;
- etudier l'apport d'optimisations futures comme la NTT sans les documenter
  prematurement comme deja integrees.
