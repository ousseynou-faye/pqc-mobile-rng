"""Je définis ici les erreurs spécifiques de la couche DRBG."""


class DRBGError(Exception):
    """Je regroupe ici les erreurs générales du DRBG."""


class InvalidDRBGStateError(DRBGError):
    """Je signale ici qu'un état logique est invalide ou incohérent."""


class InvalidStateTransitionError(InvalidDRBGStateError):
    """Je refuse ici une transition qui ne respecte pas l'automate DRBG."""


class FailStopError(DRBGError):
    """J'utilise cette erreur quand le système entre en mode FAIL_STOP."""


class HealthCheckError(DRBGError):
    """Je signale ici un échec de vérification de santé."""


class ReseedRequiredError(DRBGError):
    """Je signale ici qu'un reseed est nécessaire avant de continuer."""


class EngineUnavailableError(DRBGError):
    """Je signale ici qu'un moteur demandé n'est pas disponible."""
