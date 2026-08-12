"""
Recommendation heuristic — v4, updated with new thresholds.
Aligned with user requirements: 0-2m stable, 2-5m watch, >5m critical.
"""

# Updated thresholds (as requested)
CRITICAL_THRESHOLD_M = -5.0  # Decline > 5m over 12 months
WATCH_THRESHOLD_M = -2.0     # Decline 2–5m over 12 months


def classify_trend(forecast_head_msl: list[float]) -> tuple[str, str]:
    """Returns (trend_label, recommendation_text) from a 12-point forecast.
    
    NOTE: forecast_head_msl must be hydraulic head (m above MSL), NOT depth below ground!
    Higher values = MORE water (good), lower values = LESS water (bad).
    
    Thresholds:
    - Critical: > 5m decline
    - Watch: 2-5m decline  
    - Stable: 0-2m decline or any improvement
    """
    change = forecast_head_msl[-1] - forecast_head_msl[0]

    if change <= CRITICAL_THRESHOLD_M:
        return "Critical", (
            f"Severe water level decline projected ({abs(change):.1f}m over 12 months). "
            "Immediate action required: prioritize recharge structures, reduce abstraction, "
            "and increase monitoring frequency."
        )
    elif change <= WATCH_THRESHOLD_M:
        return "Watch", (
            f"Moderate decline projected ({abs(change):.1f}m over 12 months). "
            "Monitor closely and review local abstraction patterns."
        )
    else:
        if change > 0:
            return "Stable", (
                f"Water levels improving (+{change:.1f}m projected over 12 months). "
                "Continue current management practices."
            )
        else:
            return "Stable", (
                f"Minimal decline projected ({abs(change):.1f}m over 12 months). "
                "Continue regular monitoring."
            )


def caveat_for_zone(aquifer_zone: str) -> str | None:
    """Fractured-zone wells have the weakest model performance (R2~0.50 vs
    0.61-0.65 for Weathered/Massive, per the notebook's own evaluation) —
    surface that honestly instead of hiding it."""
    if aquifer_zone == "Fractured":
        return (
            "This well is in a Fractured-basalt zone, where the model's forecast "
            "accuracy is measurably lower (R2~0.50) than other zones. Treat this "
            "forecast as directional, not precise."
        )
    return None
