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
from software.conditioner import encode_conditioner_seed_for_drbg
from ui.services.project_facade import ProjectFacade
from ui.theme import apply_theme
from ui.utils.security import preview_bytes
from ui.utils.session import init_session_state, push_log


st.set_page_config(page_title="DRBG", page_icon="D", layout="wide")
apply_theme()
init_session_state()

facade = ProjectFacade()
hero("Laboratoire DRBG", "Instanciation, generation et observation pedagogique du DRBG Multiplexed Sponge.", eyebrow="Etape 3")

cond = st.session_state.get("last_cond")
ui_mode = st.session_state.get("ui_mode", "pedagogique")

with st.sidebar:
    st.subheader("Commandes DRBG")
    engine = st.selectbox("Moteur", ["multiplexed_sponge"])
    length = st.slider("Taille de sortie", 16, 512, 64, 16)
    decimal_limit = st.slider("Apercu decimal", 8, 128, 32, 8)
    personalization = st.text_input("Personalization", value="ui-drbg")
    additional_input = st.text_input("Additional input", value="")
    st.caption("Le moteur nominal du SDK est Multiplexed Sponge.")

step_grid(
    [
        ("Instancier", "Instanciez un moteur avec un seed material issu du conditionneur."),
        ("Generer", "Produisez un bloc d'octets et visualisez-le en hex, binaire et decimal."),
        ("Observer", "Inspectez l'etat non sensible et la sortie du Multiplexed Sponge sur une meme longueur."),
    ]
)
action_strip(
    [
        ("Action principale", "Instanciez puis generez une sortie RNG lisible en hex, binaire et decimal."),
        ("Action secondaire", "Relancez une mesure locale du moteur officiel pour comparer deux appels consecutifs."),
        ("Action canonique", "Initialisez le SDK pour rappeler le chemin nominal du projet."),
    ]
)

if cond:
    lab_seed_bundle = {
        "source": "conditionneur",
        "result": cond["result"],
        "seed_material": encode_conditioner_seed_for_drbg(cond["result"].seedinit),
        "seed_preview_hex": preview_bytes(cond["result"].seedinit, head=6, tail=6),
    }
else:
    lab_seed_bundle = facade.build_lab_seed_material(
        b"ui-drbg-seed",
        personalization=personalization.encode("utf-8"),
        extra_context=b"ui-lab-fallback-conditioned",
    )
    lab_seed_bundle["source"] = "conditionnement local"

default_seed_material = lab_seed_bundle["seed_material"]

if st.button("Instancier le DRBG", type="primary"):
    st.session_state["drbg_instances"][engine] = facade.instantiate_lab_engine(
        engine,
        seed_material=default_seed_material,
        personalization=personalization.encode("utf-8"),
    )
    push_log("DRBG", f"Instance {engine} initialisee dans le laboratoire.")

section_header("Zone d'action", "Commandes principales du laboratoire DRBG.", kicker="Actions")
actions = st.columns(3)
if actions[0].button("Generer la sortie RNG"):
    instance = st.session_state["drbg_instances"].get(engine)
    if instance is None:
        st.warning("Instanciez d'abord le moteur selectionne.")
    else:
        st.session_state["last_drbg_output"] = facade.generate_with_engine(instance, length=length, additional_input=additional_input.encode("utf-8"))
        push_log("DRBG", f"Generation executee avec {engine} sur {length} octets.")

if actions[1].button("Relancer une mesure locale"):
    st.session_state["last_drbg_compare"] = facade.compare_engines(length=length, seed_material=default_seed_material, additional_input=additional_input.encode("utf-8"))
    push_log("DRBG", f"Mesure locale replicatee sur {length} octets.")

if actions[2].button("Initialiser le SDK canonique"):
    st.session_state["last_sdk_status"] = facade.instantiate_sdk(personalization=personalization.encode("utf-8"))
    push_log("DRBG", "Service SDK canonique initialise sur Multiplexed Sponge.")

