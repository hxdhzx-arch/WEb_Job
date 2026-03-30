import os
import re

CSS_PATH = "/Users/ausstromenein/job_WEB/static/style.css"
TEMPLATES_DIR = "/Users/ausstromenein/job_WEB/templates"

NEW_CSS_VARS = """
:root{--primary:#007AFF;--primary-light:rgba(0,122,255,0.1);--primary-dark:#0056CC;--accent:#34C759;--accent-light:rgba(52,199,89,0.1);--danger:#FF3B30;--warning:#FF9F0A;--bg:#F2F2F7;--bg-card:#FFFFFF;--text-main:#1D1D1F;--text-secondary:#86868B;--text-hint:#98989D;--border:#E5E5EA;--border-focus:#007AFF;--shadow-sm:0 1px 3px rgba(0,0,0,0.02),0 1px 2px rgba(0,0,0,0.04);--shadow-md:0 4px 16px rgba(0,0,0,0.06),0 2px 4px rgba(0,0,0,0.04);--shadow-lg:0 12px 32px rgba(0,0,0,0.08),0 4px 10px rgba(0,0,0,0.04);--radius:18px;--radius-sm:10px;--transition:0.3s cubic-bezier(0.25,0.1,0.25,1)}
[data-theme="dark"]{--primary:#0A84FF;--primary-light:rgba(10,132,255,0.15);--primary-dark:#0066CC;--accent:#30D158;--accent-light:rgba(48,209,88,0.15);--danger:#FF453A;--warning:#FF9F0A;--bg:#000000;--bg-card:#1C1C1E;--text-main:#F5F5F7;--text-secondary:#86868B;--text-hint:#636366;--border:#38383A;--border-focus:#0A84FF;--shadow-sm:0 1px 3px rgba(0,0,0,0.2);--shadow-md:0 4px 16px rgba(0,0,0,0.3);--shadow-lg:0 12px 32px rgba(0,0,0,0.4)}
"""

THEME_SCRIPT = """
<!-- Theme Init -->
<script>
(function(){
  var theme = localStorage.getItem("resumeAI_theme");
  if (!theme) {
    theme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  document.documentElement.setAttribute('data-theme', theme);
})();
function toggleTheme() {
  var t = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', t);
  localStorage.setItem("resumeAI_theme", t);
  var icon = document.getElementById("theme-toggle-icon");
  if(icon) {
    icon.textContent = t === 'dark' ? '☀️' : '🌙';
  }
}
</script>
"""

THEME_TOGGLE_BTN = """<button onclick="toggleTheme()" class="nav-link" id="theme-switch" style="background:transparent;border:none;cursor:pointer;font-size:1.1rem;display:inline-flex;align-items:center;justify-content:center;padding:6px;margin-left:8px;" title="切换显示模式"><span id="theme-toggle-icon">🌙</span></button>
<script>
  setTimeout(function(){
    var t = document.documentElement.getAttribute('data-theme');
    var icon = document.getElementById("theme-toggle-icon");
    if (icon) icon.textContent = t === 'dark' ? '☀️' : '🌙';
  },0);
</script>"""

def update_css():
    with open(CSS_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace root var
    content = re.sub(r':root\s*\{.*?--transition:[^}]+\}', NEW_CSS_VARS.strip(), content, flags=re.DOTALL)

    # Convert hardcoded values in style.css to variables
    # e.g. color: #1d1d1f -> var(--text-main)
    content = content.replace('color:#1d1d1f', 'color:var(--text-main)')
    content = content.replace('color:#fff', 'color:var(--bg-card)') 
    # Exception: buttons that explicitly need white text shouldn't be var(--bg-card) if they are primary
    # Wait, instead of globally replacing #fff, let's just do it for common background areas
    content = content.replace('background:#fff', 'background:var(--bg-card)')
    content = content.replace('background:#FAFAFA', 'background:var(--bg)')
    content = content.replace('background:#F3F4F6', 'background:var(--bg)')
    content = content.replace('background:#E8E8ED', 'background:var(--bg)')
    content = content.replace('color:#6B7280', 'color:var(--text-secondary)')
    
    # Some specific fixes
    content = content.replace('.a4-paper{width:760px;min-height:1080px;background:var(--bg-card)', '.a4-paper{width:760px;min-height:1080px;background:#ffffff') # Keep A4 paper white
    content = content.replace('.nav{', '.nav{background:var(--bg-card);') # Give nav background logic
    content = content.replace('background:rgba(255,255,255,.72)', 'background:transparent') 
    
    # Modal and boxes
    content = content.replace('.cm-box{background:var(--bg-card)', '.cm-box{background:var(--bg-card)')
    
    with open(CSS_PATH, 'w', encoding='utf-8') as f:
        f.write(content)

def update_html_files():
    for f_name in os.listdir(TEMPLATES_DIR):
        if not f_name.endswith('.html'):
            continue
            
        path = os.path.join(TEMPLATES_DIR, f_name)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        original_content = content

        # Inject THEME_SCRIPT in <head>
        if 'function toggleTheme()' not in content:
            content = content.replace('</head>', f'{THEME_SCRIPT}\n</head>')

        # Inject THEME_TOGGLE_BTN into <div class="nav-links">
        if '<div class="nav-links">' in content and 'id="theme-switch"' not in content:
            content = content.replace('</div>\n</div></nav>', f'{THEME_TOGGLE_BTN}\n</div>\n</div></nav>')
            # For inline navs:
            content = content.replace('</div>\n    </div>\n</nav>', f'{THEME_TOGGLE_BTN}\n</div>\n    </div>\n</nav>')
            # Some other possible replacements based on template layout
            content = content.replace('</div></nav>', f'{THEME_TOGGLE_BTN}</div></nav>')

        # Modify hardcoded colors in HTML inline styles (<style>) to use vars to support dark mode
        # Example for index.html:
        content = content.replace('body{background:#fff;', 'body{background:var(--bg);')
        content = content.replace('color:#1d1d1f', 'color:var(--text-main)')
        content = content.replace('color:#374151', 'color:var(--text-main)')
        content = content.replace('color:#6B7280', 'color:var(--text-secondary)')
        content = content.replace('color:#9CA3AF', 'color:var(--text-hint)')
        content = content.replace('background:#F9FAFB', 'background:var(--bg-card)')
        content = content.replace('background:#F3F4F6', 'background:var(--bg)')
        content = content.replace('background:#FAFAFA', 'background:var(--bg)')
        content = content.replace('background:#fff', 'background:var(--bg-card)')
        # But for text on colored buttons (like #007AFF), white shouldn't become dark bg
        # So revert standard buttons if inadvertently changed. A common one is color:#fff on .btn
        content = content.replace('color:var(--bg-card)', 'color:#ffffff')
        
        # Replace specific borders
        content = content.replace('border:1px solid #E5E7EB', 'border:1px solid var(--border)')
        content = content.replace('border:1px solid #F3F4F6', 'border:1px solid var(--border)')
        
        # Apple styling adjustment: slightly larger text or padded areas.
        # Ensure nav backdrop blur adapts to dark mode.
        content = content.replace('background:rgba(255,255,255,.8)', 'background:rgba(var(--bg-rgb, 255,255,255), 0.72)')

        if content != original_content:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Updated {f_name}")

if __name__ == '__main__':
    print("Updating CSS...")
    update_css()
    print("Updating HTML templates...")
    update_html_files()
    print("Done.")
