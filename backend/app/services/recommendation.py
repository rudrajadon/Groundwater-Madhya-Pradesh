"""
Recommendation heuristic — v2, updated for consistency.
Aligned thresholds across both ML and statistical methods.
"""

# Updated thresholds - more conservative and aligned
CRITICAL_THRESHOLD_M = -5.0  # Decline of 5+ meters over 12 months
WATCH_THRESHOLD_M = -1.0     # Decline of 1-5 meters over 12 months


def classify_trend(forecast_head_msl: list[float]) -> tuple[str, str]:
    """Returns (trend_label, recommendation_text) from a 12-point forecast."""
    change = forecast_head_msl[-1] - forecast_head_msl[0]

    if change <= CRITICAL_THRESHOLD_M:
        return "Critical", (
            f"Hydraulic head projected to drop {abs(change):.1f}m over the next 12 months. "
            "Immediate action required: prioritize recharge structures, reduce abstraction, "
            "and increase monitoring frequency."
        )
    elif change <= WATCH_THRESHOLD_M:
        return "Watch", (
            f"Moderate decline projected ({abs(change):.1f}m over 12 months). "
            "Monitor closely and review local abstraction patterns."
        )
    else:
        if change > 0.5:
            return "Stable", f"Water levels improving (+{change:.1f}m projected). Continue current management."
        else:
            return "Stable", "No significant decline projected over the next 12 months."


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
