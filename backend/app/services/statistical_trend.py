"""
Statistical trend calculation for wells not in the trained model.

Uses linear regression on recent historical data to compute trend when
ML model prediction is not available.
"""
import numpy as np
from scipy import stats
from sqlalchemy import text
from sqlalchemy.orm import Session


def compute_statistical_trend(well_id: str, db: Session, months_lookback: int = 12) -> dict:
    """
    Compute trend classification using linear regression on recent readings.
    
    Args:
        well_id: Well identifier
        db: Database session
        months_lookback: Number of months to look back (default 12)
    
    Returns:
        dict with:
        - trend_label: 'Critical', 'Watch', or 'Stable'
        - slope_m_per_year: Rate of change in meters per year
        - recommendation: Text recommendation
        - method: 'statistical' (vs 'ml')
    """
    # Get recent readings
    query = text("""
        SELECT
            date,
            head_msl_m,
            EXTRACT(EPOCH FROM date::timestamp) / (365.25 * 24 * 3600) AS year_decimal
        FROM readings
        WHERE well_id = :wid
          AND head_msl_m IS NOT NULL
          AND date >= CURRENT_DATE - (:months * INTERVAL '1 month')
        ORDER BY date ASC
    """)

    rows = db.execute(query, {"wid": well_id, "months": months_lookback}).mappings().all()
    
    if len(rows) < 3:
        # Not enough data for trend analysis
        return {
            "trend_label": "Stable",
            "slope_m_per_year": 0.0,
            "recommendation": "Insufficient data for trend analysis (< 3 readings in past 12 months)",
            "method": "statistical",
            "confidence": "low",
            "r_squared": 0.0,
            "n_readings": len(rows)
        }
    
    # Extract time series
    years = np.array([float(r["year_decimal"]) for r in rows])
    heads = np.array([float(r["head_msl_m"]) for r in rows])
    
    # Linear regression
    slope, intercept, r_value, p_value, std_err = stats.linregress(years, heads)
    
    # Project 12 months forward
    current_year = years[-1]
    future_year = current_year + 1.0
    current_head = slope * current_year + intercept
    future_head = slope * future_year + intercept
    projected_change = future_head - current_head
    
    # Classify trend based on projected 12-month change
    # Updated thresholds to match ML classification (v2)
    if projected_change < -2.0:
        trend_label = "Critical"
        recommendation = f"Declining {abs(projected_change):.1f}m/year. Immediate action required: reduce abstraction, implement recharge measures."
    elif projected_change < -0.5:
        trend_label = "Watch"
        recommendation = f"Declining {abs(projected_change):.1f}m/year. Monitor closely and prepare mitigation measures."
    else:
        trend_label = "Stable"
        if projected_change > 0.5:
            recommendation = f"Rising {projected_change:.1f}m/year. Water levels are improving."
        else:
            recommendation = "Water levels are relatively stable. Continue monitoring."
    
    # Add confidence based on R² and number of points
    r_squared = r_value ** 2
    if r_squared > 0.7 and len(rows) >= 12:
        confidence = "high"
    elif r_squared > 0.4 and len(rows) >= 6:
        confidence = "medium"
    else:
        confidence = "low"
        recommendation += " (Low confidence - limited or noisy data)"
    
    return {
        "trend_label": trend_label,
        "slope_m_per_year": float(slope),
        "recommendation": recommendation,
        "method": "statistical",
        "confidence": confidence,
        "r_squared": float(r_squared),
        "n_readings": len(rows)
    }
