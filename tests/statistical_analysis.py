"""Facade legere pour les campagnes comparatives et le reporting."""

from analysis.campaign_runner import (
    CAMPAIGN_PRESETS,
    CampaignConfig,
    export_campaign_report,
    run_comparative_campaign,
)

__all__ = [
    "CAMPAIGN_PRESETS",
    "CampaignConfig",
    "export_campaign_report",
    "run_comparative_campaign",
]
