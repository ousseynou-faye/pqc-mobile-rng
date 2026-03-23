from __future__ import annotations

from dataclasses import dataclass

from .errors import DRBGError

"""Je regroupe ici les paramètres cryptographiques du prototype Module-LWR.

Étape 2 - gel définitif des profils :
- profil exécutable actuel = `module_lwr_proto_software_v1` ;
- profil manuscrit = aligné sur le profil exécutable pour tous les résultats réellement obtenus ;
- profil mobile futur = variante documentaire liée à la NTT, non activée dans le code courant.
"""


@dataclass(frozen=True, slots=True)
class LWRParams:
    """Je rassemble ici les paramètres publics du moteur Module-LWR."""

    n: int
    k: int
    q: int
    p: int
    secret_bound: int = 1

    def validate(self) -> None:
        """Je vérifie ici la cohérence minimale des paramètres."""

        if self.n <= 0 or self.k <= 0:
            raise DRBGError("Je dois avoir des dimensions LWR strictement positives.")
        if self.q <= 0 or self.p <= 0:
            raise DRBGError("Je dois avoir des moduli strictement positifs.")
        if self.p >= self.q:
            raise DRBGError("Je dois avoir un modulus de réduction p strictement plus petit que q.")
        if self.secret_bound != 1:
            raise DRBGError("Je limite ici le prototype au secret ternaire {-1, 0, 1}.")

    @property
    def rounding_shift(self) -> int | None:
        """Je calcule ici le décalage idéal quand q et p sont des puissances de deux."""

        if self.q <= 0 or self.p <= 0:
            return None
        if (self.q & (self.q - 1)) != 0:
            return None
        if (self.p & (self.p - 1)) != 0:
            return None
        q_bits = self.q.bit_length() - 1
        p_bits = self.p.bit_length() - 1
        if p_bits > q_bits:
            return None
        return q_bits - p_bits


@dataclass(frozen=True, slots=True)
class ParameterProfileNote:
    """Je documente ici un profil de paramètres sans l'activer automatiquement."""

    name: str
    n: int | None
    k: int | None
    q: int | None
    p: int | None
    status: str
    implemented_now: bool
    comment: str


PROFILE_PROTO_SOFTWARE = ParameterProfileNote(
    name="module_lwr_proto_software_v1",
    n=256,
    k=3,
    q=8192,
    p=1024,
    status="baseline executable actuelle",
    implemented_now=True,
    comment=(
        "Profil réellement utilisé par le code, les tests et la démonstration logicielle. "
        "Aucune NTT n'est active dans cette baseline."
    ),
)

PROFILE_MANUSCRIPT_REFERENCE = ParameterProfileNote(
    name="module_lwr_manuscript_reference_v1",
    n=256,
    k=3,
    q=8192,
    p=1024,
    status="référence manuscrit pour les résultats implémentés",
    implemented_now=True,
    comment=(
        "Le manuscrit doit utiliser ce profil pour présenter honnêtement les résultats "
        "mesurés sur le prototype réellement exécuté."
    ),
)

PROFILE_MOBILE_FUTURE = ParameterProfileNote(
    name="module_lwr_mobile_future_ntt_candidate",
    n=256,
    k=3,
    q=3329,
    p=None,
    status="variante documentaire future",
    implemented_now=False,
    comment=(
        "q=3329 est réservé à une trajectoire future compatible avec une optimisation NTT "
        "documentaire. Ce profil n'est pas activé dans le code courant et la valeur de p "
        "reste à confirmer avant toute intégration logicielle."
    ),
)


def default_lwr_params() -> LWRParams:
    """Je fournis ici le jeu de paramètres nominal gelé du prototype.

    Profil officiel exécutable : `module_lwr_proto_software_v1`
    - n = 256
    - k = 3
    - q = 8192
    - p = 1024
    - secret ternaire {-1, 0, 1}

    Remarque : ce profil reste le défaut tant qu'aucune réécriture validée du
    prototype n'introduit une variante NTT réellement testée. Le candidat
    documentaire `q = 3329` n'est donc pas injecté dans le comportement courant.
    """

    return LWRParams(
        n=PROFILE_PROTO_SOFTWARE.n,
        k=PROFILE_PROTO_SOFTWARE.k,
        q=PROFILE_PROTO_SOFTWARE.q,
        p=PROFILE_PROTO_SOFTWARE.p,
        secret_bound=1,
    )
