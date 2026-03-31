from __future__ import annotations

"""
Je lance ici une démonstration complète du projet :

SRC -> COND -> DRBG -> STATE

Mon objectif est de montrer le fonctionnement nominal, les éléments de
recherche et les contrôles de sécurité, sans modifier les couches existantes.
"""

import hashlib
import json
import secrets
import sys
from pathlib import Path
from typing import Callable

PROJET_RACINE = Path(__file__).resolve().parent.parent
if str(PROJET_RACINE) not in sys.path:
    sys.path.insert(0, str(PROJET_RACINE))
RACINE_TEMPORAIRE_DEMO = PROJET_RACINE / "demo" / ".runtime"
RACINE_TEMPORAIRE_DEMO.mkdir(parents=True, exist_ok=True)

from demo.demo_utils import (
    afficher_json,
    afficher_ligne,
    afficher_sous_titre,
    afficher_texte,
    afficher_titre,
    format_bits,
    format_hex,
    format_liste,
)
from software.conditioner import EntropyMixer
from software.entropy import CPUJitterSource, EntropyPool, SensorEntropySource
from software.lfsr import RecurrenceSequence
from software.pqc_drbg import (
    DRBGPolicy,
    EngineSelectionMode,
    FailStopError,
    PQCCompositeDRBG,
    ReseedRequiredError,
)
from software.pqc_drbg.lwr_core import ModuleLWRCore
from software.pqc_drbg.sponge_core import MultiplexedSpongeAdapter
from software.sponge import MultiplexedSponge
from software.state_manager import (
    IntegrityError,
    RollbackDetectedError,
    SimulatedTEE,
    StateManager,
)


def construire_sponge_recherche(seed_digest: bytes) -> MultiplexedSponge:
    """
    Je construis ici une vraie instance du Multiplexed Sponge de recherche.

    Je dérive deux séquences de récurrence depuis `seed_digest`, puis j'absorbe
    un petit matériau dérivé pour lier l'état initial au digest d'entrée.
    """

    graine_s = (int.from_bytes(seed_digest[:2], "big") % ((1 << 16) - 1)) + 1
    graine_t = (int.from_bytes(seed_digest[2:4], "big") % ((1 << 16) - 1)) + 1

    sequence_s = RecurrenceSequence(degree=16, seed=graine_s)
    sequence_t = RecurrenceSequence(degree=16, seed=graine_t)

    sponge = MultiplexedSponge(
        seq_s=sequence_s,
        seq_t=sequence_t,
        l=4,
        rate=128,
        capacity=128,
    )

    materiau = hashlib.shake_256(b"demo-sponge:" + seed_digest).digest(32)
    blocs = [int.from_bytes(materiau[index:index + 8], "big") for index in range(0, 32, 8)]
    sponge.absorb_blocks(blocs, block_size=64)
    return sponge


def construire_moteur_sponge() -> MultiplexedSpongeAdapter:
    """Je prépare ici l'adaptateur DRBG du moteur sponge secondaire."""

    return MultiplexedSpongeAdapter(sponge_factory=construire_sponge_recherche)


def creer_repertoire_demo(prefixe: str) -> Path:
    """
    Je crée ici un répertoire isolé pour les scénarios STATE et sécurité.

    Je ne passe pas par `TemporaryDirectory` car son nettoyage automatique
    déclenche ici des erreurs de permission dans cet environnement Windows.
    """

    chemin = RACINE_TEMPORAIRE_DEMO / f"{prefixe}_{secrets.token_hex(4)}"
    chemin.mkdir(parents=True, exist_ok=False)
    return chemin


