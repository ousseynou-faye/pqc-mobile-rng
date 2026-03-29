from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT_STR = str(PROJECT_ROOT)
if PROJECT_ROOT_STR not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_STR)

from ui.components.common import hero, note_panel, step_grid
from ui.theme import apply_theme
from ui.utils.session import init_session_state


st.set_page_config(page_title="Documentation", page_icon="G", layout="wide")
apply_theme()
init_session_state()

hero("Documentation / aide", "Guide de lancement, limites d'interpretation et rappel du statut reel de l'outil.", eyebrow="Guide d'utilisation")

step_grid(
    [
        ("Suivre le pipeline", "Commencez par Architecture, puis SRC, COND, DRBG et STATE pour une demo logique."),
        ("Basculer de vue", "Le mode pedagogique simplifie la lecture. Le mode technique ajoute plus de details."),
        ("Garder les limites en tete", "L'interface reste locale, experimentale et non assimilable a une application mobile finale."),
    ]
)
note_panel("Guide integre", "Cette page resume comment naviguer, quoi montrer au jury et quelles limites rappeler pendant la demonstration.", tone="info")

doc_path = PROJECT_ROOT / "docs" / "gui_dashboard.md"
st.markdown(doc_path.read_text(encoding="utf-8"))
