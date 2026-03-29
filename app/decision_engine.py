from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScreeningDecision:
    classification: str
    action: str
    message: str
    should_redirect_to_support: bool
    should_alert_caregiver: bool

    def to_dict(self) -> dict:
        return {
            "classification": self.classification,
            "action": self.action,
            "message": self.message,
            "should_redirect_to_support": self.should_redirect_to_support,
            "should_alert_caregiver": self.should_alert_caregiver,
        }


def decide_next_step(classification: str) -> ScreeningDecision:
    normalized = (classification or "").strip().lower()
    if normalized == "normal":
        return ScreeningDecision(
            classification="normal",
            action="exit_system",
            message="No cognitive concern detected in this screening. You may exit.",
            should_redirect_to_support=False,
            should_alert_caregiver=False,
        )
    if normalized == "mild_impairment":
        return ScreeningDecision(
            classification="mild_impairment",
            action="proceed_to_llm_support",
            message="Mild impairment indicators detected. Proceed to cognitive support interaction.",
            should_redirect_to_support=True,
            should_alert_caregiver=False,
        )
    if normalized == "moderate_impairment":
        return ScreeningDecision(
            classification="moderate_impairment",
            action="flag_warning_and_proceed",
            message="Moderate impairment indicators detected. Flag warning and proceed with support.",
            should_redirect_to_support=True,
            should_alert_caregiver=False,
        )
    return ScreeningDecision(
        classification="severe_impairment",
        action="alert_caregiver_and_proceed",
        message="Severe impairment indicators detected. Alert caregiver and proceed with support.",
        should_redirect_to_support=True,
        should_alert_caregiver=True,
    )
