"""
Je définis ici les erreurs propres à la couche STATE / TEE simulé.
"""


class StateManagerError(Exception):
    """Je regroupe ici les erreurs générales de gestion d'état."""


class IntegrityError(StateManagerError):
    """Je signale ici une violation d'intégrité du blob scellé."""


class RollbackDetectedError(StateManagerError):
    """Je signale ici une attaque de rollback détectée via le compteur monotone."""


class SealedBlobNotFoundError(StateManagerError):
    """Je signale ici qu'aucun blob scellé n'a été trouvé."""
