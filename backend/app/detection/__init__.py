"""Fraud detection framework for Anvik investigative graph investigator."""

from app.detection.base import BaseDetectionRule
from app.detection.models import DetectionAlert, HopEvidence
from app.detection.registry import RuleRegistry, registry
from app.detection.rules.rapid_transfer import RapidOnwardTransferRule
from app.detection.scoring import calculate_alert_score

__all__ = [
    "BaseDetectionRule",
    "DetectionAlert",
    "HopEvidence",
    "RapidOnwardTransferRule",
    "RuleRegistry",
    "calculate_alert_score",
    "registry",
]
