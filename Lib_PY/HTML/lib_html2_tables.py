"""
Library:      lib_html2_tables.py
Family:       HTML3
Jurisdiction: ["BEJSON_LIBRARIES", "PY"]
Status:       OFFICIAL
Author:       Elton Boehnen
Version:      2.0.1 OFFICIAL
            MFDB Version: 1.31
Format_Creator: Elton Boehnen
Date:         2026-05-18
Description:  Tabular data visualization engine for HTML components.
"""

import json
import time

COMPONENT_TEMPLATE = """
<div id="{cid}" class="bejson-comp">
    <style>
        #{cid} .bejson-comp__controls {{ display: flex; align-items: center; gap: 16px; margin-bottom: 16px; flex-wrap: wrap; }}
        #{cid} .bejson-comp__label {{ font-family: var(--font-mono); font-size: 11px; font-weight: bold; color: var(--primary-red); text-transform: uppercase; }}
        #{cid} .bejson-comp__select {{ 
            font-family: var(--font-base); font-size: 13px; padding: 4px 8px; 
            background-color: #fff; color: #000; border: none; outline: none; 
            transition: var(--transition-speed); 
        }}
        #{cid} .bejson-comp__select:focus {{ background-color: var(--primary-red); color: #fff; }}
        #{cid} .bejson-comp__count {{ margin-left: auto; font-family: var(--font-mono); color: var(--primary-red); font-size: 11px; }}
        
        /* Indicators */
        .indicator {{ font-weight: bold; text-transform: uppercase; }}
        .indicator--success {{ color: #00FF00; }}
        .indicator--fail {{ color: #FF0000; }}
        .null-val {{ color: var(--text-muted); font-style: italic; }}
    </style>
    
    <div class="bejson-comp__controls">
        <label for="{cid}_select" class="bejson-comp__label">TYPE:</label>
        <select id="{cid}_select" class="bejson-comp__select"></select>
        <span id="{cid}_count" class="bejson-comp__count">RECORDS: 0</span>
    </div>

    <div class="table-container">
        <table id="{cid}_table" class="data-table" role="table">
            <thead id="{cid}_thead"></thead>
            <tbody id="{cid}_tbody"></tbody>
        </table>
    </div>

    <script>
    (function() {{
        const bejson = {bejson_data};
        const cid = "{cid}";
        let currentSort = {{ column: null, direction: 'asc' }};
        
        const selectEl = document.getElementById(cid + '_select');
        const theadEl = document.getElementById(cid + '_thead');
        const tbodyEl = document.getElementById(cid + '_tbody');
        const countEl = document.getElementById(cid + '_count');

        function renderTable() {{
            const selectedType = selectEl.value;
            let filteredFields = (bejson.Format_Version === '104db') ? 
                bejson.Fields.filter((f, i) => i === 0 || f.Record_Type_Parent === selectedType) : 
                bejson.Fields;
            let filteredRecords = (bejson.Format_Version === '104db') ? 
                bejson.Values.filter(r => r[0] === selectedType) : 
                bejson.Values;

            if (currentSort.column) {{
                const fieldIdx = bejson.Fields.findIndex(f => f.name === currentSort.column);
                filteredRecords.sort((a, b) => {{
                    let valA = a[fieldIdx], valB = b[fieldIdx];
                    if (valA === null) return 1; if (valB === null) return -1;
                    if (typeof valA === 'string') valA = valA.toLowerCase(); 
                    if (typeof valB === 'string') valB = valB.toLowerCase();
                    if (valA < valB) return currentSort.direction === 'asc' ? -1 : 1;
                    if (valA > valB) return currentSort.direction === 'asc' ? 1 : -1;
                    return 0;
                }});
            }}

            countEl.textContent = `RECORDS: ${{filteredRecords.length}}`;

            // Render Head
            let headHtml = '<tr>';
            filteredFields.forEach(field => {{
                let sortIndicator = (currentSort.column === field.name) ? (currentSort.direction === 'asc' ? ' ▲' : ' ▼') : ' ↕';
                headHtml += `<th onclick="window['sort_${{cid}}']('${{field.name}}')">${{field.name}}${{sortIndicator}}</th>`;
            }});
            theadEl.innerHTML = headHtml + '</tr>';

            // Render Body
            let bodyHtml = '';
            filteredRecords.forEach(record => {{
                bodyHtml += '<tr>';
                filteredFields.forEach(field => {{
                    const originalIdx = bejson.Fields.findIndex(f => f.name === field.name);
                    const val = record[originalIdx];
                    let displayVal = val, cellStyle = '';
                    
                    if (val === null) {{ displayVal = '<span class="null-val">null</span>'; }}
                    else if (typeof val === 'boolean') {{ 
                        displayVal = val ? 'TRUE' : 'FALSE'; 
                        cellStyle = 'color:' + (val ? '#00FF00' : '#FF0000') + ';font-weight:bold;';
                    }}
                    else if (typeof val === 'object') {{ displayVal = '<span style="font-family:var(--font-mono);font-size:11px;">' + JSON.stringify(val) + '</span>'; }}
                    else if (val === 'SUCCESS') cellStyle = 'color:#00FF00;font-weight:bold;';
                    else if (val === 'FAIL') cellStyle = 'color:#FF0000;font-weight:bold;';
                    
                    bodyHtml += `<td style="${{cellStyle}}">${{displayVal}}</td>`;
                }});
                bodyHtml += '</tr>';
            }});
            tbodyEl.innerHTML = bodyHtml;
        }}

        window['sort_${{cid}}'] = (field) => {{
            if (currentSort.column === field) currentSort.direction = (currentSort.direction === 'asc' ? 'desc' : 'asc');
            else {{ currentSort.column = field; currentSort.direction = 'asc'; }}
            renderTable();
        }};

        if (bejson.Records_Type) {{
            bejson.Records_Type.forEach(type => {{
                const option = document.createElement('option'); 
                option.value = type; option.textContent = type.toUpperCase(); 
                selectEl.appendChild(option);
            }});
        }} else {{
            const option = document.createElement('option'); option.value = "default"; option.textContent = "RECORDS"; selectEl.appendChild(option);
        }}
        selectEl.onchange = renderTable; 
        renderTable();
    }})();
    </script>
</div>
"""

def html_table(doc: dict, container_id: str = None) -> str:
    """Generate an isolated HTML table component."""
    if not container_id:
        container_id = f"bejson_comp_{int(time.time() * 1000)}"
    return COMPONENT_TEMPLATE.format(cid=container_id, bejson_data=json.dumps(doc))
