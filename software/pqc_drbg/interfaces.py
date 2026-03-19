from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

"""
Je définis ici le contrat commun que doivent respecter les moteurs DRBG.

Je garde volontairement une interface petite et stable pour ne pas casser
le reste du projet, mais je la rends plus explicite pour mieux séparer :
- l'initialisation ;
- le reseed ;
- la génération ;
- l'export d'état non sensible ;
- la destruction logique de l'état ;
- les contrôles de santé.
"""


StateExport = dict[str, Any]


@dataclass(slots=True)
class EngineHealth:
    """Je transporte ici un diagnostic simple et sérialisable du moteur."""

    engine_name: str
    healthy: bool
    reason: str = ""
    details: StateExport = field(default_factory=dict)


class DRBGEngine(ABC):
    """Je définis ici l'API minimale que tout moteur DRBG doit respecter."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Je retourne ici l'identifiant stable du moteur."""

    @abstractmethod
    def instantiate(self, seed_material: bytes, personalization: bytes = b"") -> None:
        """J'initialise ici le moteur à partir d'une seed et d'un contexte optionnel."""

    @abstractmethod
    def reseed(self, seed_material: bytes, additional_input: bytes = b"") -> None:
        """Je mélange ici une nouvelle seed dans l'état déjà initialisé."""

    @abstractmethod
    def generate(self, nbytes: int, additional_input: bytes = b"") -> bytes:
        """Je génère ici `nbytes` octets déterministes à partir de l'état courant."""

    @abstractmethod
    def export_state(self) -> StateExport:
        """J'exporte ici un état non sensible utilisable pour l'observabilité."""

    @abstractmethod
    def zeroize(self) -> None:
        """Je détruis ici au mieux l'état sensible maintenu par le moteur."""

    @abstractmethod
    def health(self) -> EngineHealth:
        """Je retourne ici l'état de santé logique du moteur."""
