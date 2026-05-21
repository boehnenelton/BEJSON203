"""
Library:      lib_html2_charts.py
Family:       HTML3
Jurisdiction: ["BEJSON_LIBRARIES", "PY"]
Status:       OFFICIAL
Author:       Elton Boehnen
Version:      2.0.1 OFFICIAL
            MFDB Version: 1.31
Format_Creator: Elton Boehnen
Date:         2026-05-18
Description:  Data visualization engine for generating interactive charts.
"""

import json
import uuid

def html_chart(chart_type="bar", title="", labels=None, data=None, color="#DE2626", height="300px"):
    """
    Generates a responsive Chart.js canvas with inline script initialization.
    chart_type: 'bar', 'line', 'doughnut', 'pie'
    labels: list of strings (x-axis)
    data: list of numbers (y-axis)
    """
    if labels is None: labels = []
    if data is None: data = []
    
    chart_id = f"chart_{uuid.uuid4().hex[:8]}"
    
    labels_js = json.dumps(labels)
    data_js = json.dumps(data)
    
    html = f"""
    <div class="chart-container" style="position: relative; height:{height}; width:100%; margin-bottom: 20px; background: var(--bg-surface, #F8F8F8); border: 1px solid var(--border, #E1E1E1); padding: 15px; border-left: 4px solid {color};">
        {f'<h4 style="margin-top:0; font-family: var(--font-mono, monospace); font-size:14px; margin-bottom:15px; color: var(--text-main, #111); text-transform: uppercase;">{title}</h4>' if title else ''}
        <canvas id="{chart_id}"></canvas>
    </div>
    
    <script>
    (function() {{
        function initChart() {{
            const ctx = document.getElementById('{chart_id}').getContext('2d');
            new Chart(ctx, {{
                type: '{chart_type}',
                data: {{
                    labels: {labels_js},
                    datasets: [{{
                        label: '{title}',
                        data: {data_js},
                        backgroundColor: '{color}40', /* 25% opacity for fill */
                        borderColor: '{color}',
                        borderWidth: 2,
                        tension: 0.3,
                        fill: { 'true' if chart_type == 'line' else 'false' }
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{ display: { 'true' if chart_type in ('pie', 'doughnut') else 'false' } }}
                    }},
                    scales: {{
                        y: {{ beginAtZero: true, display: { 'false' if chart_type in ('pie', 'doughnut') else 'true' } }},
                        x: {{ display: { 'false' if chart_type in ('pie', 'doughnut') else 'true' } }}
                    }}
                }}
            }});
        }}

        // Dynamic Chart.js CDN injection if not present
        if (typeof Chart === 'undefined') {{
            if (!window.chartJsLoading) {{
                window.chartJsLoading = true;
                const script = document.createElement('script');
                script.src = 'https://cdn.jsdelivr.net/npm/chart.js';
                script.onload = initChart;
                document.head.appendChild(script);
            }} else {{
                const checkInterval = setInterval(() => {{
                    if (typeof Chart !== 'undefined') {{
                        clearInterval(checkInterval);
                        initChart();
                    }}
                }}, 100);
            }}
        }} else {{
            initChart();
        }}
    }})();
    </script>
    """
    return html

def html_sparkline(data=None, color="#DE2626", height="50px"):
    """
    Creates a tiny, minimalist line chart intended for embedding within stat cards.
    data: list of numbers
    """
    if data is None: data = []
    
    chart_id = f"spark_{uuid.uuid4().hex[:8]}"
    labels_js = json.dumps([""] * len(data))
    data_js = json.dumps(data)
    
    html = f"""
    <div style="height:{height}; width:100%; margin-top: 10px;">
        <canvas id="{chart_id}"></canvas>
    </div>
    <script>
    (function() {{
        function initSpark() {{
            const ctx = document.getElementById('{chart_id}').getContext('2d');
            new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: {labels_js},
                    datasets: [{{
                        data: {data_js},
                        borderColor: '{color}',
                        borderWidth: 2,
                        pointRadius: 0,
                        tension: 0.4,
                        fill: true,
                        backgroundColor: '{color}20'
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{ legend: {{ display: false }}, tooltip: {{ enabled: false }} }},
                    scales: {{ x: {{ display: false }}, y: {{ display: false }} }},
                    layout: {{ padding: 0 }}
                }}
            }});
        }}
        
        if (typeof Chart === 'undefined') {{
            if (!window.chartJsLoading) {{
                window.chartJsLoading = true;
                const script = document.createElement('script');
                script.src = 'https://cdn.jsdelivr.net/npm/chart.js';
                script.onload = initSpark;
                document.head.appendChild(script);
            }} else {{
                const checkInterval = setInterval(() => {{
                    if (typeof Chart !== 'undefined') {{ clearInterval(checkInterval); initSpark(); }}
                }}, 100);
            }}
        }} else {{ initSpark(); }}
    }})();
    </script>
    """
    return html
