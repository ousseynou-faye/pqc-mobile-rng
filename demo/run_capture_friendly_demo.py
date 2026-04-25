from __future__ import annotations

"""Version legere de la demo, orientee captures d'ecran pour le memoire."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT_STR = str(PROJECT_ROOT)
if PROJECT_ROOT_STR not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_STR)

from demo.demo_utils import afficher_ligne, afficher_sous_titre, afficher_texte, afficher_titre, format_liste
from demo.run_full_project_demo import FullDemoConfig, run_full_project_demo


def _print_output_bundle(title: str, bundle: dict[str, object]) -> None:
    afficher_sous_titre(title)
    afficher_ligne("Longueur", f"{bundle['length_bytes']} octets / {bundle['length_bits']} bits")
    afficher_ligne("Hexadecimal", bundle["hex"])
    afficher_ligne("Binaire", bundle["binary_grouped"])
    afficher_ligne("Decimal", bundle["decimal"])


def render_capture_friendly_demo() -> dict[str, object]:
    result = run_full_project_demo(
        FullDemoConfig(
            output_bytes=32,
            preview_bytes=12,
            preview_bits=48,
            phi_steps=4,
            mux_bits=12,
            sponge_trace_steps=2,
            root_dir="demo/.runtime/capture_friendly_demo",
        )
    )

    entropy = result["entropy"]
    conditioning = result["conditioning"]
    derivation = result["drbg_derivation"]
    outputs = result["rng_outputs"]
    state = result["state"]

    afficher_titre("DEMO POUR LE DEPLOIEMENT D'UN RNG MOBILE POST-QUANTIQUE")
#     afficher_texte(
#         """
# Cette version garde uniquement les sorties essentielles.
# Chaque section est volontairement courte pour faciliter les captures.
#         """
#     )

    afficher_titre("1. SRC")
    afficher_ligne(
        "CPU min-entropy / symbole",
        f"{entropy['cpu_source']['health_report']['min_entropy_per_symbol']:.6f}",
    )
    afficher_ligne(
        "Capteur min-entropy / symbole",
        f"{entropy['sensor_source']['health_report']['min_entropy_per_symbol']:.6f}",
    )
    afficher_ligne(
        "Pool min-entropy estimee",
        f"{entropy['pool']['snapshot']['estimated_min_entropy_bits']:.6f} bits",
    )
    afficher_ligne("Pool pret", entropy["pool"]["snapshot"]["ready"])
    afficher_ligne("Pool brut hex", entropy["pool"]["raw_preview"]["hex_preview"])

    afficher_titre("2. COND")
    afficher_ligne("Toeplitz input bits", conditioning["input_bits"])
    afficher_ligne("Toeplitz output bits", conditioning["output_bits"])
    afficher_ligne("Toeplitz output hex", conditioning["toeplitz_output"]["hex"])
    afficher_ligne("SHAKE-256 seedinit hex", conditioning["shake_seedinit"]["hex"])

    afficher_titre("3. DRBG")
    afficher_ligne("seed_s", derivation["seed_s"])
    afficher_ligne("seed_t", derivation["seed_t"])
    afficher_ligne("Sequence S_n", format_liste(derivation["sequence_s_preview"], max_items=16))
    afficher_ligne("Sequence T_n", format_liste(derivation["sequence_t_preview"], max_items=16))
    afficher_ligne("Sequence multiplexee", format_liste(derivation["multiplexed_sequence_preview"], max_items=16))

    afficher_sous_titre("Trace phi(l,n)")
    for row in derivation["phi_trace"]:
        afficher_ligne(
            f"n={row['n']}",
            f"phi={row['phi_decimal']} | hex={row['phi_hex']} | bin={row['phi_binary']} | bit_T={row['selected_t_bit']}",
        )

    afficher_sous_titre("Trace sponge")
    for row in derivation["sponge_trace"]:
        afficher_ligne(
            f"Etape {row['step']}",
            f"bloc={row['block_hex']} | dec={row['block_decimal']} | bin={row['block_binary']}",
        )

    afficher_titre("4. SORTIES RNG")
    _print_output_bundle("Sortie 1", outputs["generated_output_1"])
    _print_output_bundle("Sortie 2 apres reseed", outputs["generated_output_2"])
    _print_output_bundle("Sortie apres restauration", outputs["restored_output"])

    afficher_titre("5. STATE")
    afficher_ligne("Lifecycle state", state["sdk_status"]["lifecycle_state"])
    afficher_ligne("Checkpoint disponible", state["sdk_status"]["state_available"])
    afficher_ligne("Blob ID", state["checkpoint_blob"]["blob_id"])
    afficher_ligne("Compteur materiel", state["checkpoint_blob"]["hardware_counter"])
    afficher_ligne("Compteur logiciel", state["checkpoint_blob"]["software_counter"])
    afficher_ligne("TEE namespace", state["tee_status"]["namespace"])
    afficher_ligne("TEE device_id", state["tee_status"]["device_id"])

    return result


if __name__ == "__main__":
    render_capture_friendly_demo()
