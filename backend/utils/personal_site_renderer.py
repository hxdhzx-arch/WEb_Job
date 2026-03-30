"""
personal_site_renderer.py — AI 个人网站渲染引擎
4 种风格：minimal / modern / card / blog
所有输出为纯静态 HTML，零外部依赖
"""
import html as _html

# ══════════════════════════════════════
#  工具函数
# ══════════════════════════════════════

def E(text):
    if not text:
        return ""
    return _html.escape(str(text))


def _fonts():
    return "-apple-system,BlinkMacSystemFont,'PingFang SC','Hiragino Sans GB','Microsoft YaHei','Segoe UI',Roboto,sans-serif"


def _mono():
    return "'SF Mono','Menlo','Consolas','Courier New',monospace"


def _get(data, *keys, default=""):
    """安全嵌套取值"""
    d = data
    for k in keys:
        if isinstance(d, dict):
            d = d.get(k, default)
        else:
            return default
    return d or default


# ══════════════════════════════════════
#  Section 渲染器（所有模板共用）
# ══════════════════════════════════════

def _hero_section(data, config, style_fn):
    hero = data.get("hero", {})
    name = E(hero.get("name", ""))
    tagline = E(hero.get("tagline", ""))
    avatar = hero.get("avatar", "")
    cover = hero.get("cover", "")
    if not name:
        return ""
    return style_fn["hero"](name, tagline, avatar, cover)


def _about_section(data, config, style_fn):
    about = data.get("about", "")
    if not about:
        return ""
    return style_fn["section"]("关于我", f'<p class="ps-text">{E(about)}</p>')


def _experience_section(data, config, style_fn):
    items = data.get("experience", [])
    if not items:
        return ""
    html = ""
    for item in items:
        if not item.get("company") and not item.get("role"):
            continue
        desc = E(item.get("description", ""))
        desc_html = ""
        if desc:
            lines = desc.split("\n")
            if len(lines) > 1:
                desc_html = '<ul class="ps-duties">' + "".join(f"<li>{E(l)}</li>" for l in lines if l.strip()) + "</ul>"
            else:
                desc_html = f'<p class="ps-text-sm">{desc}</p>'
        html += f'''<div class="ps-exp-item">
<div class="ps-exp-header">
<div><span class="ps-exp-company">{E(item.get("company",""))}</span>
<span class="ps-exp-role">{E(item.get("role",""))}</span></div>
<span class="ps-exp-period">{E(item.get("period",""))}</span>
</div>{desc_html}</div>'''
    return style_fn["section"]("工作经历", html)


def _projects_section(data, config, style_fn):
    items = data.get("projects", [])
    if not items:
        return ""
    html = '<div class="ps-project-grid">'
    for p in items:
        if not p.get("name"):
            continue
        tags = p.get("tags", [])
        tags_html = ""
        if tags:
            tags_html = '<div class="ps-tags">' + "".join(f'<span class="ps-tag">{E(t)}</span>' for t in tags) + "</div>"
        link = p.get("link", "")
        link_html = f' <a href="{E(link)}" class="ps-link" target="_blank">查看 →</a>' if link else ""
        html += f'''<div class="ps-project-card">
<h4 class="ps-project-name">{E(p["name"])}{link_html}</h4>
<p class="ps-text-sm">{E(p.get("description",""))}</p>
{tags_html}</div>'''
    html += "</div>"
    return style_fn["section"]("项目经历", html)


def _education_section(data, config, style_fn):
    items = data.get("education", [])
    if not items:
        return ""
    html = ""
    for ed in items:
        if not ed.get("school"):
            continue
        detail = " · ".join(filter(None, [ed.get("degree", ""), ed.get("major", "")]))
        html += f'''<div class="ps-edu-item">
<div class="ps-exp-header">
<span class="ps-exp-company">{E(ed["school"])}</span>
<span class="ps-exp-period">{E(ed.get("period",""))}</span>
</div>
{f'<p class="ps-text-sm">{E(detail)}</p>' if detail else ""}
</div>'''
    return style_fn["section"]("教育背景", html)