def executer_section(
    titre: str,
    fonction: Callable[[], dict[str, object] | None],
    resultats: list[tuple[str, str, str]],
) -> dict[str, object] | None:
    """
    J'exécute ici une section de démonstration avec gestion d'erreur lisible.
    """

    afficher_titre(titre)
    try:
        resultat = fonction()
    except Exception as exc:
        afficher_ligne("Statut", "échec")
        afficher_ligne("Erreur", f"{type(exc).__name__}: {exc}")
        resultats.append((titre, "échec", f"{type(exc).__name__}: {exc}"))
        return None

    afficher_ligne("Statut", "ok")
    resultats.append((titre, "ok", "Section exécutée."))
    return resultat


def section_vue_ensemble() -> dict[str, object]:
    """Je présente ici l'architecture globale et les liens entre modules."""

    afficher_texte(
        """
Dans cette étape, je rappelle l'architecture complète du projet.
Je montre aussi quels modules Python portent chaque responsabilité.
        """
    )
    print("SRC -> COND -> DRBG -> STATE")
    afficher_json(
        {
            "SRC": [
                "software/entropy/cpu_jitter.py",
                "software/entropy/sensor_entropy.py",
                "software/entropy/health_estimator.py",
                "software/entropy/entropy_pool.py",
            ],
            "COND": [
                "software/conditioner/toeplitz_extractor.py",
                "software/conditioner/shake_conditioner.py",
                "software/conditioner/entropy_mixer.py",
            ],
            "DRBG": [
                "software/pqc_drbg/lwr_core.py",
                "software/pqc_drbg/sponge_core.py",
                "software/pqc_drbg/drbg_engine.py",
                "software/pqc_drbg/state.py",
                "software/pqc_drbg/policy.py",
            ],
            "STATE": [
                "software/state_manager/tee_simulator.py",
                "software/state_manager/state_manager.py",
            ],
        }
    )
    afficher_texte(
        """
Je considere Multiplexed Sponge comme le moteur nominal du DRBG.
Je présente le Multiplexed Sponge comme moteur secondaire de recherche.
        """
    )
    return {"architecture": "SRC -> COND -> DRBG -> STATE"}


def section_src() -> dict[str, object]:
    """Je démontre ici la collecte de la couche SRC."""

    afficher_texte(
        """
Je collecte ici deux blocs d'entropie brute.
Je montre ensuite les symboles extraits, les métadonnées et les rapports de santé.
        """
    )

    cpu = CPUJitterSource(sample_count=64, inner_loops=64, lsb_count=2, warmup_rounds=8)
    inertiel = SensorEntropySource(frame_count=16, lsb_count=2)
    pool = EntropyPool(target_min_entropy_bits=8.0, target_min_symbols=32)

    chunk_cpu = cpu.collect()
    rapport_cpu = pool.add_chunk(chunk_cpu)
    chunk_sensor = inertiel.collect()
    rapport_sensor = pool.add_chunk(chunk_sensor)
    snapshot = pool.snapshot()

    afficher_sous_titre("Source primaire : CPU jitter")
    afficher_ligne("Source", chunk_cpu.source_name)
    afficher_ligne("Symboles collectés", chunk_cpu.sample_count)
    afficher_ligne("Largeur d'un symbole", f"{chunk_cpu.symbol_bits} bits")
    afficher_ligne("Aperçu des symboles", format_liste(chunk_cpu.symbols, max_items=16))
    afficher_ligne("Octets bruts", format_hex(chunk_cpu.raw_bytes))
    afficher_ligne("Santé acceptée", rapport_cpu.accepted)
    afficher_ligne("Min-entropie par symbole", round(rapport_cpu.min_entropy_per_symbol, 4))
    afficher_ligne("Métadonnées", chunk_cpu.metadata)

    afficher_sous_titre("Source secondaire : capteurs inertiels simulés")
    afficher_ligne("Source", chunk_sensor.source_name)
    afficher_ligne("Symboles collectés", chunk_sensor.sample_count)
    afficher_ligne("Largeur d'un symbole", f"{chunk_sensor.symbol_bits} bits")
    afficher_ligne("Aperçu des symboles", format_liste(chunk_sensor.symbols, max_items=16))
    afficher_ligne("Octets bruts", format_hex(chunk_sensor.raw_bytes))
    afficher_ligne("Santé acceptée", rapport_sensor.accepted)
    afficher_ligne("Min-entropie par symbole", round(rapport_sensor.min_entropy_per_symbol, 4))
    afficher_ligne("Métadonnées", chunk_sensor.metadata)

    afficher_sous_titre("Pool d'entropie")
    afficher_ligne("Chunks acceptés", snapshot.accepted_chunks)
    afficher_ligne("Chunks rejetés", snapshot.rejected_chunks)
    afficher_ligne("Total symboles", snapshot.total_symbols)
    afficher_ligne("Total octets bruts", snapshot.total_raw_bytes)
    afficher_ligne("Min-entropie estimée", round(snapshot.estimated_min_entropy_bits, 4))
    afficher_ligne("Pool prêt pour COND", snapshot.ready)

    if snapshot.total_raw_bytes == 0:
        raise RuntimeError("Aucun octet brut n'est disponible pour le conditionnement.")

    return {
        "pool": pool,
        "cpu_chunk": chunk_cpu,
        "sensor_chunk": chunk_sensor,
        "snapshot": snapshot,
    }


