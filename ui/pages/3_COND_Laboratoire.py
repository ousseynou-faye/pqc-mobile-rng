from __future__ import annotations

import sys
from pathlib import Path

import plotly.express as px
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT_STR = str(PROJECT_ROOT)
if PROJECT_ROOT_STR not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_STR)

from ui.components.common import action_strip, hero, metric_strip, note_panel, render_logs, section_header, step_grid, text_panel
from ui.services.project_facade import ProjectFacade
from ui.theme import apply_theme
from ui.utils.session import init_session_state, push_log


st.set_page_config(page_title="COND", page_icon="C", layout="wide")
apply_theme()
init_session_state()

facade = ProjectFacade()
hero("Laboratoire COND", "Visualisation du conditionnement officiel Toeplitz + SHAKE-256 a partir d'une sortie SRC reelle.", eyebrow="Etape 2")
ui_mode = st.session_state.get("ui_mode", "pedagogique")

src = st.session_state.get("last_src")
if not src:
    st.warning("Aucun materiau SRC n'est disponible. Passez d'abord par la page SRC.")
    st.stop()

with st.sidebar:
    personalization = st.text_input("Personalization", value="ui-cond")
    extra_context = st.text_input("Contexte additionnel", value="memoire-demo")
    st.caption("Le conditionneur structure le materiau avant toute instanciation du DRBG.")

step_grid(
    [
        ("Recuperer l'entree", "Le conditionneur repart du materiau accepte par la couche SRC."),
        ("Appliquer Toeplitz", "Une extraction intermediaire est produite a partir de l'entree brute."),
        ("Finaliser Seedinit", "SHAKE-256 derive la seed finale avec le contexte et les metadonnees."),
    ]
)
action_strip(
    [
        ("Action principale", "Appliquez le conditionneur officiel pour produire `Seedinit`."),
        ("Resultat attendu", "Comparer visuellement la taille d'entree et la sortie conditionnee avant passage au DRBG."),
    ]
)

if st.button("Appliquer Toeplitz + SHAKE-256", type="primary"):
    st.session_state["last_cond"] = facade.condition_entropy(
        src["raw_data"],
        metadata=src["pool_summary"],
        personalization=personalization.encode("utf-8"),
        extra_context=extra_context.encode("utf-8"),
    )
    push_log("COND", "Conditionnement Toeplitz puis SHAKE-256 execute.")

cond = st.session_state.get("last_cond")
if not cond:
    st.info("Lancez le conditionnement pour afficher les tailles, les transformations et les apercus securises.")
    st.stop()

metric_strip(
    [
        ("Entree", f"{cond['input_bits']} bits"),
        ("Sortie Toeplitz", "256 bits"),
        ("Sortie SHAKE-256", f"{cond['output_bits']} bits"),
        ("Contexte", "present"),
    ]
)

col1, col2 = st.columns([1.1, 1.0], gap="large")
with col1:
    section_header("Transformation du materiau", "Reduction de l'entree brute vers une seed plus propre et structuree.", kicker="Resultats")
    text_panel("Role du conditionnement", "Toeplitz regularise l'entree brute et SHAKE-256 derive un `Seedinit` stable, contextualise et plus propre pour la couche DRBG.")
    fig = px.bar([{"stage": "Raw", "bits": cond["input_bits"]}, {"stage": "Seedinit", "bits": cond["output_bits"]}], x="stage", y="bits", color="stage", title="Reduction et structuration du materiau")
    fig.update_layout(height=320, margin=dict(l=0, r=0, t=40, b=0), showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    st.subheader("Apercus securises")
    st.code(f"Raw      : {cond['raw_preview_hex']}", language="text")
    st.code(f"Toeplitz : {cond['toeplitz_preview_hex']}", language="text")
    st.code(f"Seedinit : {cond['seed_preview_hex']}", language="text")

with col2:
    section_header("Lecture pedagogique", "Rappels utiles avant d'instancier le DRBG.", kicker="Explication")
    note_panel("A retenir", "La seed brute complete n'est pas exposee. L'interface ne montre que des apercus securises et le contexte utile a la lecture.", tone="warning")
    with st.expander("Contexte injecte"):
        st.write(cond["context_preview"])
    if ui_mode == "technique":
        with st.expander("Resultat detaille"):
            st.write({"input_bits": cond["input_bits"], "output_bits": cond["output_bits"]})
    with st.expander("Journal"):
        render_logs(st.session_state["ui_logs"])
