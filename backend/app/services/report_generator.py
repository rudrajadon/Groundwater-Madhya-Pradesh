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
    
    # Footer disclaimer
    disclaimer = Paragraph(
        "<i>This report is generated using PGNN-LSTM machine learning model trained on historical "
        "groundwater monitoring data. Forecasts are subject to uncertainty and should be used "
        "in conjunction with field observations and expert judgment.</i>",
        ParagraphStyle('Disclaimer', parent=body_style, fontSize=8, textColor=colors.grey)
    )
    elements.append(disclaimer)
    
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
        ['Avg Projected Decline (12mo):', f"{statistics.get('avg_decline_m', 0):.2f} m"],
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
    
    # Wells summary table
    wells_heading = Paragraph("Wells Summary", styles['Heading2'])
    elements.append(wells_heading)
    
    wells_table_data = [['Well ID', 'Block', 'Trend', 'Geology', '12mo Change (m)']]
    
    # Show all wells (or up to 200 for very large districts)
    wells_to_show = wells_summary[:200]
    
    for well in wells_to_show:
        wells_table_data.append([
            well.get('well_id', ''),
            well.get('block', ''),
            well.get('trend_label', ''),
            well.get('geology_type', ''),
            f"{well.get('forecast_change', 0):.2f}"
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