def section_cond(pool: EntropyPool) -> dict[str, object]:
    """Je montre ici la transformation brute -> Seedinit."""

    afficher_texte(
        """
Je récupère ici les octets bruts produits par SRC.
J'applique ensuite Toeplitz puis SHAKE-256 pour dériver la seed finale `Seedinit`.
        """
    )

    mixer = EntropyMixer(toeplitz_output_bits=256, shake_output_bytes=32)
    resultat = mixer.condition_from_pool(
        pool,
        personalization=b"memoire-demo",
        extra_context=b"full-project-demo",
    )

    afficher_ligne("Raw_Data", format_hex(resultat.raw_data))
    afficher_ligne("Raw_Data en bits", format_bits(resultat.raw_data))
    afficher_ligne("Toeplitz seed", format_hex(resultat.toeplitz_seed))
    afficher_ligne("Toeplitz output", format_hex(resultat.toeplitz_output))
    afficher_ligne("Context_Info", resultat.context_info.decode("utf-8", errors="replace"))
    afficher_ligne("Seedinit", format_hex(resultat.seedinit))
    afficher_texte(
        """
Je montre ici que la couche COND ne transmet jamais l'entropie brute telle quelle au DRBG.
Je passe par une extraction structurée, puis par une dérivation finale stable.
        """
    )
    return {"conditioning": resultat}


def section_drbg_module_lwr(seedinit: bytes) -> dict[str, object]:
    """Je demontre ici le moteur secondaire Module-LWR."""

    afficher_texte(
        """
Je lance ici le moteur secondaire Module-LWR.
Je montre une instanciation, une génération, un reseed, puis l'export d'état non sensible.
        """
    )

    moteur = ModuleLWRCore()
    moteur.instantiate(seedinit, personalization=b"demo-lwr")
    sortie_1 = moteur.generate(32)
    etat_1 = moteur.export_state()

    seed_reseed = hashlib.shake_256(seedinit + b"demo-lwr-reseed").digest(32)
    moteur.reseed(seed_reseed, additional_input=b"demo-context")
    sortie_2 = moteur.generate(32)
    etat_2 = moteur.export_state()

    afficher_ligne("Sortie avant reseed", format_hex(sortie_1))
    afficher_ligne("Sortie avant reseed en bits", format_bits(sortie_1))
    afficher_ligne("Sortie après reseed", format_hex(sortie_2))
    afficher_ligne("Flux modifié par reseed", sortie_1 != sortie_2)
    afficher_ligne("État exporté après génération", etat_2)

    return {
        "lwr_output_before_reseed": sortie_1,
        "lwr_output_after_reseed": sortie_2,
        "lwr_state_before_reseed": etat_1,
        "lwr_state_after_reseed": etat_2,
    }