def _skills_section(data, config, style_fn):
    skills = data.get("skills", [])
    if not skills:
        return ""
    html = ""
    if isinstance(skills, list) and skills:
        if isinstance(skills[0], dict):
            # [{"category":"...", "items":["..."]}]
            for group in skills:
                cat = E(group.get("category", ""))
                items = group.get("items", [])
                tags = "".join(f'<span class="ps-tag">{E(i)}</span>' for i in items)
                html += f'{f"<h4 class=ps-skill-cat>{cat}</h4>" if cat else ""}<div class="ps-tags">{tags}</div>'
        else:
            # ["skill1", "skill2"]
            html = '<div class="ps-tags">' + "".join(f'<span class="ps-tag">{E(s)}</span>' for s in skills) + "</div>"
    elif isinstance(skills, str):
        import re
        items = [s.strip() for s in re.split(r'[,，、\n]+', skills) if s.strip()]
        html = '<div class="ps-tags">' + "".join(f'<span class="ps-tag">{E(s)}</span>' for s in items) + "</div>"
    return style_fn["section"]("技能", html)


def _contact_section(data, config, style_fn):
    contact = data.get("contact", {})
    if not contact:
        return ""
    items = []
    labels = {"email": "📧 邮箱", "phone": "📱 手机", "github": "🔗 GitHub", "linkedin": "🔗 LinkedIn", "website": "🌐 网站", "wechat": "💬 微信"}
    for key, label in labels.items():
        val = contact.get(key, "")
        if val:
            if key in ("github", "linkedin", "website") and val.startswith("http"):
                items.append(f'<div class="ps-contact-item">{label}: <a href="{E(val)}" target="_blank">{E(val)}</a></div>')
            else:
                items.append(f'<div class="ps-contact-item">{label}: {E(val)}</div>')
    if not items:
        return ""
    return style_fn["section"]("联系方式", "\n".join(items))


SECTION_ORDER = ["about", "experience", "projects", "education", "skills", "contact"]
SECTION_RENDERERS = {
    "about": _about_section,
    "experience": _experience_section,
    "projects": _projects_section,
    "education": _education_section,
    "skills": _skills_section,
    "contact": _contact_section,
}


def _render_all_sections(data, config, style_fn):
    order = config.get("section_order", SECTION_ORDER) if config else SECTION_ORDER
    html = ""
    for key in order:
        fn = SECTION_RENDERERS.get(key)
        if fn:
            html += fn(data, config, style_fn)
    return html


# ══════════════════════════════════════
#  公共 CSS
# ══════════════════════════════════════

def _base_css(accent="#8B5CF6"):
    return f"""
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
html{{scroll-behavior:smooth}}
body{{font-family:{_fonts()};line-height:1.7;-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale}}
a{{color:{accent};text-decoration:none}}
a:hover{{text-decoration:underline}}
.ps-container{{max-width:820px;margin:0 auto;padding:0 24px}}
.ps-section{{margin-bottom:40px}}
.ps-section-title{{font-size:1.2rem;font-weight:700;margin-bottom:18px;display:flex;align-items:center;gap:8px}}
.ps-text{{line-height:1.8;font-size:.95rem}}
.ps-text-sm{{font-size:.9rem;line-height:1.7}}
.ps-exp-item{{margin-bottom:22px}}
.ps-exp-header{{display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:6px;margin-bottom:4px}}
.ps-exp-company{{font-weight:700;font-size:1rem}}
.ps-exp-role{{font-size:.9rem;margin-left:8px}}
.ps-exp-period{{font-size:.82rem;white-space:nowrap}}
.ps-duties{{margin:6px 0 0;padding-left:18px;font-size:.9rem}}
.ps-duties li{{margin-bottom:4px}}
.ps-project-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px}}
.ps-project-card{{padding:20px;border-radius:12px}}
.ps-project-name{{font-weight:700;font-size:.95rem;margin-bottom:6px}}
.ps-link{{font-size:.82rem}}
.ps-tags{{display:flex;flex-wrap:wrap;gap:8px;margin-top:8px}}
.ps-tag{{padding:4px 12px;border-radius:6px;font-size:.82rem;font-weight:500}}
.ps-skill-cat{{font-size:.88rem;font-weight:600;margin:12px 0 6px}}
.ps-edu-item{{margin-bottom:14px}}
.ps-contact-item{{padding:6px 0;font-size:.9rem}}
.ps-footer{{text-align:center;padding:32px 0;font-size:.78rem;border-top:1px solid #eee;margin-top:48px}}
.ps-dark-btn{{position:fixed;bottom:20px;right:20px;width:42px;height:42px;border-radius:50%;border:none;
  background:{accent};color:#fff;font-size:1.1rem;cursor:pointer;box-shadow:0 4px 14px rgba(0,0,0,.15);
  display:flex;align-items:center;justify-content:center;transition:all .3s;z-index:100}}
.ps-dark-btn:hover{{transform:scale(1.1)}}
@media(max-width:600px){{
  .ps-container{{padding:0 16px}}
  .ps-exp-header{{flex-direction:column}}
  .ps-project-grid{{grid-template-columns:1fr}}
}}
@media print{{.ps-dark-btn,.ps-footer{{display:none}}body{{background:#fff!important;color:#1f2937!important}}}}
"""


