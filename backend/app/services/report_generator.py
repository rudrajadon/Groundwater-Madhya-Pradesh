"""
Report generation service for policy PDF and CSV exports.
CGWB-compliant templates for official groundwater monitoring reports.
"""
import io
import csv
from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, 
    PageBreak, Image, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas


def generate_district_map_image(
    district_name: str,
    wells_data: List[Dict],
    output_path: str
) -> Optional[str]:
    """
    Generate a map showing the district boundary with well locations.
    
    Args:
        district_name: Name of the district
        wells_data: List of well dicts with lat, lon, trend_label
        output_path: Path to save the PNG image
        
    Returns:
        Path to generated image file, or None if generation failed
    """
    if not GEOPANDAS_AVAILABLE:
        return None
        
    try:
        # Load district boundaries
        shp_paths = [
            Path("/app/23/MP_DISTRICT_BDY.shp"),
            Path(__file__).parent.parent.parent.parent.parent / "23" / "MP_DISTRICT_BDY.shp",
        ]
        
        districts_gdf = None
        for shp_path in shp_paths:
            if shp_path.exists():
                districts_gdf = gpd.read_file(shp_path)
                districts_gdf = districts_gdf.to_crs("EPSG:4326")
                break
        
        if districts_gdf is None:
            print(f"[PDF] District shapefile not found, skipping map")
            return None
        
        # Standardize column names
        if 'DISTRICT' in districts_gdf.columns:
            districts_gdf = districts_gdf.rename(columns={'DISTRICT': 'district'})
        districts_gdf['district'] = districts_gdf['district'].str.strip().str.upper()
        
        # Find the target district
        target_district = districts_gdf[
            districts_gdf['district'] == district_name.upper()
        ]
        
        if target_district.empty:
            print(f"[PDF] District {district_name} not found in shapefile")
            return None
        
        # Create figure
        fig, ax = plt.subplots(1, 1, figsize=(6, 6), dpi=150)
        
        # Plot district boundary
        target_district.boundary.plot(
            ax=ax,
            color='#1e40af',
            linewidth=2,
            label='District Boundary'
        )
        
        # Fill district with light color
        target_district.plot(
            ax=ax,
            color='#e0e7ff',
            alpha=0.3,
            edgecolor='none'
        )
        
        # Plot wells by trend
        if wells_data:
            trend_colors = {
                'Critical': '#dc2626',  # red
                'Watch': '#f59e0b',     # orange
                'Stable': '#22c55e',    # green
                'Unknown': '#9ca3af'    # gray
            }
            
            for trend, color in trend_colors.items():
                trend_wells = [w for w in wells_data if w.get('trend_label') == trend]
                if trend_wells:
                    lats = [w['lat'] for w in trend_wells]
                    lons = [w['lon'] for w in trend_wells]
                    ax.scatter(
                        lons, lats,
                        c=color,
                        s=30,
                        alpha=0.7,
                        edgecolors='white',
                        linewidths=0.5,
                        label=f'{trend} ({len(trend_wells)})',
                        zorder=5
                    )
        
        # Add district name as title
        ax.set_title(
            f'{district_name} District\nGroundwater Monitoring Wells',
            fontsize=12,
            fontweight='bold',
            pad=10
        )
        
        # Remove axis labels
        ax.set_xlabel('Longitude', fontsize=9)
        ax.set_ylabel('Latitude', fontsize=9)
        ax.tick_params(labelsize=8)
        
        # Add legend
        ax.legend(
            loc='upper right',
            fontsize=8,
            framealpha=0.9,
            edgecolor='gray'
        )
        
        # Add grid
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
        
        # Tight layout
        plt.tight_layout()
        
        # Save
        plt.savefig(output_path, format='png', dpi=150, bbox_inches='tight')
        plt.close()
        
        return output_path
        
    except Exception as e:
        print(f"[PDF] Error generating district map: {e}")
        import traceback
        traceback.print_exc()
        return None

# For district map generation (optional)
try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon
    from matplotlib.collections import PatchCollection
    import geopandas as gpd
    from pathlib import Path
    import numpy as np
    GEOPANDAS_AVAILABLE = True
except ImportError:
    GEOPANDAS_AVAILABLE = False
    print("[WARN] geopandas/matplotlib not available - district maps in PDFs will be disabled")