def section_sponge_recherche(seedinit: bytes, reference_lwr: bytes) -> dict[str, object]:
    """Je présente ici le moteur secondaire Multiplexed Sponge."""

    afficher_texte(
        """
Je montre maintenant le moteur secondaire Multiplexed Sponge.
Je l'instancie pour la recherche et je le compare simplement au flux Module-LWR.
        """
    )

    moteur = construire_moteur_sponge()
    moteur.instantiate(seedinit, personalization=b"demo-sponge")
    sortie = moteur.generate(32, additional_input=b"demo-recherche")
    etat = moteur.export_state()

    afficher_ligne("Sortie sponge", format_hex(sortie))
    afficher_ligne("Sortie sponge en bits", format_bits(sortie))
    afficher_ligne("État exporté", etat)
    afficher_ligne("Même sortie que Module-LWR", sortie == reference_lwr)
    afficher_texte(
        """
Je précise ici que cette sortie ne remplace pas le moteur nominal.
Je l'utilise uniquement comme moteur secondaire de recherche et de comparaison.
        """
    )

    return {"sponge_output": sortie, "sponge_state": etat}


def section_gestionnaire_composite(seedinit: bytes) -> dict[str, object]:
    """Je démontre ici le gestionnaire composite et ses modes de politique."""

    afficher_texte(
        """
Je compare ici les trois usages principaux du gestionnaire composite :
- mode strict LWR ;
- mode recherche sponge ;
- mode fallback expérimental contrôlé.
        """
    )

    strict = PQCCompositeDRBG(
        sponge_engine=construire_moteur_sponge(),
        policy=DRBGPolicy(selection_mode=EngineSelectionMode.STRICT_SPONGE_ONLY),
    )
    strict.instantiate(seedinit)
    strict_output = strict.generate(24)

    recherche = PQCCompositeDRBG(
        sponge_engine=construire_moteur_sponge(),
        policy=DRBGPolicy(selection_mode=EngineSelectionMode.FORCE_LWR_RESEARCH),
    )
    recherche.instantiate(seedinit)
    recherche_output = recherche.generate(24)

    fallback = PQCCompositeDRBG(
        sponge_engine=construire_moteur_sponge(),
        policy=DRBGPolicy(
            selection_mode=EngineSelectionMode.ALLOW_EXPERIMENTAL_LWR_FALLBACK,
            allow_fallback_on_unavailability_only=True,
        ),
    )
    fallback.sponge_engine.instantiate(
        hashlib.shake_256(seedinit + b"fallback-sponge-ready").digest(32),
        personalization=b"demo-fallback-ready",
    )
    fallback.instantiate(seedinit)

    def generation_indisponible(nbytes: int, additional_input: bytes = b"") -> bytes:
        raise RuntimeError("Indisponibilité technique simulée du moteur LWR.")

    fallback.lwr_engine.generate = generation_indisponible
    fallback_output = fallback.generate(24)

    afficher_sous_titre("Mode strict LWR")
    afficher_ligne("Moteur actif", strict.export_state()["manager_state"]["active_engine"])
    afficher_ligne("Sortie", format_hex(strict_output, max_octets=24))
    afficher_ligne("État exporté", strict.export_state()["manager_state"])

    afficher_sous_titre("Mode recherche sponge")
    afficher_ligne("Moteur actif", recherche.export_state()["manager_state"]["active_engine"])
    afficher_ligne("Sortie", format_hex(recherche_output, max_octets=24))
    afficher_ligne("État exporté", recherche.export_state()["manager_state"])

    afficher_sous_titre("Mode fallback expérimental")
    afficher_ligne("Moteur actif après panne simulée", fallback.export_state()["manager_state"]["active_engine"])
    afficher_ligne("Sortie", format_hex(fallback_output, max_octets=24))
    afficher_ligne("État exporté", fallback.export_state()["manager_state"])

    return {
        "strict_state": strict.export_state(),
        "research_state": recherche.export_state(),
        "fallback_state": fallback.export_state(),
    }


