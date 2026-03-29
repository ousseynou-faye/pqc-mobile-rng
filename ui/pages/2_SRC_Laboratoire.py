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


st.set_page_config(page_title="SRC", page_icon="S", layout="wide")
apply_theme()
init_session_state()

facade = ProjectFacade()
hero("Laboratoire SRC", "Collecte locale d'entropie, metriques prudentes et health checks des sources.", eyebrow="Etape 1")
ui_mode = st.session_state.get("ui_mode", "pedagogique")

with st.sidebar:
    st.subheader("Configuration SRC")
    use_cpu = st.checkbox("Activer CPU jitter", value=True)
    use_sensor = st.checkbox("Activer source capteur simulee", value=True)
    cpu_sample_count = st.slider("CPU sample_count", 64, 1024, 256, 64)
    sensor_frame_count = st.slider("Sensor frame_count", 16, 256, 64, 16)
    cpu_lsb_count = st.slider("CPU LSB", 1, 4, 2)
    sensor_lsb_count = st.slider("Sensor LSB", 1, 4, 2)
    st.caption("Commencez ici pour alimenter la couche COND avec un materiau reel.")

step_grid(
    [
        ("Selectionner les sources", "Activez CPU jitter, la source capteur simulee, ou les deux selon le scenario de demonstration."),
        ("Collecter", "Declenchez la collecte pour alimenter le pool et executer les checks prudents."),
        ("Observer", "Lisez les apercus, l'histogramme et les rapports de sante avant de passer au conditionneur."),
    ]
)
action_strip(
    [
        ("Action principale", "Generez l'entropie pour remplir le pool et debloquer la suite du pipeline."),
        ("Resultat attendu", "Obtenir au moins un chunk accepte et un pool pret ou presque pret pour COND."),
    ]
)

if st.button("Generer l'entropie", type="primary"):
    st.session_state["last_src"] = facade.collect_entropy(
        use_cpu=use_cpu,
        use_sensor=use_sensor,
        cpu_sample_count=cpu_sample_count,
        sensor_frame_count=sensor_frame_count,
        cpu_lsb_count=cpu_lsb_count,
        sensor_lsb_count=sensor_lsb_count,
    )
    push_log("SRC", "Collecte d'entropie realisee avec les sources selectionnees.")

src = st.session_state.get("last_src")
if not src:
    st.info("Lancez une collecte pour visualiser les chunks, les tests de sante et le pool.")
    st.stop()

pool = src["pool_summary"]
metric_strip(
    [
        ("Chunks acceptes", str(pool["accepted_chunks"])),
        ("Chunks rejetes", str(pool["rejected_chunks"])),
        ("Symboles", str(pool["total_symbols"])),
        ("Octets bruts", str(pool["total_raw_bytes"])),
        ("Min-entropie estimee", f"{pool['estimated_min_entropy_bits']:.2f} bits"),
        ("Pool pret", "oui" if pool["ready"] else "non"),
    ]
)

col1, col2 = st.columns([1.2, 1.0], gap="large")
with col1:
    section_header("Resultats SRC", "Lecture du pool, apercu du materiau et histogramme local.", kicker="Resultats")
    text_panel("Ce que montre cette page", "La couche SRC expose le materiau brut, les compteurs du pool et des tests de sante prudents. Les donnees affichees sont tronquees pour rester demonstratives et non invasives.")
    st.subheader("Apercu du materiau collecte")
    st.code(src["raw_preview_hex"], language="text")
    st.caption(src["raw_preview_bits"])
    if src["symbol_histogram"]:
        fig = px.bar(src["symbol_histogram"], x="symbol", y="count", title="Histogramme des symboles")
        fig.update_layout(height=320, margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig, use_container_width=True)

with col2:
    section_header("Aide a l'interpretation", "Messages utiles, prochaine etape et journal de collecte.", kicker="Accompagnement")
    note_panel("Etape suivante recommandee", "Si le pool est pret, passez a la page COND pour appliquer Toeplitz puis SHAKE-256.", tone="info")
    st.subheader("Journal technique")
    render_logs(st.session_state["ui_logs"])

section_header("Rapports par source", "Chaque source affiche ses metadonnees, ses checks et un apercu limite.", kicker="Details")
for source in src["sources"]:
    with st.expander(f"{source['source_name']} | accepted={source['report']['accepted']}", expanded=True):
        st.write(source["metadata"])
        st.write(source["report"])
        st.code(source["raw_preview_hex"], language="text")
        if ui_mode == "technique":
            st.write({"preview_bits": source["raw_preview_bits"], "sample_count": source["sample_count"]})