instance = st.session_state["drbg_instances"].get(engine)
if instance is not None:
    state = instance.export_state()["manager_state"]
    metric_strip([("Moteur actif", state["active_engine"] or "aucun"), ("Etat", state["lifecycle_state"]), ("Requetes", str(state["request_counter"])), ("Bytes depuis reseed", str(state["generated_bytes_since_reseed"]))])
else:
    note_panel("Etape suivante recommandee", "Instanciez d'abord un moteur pour activer les vues de sortie et la comparaison.", tone="info")

left, right = st.columns([1.15, 1.0], gap="large")
with left:
    section_header("Sortie RNG", "Visualisation de la derniere generation avec plusieurs formats de lecture.", kicker="Resultats")
    output = st.session_state.get("last_drbg_output")
    if output:
        st.subheader("Derniere generation")
        metric_strip(
            [
                ("Longueur", str(output["length"])),
                ("Temps", f"{output['elapsed_ns'] / 1_000_000:.3f} ms"),
                ("Valeurs distinctes", str(output["byte_summary"]["unique_values"])),
                ("Moyenne", str(output["byte_summary"]["mean"])),
            ]
        )
        tabs = st.tabs(["Hex", "Binaire", "Decimal", "Statistiques"])
        with tabs[0]:
            st.code(output["preview_hex"], language="text")
        with tabs[1]:
            st.code(output["preview_bits"], language="text")
        with tabs[2]:
            decimal_rows = output["decimal_rows"][:decimal_limit]
            compact = " | ".join(f"{row['index']}:{row['decimal']}" for row in decimal_rows)
            st.code(compact, language="text")
            st.dataframe(decimal_rows, width="stretch", hide_index=True)
        with tabs[3]:
            hist_rows = output["byte_histogram"]
            if hist_rows:
                hist_fig = px.bar(hist_rows, x="byte", y="count", title="Distribution locale des octets")
                hist_fig.update_layout(height=280, margin=dict(l=0, r=0, t=40, b=0))
                st.plotly_chart(hist_fig, width="stretch")
            st.write(output["byte_summary"])
        with st.expander("Etat non sensible du moteur"):
            st.json(output["state"])
        if ui_mode == "technique":
            with st.expander("Details techniques"):
                st.write({"elapsed_ns": output["elapsed_ns"], "length": output["length"]})
    else:
        st.info("Aucune generation n'a encore ete lancee.")

with right:
    section_header("Mesure locale", "Observer des generations repetees du moteur officiel sans changer la baseline.", kicker="Analyse")
    text_panel("Lecture pedagogique", f"Multiplexed Sponge est l'unique moteur DRBG de la baseline. Le laboratoire utilise un seed material derive du conditionneur ({lab_seed_bundle['source']}).")
    st.caption(f"Seedinit actif: {lab_seed_bundle['seed_preview_hex']}")
    compare = st.session_state.get("last_drbg_compare")
    if compare:
        rows = [{"engine": name, "elapsed_ns": result["elapsed_ns"], "length": result["length"], "preview": preview_bytes(result["data"])} for name, result in compare.items()]
        fig = px.bar(rows, x="engine", y="elapsed_ns", color="engine", title="Comparaison locale par appel")
        fig.update_layout(height=320, margin=dict(l=0, r=0, t=40, b=0), showlegend=False)
        st.plotly_chart(fig, width="stretch")
        st.dataframe(rows, width="stretch", hide_index=True)
        if ui_mode == "technique":
            compare_stats = [
                {
                    "engine": name,
                    "mean_byte": result["byte_summary"]["mean"],
                    "unique_values": result["byte_summary"]["unique_values"],
                    "min": result["byte_summary"]["min"],
                    "max": result["byte_summary"]["max"],
                }
                for name, result in compare.items()
            ]
            st.dataframe(compare_stats, width="stretch", hide_index=True)
    else:
        st.info("Utilisez le bouton secondaire pour relancer une mesure sur le moteur officiel.")

with st.expander("Journal des actions"):
    render_logs(st.session_state["ui_logs"])
note_panel("Limite d'interpretation", "Cette page observe un prototype logiciel local. Elle n'etablit ni conformite NIST ni validation mobile materielle.", tone="warning")