def section_machine_etats(seedinit: bytes) -> dict[str, object]:
    """Je trace ici les états clés du DRBG composite."""

    afficher_texte(
        """
Dans cette étape, je vérifie explicitement la machine à états :
état initial, READY, NEED_RESEED, FAIL_STOP et ZEROIZED.
        """
    )

    drbg = PQCCompositeDRBG(
        sponge_engine=construire_moteur_sponge(),
        policy=DRBGPolicy(reseed_interval_requests=1),
    )

    afficher_ligne("État initial", drbg.export_state()["manager_state"]["lifecycle_state"])

    drbg.instantiate(seedinit)
    afficher_ligne("Après instantiate", drbg.export_state()["manager_state"]["lifecycle_state"])

    _ = drbg.generate(16)
    afficher_ligne("Après première génération", drbg.export_state()["manager_state"]["lifecycle_state"])

    try:
        drbg.generate(16)
    except ReseedRequiredError as exc:
        afficher_ligne("Passage à NEED_RESEED", exc)

    afficher_ligne("État courant", drbg.export_state()["manager_state"]["lifecycle_state"])

    drbg.reseed(hashlib.shake_256(seedinit + b"machine-reseed").digest(32), reason="demo_machine_reseed")
    afficher_ligne("Après reseed", drbg.export_state()["manager_state"]["lifecycle_state"])

    drbg.lwr_engine.zeroize()
    try:
        drbg.generate(16)
    except FailStopError as exc:
        afficher_ligne("Passage à FAIL_STOP", exc)

    afficher_ligne("État courant", drbg.export_state()["manager_state"]["lifecycle_state"])

    drbg.zeroize()
    etat_final = drbg.export_state()["manager_state"]
    afficher_ligne("Après zeroize", etat_final["lifecycle_state"])

    afficher_sous_titre("Trace des transitions")
    afficher_json(etat_final["transition_history"], max_lignes=20)

    return {"state_machine": etat_final}


def section_state_tee(seedinit: bytes) -> dict[str, object]:
    """Je démontre ici `seal`, `unseal` et la restauration d'état DRBG."""

    afficher_texte(
        """
Je montre maintenant la couche STATE / TEE simulé.
Je scelle un payload simple, puis je restaure un état complet de DRBG composite.
        """
    )

    racine = creer_repertoire_demo("pqc_demo_state")
    tee = SimulatedTEE(root_dir=racine, device_id="jury-device", namespace="memoire-pqc")
    manager_simple = StateManager(tee=tee, blob_id="demo_payload")

    payload = {
        "active_engine": "multiplexed_sponge",
        "counter": 1,
        "seedinit_prefix": seedinit[:8].hex(),
    }
    metadata = {"purpose": "demo_payload"}

    blob = manager_simple.seal_payload(payload, payload_metadata=metadata)
    restaure = manager_simple.unseal_payload(payload_metadata=metadata)
    contenu_blob = json.loads(tee._blob_path(blob.blob_id).read_text(encoding="utf-8"))

    afficher_sous_titre("Scellement d'un payload simple")
    afficher_ligne("Répertoire de travail", racine)
    afficher_ligne("Blob scellé", tee._blob_path(blob.blob_id))
    afficher_ligne("Compteur matériel", tee.hardware_counter)
    afficher_ligne("Payload restauré", restaure)
    afficher_json(contenu_blob, max_lignes=16)

    manager_drbg = StateManager(tee=tee, blob_id="demo_drbg")
    drbg = PQCCompositeDRBG(
        sponge_engine=construire_moteur_sponge(),
        policy=DRBGPolicy(selection_mode=EngineSelectionMode.STRICT_SPONGE_ONLY),
    )
    drbg.instantiate(seedinit)
    _ = drbg.generate(16)
    checkpoint = manager_drbg.checkpoint_drbg(drbg, payload_metadata={"purpose": "checkpoint"})

    restaure_drbg = PQCCompositeDRBG(
        sponge_engine=construire_moteur_sponge(),
        policy=DRBGPolicy(selection_mode=EngineSelectionMode.STRICT_SPONGE_ONLY),
    )
    payload_restaure = manager_drbg.restore_drbg(
        restaure_drbg,
        payload_metadata={"purpose": "checkpoint"},
    )

    afficher_sous_titre("Checkpoint et restauration du DRBG")
    afficher_ligne("Blob DRBG scellé", tee._blob_path(checkpoint.blob_id))
    afficher_ligne("Moteur actif restauré", payload_restaure["manager_state"]["active_engine"])
    afficher_ligne(
        "État restauré côté DRBG",
        restaure_drbg.export_state()["manager_state"]["lifecycle_state"],
    )
    afficher_ligne("Intégrité simple", payload_restaure["manager_state"]["active_engine"] == "multiplexed_sponge")

    return {
        "sealed_blob": contenu_blob,
        "restored_payload": restaure,
        "restored_drbg_state": restaure_drbg.export_state(),
    }


