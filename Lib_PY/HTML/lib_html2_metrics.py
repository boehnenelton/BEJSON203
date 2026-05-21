"""
Library:      lib_html2_metrics.py
Family:       HTML3
Jurisdiction: ["BEJSON_LIBRARIES", "PY"]
Status:       OFFICIAL
Author:       Elton Boehnen
Version:      2.0.1 OFFICIAL
            MFDB Version: 1.31
Format_Creator: Elton Boehnen
Date:         2026-05-18
Description:  System and application performance metrics tracker.
"""

import math

def calculate_trend(current, previous):
    """Calculates the percentage trend between two numbers."""
    if previous == 0:
        return 100.0 if current > 0 else 0.0
    return ((current - previous) / previous) * 100.0

def html_metric_card(title, value, previous_value=None, prefix="", suffix="", inverse_colors=False, color="var(--primary-red, #DE2626)"):
    """
    Generates a statistical metric card with an optional trend indicator.
    inverse_colors: if True, a positive trend is red and negative is green (e.g., for error rates).
    """
    trend_html = ""
    if previous_value is not None:
        trend = calculate_trend(value, previous_value)
        is_positive = trend > 0
        is_neutral = trend == 0
        
        if is_neutral:
            trend_color = "var(--text-muted, #555555)"
            arrow = "⬌"
        else:
            if inverse_colors:
                trend_color = "var(--primary-red, #DE2626)" if is_positive else "#2E7D32" # Green
            else:
                trend_color = "#2E7D32" if is_positive else "var(--primary-red, #DE2626)"
            arrow = "▲" if is_positive else "▼"
            
        trend_html = f"""
        <div style="font-family: var(--font-mono, monospace); font-size: 12px; color: {trend_color}; margin-top: 8px; font-weight: bold;">
            {arrow} {abs(trend):.1f}% <span style="color: var(--text-muted, #555555); font-weight: normal; font-size: 11px;">vs previous</span>
        </div>
        """

    html = f"""
    <div class="metric-card" style="background: var(--bg-surface, #F8F8F8); border: 1px solid var(--border, #E1E1E1); padding: 20px; border-top: 3px solid {color}; transition: var(--transition-speed, 0.15s) ease;">
        <div style="font-family: var(--font-mono, monospace); font-size: 11px; color: var(--text-muted, #555555); text-transform: uppercase; margin-bottom: 5px;">{title}</div>
        <div style="font-size: 28px; font-weight: 700; color: var(--text-main, #111111);">{prefix}{value}{suffix}</div>
        {trend_html}
    </div>
    """
    return html

def html_data_distribution(title, data_dict, color="var(--primary-red, #DE2626)"):
    """
    Generates a horizontal stacked distribution bar (e.g., Firebase Quota usage).
    data_dict: dict of { "label": value }
    """
    total = sum(data_dict.values())
    if total == 0: total = 1
    
    bars_html = ""
    legend_html = ""
    
    # Alternate opacities for the theme color to distinguish segments
    opacities = [1.0, 0.7, 0.4, 0.2, 0.1]
    
    for i, (label, val) in enumerate(data_dict.items()):
        percentage = (val / total) * 100
        opacity = opacities[i % len(opacities)]
        
        bg_style = f"background: {color}; opacity: {opacity};"
        
        bars_html += f'<div style="height: 100%; width: {percentage}%; {bg_style} float: left;" title="{label}: {val} ({percentage:.1f}%)"></div>'
        
        legend_html += f"""
        <div style="display: flex; align-items: center; gap: 5px; font-family: var(--font-mono, monospace); font-size: 11px; color: var(--text-main, #111111);">
            <div style="width: 10px; height: 10px; {bg_style}"></div>
            <span>{label}: <b>{val}</b> ({percentage:.1f}%)</span>
        </div>
        """

    html = f"""
    <div class="data-distribution" style="margin-bottom: 20px; background: var(--bg-surface, #F8F8F8); border: 1px solid var(--border, #E1E1E1); padding: 15px;">
        <div style="font-family: var(--font-mono, monospace); font-size: 12px; color: var(--text-muted, #555555); text-transform: uppercase; margin-bottom: 10px; font-weight: bold;">{title}</div>
        <div style="width: 100%; height: 12px; background: var(--border, #EAEAEA); overflow: hidden; margin-bottom: 15px;">
            {bars_html}
        </div>
        <div style="display: flex; flex-wrap: wrap; gap: 15px;">
            {legend_html}
        </div>
    </div>
    """
    return html

def html_summary_statistics(title, data_list, prefix="", suffix="", color="var(--primary-red, #DE2626)"):
    """
    Calculates and displays mean, median, min, and max for a dataset.
    """
    if not data_list:
        return f"<div style='padding: 15px; border: 1px solid var(--border);'>No data for {title}</div>"
        
    sorted_data = sorted(data_list)
    n = len(sorted_data)
    
    val_min = sorted_data[0]
    val_max = sorted_data[-1]
    mean = sum(sorted_data) / n
    
    if n % 2 == 0:
        median = (sorted_data[n//2 - 1] + sorted_data[n//2]) / 2
    else:
        median = sorted_data[n//2]
        
    stats = [
        ("Count", f"{n}"),
        ("Mean", f"{prefix}{mean:.2f}{suffix}"),
        ("Median", f"{prefix}{median:.2f}{suffix}"),
        ("Min", f"{prefix}{val_min}{suffix}"),
        ("Max", f"{prefix}{val_max}{suffix}")
    ]
    
    stats_html = ""
    for label, val in stats:
        stats_html += f"""
        <div style="flex: 1; min-width: 80px; text-align: center; border-right: 1px solid var(--border, #E1E1E1); padding: 10px;">
            <div style="font-family: var(--font-mono, monospace); font-size: 10px; color: var(--text-muted, #555555); text-transform: uppercase;">{label}</div>
            <div style="font-size: 16px; font-weight: bold; color: {color}; margin-top: 5px;">{val}</div>
        </div>
        """
        
    html = f"""
    <div class="summary-stats" style="margin-bottom: 20px; background: var(--bg-surface, #F8F8F8); border: 1px solid var(--border, #E1E1E1); display: flex; flex-direction: column;">
        <div style="padding: 10px 15px; border-bottom: 1px solid var(--border, #E1E1E1); font-family: var(--font-mono, monospace); font-size: 12px; font-weight: bold; color: var(--text-main, #111111); text-transform: uppercase;">
            {title}
        </div>
        <div style="display: flex; flex-wrap: wrap; background: var(--bg-dark, #FFFFFF);">
            {stats_html}
        </div>
    </div>
    """
    return html
