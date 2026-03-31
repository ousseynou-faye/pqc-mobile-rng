# GUI Dashboard

Le tableau de bord Streamlit visualise:

- l'architecture `SRC -> COND -> DRBG -> STATE`
- l'instanciation du DRBG officiel
- les sorties locales du `Multiplexed Sponge`
- l'etat scellable et la restauration

La page DRBG n'expose qu'un seul moteur afin de rester conforme a la baseline sponge-only.
