from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT_STR = str(PROJECT_ROOT)
if PROJECT_ROOT_STR not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_STR)

from ui.components.common import action_strip, hero, metric_strip, note_panel, render_logs, section_header, step_grid, text_panel
from ui.services.project_facade import ProjectFacade
from ui.theme import apply_theme
from ui.utils.session import init_session_state, push_log


st.set_page_config(page_title="STATE", page_icon="T", layout="wide")
apply_theme()
init_session_state()

facade = ProjectFacade()
hero("Laboratoire STATE", "Visualisation de la persistence simulee, des transitions logiques et des operations sensibles.", eyebrow="Etape 4")
ui_mode = st.session_state.get("ui_mode", "pedagogique")

step_grid(
    [
        ("Checkpoint", "Capture un etat scelle administré par la couche STATE du prototype."),
        ("Restore", "Recharge un etat scelle lorsqu'un blob coherent est disponible."),
        ("Zeroize", "Efface l'etat logique en memoire avant reinitialisation explicite."),
    ]
)
action_strip(
    [
        ("Checkpoint", "Sauvegarde un etat scelle du prototype sans exposer son contenu complet."),
        ("Restore", "Recharge un etat si un blob valide a deja ete cree."),
        ("Action sensible", "Zeroize efface l'etat logique et exige ensuite une reinitialisation."),
    ]
)

section_header("Zone d'action", "Operations principales de la couche STATE.", kicker="Actions")
actions = st.columns(4)
if actions[0].button("Sauvegarder l'etat", type="primary"):
    st.session_state["last_state_blob"] = facade.sdk_checkpoint()
    push_log("STATE", "Checkpoint d'etat effectue via la couche canonique.")
if actions[1].button("Restaurer l'etat"):
    try:
        st.session_state["last_state_restore"] = facade.sdk_restore()
        push_log("STATE", "Restauration d'etat effectuee.")
    except Exception as exc:
        st.error(str(exc))
if actions[2].button("Effacer l'etat"):
    st.session_state["last_state_zeroize"] = facade.sdk_zeroize()
    push_log("STATE", "Zeroize demande sur le service.")
if actions[3].button("Rafraichir l'etat"):
    st.session_state["last_state_details"] = facade.sdk_state_details()

details = st.session_state.get("last_state_details") or facade.sdk_state_details()
sdk_status = details["sdk_status"]
metric_strip([("Initialise", str(sdk_status["initialized"])), ("Etat logique", sdk_status["lifecycle_state"] or "absent"), ("Blob disponible", str(sdk_status["state_available"])), ("Derniere operation", sdk_status["last_operation"] or "aucune")])

left, right = st.columns([1.1, 1.0], gap="large")
with left:
    section_header("Etat logique", "Vue non sensible du composant et de ses transitions.", kicker="Resultats")
    text_panel("Ce que vous voyez", "La couche STATE montre uniquement l'etat logique et les transitions non sensibles. Les materiaux internes du blob restent masques.")
    st.subheader("Etat non sensible")
    st.json(details["drbg_state"])
    history = details["drbg_state"].get("manager_state", {}).get("transition_history", []) if isinstance(details["drbg_state"], dict) else []
    if history:
        st.subheader("Transitions")
        st.dataframe(history, use_container_width=True, hide_index=True)

with right:
    section_header("Operations sensibles", "Lecture prudente des checkpoint, restore et zeroize.", kicker="Securite")
    st.subheader("Operations sensibles")
    note_panel("Avertissement", "Le blob d'etat est tronque dans l'interface. Les materiaux sensibles complets ne sont pas affiches.", tone="warning")
    if st.session_state.get("last_state_blob"):
        st.json(st.session_state["last_state_blob"]["blob"])
    restore = st.session_state.get("last_state_restore")
    if restore:
        st.success("Restauration reussie.")
        st.write(restore["status"])
    if ui_mode == "technique":
        note_panel("Point technique", "La persistance repose ici sur un TEE simule et sur le format scelle du prototype Python.", tone="info")

with st.expander("Journal technique"):
    render_logs(st.session_state["ui_logs"])
