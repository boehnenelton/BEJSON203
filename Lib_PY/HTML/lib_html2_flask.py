"""
Library:      lib_html2_flask.py
Family:       HTML3
Jurisdiction: ["BEJSON_LIBRARIES", "PY"]
Status:       OFFICIAL
Author:       Elton Boehnen
Version:      2.0.1 OFFICIAL
            MFDB Version: 1.31
Format_Creator: Elton Boehnen
Date:         2026-05-18
Description:  Middleware for serving BEJSON content via Flask web servers.
"""

import os
import json
import uuid
from flask import request, render_template_string

# Core UI imports
from lib_bejson_html2_skeletons import COLOR, CSS_CORE, HTML_SKELETON
from lib_html2_page_templates import html_page
from lib_html2_tables import html_table
from lib_html2_body import html_stats_bar, html_card, html_card_grid, html_badge

class FlaskDashboard:
    """
    Streamlines Core-Command dashboard creation in Flask.
    Usage:
        dash = FlaskDashboard(app, "My System", nav_links=...)
        @app.route("/")
        def home():
            return dash.render("Home", "Welcome!", active_url="/")
    """
    def __init__(self, app=None, title="Control Center", nav_links=None, status_extra=""):
        self.app = app
        self.title = title
        self.nav_links = nav_links or []
        self.status_extra = status_extra
        
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Register filters and context processors."""
        @app.context_processor
        def ui_context():
            return {"css_core": CSS_CORE.format(**COLOR), "nav_links": self.nav_links}
            
        app.jinja_env.globals.update(
            html_stats_bar=html_stats_bar,
            html_card=html_card,
            html_badge=html_badge,
            html_table=html_table
        )

    def render(self, page_title, content, active_url="", status_extra=None):
        """Renders a full dashboard page."""
        return html_page(
            title=f"{page_title} - {self.title}",
            content=content,
            nav_links=self.nav_links,
            status_extra=status_extra or self.status_extra,
            active_url=active_url
        )

    @staticmethod
    def list_to_bejson(data_list, entity_name="Entity"):
        """Utility: Converts list[dict] (from MFDB) to BEJSON 104 dict."""
        if not data_list:
            return {"Format": "BEJSON", "Format_Version": "104", "Records_Type": [entity_name], "Fields": [], "Values": []}
        field_names = list(data_list[0].keys())
        fields = [{"name": fn, "type": "string"} for fn in field_names]
        values = [[d.get(fn) for fn in field_names] for d in data_list]
        return {"Format": "BEJSON", "Format_Version": "104", "Records_Type": [entity_name], "Fields": fields, "Values": values}

    def render_table(self, data_list, entity_name="Entity"):
        """Convenience: Renders MFDB data list as a searchable html2 table."""
        if not data_list: return '<div class="card">No records found.</div>'
        doc = self.list_to_bejson(data_list, entity_name)
        return html_table(doc)

def flask_toggle_button(action_url, sid, current_value, label=None):
    """Generates a standard activation/deactivation form/button."""
    is_on = str(current_value).lower() == 'true'
    btn_text = 'DEACTIVATE' if is_on else 'ACTIVATE'
    return f"""
    <form action="{action_url}" method="POST" style="display:inline;">
        <input type="hidden" name="sid" value="{sid}">
        <input type="hidden" name="current" value="{current_value}">
        <button type="submit" class="form__button">{label or btn_text}</button>
    </form>"""

def flask_quick_form(action_url, fields, submit_label="SUBMIT"):
    """
    Generate a simple light-theme form.
    :param fields: List of {"name": "...", "placeholder": "..."}
    """
    fields_html = ""
    for f in fields:
        fields_html += f'<input type="text" name="{f["name"]}" placeholder="{f["placeholder"]}" required style="padding:8px; margin:5px; border:1px solid #ddd; border-radius:4px;">\n'
    
    return f"""
    <div class="card">
        <form action="{action_url}" method="POST">
            {fields_html}
            <button type="submit" class="form__button">{submit_label}</button>
        </form>
    </div>"""
