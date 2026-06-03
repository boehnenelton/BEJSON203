/**
 * Library:      lib_html3_table.js
 * Family:       HTML3
 * Jurisdiction: ["BEJSON_LIBRARIES", "JS"]
 * Status:       OFFICIAL
 * Author:       Elton Boehnen
 * Version:      2.0.1 OFFICIAL (Event Delegation)
 * Date:         2026-06-02
 * Description:  Standardized table rendering engine for HTML3.
 *               Supports Multi-Column (Desktop) and Single-Column (Mobile) modes.
 *               Refactored for BEM, OKLCH, and Modular CSS Standards.
 * 
 * REMEDIATED:   Phase 4 Safe Event Delegation (XSS Protection).
 */

'use strict';

(function() {
    const HTML3_Table = {
        render: function(doc, options) {
            options = options || {};
            var recordType    = options.recordType    !== undefined ? options.recordType    : doc.Records_Type[0];
            var showActions   = options.showActions   !== undefined ? options.showActions   : true;
            var showSysFields = options.showSysFields !== undefined ? options.showSysFields : false;
            var pinnedFieldIdx = options.pinnedFieldIdx !== undefined ? options.pinnedFieldIdx : null;
            var sortAsc       = options.sortAsc       !== undefined ? options.sortAsc       : true;
            var selectedRows  = options.selectedRows  instanceof Set ? options.selectedRows : new Set();
            var mobileMode    = options.mobileMode    !== undefined ? options.mobileMode    : false;
            var activeFieldIdx = options.activeFieldIdx !== undefined ? options.activeFieldIdx : null;

            // FIX H6: validate onFieldChange as a safe dotted-identifier path.
            var rawCallback   = (options.onFieldChange !== undefined) ? options.onFieldChange : 'app.setViewField';
            var onFieldChange = /^[a-zA-Z_$][\w$]*(?:\.[a-zA-Z_$][\w$]*)*$/.test(rawCallback)
                ? rawCallback
                : 'app.setViewField';

            // FIX H1: resolve field indices via the cache once per render() call
            var fieldMap = (window.BEJSON && window.BEJSON.bejson_core_get_field_map)
                ? window.BEJSON.bejson_core_get_field_map(doc)
                : null;

            var _getIdx = function(name) {
                if (fieldMap && fieldMap[name] !== undefined) return fieldMap[name];
                return doc.Fields.findIndex(function(f) { return f.name === name; });
            };

            var rtpIdx = _getIdx('Record_Type_Parent');

            var fields = doc.Fields.map(function(f, i) { return Object.assign({}, f, { orgIdx: i }); });

            var activeFields = fields.filter(function(f) {
                var isSys     = f.name === 'Record_Type_Parent';
                var matchType = !f.Record_Type_Parent || f.Record_Type_Parent === recordType;
                return matchType && (showSysFields || !isSys);
            });

            var renderFields = activeFields;
            if (mobileMode) {
                var targetIdx = (activeFieldIdx !== null) ? activeFieldIdx : (activeFields[0] ? activeFields[0].orgIdx : 0);
                renderFields = activeFields.filter(function(f) { return f.orgIdx === targetIdx; });
            } else if (pinnedFieldIdx !== null) {
                var pin = activeFields.find(function(f) { return f.orgIdx === pinnedFieldIdx; });
                if (pin) {
                    renderFields = activeFields.filter(function(f) { return f.orgIdx !== pinnedFieldIdx; });
                    renderFields.unshift(pin);
                }
            }

            var records = doc.Values
                .map(function(v, i) { return { val: v, orgIdx: i }; })
                .filter(function(r) { return r.val[rtpIdx] === recordType; });

            var html = '<div class="c-bejson-table ' + (mobileMode ? 'c-bejson-table--mobile' : '') + '" data-bejson-table>';
            html += '<div class="c-bejson-table__scroller">';
            html += '<table class="c-bejson-table__table">';

            // Header
            html += '<thead><tr>';
            html += '<th class="c-bejson-table__th" style="width:60px; text-align:center;"><input type="checkbox" data-action="toggle-select-all"></th>';
            html += '<th class="c-bejson-table__th" style="width:50px; text-align:center;">#</th>';

            if (mobileMode && activeFields.length > 0) {
                var currentField = activeFields.find(function(f) { return f.orgIdx === activeFieldIdx; }) || activeFields[0];
                html += '<th class="c-bejson-table__th" style="width:100%;">';
                html += '<div class="c-bejson-table__mobile-selector">';
                html += '<select data-action="view-field-change" class="c-input" style="height:32px; font-size:0.8rem; width:100%;" data-callback="' + onFieldChange + '">';
                activeFields.forEach(function(f) {
                    html += '<option value="' + f.orgIdx + '"' + (f.orgIdx === currentField.orgIdx ? ' selected' : '') + '>' + HTML3_Table.esc(f.name) + ' (' + f.type + ')</option>';
                });
                html += '</select>';
                html += '<button class="c-bejson-table__btn" style="padding:0 8px;" data-action="sort" data-idx="' + currentField.orgIdx + '" data-asc="' + (!sortAsc) + '">' + (sortAsc ? '▲' : '▼') + '</button>';
                html += '</div></th>';
            } else {
                activeFields.forEach(function(f) {
                    var isPinned = f.orgIdx === pinnedFieldIdx;
                    var pinCls   = isPinned ? 'c-bejson-table__th--pinned' : '';
                    var sortIco  = isPinned ? (sortAsc ? ' ▲' : ' ▼') : '';
                    html += '<th class="c-bejson-table__th ' + pinCls + '">';
                    html += '<div class="c-bejson-table__header-wrap" data-action="select-field" data-idx="' + f.orgIdx + '" data-context-action="header-menu">';
                    html += '<span class="c-bejson-table__field-name">' + HTML3_Table.esc(f.name) + sortIco + '</span>';
                    html += '<span class="c-bejson-table__type">[' + f.type + ']</span>';
                    html += '</div></th>';
                });
            }

            if (showActions && !mobileMode) html += '<th class="c-bejson-table__th">Actions</th>';
            html += '</tr></thead>';

            // Body
            html += '<tbody>';
            if (records.length === 0) {
                html += '<tr><td colspan="' + ((mobileMode ? 1 : activeFields.length) + 3) + '" style="padding:60px; text-align:center; color:var(--text-muted);">No records found.</td></tr>';
            } else {
                var isB64Idx = _getIdx('is_base64');
                var nameIdx  = _getIdx('file_name');

                records.forEach(function(row, rIdx) {
                    var isSelected = selectedRows.has(row.orgIdx);
                    var rowCls = isSelected ? 'c-bejson-table__tr--selected' : '';

                    html += '<tr class="c-bejson-table__tr ' + rowCls + '">';
                    html += '<td class="c-bejson-table__td" style="text-align:center;"><input type="checkbox" class="rec-chk" data-idx="' + row.orgIdx + '"' + (isSelected ? ' checked' : '') + '></td>';
                    html += '<td class="c-bejson-table__td c-bejson-table__td--num">' + (rIdx + 1) + '</td>';

                    renderFields.forEach(function(f) {
                        var val = row.val[f.orgIdx];
                        var pinnedCls = (!mobileMode && f.orgIdx === pinnedFieldIdx) ? 'c-bejson-table__td--pinned' : '';
                        html += '<td class="c-bejson-table__td ' + pinnedCls + '">';
                        html += HTML3_Table.renderCell(val, f, row.orgIdx, doc, options, isB64Idx, nameIdx);
                        html += '</td>';
                    });

                    if (showActions && !mobileMode && activeFields.length > 0) {
                        var firstField = activeFields[0];
                        html += '<td class="c-bejson-table__td">';
                        html += '<button class="c-bejson-table__btn" data-action="edit-row" data-rowidx="' + row.orgIdx + '" data-fieldidx="' + firstField.orgIdx + '" data-field="' + HTML3_Table.esc(firstField.name) + '">EDIT</button>';
                        html += '</td>';
                    }
                    html += '</tr>';
                });
            }
            html += '</tbody></table></div>';

            html += '<div class="c-bejson-table__footer">';
            html += '<span class="u-text-muted">Total: ' + records.length + ' records</span>';
            if (mobileMode) {
                html += '<button class="c-btn c-btn--secondary" style="height:24px; padding:0 8px; font-size:0.7rem;" data-action="set-mobile" data-value="false">Desktop View</button>';
            } else {
                html += '<button class="c-btn c-btn--secondary" style="height:24px; padding:0 8px; font-size:0.7rem;" data-action="set-mobile" data-value="true">Mobile View</button>';
            }
            html += '<span class="u-text-muted">DEP81</span>';
            html += '</div></div>';

            return html;
        },

        renderCell: function(val, field, rowIdx, doc, options, isB64Idx, nameIdx) {
            if (isB64Idx === undefined) isB64Idx = doc.Fields.findIndex(function(f) { return f.name === 'is_base64'; });
            if (nameIdx  === undefined) nameIdx  = doc.Fields.findIndex(function(f) { return f.name === 'file_name'; });

            var isB64 = isB64Idx !== -1 && doc.Values[rowIdx][isB64Idx] === true;

            if (val === null) return '<span class="c-bejson-table__null">null</span>';

            if (field.type === 'boolean') {
                var statusCls = val ? 'c-bejson-table__status--true' : 'c-bejson-table__status--false';
                var label = val ? 'TRUE' : 'FALSE';
                return '<span class="c-bejson-table__status ' + statusCls + '" data-action="update-bool" data-rowidx="' + rowIdx + '" data-fieldidx="' + field.orgIdx + '" data-value="' + val + '">' + label + '</span>';
            }

            if (isB64 && field.name === 'content') {
                var fileName = nameIdx !== -1 ? doc.Values[rowIdx][nameIdx] : 'binary_file';
                return '<div class="c-bejson-table__b64" data-action="download-b64" data-val="' + val + '" data-filename="' + this.esc(String(fileName)) + '" title="Binary data asset">📎 Download Binary</div>';
            }

            if (typeof val === 'object' || Array.isArray(val)) {
                return '<code class="c-bejson-table__code">' + this.esc(JSON.stringify(val)) + '</code>';
            }

            var sv = this.esc(String(val));

            return '<input type="text" class="c-bejson-table__input" value="' + sv + '"'
                + ' data-rowidx="' + rowIdx + '" data-fieldidx="' + field.orgIdx + '" data-field="' + this.esc(field.name) + '"'
                + ' data-action="update-value"'
                + '>';
        },

        bindEvents: function(container, appRef) {
            const app = appRef || window.app;
            if (!app) return;

            container.addEventListener('click', function(e) {
                var target = e.target.closest('[data-action]');
                if (!target) return;

                var action = target.dataset.action;
                var idx = target.dataset.idx | 0;
                var rowIdx = target.dataset.rowidx | 0;
                var fieldIdx = target.dataset.fieldidx | 0;

                switch(action) {
                    case 'select-field':
                        if (app.selectField) app.selectField(idx);
                        break;
                    case 'sort':
                        if (app.sortData) app.sortData(idx, target.dataset.asc === 'true');
                        break;
                    case 'edit-row':
                        if (app.cellExpandOpen) app.cellExpandOpen(null, rowIdx, fieldIdx, target.dataset.field);
                        break;
                    case 'set-mobile':
                        if (app.setMobileMode) app.setMobileMode(target.dataset.value === 'true');
                        break;
                    case 'update-bool':
                        if (app.updateValue) app.updateValue(rowIdx, fieldIdx, target.dataset.value !== 'true');
                        break;
                    case 'download-b64':
                        if (window.BEJSON && window.BEJSON.Utility && window.BEJSON.Utility.downloadBase64) {
                            window.BEJSON.Utility.downloadBase64(target.dataset.val, target.dataset.filename);
                        }
                        break;
                }
            });

            container.addEventListener('change', function(e) {
                var target = e.target;
                var action = target.dataset.action;
                if (!action) return;

                switch(action) {
                    case 'toggle-select-all':
                        if (app.toggleSelectAll) app.toggleSelectAll(target.checked);
                        break;
                    case 'view-field-change':
                        var callback = target.dataset.callback || 'app.setViewField';
                        var parts = callback.split('.');
                        var func = window;
                        for(var i=0; i<parts.length; i++) func = func ? func[parts[i]] : null;
                        if (typeof func === 'function') func(parseInt(target.value));
                        break;
                    case 'update-value':
                        var rowIdx = target.dataset.rowidx | 0;
                        var fieldIdx = target.dataset.fieldidx | 0;
                        if (app.updateValue) app.updateValue(rowIdx, fieldIdx, target.value);
                        break;
                }
            });

            container.addEventListener('dblclick', function(e) {
                var target = e.target.closest('[data-field]');
                if (!target) return;
                var rowIdx = target.dataset.rowidx | 0;
                var fieldIdx = target.dataset.fieldidx | 0;
                if (app.cellExpandOpen) app.cellExpandOpen(target, rowIdx, fieldIdx, target.dataset.field);
            });

            container.addEventListener('contextmenu', function(e) {
                var target = e.target.closest('[data-context-action] , [data-field]');
                if (!target) return;
                e.preventDefault();
                var action = target.dataset.contextAction || 'input-menu';
                var rowIdx = target.dataset.rowidx | 0;
                var fieldIdx = target.dataset.fieldidx | 0;
                var idx = target.dataset.idx | 0;

                if (action === 'header-menu' && app.headerContextMenu) {
                    app.headerContextMenu(e, idx);
                } else if (app.inputContextMenu) {
                    app.inputContextMenu(e, target, rowIdx, fieldIdx, target.dataset.field);
                }
            });
        },

        esc: function(s) {
            if (!s) return '';
            return String(s)
                .replace(/&/g,  '&amp;')
                .replace(/</g,  '&lt;')
                .replace(/>/g,  '&gt;')
                .replace(/"/g,  '&quot;')
                .replace(/'/g,  '&#039;');
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