def section_verifications_securite(seedinit: bytes) -> dict[str, object]:
    """Je regroupe ici les vérifications de sécurité attendues."""

    afficher_texte(
        """
Je vérifie ici les protections importantes de la démo :
reseed obligatoire, FAIL_STOP, détection d'altération et rollback.
        """
    )

    resume: dict[str, object] = {}

    drbg_reseed = PQCCompositeDRBG(policy=DRBGPolicy(reseed_interval_requests=1))
    drbg_reseed.instantiate(seedinit)
    _ = drbg_reseed.generate(8)
    try:
        drbg_reseed.generate(8)
    except ReseedRequiredError as exc:
        afficher_ligne("Reseed obligatoire détecté", exc)
        resume["reseed_required"] = True

    drbg_fail_stop = PQCCompositeDRBG()
    drbg_fail_stop.instantiate(seedinit)
    drbg_fail_stop.lwr_engine.zeroize()
    try:
        drbg_fail_stop.generate(8)
    except FailStopError as exc:
        afficher_ligne("FAIL_STOP déclenché", exc)
        resume["fail_stop"] = True

    racine_integrite = creer_repertoire_demo("pqc_demo_security")
    tee = SimulatedTEE(root_dir=racine_integrite, device_id="jury-device", namespace="memoire-pqc")
    manager = StateManager(tee=tee, blob_id="security_blob")
    metadata = {"purpose": "security_demo"}

    blob = manager.seal_payload({"epoch": 1, "engine": "module_lwr"}, payload_metadata=metadata)
    chemin_blob = tee._blob_path(blob.blob_id)
    donnees = json.loads(chemin_blob.read_text(encoding="utf-8"))
    donnees["ciphertext_hex"] = ("0" if donnees["ciphertext_hex"][0] != "0" else "1") + donnees["ciphertext_hex"][1:]
    chemin_blob.write_text(json.dumps(donnees, indent=2), encoding="utf-8")

    try:
        manager.unseal_payload(payload_metadata=metadata)
    except IntegrityError as exc:
        afficher_ligne("Altération d'intégrité détectée", exc)
        resume["integrity"] = True

    racine_rollback = creer_repertoire_demo("pqc_demo_rollback")
    tee = SimulatedTEE(root_dir=racine_rollback, device_id="jury-device", namespace="memoire-pqc")
    manager = StateManager(tee=tee, blob_id="rollback_blob")
    metadata = {"purpose": "rollback_demo"}

    ancien_blob = manager.seal_payload({"epoch": 1}, payload_metadata=metadata)
    _ = manager.seal_payload({"epoch": 2}, payload_metadata=metadata)

    try:
        tee.unseal(ancien_blob, expected_aad=manager._make_aad(metadata))
    except RollbackDetectedError as exc:
        afficher_ligne("Rollback détecté", exc)
        resume["rollback"] = True

    return resume