def _dark_css():
    return """
body.dark{background:#0B0F19;color:#E2E8F0}
body.dark .ps-exp-company,body.dark .ps-project-name{color:#F1F5F9}
body.dark .ps-text,body.dark .ps-text-sm,body.dark .ps-exp-role,body.dark .ps-duties,body.dark .ps-contact-item{color:#94A3B8}
body.dark .ps-exp-period{color:#64748B}
body.dark .ps-tag{background:rgba(139,92,246,.15)!important;color:#A78BFA!important}
body.dark .ps-project-card{background:#111827!important;border-color:#1E293B!important}
body.dark .ps-footer{border-color:#1E293B;color:#475569}
body.dark .ps-section-title{color:#F1F5F9}
"""


def _toggle_js():
    return """
(function(){
  var btn=document.getElementById('ps-dark-btn');
  if(!btn)return;
  var dark=localStorage.getItem('ps-dark')==='1';
  if(dark)document.body.classList.add('dark');
  btn.textContent=dark?'☀':'🌙';
  btn.addEventListener('click',function(){
    dark=!dark;
    document.body.classList.toggle('dark',dark);
    btn.textContent=dark?'☀':'🌙';
    localStorage.setItem('ps-dark',dark?'1':'0');
  });
})();
"""


# ══════════════════════════════════════
#  Style 1: minimal — 极简风
# ══════════════════════════════════════

def _style_minimal():
    accent = "#1E293B"
    extra_css = f"""
body{{background:#FAFAF9;color:#1C1C1E}}
.ps-section-title{{padding-bottom:8px;border-bottom:1.5px solid #1C1C1E;color:#1C1C1E}}
.ps-tag{{background:#F1F5F9;color:#475569}}
.ps-project-card{{background:#fff;border:1px solid #E5E7EB}}
.ps-exp-role,.ps-exp-period,.ps-text-sm{{color:#6B7280}}
"""
    def hero(name, tagline, avatar, cover):
        avatar_html = f'<img src="{avatar}" style="width:80px;height:80px;border-radius:50%;object-fit:cover;border:2px solid #E5E7EB;margin-bottom:16px" alt="">' if avatar else ""
        return f'''<header style="text-align:center;padding:60px 0 40px">
<div class="ps-container">
{avatar_html}
<h1 style="font-size:2.2rem;font-weight:800;letter-spacing:-.02em;color:#1C1C1E">{name}</h1>
{f'<p style="font-size:1rem;color:#6B7280;margin-top:8px">{tagline}</p>' if tagline else ""}
</div></header>'''

    def section(title, content):
        return f'<section class="ps-section"><div class="ps-container"><div class="ps-section-title">{title}</div>{content}</div></section>'

    return {"hero": hero, "section": section, "accent": accent, "extra_css": extra_css}


# ══════════════════════════════════════
#  Style 2: modern — 现代科技感
# ══════════════════════════════════════

