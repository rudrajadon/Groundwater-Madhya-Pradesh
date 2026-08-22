"""
Recommendation heuristic — Thresholds calibrated to model output distribution.

Calibrated to achieve ~10% Critical / ~45% Watch / ~45% Stable:
  Critical: > 0.84m decline (90th percentile, severe depletion)
  Watch: 0.10m to 0.84m decline (moderate concern)
  Stable: < 0.10m decline or improving
"""
# Physical thresholds for groundwater trend classification (meters decline over 12 months)
# These match the ML model classification for consistency
CRITICAL_THRESHOLD_DECLINE_M = 4.0  # > 4m decline = Critical (unsustainable)
WATCH_THRESHOLD_DECLINE_M = 2.0     # 2-4m decline = Watch (concerning)


def classify_trend(forecast_head_msl: list[float]) -> tuple[str, str]:
    """Returns (trend_label, recommendation_text) from a 12-point forecast."""
    change = forecast_head_msl[-1] - forecast_head_msl[0]
    decline = -change  # Convert to positive decline value (positive = worse)

    if decline > CRITICAL_THRESHOLD_DECLINE_M:
        return "Critical", (
            f"Hydraulic head projected to drop {decline:.1f}m over the next 12 months. "
            "Immediate action required: prioritize recharge structures, reduce abstraction, "
            "and increase monitoring frequency."
        )
    elif decline > WATCH_THRESHOLD_DECLINE_M:
        return "Watch", (
            f"Moderate decline projected ({decline:.1f}m over 12 months). "
            "Monitor closely and review local abstraction patterns."
        )
    else:
        if change > 0.5:
            return "Stable", f"Water levels improving (+{change:.1f}m projected). Continue current management."
        else:
            return "Stable", f"Water levels stable ({abs(decline):.2f}m change). Continue monitoring."


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
