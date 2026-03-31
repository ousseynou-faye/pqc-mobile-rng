from __future__ import annotations

import sys
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT_STR = str(PROJECT_ROOT)
if PROJECT_ROOT_STR not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_STR)

from ui.components.common import hero, info_card, metric_strip, note_panel, step_grid, text_panel
from ui.services.project_facade import ProjectFacade
from ui.theme import apply_theme
from ui.utils.session import init_session_state


st.set_page_config(page_title="RNG Mobile Post-Quantique", page_icon="R", layout="wide", initial_sidebar_state="expanded")
apply_theme()
init_session_state()

facade = ProjectFacade()
overview = facade.system_overview()

with st.sidebar:
    st.title("Navigation")
    st.caption("Interface locale de demonstration")
    st.radio("Mode d'affichage", ["pedagogique", "technique"], key="ui_mode")
    st.caption("Suivez le pipeline dans l'ordre logique du projet.")
    st.divider()
    st.page_link("Home.py", label="Accueil")
    st.page_link("pages/1_Architecture.py", label="Architecture")
    st.page_link("pages/2_SRC_Laboratoire.py", label="SRC")
    st.page_link("pages/3_COND_Laboratoire.py", label="COND")
    st.page_link("pages/4_DRBG_Laboratoire.py", label="DRBG")
    st.page_link("pages/5_STATE_Laboratoire.py", label="STATE")
    st.page_link("pages/6_Validation.py", label="Validation")
    st.page_link("pages/7_Benchmarks.py", label="Benchmarks")
    st.page_link("pages/8_Documentation.py", label="Documentation")

hero(
    overview["project_title"],
    "Un tableau de bord scientifique local pour comprendre, tester et presenter le pipeline RNG post-quantique du memoire.",
    eyebrow="Prototype academique local",
)
metric_strip([
    ("Pipeline", overview["pipeline"]),
    ("Moteur nominal", "Multiplexed Sponge"),
    ("Mode DRBG", "Sponge-only"),
    ("Conditionneur", overview["conditioner"]),
    ("Statut", overview["prototype_status"]),
])

col_a, col_b = st.columns([1.2, 1.0], gap="large")
with col_a:
    info_card("Vue d'ensemble", "Cette interface est branchee sur le vrai coeur Python du projet. Elle montre ce qui est implemente, ce qui est experimental et ce qui reste futur, sans presenter le depot comme une application mobile finale.", badges=[("Prototype local", "implemented"), ("Memoire / soutenance", "experimental")])
    note_panel("A retenir", "Le projet reste un SDK Python local avec trajectoire mobile documentee. Il ne faut pas le presenter comme une application mobile finale.", tone="warning")
    for card in facade.architecture_cards()[:3]:
        info_card(card["title"], card["body"], badges=[(card["name"], card["status"])])

with col_b:
    fig = go.Figure(
        go.Sankey(
            arrangement="snap",
            node=dict(
                pad=22,
                thickness=24,
                line=dict(color="rgba(31,42,46,0.18)", width=1),
                label=["SRC", "COND", "DRBG", "STATE"],
                color=["#c8a94d", "#0e6b5c", "#183a44", "#b85c38"],
            ),
            link=dict(
                source=[0, 1, 2],
                target=[1, 2, 3],
                value=[1, 1, 1],
                color=["rgba(200,169,77,0.35)", "rgba(14,107,92,0.35)", "rgba(184,92,56,0.32)"],
            ),
        )
    )
    fig.update_layout(height=340, margin=dict(l=0, r=0, t=10, b=10), paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, width="stretch")
    status = overview["sdk_status"]
    info_card("Etat global du SDK", f"Initialise: {status['initialized']} | Etat logique: {status['lifecycle_state'] or 'absent'} | Derniere operation: {status['last_operation'] or 'aucune'}", badges=[(status["health_status"], "implemented" if status["health_status"] == "ok" else "experimental")])

step_grid(
    [
        ("Comprendre l'architecture", "Commencez par la vue d'architecture pour voir les couches implementees, experimentales et futures."),
        ("Explorer les donnees", "Collectez l'entropie, conditionnez-la, puis instanciez le DRBG pour suivre le pipeline."),
        ("Valider et documenter", "Terminez par les smoke tests, les benchmarks locaux et la documentation du pipeline."),
    ]
)

st.subheader("Acces rapides")
quick_1, quick_2, quick_3 = st.columns(3)
with quick_1:
    st.page_link("pages/2_SRC_Laboratoire.py", label="Explorer la couche SRC")
with quick_2:
    st.page_link("pages/4_DRBG_Laboratoire.py", label="Tester les moteurs DRBG")
with quick_3:
    st.page_link("pages/7_Benchmarks.py", label="Lancer les benchmarks legers")

doc_col, next_col = st.columns([1.1, 1.0], gap="large")
with doc_col:
    text_panel("Comment utiliser ce tableau de bord", "Le flux recommande est simple: Architecture, SRC, COND, DRBG, STATE, puis Validation et Benchmarks. Chaque page combine un resume pedagogique, des actions visibles et des details techniques optionnels.")
with next_col:
    next_step = "Passez a SRC pour produire un premier materiau d'entropie." if not status["initialized"] else "Passez a DRBG ou STATE pour manipuler le service deja instancie."
    note_panel("Etape suivante recommandee", next_step, tone="info")