def section_resume_final() -> dict[str, object]:
    """Je résume ici ce qui est nominal, expérimental et encore ouvert."""

    afficher_texte(
        """
Je clôture ici la démonstration en distinguant :
- ce qui fonctionne nominalement ;
- ce qui reste volontairement expérimental ;
- ce qui relève d'un futur durcissement.
        """
    )
    afficher_json(
        {
            "nominal": [
                "SRC avec collecte, métadonnées et rapports de santé",
                "COND avec Toeplitz puis SHAKE-256 vers Seedinit",
                "DRBG nominal Module-LWR",
                "Gestion de reseed et export d'état",
                "Scellement et restauration via TEE simulé",
            ],
            "expérimental": [
                "Multiplexed Sponge comme moteur secondaire de recherche",
                "Fallback sponge limité à un cadre contrôlé",
                "Capteurs inertiels en mode simulation",
            ],
            "à renforcer plus tard": [
                "Portage vers un vrai TEE mobile",
                "Compteur monotone matériel réel",
                "Durcissement cryptographique de la couche de scellement",
            ],
        }
    )
    return {"summary": "ok"}


def main() -> None:
    """Je pilote ici toute la démo de bout en bout."""

    afficher_titre("DEMONSTRATION GLOBALE DU PROJET PQC MOBILE RNG")
    afficher_texte(
        """
Je déroule ici une démonstration complète, structurée et pédagogique.
Je pars de la collecte d'entropie et je termine par la persistance protégée de l'état.
        """
    )

    bilan: list[tuple[str, str, str]] = []

    executer_section("1. Vue d'ensemble du projet", section_vue_ensemble, bilan)
    resultat_src = executer_section("2. Démonstration de la couche SRC", section_src, bilan)

    if resultat_src is None:
        pool = None
        seedinit = None
        lwr_reference = None
    else:
        pool = resultat_src["pool"]
        resultat_cond = executer_section(
            "3. Démonstration de la couche COND",
            lambda: section_cond(pool),
            bilan,
        )
        if resultat_cond is None:
            seedinit = None
            lwr_reference = None
        else:
            seedinit = resultat_cond["conditioning"].seedinit
            resultat_lwr = executer_section(
                "4. Démonstration de la couche DRBG nominale",
                lambda: section_drbg_module_lwr(seedinit),
                bilan,
            )
            lwr_reference = None if resultat_lwr is None else resultat_lwr["lwr_output_after_reseed"]

    if seedinit is not None and lwr_reference is not None:
        executer_section(
            "5. Démonstration du moteur secondaire Multiplexed Sponge",
            lambda: section_sponge_recherche(seedinit, lwr_reference),
            bilan,
        )
        executer_section(
            "6. Démonstration du gestionnaire composite",
            lambda: section_gestionnaire_composite(seedinit),
            bilan,
        )
        executer_section(
            "7. Démonstration de la machine à états",
            lambda: section_machine_etats(seedinit),
            bilan,
        )
        executer_section(
            "8. Démonstration de la couche STATE / TEE simulé",
            lambda: section_state_tee(seedinit),
            bilan,
        )
        executer_section(
            "9. Démonstration des vérifications de sécurité",
            lambda: section_verifications_securite(seedinit),
            bilan,
        )
    else:
        bilan.append(("5-9. Sections dépendantes du seedinit", "échec", "Seedinit indisponible."))

    executer_section("10. Résumé final de la démonstration", section_resume_final, bilan)

    afficher_titre("BILAN DE LA DEMONSTRATION")
    for titre, statut, detail in bilan:
        afficher_ligne(titre, f"{statut} | {detail}")


if __name__ == "__main__":
    main()
