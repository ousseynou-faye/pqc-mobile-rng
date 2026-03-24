from __future__ import annotations


class RNGAPIError(RuntimeError):
    """Erreur de base de la surface publique du SDK RNG."""


class RNGNotInitializedError(RNGAPIError):
    """Le SDK RNG est utilise avant une initialisation valide."""


class RNGInvalidLengthError(RNGAPIError, ValueError):
    """La taille demandee a l'API publique est invalide."""


class RNGStateError(RNGAPIError):
    """Le SDK RNG ne peut pas accomplir l'operation demandee."""


class RNGRestoreError(RNGStateError):
    """La restauration administree de l'etat RNG a echoue."""


class RNGProfileError(RNGAPIError, ValueError):
    """Le profil demande n'est pas supporte par le SDK public."""
