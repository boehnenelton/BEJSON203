"""
Library:      lib_bejson_html3_component_css.py
Family:       HTML3
Jurisdiction: ["BEJSON_LIBRARIES", "PY"]
Status:       OFFICIAL
Author:       Elton Boehnen
Version:      3.0.1 OFFICIAL
            MFDB Version: 1.31
Format_Creator: Elton Boehnen
Date:         2026-05-29
Description:  Central registry for BECSS component styles.
              Organized into the @layer components layer.
"""

VERSION = "3.0.1"
SCRIPT_NAME = "lib_bejson_html3_component_css.py"
RELATIONAL_ID = "c7d6b5a4-1f8a-4e8a-9d6c-5f4b5a6c7d8f"

COMPONENT_CSS = """
@layer components {
    /* Stats Bar */
    .c-stats-bar {
        display: flex; gap: 24px; padding: 24px;
        background: var(--bg-surface); margin-bottom: 24px;
        border-left: 4px solid var(--primary);
        overflow-x: auto; scrollbar-width: none; -ms-overflow-style: none;
    }
    .c-stats-bar::-webkit-scrollbar { display: none; }
    .c-stats-bar__item { flex: 1; min-width: 120px; }
    .c-stats-bar__label {
        font-size: 0.65rem; color: var(--text-muted);
        font-family: var(--font-mono); text-transform: uppercase;
    }
    .c-stats-bar__value {
        font-size: 1.5rem; font-weight: 800; color: var(--primary);
    }

    /* Cards */
    .c-card {
        background: var(--bg-page); border: 1px solid var(--border);
        padding: 24px; margin-bottom: 24px; border-radius: var(--radius);
        box-shadow: var(--shadow-sm);
        width: 100%; box-sizing: border-box;
    }
    .c-card__title {
        font-size: 1.1rem; color: var(--primary);
        text-transform: uppercase; letter-spacing: 0.05em;
        margin-bottom: 12px; font-weight: 800;
    }
    .c-card__body { font-size: 0.95rem; color: var(--text-main); }

    .c-card--brutal {
        border: 4px solid var(--border); border-radius: 0;
        box-shadow: 8px 8px 0px var(--border);
    }

    /* Badges */
    .c-badge {
        font-family: var(--font-mono); font-size: 0.65rem;
        font-weight: 800; padding: 2px 8px;
        background: var(--bg-alt); border-radius: 2px;
        text-transform: uppercase;
    }
    .c-badge--success { color: oklch(70% 0.2 140); }
    .c-badge--fail { color: oklch(60% 0.2 25); }

    /* Code Box */
    .c-code-box {
        background: #000; border-left: 4px solid var(--primary);
        margin: 24px 0; position: relative;
        width: 100%; box-sizing: border-box;
    }
    .c-code-box__header {
        display: flex; justify-content: space-between; align-items: center;
        padding: 8px 16px; background: rgba(255,255,255,0.05);
        border-bottom: 1px solid rgba(255,255,255,0.1);
    }
    .c-code-box__title {
        font-family: var(--font-mono); font-size: 0.7rem;
        color: var(--primary); font-weight: 800; text-transform: uppercase;
    }
    .c-code-box__copy {
        background: var(--primary); color: white; border: none;
        padding: 4px 12px; font-size: 0.65rem; font-weight: 800;
        cursor: pointer; text-transform: uppercase;
    }
    .c-code-box__pre { margin: 0; padding: 20px; color: oklch(85% 0.2 140); overflow-x: auto; }
    .c-code-box__code { font-family: var(--font-mono); font-size: 0.85rem; }

    /* Tables */
    .c-bejson-table-wrapper { width: 100%; box-sizing: border-box; }
    .c-table-container { 
        width: 100%; 
        overflow: auto; 
        max-height: 80vh;
        margin-bottom: 24px; 
        border: 1px solid var(--border);
        border-radius: var(--radius);
        scrollbar-width: thin;
    }
    .c-table {
        width: 100%; border-collapse: collapse; font-size: 0.9rem;
        min-width: 600px;
    }
    .c-table thead th {
        background: var(--bg-alt); padding: 12px; text-align: left;
        font-weight: 800; text-transform: uppercase; font-size: 0.75rem;
        border-bottom: 2px solid var(--border); color: var(--text-muted);
        position: sticky; top: 0; z-index: 10;
        white-space: nowrap;
    }
    .c-table th { padding: 12px; text-align: left; font-weight: 800; }
    .c-table td { 
        padding: 12px; 
        border-bottom: 1px solid var(--border-muted); 
        word-break: break-word;
        overflow-wrap: anywhere;
    }
    .c-table tr:hover { background: var(--bg-alt); }

    /* Tabs & Content */
    .c-subtabs { 
        display: flex; 
        gap: 0; 
        margin-bottom: 12px; 
        border: 1px solid var(--border); 
        width: 100%; 
        overflow-x: auto; 
        scrollbar-width: none; 
        -ms-overflow-style: none;
    }
    .c-subtabs::-webkit-scrollbar { display: none; }
    .c-subtabs__btn {
        border: none; padding: 12px 24px; font-weight: 800; font-size: 0.8rem;
        cursor: pointer; font-family: var(--font-sans); background: transparent;
        color: var(--text-muted); transition: var(--transition);
        white-space: nowrap;
        border-right: 1px solid var(--border);
    }
    .c-subtabs__btn:last-child { border-right: none; }
    .c-subtabs__btn:hover { background: var(--bg-alt); color: var(--primary); }
    .c-subtabs__btn--active { background: var(--primary) !important; color: white !important; }

    .c-tab-content { width: 100%; box-sizing: border-box; }

    /* Layout System (BECSS Standard) */
    .c-app-shell { display: flex; flex-direction: column; height: 100vh; overflow: hidden; }
    .c-app-container { display: flex; flex: 1; overflow: hidden; position: relative; }

    .c-header { 
        height: 60px; background: var(--bg-surface); border-bottom: 1px solid var(--border); 
        display: flex; align-items: center; padding: 0 24px; gap: 20px; flex-shrink: 0;
        z-index: 100;
    }
    .c-header__logo { font-weight: 800; letter-spacing: 2px; color: var(--primary); text-transform: uppercase; font-size: 1rem; }

    .c-sidebar { 
        width: 280px; background: var(--bg-surface); border-right: 1px solid var(--border); 
        transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        display: flex; flex-direction: column; z-index: 90;
    }
    .c-sidebar--collapsed { transform: translateX(-280px); margin-right: -280px; }

    .c-sidebar-overlay { 
        display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.8); z-index: 80; 
    }
    .c-sidebar-overlay--active { display: block; }

    .c-app-main { flex: 1; overflow-y: auto; padding: 2rem; position: relative; scrollbar-width: thin; }

    @media (max-width: 768px) {
        .c-sidebar { position: fixed; height: calc(100% - 60px); top: 60px; transform: translateX(-100%); }
        .c-sidebar--open { transform: translateX(0); }
        .c-sidebar--collapsed { margin-right: 0; }
    }

    .c-hamburger { cursor: pointer; display: flex; flex-direction: column; gap: 5px; width: 24px; background: none; border: none; padding: 0; }
    .c-hamburger span { display: block; height: 2px; background: var(--text-main); width: 100%; transition: 0.3s; }

    .c-sidebar__link {
        display: flex; align-items: center; gap: 12px; padding: 12px 24px;
        color: var(--text-main); text-decoration: none; font-weight: 700;
        font-size: 0.85rem; border-bottom: 1px solid var(--border-muted);
        transition: var(--transition);
    }
    .c-sidebar__link:hover { background: var(--bg-alt); color: var(--primary); }
    .c-sidebar__link span { color: var(--primary); font-size: 0.7rem; }

    /* Typography & Body Text */
    .c-card__body { 
        font-size: 0.95rem; 
        color: var(--text-main); 
        line-height: 1.7;
        max-width: 100%;
        overflow-wrap: anywhere;
        word-break: break-word;
    }
    .c-card__body p { margin-bottom: 1.25rem; }
    .c-card__body ul, .c-card__body ol { margin-bottom: 1.25rem; padding-left: 1.5rem; }
    .c-card__body li { margin-bottom: 0.6rem; }
    .c-card__body h1, .c-card__body h2, .c-card__body h3 { 
        color: var(--primary); 
        margin-top: 1.5rem; 
        margin-bottom: 0.75rem; 
        text-transform: uppercase;
        font-weight: 800;
        letter-spacing: 0.05em;
    }

    .c-dl { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
    .c-dl__item { margin-bottom: 12px; border-left: 2px solid var(--border); padding-left: 12px; }
    .c-dl__term { font-size: 0.65rem; font-family: var(--font-mono); color: var(--text-muted); text-transform: uppercase; }
    .c-dl__desc { font-weight: 700; font-size: 1rem; color: var(--text-main); }
    /* Card Grid */
    .c-card-grid {
        display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 300px), 1fr));
        gap: 24px; width: 100%;
    }

    /* Widgets */
    .c-widget {
        background: var(--bg-page); border: 1px solid var(--border);
        display: flex; flex-direction: column; overflow: hidden;
        border-radius: var(--radius); box-shadow: var(--shadow-sm);
        max-width: 100%; box-sizing: border-box;
    }
    .c-widget__header {
        padding: 8px 16px; background: var(--bg-alt);
        border-bottom: 1px solid var(--border); display: flex;
        justify-content: space-between; font-family: var(--font-mono);
        font-size: 0.7rem; font-weight: 700;
    }
    .c-widget__body { flex: 1; padding: 16px; overflow: auto; }

    /* Gallery */
    .c-gallery-grid {
        display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
        gap: 16px; width: 100%;
    }
    .c-gallery-item {
        background: var(--bg-surface); border: 1px solid var(--border);
        padding: 8px; border-radius: var(--radius); transition: var(--transition);
    }
    .c-gallery-item:hover { transform: translateY(-2px); box-shadow: var(--shadow-sm); }
    .c-gallery-item img { width: 100%; height: 150px; object-fit: cover; border-radius: 4px; display: block; }
    .c-gallery-item__label {
        margin-top: 8px; font-size: 0.75rem; color: var(--text-muted);
        text-align: center; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
    }

    /* Video Grid */
    .c-video-grid {
        display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
        gap: 24px; width: 100%;
    }
    .c-video-card {
        background: var(--bg-page); border: 1px solid var(--border);
        border-radius: var(--radius); overflow: hidden;
    }
    .c-video-card__header {
        padding: 10px 16px; background: var(--bg-alt);
        font-weight: 700; font-size: 0.85rem; border-bottom: 1px solid var(--border);
    }
    .c-video-card__embed { position: relative; padding-bottom: 56.25%; height: 0; }
    .c-video-card__embed iframe {
        position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: none;
    }

    /* Info Box */
    .c-info-box {
        background: var(--bg-page); border: 1px solid var(--border);
        padding: 24px; border-radius: var(--radius); position: relative;
        width: 100%; box-sizing: border-box;
    }
    .c-info-box__title {
        font-size: 1rem; font-weight: 800; color: var(--primary);
        margin-bottom: 12px; display: flex; align-items: center; gap: 8px;
    }
    .c-info-box__dot { width: 8px; height: 8px; background: var(--primary); border-radius: 50%; }
    .c-info-box__content { font-size: 0.95rem; color: var(--text-main); line-height: 1.5; }
    .c-info-box__link {
        display: inline-block; margin-top: 16px; font-size: 0.85rem;
        font-weight: 700; color: var(--primary); text-decoration: none;
    }

    /* Carousel */
    .c-carousel { position: relative; overflow: hidden; width: 100%; border: 1px solid var(--border); background: var(--bg-surface); }
    .c-carousel__track { display: flex; transition: transform 0.3s ease; }
    .c-carousel__slide { min-width: 100%; padding: 20px; box-sizing: border-box; }
    .c-carousel__controls { display: flex; justify-content: space-between; padding: 10px; background: rgba(0,0,0,0.05); }
    .c-carousel__btn {
        background: transparent; border: 1px solid var(--primary);
        color: var(--primary); font-family: var(--font-mono);
        padding: 5px 12px; cursor: pointer; font-weight: 700; font-size: 0.75rem;
    }
    .c-carousel__btn:hover { background: var(--primary); color: white; }

    /* Dialog */
    .c-dialog-mask {
        display: none; position: fixed; z-index: 4000; left: 0; top: 0; width: 100%; height: 100%;
        background-color: rgba(0,0,0,0.6); backdrop-filter: blur(4px);
    }
    .c-dialog {
        position: relative; background-color: var(--bg-page); margin: 10% auto; padding: 0;
        border: 2px solid var(--primary); width: 80%; max-width: 600px;
        box-shadow: 10px 10px 0px rgba(0,0,0,0.1); border-radius: var(--radius);
    }
    .c-dialog__header {
        padding: 12px 20px; background: var(--bg-alt); border-bottom: 1px solid var(--border);
        display: flex; justify-content: space-between; align-items: center;
    }
    .c-dialog__title { font-family: var(--font-mono); font-weight: 800; font-size: 0.85rem; text-transform: uppercase; color: var(--primary); }
    .c-dialog__close { background: none; border: none; font-size: 24px; cursor: pointer; color: var(--text-muted); }
    .c-dialog__body { padding: 24px; font-size: 0.95rem; color: var(--text-main); line-height: 1.6; }
    .c-dialog__footer {
        padding: 12px 20px; background: var(--bg-alt); border-top: 1px solid var(--border);
        display: flex; justify-content: flex-end; gap: 12px;
    }

    /* Lightbox */
    .c-lightbox { display: none; position: fixed; z-index: 5000; left: 0; top: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.95); }
    .c-lightbox__content { margin: auto; display: block; width: 85%; max-width: 1200px; max-height: 85%; margin-top: 5%; object-fit: contain; }
    .c-lightbox__caption { margin: auto; display: block; width: 80%; text-align: center; color: white; padding: 20px 0; font-family: var(--font-mono); font-size: 0.9rem; }
    .c-lightbox__close { position: absolute; top: 20px; right: 30px; color: white; font-size: 40px; font-weight: bold; cursor: pointer; }

    /* Table Controls & Pagination */
        .c-table-controls { 
        display: flex; align-items: center; gap: 16px; margin-bottom: 16px; 
        overflow-x: auto; white-space: nowrap; scrollbar-width: none;
    }
    .c-table-controls::-webkit-scrollbar { display: none; }
    .c-table-controls__label { font-family: var(--font-mono); font-size: 0.7rem; font-weight: 800; color: var(--primary); text-transform: uppercase; }
    .c-table-controls__select, .c-table-controls__input { 
        font-family: var(--font-sans); font-size: 0.8rem; padding: 4px 12px; 
        background-color: var(--bg-page); color: var(--text-main); border: 1px solid var(--border); 
        border-radius: var(--radius); outline: none; cursor: pointer;
    }
    .c-table-controls__select:focus, .c-table-controls__input:focus { border-color: var(--primary); }
    .c-table-controls__count { margin-left: auto; font-family: var(--font-mono); color: var(--text-muted); font-size: 0.7rem; font-weight: 700; }

    .c-pagination { display: flex; align-items: center; gap: 8px; margin-top: 16px; }
    .c-pagination__btn {
        background: var(--bg-alt); border: 1px solid var(--border);
        padding: 4px 12px; border-radius: var(--radius); cursor: pointer;
        font-family: var(--font-mono); font-size: 0.75rem; font-weight: 700;
        transition: var(--transition);
    }
    .c-pagination__btn:hover:not(:disabled) { background: var(--primary); color: white; border-color: var(--primary); }
    .c-pagination__btn:disabled { opacity: 0.4; cursor: not-allowed; }
    .c-pagination__info { font-family: var(--font-mono); font-size: 0.75rem; color: var(--text-muted); }

    /* Indicators (Used in Table Cells) */
    .c-indicator { font-weight: 800; text-transform: uppercase; }
    .c-indicator--success { color: oklch(70% 0.2 140); }
    .c-indicator--fail { color: oklch(60% 0.2 25); }
    .c-null-val { color: var(--text-muted); font-style: italic; opacity: 0.7; }

    /* Charts & Sparklines */
    .c-chart-container {
        position: relative; width: 100%; margin-bottom: 24px;
        background: var(--bg-surface); border: 1px solid var(--border);
        padding: 20px; border-left: 4px solid var(--primary);
        border-radius: var(--radius); box-sizing: border-box;
    }
    .c-sparkline { height: 50px; width: 100%; margin-top: 10px; }
}
"""
