from __future__ import annotations

import sys
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT_STR = str(PROJECT_ROOT)
if PROJECT_ROOT_STR not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_STR)

from ui.components.common import hero, info_card, note_panel, step_grid, text_panel
from ui.services.project_facade import ProjectFacade
from ui.theme import apply_theme
from ui.utils.session import init_session_state


st.set_page_config(page_title="Architecture", page_icon="A", layout="wide")
apply_theme()
init_session_state()

facade = ProjectFacade()
hero("Architecture generale", "Lecture visuelle, structuree et pedagogique du pipeline officiel SRC -> COND -> DRBG -> STATE.", eyebrow="Vue de reference")

cards = facade.architecture_cards()
cols = st.columns(3, gap="large")
for index, card in enumerate(cards):
    with cols[index % 3]:
        info_card(card["title"], card["body"], badges=[(card["name"], card["status"])])

st.subheader("Flux de donnees")
fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=[0, 1, 2, 3],
        y=[0, 0, 0, 0],
        mode="markers+text+lines",
        text=["SRC", "COND", "DRBG", "STATE"],
        textposition="top center",
        marker=dict(size=[48, 48, 54, 48], color=["#c8a94d", "#0e6b5c", "#183a44", "#b85c38"]),
        line=dict(color="#5c6a70", width=5),
        hoverinfo="skip",
    )
)
fig.update_layout(height=240, showlegend=False, xaxis=dict(visible=False), yaxis=dict(visible=False), margin=dict(l=0, r=0, t=10, b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
st.plotly_chart(fig, use_container_width=True)

step_grid(
    [
        ("SRC", "La couche collecte des symboles bruts depuis CPU jitter et une source capteur simulee."),
        ("COND", "La couche conditionne ce materiau par Toeplitz puis SHAKE-256 avant toute instanciation."),
        ("DRBG", "Le moteur nominal est Module-LWR. Multiplexed Sponge reste disponible pour l'exploration de recherche."),
        ("STATE", "La couche gere les transitions logiques, le checkpoint, la restauration et l'effacement."),
    ]
)

left, right = st.columns([1.2, 1.0], gap="large")
with left:
    text_panel("Ce qui est implemente", "SRC collecte l'entropie locale, COND applique Toeplitz + SHAKE-256, DRBG utilise Module-LWR comme chemin nominal, et STATE gere la machine a etats avec persistence simulee.")
    text_panel("Ce qui est experimental", "Multiplexed Sponge reste un moteur secondaire de recherche. La trajectoire mobile ajoute une frontiere FFI de transition et un protocole de profilage honnete.")
    text_panel("Ce qui reste futur", "La NTT active, les drivers Android/Linux reels, le wrapper JNI/NDK et la validation sur cible mobile restent hors de la baseline executable actuelle.")
with right:
    note_panel("Important", "Cette interface de demonstration ne doit pas etre lue comme une preuve d'integration mobile reelle.", tone="warning")
    note_panel("Point d'integration", "La reference fonctionnelle reste l'orchestration canonique exposee par `software/api/rng_service.py`.", tone="info")
