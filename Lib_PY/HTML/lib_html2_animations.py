"""
Library:      lib_html2_animations.py
Family:       HTML3
Jurisdiction: ["BEJSON_LIBRARIES", "PY"]
Status:       OFFICIAL
Author:       Elton Boehnen
Version:      2.0.1 OFFICIAL
            MFDB Version: 1.31
Format_Creator: Elton Boehnen
Date:         2026-05-18
Description:  CSS-based animation library for modern web interfaces.
"""

def css_animation_keyframes():
    """Returns global keyframes for system animations."""
    return """
/* --- Core-Command Animation Keyframes --- */
@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }

@keyframes scanMove { 0% { top: 20%; } 100% { top: 80%; } }

@keyframes expandBrackets {
    0% { gap: 0; opacity: 0; transform: translate(-50%, -50%) scale(0.8); }
    15% { opacity: 1; transform: translate(-50%, -50%) scale(1.1); }
    30% { gap: clamp(10rem, 20vw, 22rem); transform: translate(-50%, -50%) scale(1); }
    85% { gap: clamp(10rem, 20vw, 22rem); opacity: 1; transform: translate(-50%, -50%) scale(1); }
    100% { gap: clamp(15rem, 30vw, 30rem); opacity: 0; transform: translate(-50%, -50%) scale(1.2); }
}

@keyframes glitch-anim-1 {
    0% { clip-path: polygon(0 10%, 100% 10%, 100% 30%, 0 30%); transform: translate(0); }
    20% { clip-path: polygon(0 50%, 100% 50%, 100% 60%, 0 60%); transform: translate(-5px, 2px); }
    40% { clip-path: polygon(0 15%, 100% 15%, 100% 25%, 0 25%); transform: translate(5px, -2px); }
    100% { clip-path: polygon(0 40%, 100% 40%, 100% 50%, 0 50%); transform: translate(0); }
}

@keyframes flashBang {
    0% { opacity: 0; }
    10% { opacity: 1; background-color: #ffffff; }
    20% { background-color: #DE2626; }
    100% { opacity: 0; }
}

@keyframes cinematicZoom {
    0% { opacity: 1; transform: scale(1.1); filter: blur(4px); }
    15% { opacity: 1; transform: scale(1); filter: blur(0); }
    80% { opacity: 1; transform: scale(0.98); filter: blur(0); }
    100% { opacity: 0; transform: scale(0.95); filter: blur(10px); }
}
"""

def html_intro_terminal(lines, impact_callback="null"):
    """
    Generates a terminal typewriter boot sequence.
    'lines' should be a list of strings.
    """
    import json
    lines_json = json.dumps(lines)
    
    return f"""
    <div id="terminal-boot" style="font-family: var(--font-family-mono); color: #888; padding: 20px;"></div>
    <script>
    (function() {{
        const lines = {lines_json};
        const el = document.getElementById('terminal-boot');
        let delay = 0;
        lines.forEach((text, i) => {{
            delay += 300 - (i * 20);
            setTimeout(() => {{
                const div = document.createElement('div');
                div.style.marginBottom = '5px';
                div.innerHTML = text;
                el.appendChild(div);
                if (i === lines.length - 1) {{
                    setTimeout(() => {{ 
                        el.style.opacity = '0';
                        el.style.transition = 'opacity 0.5s';
                        if (window['{impact_callback}']) window['{impact_callback}']();
                    }}, 600);
                }}
            }}, delay);
        }});
    }})();
    </script>
    """

def html_glitch_reveal(text, subtitle=""):
    """Generates a heavy glitch cinematic reveal for a logo or title."""
    return f"""
    <div class="glitch-wrapper" style="position: relative; text-align: center;">
        <h1 class="glitch-text" data-text="{text}" style="font-size: clamp(3rem, 10vw, 7rem); font-weight: 900; letter-spacing: 0.5rem; color: #fff;">{text}</h1>
        <p style="color: #DE2626; letter-spacing: 0.3rem; margin-top: 1rem;">{subtitle}</p>
    </div>
    <style>
    .glitch-text::before, .glitch-text::after {{
        content: attr(data-text); position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: transparent;
    }}
    .glitch-text::before {{ left: 4px; text-shadow: -3px 0 #DE2626; clip-path: polygon(0 0, 100% 0, 100% 35%, 0 35%); animation: glitch-anim-1 0.4s infinite; }}
    .glitch-text::after {{ left: -4px; text-shadow: 3px 0 #fff; clip-path: polygon(0 65%, 100% 65%, 100% 100%, 0 100%); animation: glitch-anim-1 0.3s infinite reverse; }}
    </style>
    """
