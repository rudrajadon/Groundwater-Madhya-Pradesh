#!/usr/bin/env python3
"""
Check which wells are using ML vs statistical predictions.
"""
import psycopg2
import requests
import json

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'groundwater',
    'user': 'gwuser',
    'password': 'changeme'
}

def main():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # Get all wells
    cur.execute("SELECT well_id, trend_label FROM wells ORDER BY well_id")
    wells = cur.fetchall()
    
    ml_predictions = []
    statistical_predictions = []
    errors = []
    
    print(f"Checking {len(wells)} wells...")
    
    for i, (well_id, trend_label) in enumerate(wells):
        if (i + 1) % 100 == 0:
            print(f"  Checked {i+1}/{len(wells)} wells...")
        
        try:
            response = requests.get(f"http://localhost:8000/api/v1/forecast/well/{well_id}", timeout=5)
            if response.status_code == 200:
                data = response.json()
                model_version = data.get('model_version', 'unknown')
                
                if model_version == 'statistical_fallback':
                    statistical_predictions.append({
                        'well_id': well_id,
                        'trend_label': trend_label,
                        'caveat': data.get('caveat', '')
                    })
                elif model_version == 'pgnn_lstm_v1':
                    ml_predictions.append({
                        'well_id': well_id,
                        'trend_label': trend_label
                    })
                else:
                    errors.append((well_id, f"Unknown model version: {model_version}"))
            else:
                errors.append((well_id, f"HTTP {response.status_code}"))
        except Exception as e:
            errors.append((well_id, str(e)))
    
    print(f"\n{'='*80}")
    print("PREDICTION COVERAGE REPORT")
    print(f"{'='*80}\n")
    
    print(f"Total wells: {len(wells)}")
    print(f"  ML predictions: {len(ml_predictions)} ({len(ml_predictions)/len(wells)*100:.1f}%)")
    print(f"  Statistical fallback: {len(statistical_predictions)} ({len(statistical_predictions)/len(wells)*100:.1f}%)")
    print(f"  Errors: {len(errors)}")
    
    if statistical_predictions:
        print(f"\n{'='*80}")
        print(f"WELLS USING STATISTICAL FALLBACK ({len(statistical_predictions)} total)")
        print(f"{'='*80}\n")
        
        # Group by caveat reason
        reasons = {}
        for pred in statistical_predictions:
            caveat = pred['caveat'] or 'Unknown reason'
            # Extract just the reason
            if 'Insufficient data' in caveat:
                reason = caveat.split('.')[0]
            else:
                reason = caveat[:80]
            
            reasons.setdefault(reason, []).append(pred['well_id'])
        
        for reason, well_list in reasons.items():
            print(f"{reason}")
            print(f"  Wells: {len(well_list)}")
            if len(well_list) <= 10:
                print(f"  Examples: {', '.join(well_list)}")
            else:
                print(f"  Examples: {', '.join(well_list[:10])}... and {len(well_list)-10} more")
            print()
    
    if errors:
        print(f"\n{'='*80}")
        print(f"ERRORS ({len(errors)} wells)")
        print(f"{'='*80}\n")
        for well_id, error in errors[:10]:
            print(f"  {well_id}: {error}")
        if len(errors) > 10:
            print(f"  ... and {len(errors)-10} more errors")
    
    # Save summary
    summary = {
        'total_wells': len(wells),
        'ml_predictions': len(ml_predictions),
        'statistical_predictions': len(statistical_predictions),
        'errors': len(errors),
        'statistical_wells': [p['well_id'] for p in statistical_predictions]
    }
    
    with open('prediction_coverage_report.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n✓ Report saved to prediction_coverage_report.json")
    
    conn.close()
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