def _style_modern():
    accent = "#8B5CF6"
    extra_css = f"""
body{{background:#0B0F19;color:#E2E8F0}}
.ps-section-title{{color:{accent};position:relative;padding-left:18px}}
.ps-section-title::before{{content:'';position:absolute;left:0;top:50%;transform:translateY(-50%);width:4px;height:20px;border-radius:2px;background:{accent}}}
.ps-tag{{background:rgba(139,92,246,.12);color:#A78BFA}}
.ps-project-card{{background:#111827;border:1px solid #1E293B;transition:transform .2s,box-shadow .2s}}
.ps-project-card:hover{{transform:translateY(-3px);box-shadow:0 8px 24px rgba(0,0,0,.3)}}
.ps-exp-company{{color:#F1F5F9}}
.ps-exp-role,.ps-text-sm,.ps-duties,.ps-contact-item{{color:#94A3B8}}
.ps-exp-period{{color:#64748B}}
.ps-footer{{border-color:#1E293B;color:#475569}}
"""
    def hero(name, tagline, avatar, cover):
        bg = f'background-image:linear-gradient(rgba(11,15,25,.7),rgba(11,15,25,.95)),url({cover});background-size:cover;background-position:center;' if cover else f'background:linear-gradient(135deg,{accent}22,#3B82F622);'
        avatar_html = f'<img src="{avatar}" style="width:90px;height:90px;border-radius:50%;object-fit:cover;border:3px solid {accent}44;margin-bottom:16px" alt="">' if avatar else ""
        return f'''<header style="{bg}padding:80px 0 50px;text-align:center">
<div class="ps-container">
{avatar_html}
<h1 style="font-size:2.4rem;font-weight:800;background:linear-gradient(135deg,{accent},#3B82F6);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text">{name}</h1>
{f'<p style="font-size:1.05rem;color:#94A3B8;margin-top:10px">{tagline}</p>' if tagline else ""}
</div></header>'''

    def section(title, content):
        return f'<section class="ps-section"><div class="ps-container"><div class="ps-section-title">{title}</div>{content}</div></section>'

    return {"hero": hero, "section": section, "accent": accent, "extra_css": extra_css}


# ══════════════════════════════════════
#  Style 3: card — 卡片式
# ══════════════════════════════════════

def _style_card():
    accent = "#0EA5E9"
    extra_css = f"""
body{{background:#F1F5F9;color:#1E293B}}
.ps-section{{background:#fff;border-radius:16px;padding:28px;box-shadow:0 1px 6px rgba(0,0,0,.05);border:1px solid #E2E8F0}}
.ps-section-title{{color:{accent}}}
.ps-tag{{background:{accent}12;color:{accent}}}
.ps-project-card{{background:#F8FAFC;border:1px solid #E2E8F0}}
.ps-exp-role,.ps-text-sm{{color:#64748B}}
.ps-exp-period{{color:#9CA3AF}}
.ps-container{{display:flex;flex-direction:column;gap:20px;padding-top:24px;padding-bottom:40px}}
"""
    def hero(name, tagline, avatar, cover):
        bg_style = f'background:linear-gradient(135deg,{accent},#6366F1);' if not cover else f'background-image:linear-gradient(rgba(14,165,233,.8),rgba(99,102,241,.9)),url({cover});background-size:cover;'
        avatar_html = f'<img src="{avatar}" style="width:80px;height:80px;border-radius:50%;object-fit:cover;border:3px solid rgba(255,255,255,.3);margin-bottom:16px" alt="">' if avatar else ""
        return f'''<header style="{bg_style}color:#fff;padding:56px 24px;text-align:center;border-radius:0 0 24px 24px;margin-bottom:-8px">
{avatar_html}
<h1 style="font-size:2rem;font-weight:800">{name}</h1>
{f'<p style="font-size:1rem;opacity:.85;margin-top:6px">{tagline}</p>' if tagline else ""}
</header>'''

    def section(title, content):
        return f'<section class="ps-section"><div class="ps-section-title">{title}</div>{content}</section>'

    return {"hero": hero, "section": section, "accent": accent, "extra_css": extra_css}


# ══════════════════════════════════════
#  Style 4: blog — 博客风格
# ══════════════════════════════════════

