from __future__ import annotations

"""
Je centralise ici les petits utilitaires d'affichage de la démo.

Je veux garder le script principal lisible, tout en produisant une sortie
terminal propre et directement exploitable devant un jury.
"""

import json
from typing import Any, Iterable


def afficher_titre(texte: str) -> None:
    """J'affiche ici un titre de section bien visible dans le terminal."""

    barre = "=" * len(texte)
    print()
    print(barre)
    print(texte)
    print(barre)


def afficher_sous_titre(texte: str) -> None:
    """J'affiche ici un sous-titre plus compact."""

    print()
    print(f"[{texte}]")


def afficher_ligne(libelle: str, valeur: Any) -> None:
    """J'affiche ici une ligne clé/valeur simple et lisible."""

    print(f"- {libelle}: {valeur}")


def afficher_texte(texte: str) -> None:
    """J'affiche ici un paragraphe court de commentaire pédagogique."""

    for ligne in texte.strip().splitlines():
        print(ligne.rstrip())


def format_hex(data: bytes | bytearray | None, *, max_octets: int = 32) -> str:
    """Je formate ici une valeur binaire en hexadécimal abrégé."""

    if not data:
        return "(vide)"

    brut = bytes(data)
    extrait = brut[:max_octets].hex()
    if len(brut) > max_octets:
        return f"{extrait}... ({len(brut)} octets)"
    return f"{extrait} ({len(brut)} octets)"


def format_bits(data: bytes | bytearray | None, *, max_bits: int = 64) -> str:
    """Je formate ici un aperçu de bits pour la présentation terminal."""

    if not data:
        return "(vide)"

    bits = "".join(f"{octet:08b}" for octet in bytes(data))
    extrait = bits[:max_bits]
    if len(bits) > max_bits:
        return f"{extrait}... ({len(bits)} bits)"
    return f"{extrait} ({len(bits)} bits)"


def format_liste(valeurs: Iterable[Any], *, max_items: int = 12) -> str:
    """Je réduis ici une liste pour éviter de saturer la sortie terminal."""

    liste = list(valeurs)
    extrait = liste[:max_items]
    suffixe = "..." if len(liste) > max_items else ""
    return f"{extrait}{suffixe}"


def format_json(objet: Any, *, max_lignes: int = 18) -> str:
    """Je sérialise ici un objet JSON en tronquant les sorties trop longues."""

    rendu = json.dumps(objet, indent=2, ensure_ascii=False, sort_keys=True)
    lignes = rendu.splitlines()
    if len(lignes) <= max_lignes:
        return rendu
    return "\n".join(lignes[:max_lignes] + ["  ..."])


def afficher_json(objet: Any, *, max_lignes: int = 18) -> None:
    """J'affiche ici un bloc JSON compact pour la démonstration."""

    print(format_json(objet, max_lignes=max_lignes))
