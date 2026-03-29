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


st.set_page_config(page_title="Benchmarks", page_icon="B", layout="wide")
apply_theme()
init_session_state()

facade = ProjectFacade()
hero("Benchmarks / comparaison experimentale", "Benchmarks legers du prototype local et profilage honnete de la trajectoire mobile.", eyebrow="Mesures locales")

step_grid(
    [
        ("Comparer les moteurs", "Visualisez instanciation, reseed et generation sur le prototype local."),
        ("Lire le contexte", "Interpretez toujours les chiffres a l'aune de l'hote courant."),
        ("Eviter la surinterpretation", "Sans execution ARM reelle, ces chiffres restent des mesures desktop/locales."),
    ]
)
action_strip(
    [
        ("Action principale", "Lancez un benchmark smoke lisible pour la soutenance."),
        ("Resultat attendu", "Comparer les temps locaux des moteurs et rappeler les limites de l'hote courant."),
    ]
)

if st.button("Lancer le benchmark local", type="primary"):
    st.session_state["last_benchmarks"] = facade.run_benchmark_smoke()
    push_log("BENCH", "Benchmarks smoke executes.")

bench = st.session_state.get("last_benchmarks")
if not bench:
    st.info("Lancez les benchmarks pour afficher les temps d'instanciation, de generation et le profilage mobile.")
    st.stop()

performance = bench["performance"]
section_header("Resultats de performance", "Comparaison locale des operations principales par moteur.", kicker="Resultats")
rows = []
for engine_name, engine_report in performance["engines"].items():
    rows.append({"engine": engine_name, "metric": "instantiate", "mean_ns": engine_report["instantiate"]["timing"]["mean_ns"]})
    rows.append({"engine": engine_name, "metric": "reseed", "mean_ns": engine_report["reseed"]["timing"]["mean_ns"]})
    largest = max(engine_report["generation"], key=lambda key: int(key))
    rows.append({"engine": engine_name, "metric": f"generate_{largest}B", "mean_ns": engine_report["generation"][largest]["timing"]["mean_ns"]})

fig = px.bar(rows, x="metric", y="mean_ns", color="engine", barmode="group", title="Comparaison locale des temps moyens")
fig.update_layout(height=360, margin=dict(l=0, r=0, t=40, b=0))
st.plotly_chart(fig, use_container_width=True)
st.dataframe(rows, use_container_width=True, hide_index=True)

mobile = bench["mobile_profile"]["metadata"]
section_header("Profilage mobile de trajectoire", "Ce panneau rappelle si l'execution a reellement eu lieu sur ARM.", kicker="Contexte")
text_panel("Ce que mesure cette page", "Les temps affiches proviennent du prototype local Python. La section mobile indique honnetement si une execution ARM reelle a eu lieu ou non.")
st.write(mobile)
for warning in bench["warnings"]:
    note_panel("Avertissement", warning, tone="warning")
if mobile["not_measured_on_arm"]:
    st.error("Aucune mesure ARM reelle n'a ete observee dans cette execution.")