def _style_blog():
    accent = "#059669"
    extra_css = f"""
body{{background:#FFFBEB;color:#1C1917}}
.ps-section-title{{font-size:1.3rem;color:{accent};letter-spacing:-.01em;margin-bottom:20px;padding-bottom:10px;border-bottom:2px dashed {accent}44}}
.ps-tag{{background:#ECFDF5;color:{accent}}}
.ps-project-card{{background:#FFFEF0;border:1px solid #FDE68A;border-radius:8px}}
.ps-exp-role,.ps-text-sm,.ps-duties{{color:#78716C}}
.ps-exp-company{{color:#292524}}
.ps-exp-period{{color:#A8A29E}}
.ps-text{{font-size:1rem;line-height:1.9}}
"""
    def hero(name, tagline, avatar, cover):
        avatar_html = f'<img src="{avatar}" style="width:100px;height:100px;border-radius:16px;object-fit:cover;border:3px solid #FDE68A" alt="">' if avatar else ""
        return f'''<header style="padding:60px 0 40px;border-bottom:1px solid #FDE68A">
<div class="ps-container" style="display:flex;align-items:center;gap:24px;flex-wrap:wrap">
{avatar_html}
<div>
<h1 style="font-size:2rem;font-weight:800;color:#1C1917">{name}</h1>
{f'<p style="font-size:1rem;color:#78716C;margin-top:4px">{tagline}</p>' if tagline else ""}
</div>
</div></header>'''

    def section(title, content):
        return f'<section class="ps-section"><div class="ps-container"><div class="ps-section-title">{title}</div>{content}</div></section>'

    return {"hero": hero, "section": section, "accent": accent, "extra_css": extra_css}


# ══════════════════════════════════════
#  页面包装
# ══════════════════════════════════════

STYLES = {
    "minimal": _style_minimal,
    "modern": _style_modern,
    "card": _style_card,
    "blog": _style_blog,
}

DEFAULT_STYLE = "modern"


def _wrap_page(data, config, style_fn, css, body):
    hero = data.get("hero", {})
    name = E(hero.get("name", "个人网站"))
    tagline = E(hero.get("tagline", ""))
    title = f"{name} — 个人主页"
    desc = tagline or E((data.get("about", "") or "")[:160])

    footer = '<footer class="ps-footer"><div class="ps-container">由 <strong>简历 AI</strong> 生成</div></footer>'

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta name="robots" content="noindex,nofollow">
<style>
{_base_css(style_fn["accent"])}
{_dark_css()}
{style_fn["extra_css"]}
</style>
</head>
<body>
{body}
{footer}
<button class="ps-dark-btn" id="ps-dark-btn" title="切换暗色模式">🌙</button>
<script>{_toggle_js()}</script>
</body>
</html>'''


# ══════════════════════════════════════
#  公开 API
# ══════════════════════════════════════

def render_personal_site(site_data, site_config=None, style=None):
    """
    渲染个人网站 HTML。

    Args:
        site_data: structured profile data dict
        site_config: style/theme config dict
        style: style name (minimal/modern/card/blog)

    Returns:
        Complete HTML string
    """
    if not style:
        style = (site_config or {}).get("style", DEFAULT_STYLE)
    if style not in STYLES:
        style = DEFAULT_STYLE

    style_fn = STYLES[style]()
    hero_html = _hero_section(site_data, site_config, style_fn)
    sections_html = _render_all_sections(site_data, site_config, style_fn)

    # Card style uses container differently
    if style == "card":
        body = hero_html + '<div class="ps-container">' + sections_html + '</div>'
    else:
        body = hero_html + '<main style="padding:40px 0">' + sections_html + '</main>'

    return _wrap_page(site_data, site_config, style_fn, "", body)


def list_styles():
    return [
        {"id": "minimal", "name": "极简白", "description": "大留白、清爽、专注内容", "emoji": "📃"},
        {"id": "modern", "name": "科技感", "description": "暗色主题、渐变色、现代感", "emoji": "🚀"},
        {"id": "card", "name": "卡片式", "description": "圆角卡片、微阴影、分区清晰", "emoji": "🃏"},
        {"id": "blog", "name": "博客风", "description": "暖色调、轻松亲切、适合个人品牌", "emoji": "📝"},
    ]