def generate_well_forecast_pdf(
    well_data: Dict,
    forecast_data: List[Dict],
    output_buffer: io.BytesIO,
    include_charts: bool = True
) -> io.BytesIO:
    """
    Generate CGWB-compliant PDF report for a single well forecast.
    
    Args:
        well_data: Dict with well metadata (well_id, lat, lon, district, etc.)
        forecast_data: List of forecast points (month_index, head_msl_m, lower_m, upper_m)
        output_buffer: BytesIO buffer to write PDF to
        include_charts: Whether to include forecast visualization
        
    Returns:
        BytesIO buffer with generated PDF
    """
    doc = SimpleDocTemplate(
        output_buffer,
        pagesize=A4,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=1*inch,
        bottomMargin=0.75*inch
    )
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=8,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    body_style = styles['BodyText']
    
    # Header
    header_text = "CENTRAL GROUND WATER BOARD"
    header = Paragraph(header_text, title_style)
    elements.append(header)
    
    subtitle = Paragraph("Groundwater Level Forecast Report", heading_style)
    elements.append(subtitle)
    
    # Report metadata
    report_date = datetime.now().strftime("%B %d, %Y")
    metadata = Paragraph(f"<b>Report Generated:</b> {report_date}", body_style)
    elements.append(metadata)
    elements.append(Spacer(1, 0.2*inch))
    
    # Well Information Section
    well_info_heading = Paragraph("Well Information", heading_style)
    elements.append(well_info_heading)
    
    well_info_data = [
        ['Well ID:', well_data.get('well_id', 'N/A')],
        ['District:', well_data.get('district', 'Unknown')],
        ['Block:', well_data.get('block', 'Unknown')],
        ['Coordinates:', f"{well_data.get('lat', 0):.4f}°N, {well_data.get('lon', 0):.4f}°E"],
        ['Geology Type:', well_data.get('geology_type', 'Unknown')],
        ['Aquifer Classification:', well_data.get('aquifer_classification', 'Unknown')],
        ['Current Trend:', well_data.get('trend_label', 'Unknown')],
    ]
    
    well_info_table = Table(well_info_data, colWidths=[2*inch, 4*inch])
    well_info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e0e7ff')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(well_info_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Forecast Section
    forecast_heading = Paragraph("12-Month Groundwater Level Forecast", heading_style)
    elements.append(forecast_heading)
    
    # Forecast table
    forecast_table_data = [['Month', 'Predicted Level (m MSL)', 'Lower Bound (m)', 'Upper Bound (m)']]
    
    for point in forecast_data:
        month_idx = point.get('month_index', 0)
        forecast_table_data.append([
            f"Month +{month_idx}",
            f"{point.get('head_msl_m', 0):.2f}",
            f"{point.get('lower_m', 0):.2f}",
            f"{point.get('upper_m', 0):.2f}"
        ])
    
    forecast_table = Table(forecast_table_data, colWidths=[1.5*inch, 2*inch, 1.5*inch, 1.5*inch])
    forecast_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f3f4f6')]),
    ]))
    elements.append(forecast_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Recommendations Section
    recommendations_heading = Paragraph("Recommendations", heading_style)
    elements.append(recommendations_heading)
    
    recommendation_text = well_data.get('recommendation', 'Monitor regularly.')
    rec_para = Paragraph(recommendation_text, body_style)
    elements.append(rec_para)
    elements.append(Spacer(1, 0.2*inch))
    
    # Model Information
    model_info_heading = Paragraph("Model Information", heading_style)
    elements.append(model_info_heading)
    
    model_info_text = f"""
    <b>Model Version:</b> {well_data.get('model_version', 'PGNN-LSTM v1.0')}<br/>
    <b>Confidence:</b> {well_data.get('confidence', 'High')}<br/>
    <b>Last Updated:</b> {report_date}<br/>
    """
    if well_data.get('caveat'):
        model_info_text += f"<br/><b>Note:</b> {well_data.get('caveat')}"
    
    model_info = Paragraph(model_info_text, body_style)
    elements.append(model_info)
    elements.append(Spacer(1, 0.3*inch))
    
    # Build PDF
    doc.build(elements)
    output_buffer.seek(0)
    return output_buffer


def generate_wells_forecast_csv(
    wells_data: List[Dict],
    forecasts_data: Dict[str, List[Dict]],
    output_buffer: io.StringIO
) -> io.StringIO:
    """
    Generate CSV export of multiple wells' forecasts.
    
    Args:
        wells_data: List of well metadata dicts
        forecasts_data: Dict mapping well_id to list of forecast points
        output_buffer: StringIO buffer to write CSV to
        
    Returns:
        StringIO buffer with generated CSV
    """
    rows = []
    
    # Header row
    rows.append([
        'Well ID', 'District', 'Block', 'Latitude', 'Longitude',
        'Geology Type', 'Aquifer Classification', 'Current Trend',
        'Month Index', 'Predicted Level (m MSL)', 'Lower Bound (m)', 'Upper Bound (m)',
        'Recommendation', 'Model Version', 'Report Date'
    ])
    
    report_date = datetime.now().strftime("%Y-%m-%d")
    
    for well in wells_data:
        well_id = well.get('well_id')
        forecast_points = forecasts_data.get(well_id, [])
        
        if not forecast_points:
            # Add well info even without forecast
            rows.append([
                well_id,
                well.get('district', 'Unknown'),
                well.get('block', 'Unknown'),
                f"{well.get('lat', 0):.6f}",
                f"{well.get('lon', 0):.6f}",
                well.get('geology_type', 'Unknown'),
                well.get('aquifer_classification', 'Unknown'),
                well.get('trend_label', 'Unknown'),
                '', '', '', '',
                well.get('recommendation', ''),
                well.get('model_version', 'PGNN-LSTM'),
                report_date
            ])
        else:
            for point in forecast_points:
                rows.append([
                    well_id,
                    well.get('district', 'Unknown'),
                    well.get('block', 'Unknown'),
                    f"{well.get('lat', 0):.6f}",
                    f"{well.get('lon', 0):.6f}",
                    well.get('geology_type', 'Unknown'),
                    well.get('aquifer_classification', 'Unknown'),
                    well.get('trend_label', 'Unknown'),
                    point.get('month_index', ''),
                    f"{point.get('head_msl_m', 0):.2f}",
                    f"{point.get('lower_m', 0):.2f}",
                    f"{point.get('upper_m', 0):.2f}",
                    well.get('recommendation', ''),
                    well.get('model_version', 'PGNN-LSTM'),
                    report_date
                ])
    
    # Write CSV
    writer = csv.writer(output_buffer)
    writer.writerows(rows)
    
    output_buffer.seek(0)
    return output_buffer


def generate_district_summary_pdf(
    district_name: str,
    wells_summary: List[Dict],
    statistics: Dict,
    output_buffer: io.BytesIO
) -> io.BytesIO:
    """
    Generate district-level summary report PDF.
    
    Args:
        district_name: Name of the district
        wells_summary: List of well summary dicts
        statistics: Dict with district statistics (total_wells, critical_count, etc.)
        output_buffer: BytesIO buffer to write PDF to
        
    Returns:
        BytesIO buffer with generated PDF
    """
    doc = SimpleDocTemplate(
        output_buffer,
        pagesize=A4,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=1*inch,
        bottomMargin=0.75*inch
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title = Paragraph(
        f"Groundwater Status Report<br/>{district_name} District",
        ParagraphStyle('Title', parent=styles['Heading1'], alignment=TA_CENTER, fontSize=16)
    )
    elements.append(title)
    elements.append(Spacer(1, 0.3*inch))
    
    # Summary statistics
    stats_data = [
        ['Total Monitoring Wells:', str(statistics.get('total_wells', 0))],
        ['Critical Wells:', f"{statistics.get('critical_count', 0)} ({statistics.get('critical_pct', 0):.1f}%)"],
        ['Watch Wells:', f"{statistics.get('watch_count', 0)} ({statistics.get('watch_pct', 0):.1f}%)"],
        ['Stable Wells:', f"{statistics.get('stable_count', 0)} ({statistics.get('stable_pct', 0):.1f}%)"],
    ]
    
    stats_table = Table(stats_data, colWidths=[3*inch, 2*inch])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e0e7ff')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
    ]))
    elements.append(stats_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # DISABLED: Map generation is slow (causes timeouts)
    # TODO: Re-enable after optimizing map rendering
    # import tempfile
    # with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
    #     map_path = tmp.name
    # 
    # map_image_path = generate_district_map_image(
    #     district_name=district_name,
    #     wells_data=wells_summary,
    #     output_path=map_path
    # )
    # 
    # if map_image_path:
    #     try:
    #         map_heading = Paragraph("District Map", styles['Heading2'])
    #         elements.append(map_heading)
    #         
    #         # Add the map image
    #         img = Image(map_image_path, width=5*inch, height=5*inch)
    #         elements.append(img)
    #         elements.append(Spacer(1, 0.2*inch))
    #         
    #         # Clean up temp file
    #         import os
    #         os.unlink(map_image_path)
    #     except Exception as e:
    #         print(f"[PDF] Could not add map image: {e}")
    
    # Wells summary table
    wells_heading = Paragraph("Wells Summary", styles['Heading2'])
    elements.append(wells_heading)
    
    wells_table_data = [['Well ID', 'Block', 'Trend', 'Geology', '12mo Change (m)']]
    
    # Show all wells (or up to 200 for very large districts)
    wells_to_show = wells_summary[:200]
    
    for well in wells_to_show:
        # Get the forecast change value
        # forecast_decline_m stores the decline amount (positive = decline, negative = rise)
        change_value = well.get('forecast_change', 0)
        
        # Show as negative for decline (fall), positive for rise
        # If forecast_decline_m is positive (decline), show as negative
        if change_value > 0:
            change_str = f"-{change_value:.2f}"
        elif change_value < 0:
            change_str = f"+{abs(change_value):.2f}"
        else:
            change_str = "0.00"
        
        wells_table_data.append([
            well.get('well_id', ''),
            well.get('block', ''),
            well.get('trend_label', ''),
            well.get('geology_type', ''),
            change_str
        ])
    
    wells_table = Table(wells_table_data, colWidths=[1.5*inch, 1.5*inch, 1*inch, 1.2*inch, 1.3*inch])
    wells_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f3f4f6')]),
    ]))
    elements.append(wells_table)
    
    if len(wells_summary) > 200:
        note = Paragraph(f"<i>Note: Showing first 200 of {len(wells_summary)} wells. Use CSV format for complete data.</i>", styles['Normal'])
        elements.append(note)
    
    doc.build(elements)
    output_buffer.seek(0)
    return output_buffer
