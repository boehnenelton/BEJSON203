class HTML3_App_Layout:
    """
    Standard layout engine for HTML3 Applications.
    Features: Hamburger Sidebar, Sticky Header, Responsive Container.
    """
    
    @staticmethod
    def get_template():
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="css/becss-core.css">
    <link rel="stylesheet" href="css/becss-components.css">
</head>
<body class="c-app-shell">
    <header class="c-header">
        <button class="c-hamburger" id="navToggle"><span></span><span></span><span></span></button>
        <div class="c-header__logo">BEJSON ECOSYSTEM</div>
        <div style="flex:1"></div>
        <div style="font-size:0.6rem; color:var(--text-muted); font-family:var(--font-mono);">MFDB v1.31 | HTML3 v1.2</div>
    </header>

    <div class="c-sidebar-overlay" id="overlay"></div>

    <div class="c-app-container">
        <aside class="c-sidebar c-sidebar--collapsed" id="sidebar">
            {sidebar_content}
        </aside>

        <main class="c-app-main">
            <div class="u-fs-tiny u-font-mono u-mb-8" style="color:var(--text-muted); text-transform:uppercase;">REGISTRY / <span style="color:var(--primary);">{entity_name}</span></div>
            {body_content}
        </main>
    </div>

    <script>
        const btn = document.getElementById('navToggle');
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('overlay');

        function toggle() {{
            const isMobile = window.innerWidth <= 768;
            if (isMobile) {{
                sidebar.classList.toggle('c-sidebar--open');
                overlay.classList.toggle('c-sidebar-overlay--active');
            }} else {{
                sidebar.classList.toggle('c-sidebar--collapsed');
            }}
        }}

        btn.addEventListener('click', toggle);
        overlay.addEventListener('click', toggle);

        // Auto-highlight active link
        const currentPath = window.location.pathname.split('/').pop() || 'index.html';
        document.querySelectorAll('.c-sidebar__link').forEach(link => {{
            if (link.getAttribute('href') === currentPath) {{
                link.classList.add('is-active');
            }}
        }});
    </script>
</body>
</html>"""
