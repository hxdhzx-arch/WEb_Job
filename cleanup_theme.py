import os

TEMPLATES_DIR = "/Users/ausstromenein/job_WEB/templates"

THEME_TOGGLE_BTN = """<button onclick="toggleTheme()" class="nav-link" id="theme-switch" style="background:transparent;border:none;cursor:pointer;font-size:1.1rem;display:inline-flex;align-items:center;justify-content:center;padding:6px;margin-left:8px;" title="切换显示模式"><span id="theme-toggle-icon">🌙</span></button>
<script>
  setTimeout(function(){
    var t = document.documentElement.getAttribute('data-theme');
    var icon = document.getElementById("theme-toggle-icon");
    if (icon) icon.textContent = t === 'dark' ? '☀️' : '🌙';
  },0);
</script>"""

THEME_TOGGLE_BTN_SINGLE = THEME_TOGGLE_BTN.strip()

def cleanup_html_files():
    for f_name in os.listdir(TEMPLATES_DIR):
        if not f_name.endswith('.html'):
            continue
            
        path = os.path.join(TEMPLATES_DIR, f_name)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        original_content = content

        # Remove all instances of the button string
        temp_content = content.replace(THEME_TOGGLE_BTN_SINGLE, '<!--TEMP_TOGGLE-->')
        # Sometimes there's a trailing newline
        temp_content = temp_content.replace(THEME_TOGGLE_BTN_SINGLE + '\n', '<!--TEMP_TOGGLE-->')
        temp_content = temp_content.replace(THEME_TOGGLE_BTN, '<!--TEMP_TOGGLE-->')
        
        while '<!--TEMP_TOGGLE-->\n<!--TEMP_TOGGLE-->' in temp_content:
            temp_content = temp_content.replace('<!--TEMP_TOGGLE-->\n<!--TEMP_TOGGLE-->', '<!--TEMP_TOGGLE-->')
        while '<!--TEMP_TOGGLE--><!--TEMP_TOGGLE-->' in temp_content:
            temp_content = temp_content.replace('<!--TEMP_TOGGLE--><!--TEMP_TOGGLE-->', '<!--TEMP_TOGGLE-->')
        
        # In index.html, it put it inside nav-links and outside it.
        # Let's completely remove it from the file, and insert it only once before closing </nav>.
        # Actually it's best placed at the end of <div class="nav-links">.
        clean_content = content
        while 'id="theme-switch"' in clean_content:
            start_idx = clean_content.find('<button onclick="toggleTheme()" class="nav-link" id="theme-switch"')
            if start_idx == -1:
                break
            end_idx = clean_content.find('</script>', start_idx) + len('</script>')
            clean_content = clean_content[:start_idx] + clean_content[end_idx:]
            
        # Also clean up duplicate new tags if any
        # Now re-insert exactly ONCE at the end of nav-links
        if '<div class="nav-links">' in clean_content:
            # find where nav-links ends. Wait, nav-links might be followed by </div>.
            # We can use regex to inject it safely, but just replace `<div class="nav-links">.*?</div>` is hard without proper regex.
            # Easiest way: just re-insert it right after `<div class="nav-links">`.
            # We can just put it before the closing `</nav>`.
            # Let's insert before `</div></nav>` or `</div>\n</nav>`
            if '</div>\n</div></nav>' in clean_content:
                clean_content = clean_content.replace('</div>\n</div></nav>', f'{THEME_TOGGLE_BTN}\n</div>\n</div></nav>')
            elif '</div></nav>' in clean_content:
                clean_content = clean_content.replace('</div></nav>', f'{THEME_TOGGLE_BTN}</div></nav>')
            elif '</div>\n    </div>\n</nav>' in clean_content:
                clean_content = clean_content.replace('</div>\n    </div>\n</nav>', f'{THEME_TOGGLE_BTN}\n</div>\n    </div>\n</nav>')

        if clean_content != original_content:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(clean_content)
            print(f"Cleaned up {f_name}")

if __name__ == '__main__':
    cleanup_html_files()
    print("Cleanup done.")
