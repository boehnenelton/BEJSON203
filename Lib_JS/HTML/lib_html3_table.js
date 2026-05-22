/**
 * Library:      lib_html3_table.js
 * Family:       HTML3
 * Jurisdiction: ["BEJSON_LIBRARIES", "JS"]
 * Status:       OFFICIAL
 * Author:       Elton Boehnen
 * Version:      1.2.0 OFFICIAL (Mobile-Optimized)
 * Date:         2026-05-21
 * Description:  Standardized table rendering engine for HTML3.
 *               Supports Multi-Column (Desktop) and Single-Column (Mobile) modes.
 *               Refactored for BEM, OKLCH, and Modular CSS Standards.
 */

'use strict';

(function() {
    const HTML3_Table = {
        render: function(doc, options = {}) {
            const {
                recordType = doc.Records_Type[0],
                showActions = true,
                showSysFields = false,
                pinnedFieldIdx = null,
                sortAsc = true,
                selectedRows = new Set(),
                mobileMode = false,
                activeFieldIdx = null, // Used in mobileMode to select which column to show
                onFieldChange = "app.setViewField" // JS callback for selector
            } = options;

            const rtpIdx = doc.Fields.findIndex(f => f.name === 'Record_Type_Parent');
            const fields = doc.Fields.map((f, i) => ({ ...f, orgIdx: i }));
            
            let activeFields = fields.filter(f => {
                const isSys = f.name === 'Record_Type_Parent';
                const matchType = !f.Record_Type_Parent || f.Record_Type_Parent === recordType;
                return matchType && (showSysFields || !isSys);
            });

            // Mobile-Specific Logic
            let renderFields = activeFields;
            if (mobileMode) {
                // In mobile mode, we only show ONE field at a time (plus meta cols)
                const targetIdx = (activeFieldIdx !== null) ? activeFieldIdx : (activeFields[0] ? activeFields[0].orgIdx : 0);
                renderFields = activeFields.filter(f => f.orgIdx === targetIdx);
            } else if (pinnedFieldIdx !== null) {
                const pin = activeFields.find(f => f.orgIdx === pinnedFieldIdx);
                if (pin) {
                    renderFields = activeFields.filter(f => f.orgIdx !== pinnedFieldIdx);
                    renderFields.unshift(pin);
                }
            }

            const records = doc.Values
                .map((v, i) => ({ val: v, orgIdx: i }))
                .filter(r => r.val[rtpIdx] === recordType);

            let html = `<div class="c-bejson-table ${mobileMode ? 'c-bejson-table--mobile' : ''}">`;
            html += `<div class="c-bejson-table__scroller">`;
            html += `<table class="c-bejson-table__table">`;
            
            // Header
            html += `<thead><tr>`;
            html += `<th class="c-bejson-table__th" style="width:60px; text-align:center;"><input type="checkbox" onchange="app.toggleSelectAll(this.checked)"></th>`;
            html += `<th class="c-bejson-table__th" style="width:50px; text-align:center;">#</th>`;
            
            if (mobileMode && activeFields.length > 0) {
                // Mobile Header: Field Selector
                const currentField = activeFields.find(f => f.orgIdx === activeFieldIdx) || activeFields[0];
                html += `<th class="c-bejson-table__th" style="width:100%;">
                    <div class="c-bejson-table__mobile-selector">
                        <select onchange="${onFieldChange}(parseInt(this.value))" class="c-input" style="height:32px; font-size:0.8rem; width:100%;">
                            ${activeFields.map(f => `<option value="${f.orgIdx}" ${f.orgIdx === currentField.orgIdx ? 'selected' : ''}>${this.esc(f.name)} (${f.type})</option>`).join('')}
                        </select>
                        <button class="c-bejson-table__btn" style="padding:0 8px;" onclick="app.sortData(${currentField.orgIdx}, !appState.sortAsc)">
                            ${sortAsc ? '▲' : '▼'}
                        </button>
                    </div>
                </th>`;
            } else {
                // Desktop Header: Standard Multi-Column
                activeFields.forEach(f => {
                    const isPinned = f.orgIdx === pinnedFieldIdx;
                    const pinCls = isPinned ? 'c-bejson-table__th--pinned' : '';
                    const sortIco = isPinned ? (sortAsc ? ' ▲' : ' ▼') : '';
                    
                    html += `<th class="c-bejson-table__th ${pinCls}">
                        <div class="c-bejson-table__header-wrap" 
                             onclick="app.selectField(${f.orgIdx})" 
                             oncontextmenu="app.headerContextMenu(event, ${f.orgIdx})">
                            <span class="c-bejson-table__field-name">${this.esc(f.name)}${sortIco}</span>
                            <span class="c-bejson-table__type">[${f.type}]</span>
                        </div>
                    </th>`;
                });
            }
            
            if (showActions && !mobileMode) html += `<th class="c-bejson-table__th">Actions</th>`;
            html += `</tr></thead>`;

            // Body
            html += `<tbody>`;
            if (records.length === 0) {
                html += `<tr><td colspan="${(mobileMode ? 1 : activeFields.length) + 3}" style="padding:60px; text-align:center; color:var(--text-muted);">No records found.</td></tr>`;
            } else {
                records.forEach((row, rIdx) => {
                    const isSelected = (typeof selectedRows.has === 'function') ? selectedRows.has(row.orgIdx) : false;
                    const rowCls = isSelected ? 'c-bejson-table__tr--selected' : '';
                    
                    html += `<tr class="c-bejson-table__tr ${rowCls}">`;
                    html += `<td class="c-bejson-table__td" style="text-align:center;"><input type="checkbox" class="rec-chk" data-idx="${row.orgIdx}" ${isSelected ? 'checked' : ''}></td>`;
                    html += `<td class="c-bejson-table__td c-bejson-table__td--num">${rIdx + 1}</td>`;
                    
                    renderFields.forEach(f => {
                        const val = row.val[f.orgIdx];
                        const pinnedCls = (!mobileMode && f.orgIdx === pinnedFieldIdx) ? 'c-bejson-table__td--pinned' : '';
                        
                        html += `<td class="c-bejson-table__td ${pinnedCls}">`;
                        html += this.renderCell(val, f, row.orgIdx, doc, options);
                        html += `</td>`;
                    });

                    if (showActions && !mobileMode) {
                        html += `<td class="c-bejson-table__td">
                            <button class="c-bejson-table__btn" onclick="app.cellExpandOpen(null, ${row.orgIdx}, ${activeFields[0].orgIdx}, '${activeFields[0].name.replace(/'/g, "\\'")}')">EDIT</button>
                        </td>`;
                    }
                    html += `</tr>`;
                });
            }
            html += `</tbody></table></div>`;
            
            // Footer
            html += `<div class="c-bejson-table__footer">
                <span class="u-text-muted">Total: ${records.length} records</span>
                ${mobileMode ? `<button class="c-btn c-btn--secondary" style="height:24px; padding:0 8px; font-size:0.7rem;" onclick="app.setMobileMode(false)">Desktop View</button>` : `<button class="c-btn c-btn--secondary" style="height:24px; padding:0 8px; font-size:0.7rem;" onclick="app.setMobileMode(true)">Mobile View</button>`}
                <span class="u-text-muted">DEP81</span>
            </div></div>`;

            return html;
        },

        renderCell: function(val, field, rowIdx, doc, options) {
            const isB64Idx = doc.Fields.findIndex(fff => fff.name === 'is_base64');
            const isB64 = isB64Idx !== -1 && doc.Values[rowIdx][isB64Idx] === true;
            
            if (val === null) return `<span class="c-bejson-table__null">null</span>`;
            
            if (field.type === 'boolean') {
                const statusCls = val ? 'c-bejson-table__status--true' : 'c-bejson-table__status--false';
                const label = val ? 'TRUE' : 'FALSE';
                return `<span class="c-bejson-table__status ${statusCls}" onclick="app.updateValue(${rowIdx}, ${field.orgIdx}, ${!val})">${label}</span>`;
            }
            
            if (isB64 && field.name === 'content') {
                const nameIdx = doc.Fields.findIndex(fff => fff.name === 'file_name');
                const fileName = nameIdx !== -1 ? doc.Values[rowIdx][nameIdx] : "binary_file";
                return `<div class="c-bejson-table__b64" onclick="BEJSON.Utility.downloadBase64('${val}', '${fileName}')" title="Binary data asset">📎 Download Binary</div>`;
            }

            if (typeof val === 'object' || Array.isArray(val)) {
                return `<code class="c-bejson-table__code">${this.esc(JSON.stringify(val))}</code>`;
            }

            const sv = this.esc(String(val));
            const fn = field.name.replace(/\\/g,'\\\\').replace(/'/g,"\\'");
            
            return `<input type="text" class="c-bejson-table__input" value="${sv}" 
                           onchange="app.updateValue(${rowIdx}, ${field.orgIdx}, this.value)"
                           ondblclick="app.cellExpandOpen(this, ${rowIdx}, ${field.orgIdx}, '${fn}')"
                           oncontextmenu="app.inputContextMenu(event, this, ${rowIdx}, ${field.orgIdx}, '${fn}')">`;
        },

        esc: function(s) {
            if (!s) return "";
            return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
        }
    };

    if (typeof module !== 'undefined' && module.exports) {
        module.exports = HTML3_Table;
    }
    if (typeof window !== 'undefined') {
        window.HTML3 = window.HTML3 || {};
        window.HTML3.Table = HTML3_Table;
    }
})();
