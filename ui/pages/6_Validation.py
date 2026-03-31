from __future__ import annotations

import sys
from pathlib import Path

import plotly.express as px
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT_STR = str(PROJECT_ROOT)
if PROJECT_ROOT_STR not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_STR)

from ui.components.common import action_strip, hero, note_panel, section_header, step_grid, text_panel
from ui.services.project_facade import ProjectFacade
from ui.theme import apply_theme
from ui.utils.session import init_session_state, push_log


st.set_page_config(page_title="Validation", page_icon="V", layout="wide")
apply_theme()
init_session_state()

facade = ProjectFacade()
hero("Validation / tests", "Lancement de verifications legeres locales sans demarrer les campagnes lourdes du depot.", eyebrow="Verification")

step_grid(
    [
        ("API publique", "Verifie que le SDK canonique s'initialise et genere correctement."),
        ("SRC", "Controle que la collecte locale et les checks prudents restent operationnels."),
        ("Statistique legere", "Ajoute une suite experimentale courte pour la demonstration, sans pretendre a une preuve cryptographique."),
    ]
)
action_strip(
    [
        ("Smoke tests", "Lance une verification rapide de bout en bout sur le prototype local."),
        ("Campagne statistique", "Ajoute une campagne courte sur le moteur Multiplexed Sponge de la baseline."),
    ]
)

cols = st.columns(2)
if cols[0].button("Lancer les smoke tests", type="primary"):
    st.session_state["last_validation"] = facade.run_validation_smoke()
    push_log("VALIDATION", "Smoke tests UI executes.")
if cols[1].button("Lancer la comparaison smoke"):
    st.session_state["last_validation_campaign"] = facade.run_campaign_smoke()
    push_log("VALIDATION", "Campagne comparative smoke executee.")

validation = st.session_state.get("last_validation")
if validation:
    section_header("Resultats de validation", "Lecture rapide des checks fonctionnels et statistiques locaux.", kicker="Resultats")
    note_panel("Lecture recommandee", "Considerez ces checks comme des smoke tests de demonstration. Ils ne remplacent pas les campagnes completes du projet.", tone="info")
    st.subheader("Resultats des smoke tests")
    st.dataframe(validation["results"], width="stretch", hide_index=True)
    fig = px.bar(validation["results"], x="name", y="duration_ms", color="success", title="Duree des checks")
    fig.update_layout(height=320, margin=dict(l=0, r=0, t=40, b=0))
    st.plotly_chart(fig, width="stretch")
    for warning in validation["warnings"]:
        st.warning(warning)

campaign = st.session_state.get("last_validation_campaign")
if campaign:
    section_header("Comparaison experimentale", "Resume de la campagne comparative courte.", kicker="Comparaison")
    st.subheader("Comparaison experimentale smoke")
    rows = [{"engine": name, **values} for name, values in campaign["engines"].items()]
    st.dataframe(rows, width="stretch", hide_index=True)
    text_panel("Limite methodologique", "Ces indicateurs restent experimentaux et ne constituent pas une validation cryptographique formelle.")
