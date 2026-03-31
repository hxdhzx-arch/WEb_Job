"""
personal_site_renderer.py — AI 个人网站渲染引擎 (Block 版)
支持 4 套模板风格 + 区块化渲染 + 动效语言
"""
import html as _html


def E(text):
    if text is None:
        return ""
    return _html.escape(str(text))


def _fonts():
    return "-apple-system,BlinkMacSystemFont,'PingFang SC','Hiragino Sans GB','Microsoft YaHei','Segoe UI',Roboto,sans-serif"


def _as_list(v):
    if isinstance(v, list):
        return v
    if isinstance(v, str):
        return [i.strip() for i in v.split(",") if i.strip()]
    return []


def _style_cls(block):
    style = block.get("style", {}) if isinstance(block, dict) else {}
    return f"pb-variant-{style.get('variant', 'card')} pb-layout-{style.get('layout', 'left')}"


def _section_open(block, sec_cls):
    return f'<section class="{sec_cls} {_style_cls(block)}" id="block-{E(block.get("id",""))}"><div class="pb-container">'


def _section_close():
    return "</div></section>"


def render_hero(b):
    c = b.get("content", {})
    name = E(c.get("name", "Your Name"))
    subtitle = E(c.get("subtitle", "Creative professional"))
    avatar = E(c.get("avatar", ""))
    cta = c.get("cta", {}) if isinstance(c.get("cta"), dict) else {}
    cta_text = E(cta.get("text", "Contact"))
    cta_url = E(cta.get("url", "#"))
    links = []
    if c.get("github"):
        links.append(f'<a href="{E(c.get("github"))}" target="_blank" rel="noopener">GitHub</a>')
    if c.get("linkedin"):
        links.append(f'<a href="{E(c.get("linkedin"))}" target="_blank" rel="noopener">LinkedIn</a>')
    if c.get("website"):
        links.append(f'<a href="{E(c.get("website"))}" target="_blank" rel="noopener">Website</a>')
    links_html = f'<div class="pb-hero-links">{"".join(links)}</div>' if links else ""

    avatar_html = f'<img class="pb-avatar" src="{avatar}" alt="{name}"/>' if avatar else '<div class="pb-avatar pb-avatar-fallback">✦</div>'
    return (
        _section_open(b, "pb-hero pb-reveal")
        + '<div class="pb-hero-glow"></div><div class="pb-hero-line"></div>'
        + '<div class="pb-hero-grid">'
        + f'<div class="pb-hero-left">{avatar_html}</div>'
        + '<div class="pb-hero-right">'
        + f'<h1 class="pb-title">{name}</h1><p class="pb-subtitle">{subtitle}</p>'
        + f'<div class="pb-hero-actions"><a href="{cta_url}" class="pb-btn pb-btn-primary">{cta_text}</a></div>{links_html}'
        + "</div></div>"
        + _section_close()
    )


def render_about(b):
    c = b.get("content", {})
    title = E(b.get("title", "About"))
    paras = [p.strip() for p in str(c.get("text", "")).split("\n") if p.strip()]
    body = "".join([f"<p>{E(p)}</p>" for p in paras]) if paras else "<p>Tell your story here.</p>"
    return _section_open(b, "pb-about pb-reveal") + f'<h2 class="pb-sec-title">{title}</h2><div class="pb-prose">{body}</div>' + _section_close()


def render_projects(b):
    items = _as_list(b.get("content", {}).get("items"))
    title = E(b.get("title", "Projects"))
    if not items:
        return ""
    cards = []
    for p in items:
        if not isinstance(p, dict):
            continue
        cover = E(p.get("cover", ""))
        cover_html = f'<img class="pb-proj-cover" src="{cover}" alt="{E(p.get("title","Project"))}"/>' if cover else '<div class="pb-proj-cover pb-cover-fallback">Project</div>'
        tags = _as_list(p.get("tags"))
        tags_html = "".join([f'<span class="pb-tag">{E(t)}</span>' for t in tags if t])
        links = []
        if p.get("link"):
            links.append(f'<a href="{E(p.get("link"))}" target="_blank" rel="noopener" class="pb-btn pb-btn-sm">Live</a>')
        if p.get("github"):
            links.append(f'<a href="{E(p.get("github"))}" target="_blank" rel="noopener" class="pb-btn pb-btn-sm pb-btn-outline">GitHub</a>')
        links_html = f'<div class="pb-proj-links">{"".join(links)}</div>' if links else ""
        cards.append(
            '<article class="pb-proj-card pb-reveal">'
            + cover_html
            + '<div class="pb-proj-body">'
            + f'<h3 class="pb-proj-title">{E(p.get("title",""))}</h3><p class="pb-proj-desc">{E(p.get("desc",""))}</p>'
            + (f'<div class="pb-tags">{tags_html}</div>' if tags_html else "")
            + links_html
            + "</div></article>"
        )
    return _section_open(b, "pb-projects") + f'<h2 class="pb-sec-title">{title}</h2><div class="pb-grid pb-proj-grid">{"".join(cards)}</div>' + _section_close()


def render_skills(b):
    items = _as_list(b.get("content", {}).get("items"))
    title = E(b.get("title", "Skills"))
    if not items:
        return ""
    tags = "".join([f'<span class="pb-tag pb-tag-lg">{E(t)}</span>' for t in items if t])
    return _section_open(b, "pb-skills pb-reveal") + f'<h2 class="pb-sec-title">{title}</h2><div class="pb-tags-wrap">{tags}</div>' + _section_close()


def render_experience(b):
    items = _as_list(b.get("content", {}).get("items"))
    title = E(b.get("title", "Experience"))
    if not items:
        return ""
    rows = []
    for it in items:
        if not isinstance(it, dict):
            continue
        desc = it.get("desc", [])
        if isinstance(desc, str):
            desc = [d.strip() for d in desc.split("\n") if d.strip()]
        desc_html = "".join([f"<li>{E(d)}</li>" for d in desc if d]) if desc else ""
        rows.append(
            '<article class="pb-exp-item pb-reveal"><div class="pb-exp-head"><div class="pb-exp-main">'
            + f'<span class="pb-company">{E(it.get("company",""))}</span><span class="pb-role">{E(it.get("role",""))}</span></div>'
            + f'<span class="pb-period">{E(it.get("period",""))}</span></div>'
            + (f'<ul class="pb-list">{desc_html}</ul>' if desc_html else "")
            + "</article>"
        )
    return _section_open(b, "pb-experience") + f'<h2 class="pb-sec-title">{title}</h2><div class="pb-items">{"".join(rows)}</div>' + _section_close()


def render_education(b):
    items = _as_list(b.get("content", {}).get("items"))
    title = E(b.get("title", "Education"))
    if not items:
        return ""
    rows = []
    for it in items:
        if not isinstance(it, dict):
            continue
        rows.append(
            '<article class="pb-edu-item pb-reveal"><div class="pb-exp-head"><div class="pb-exp-main">'
            + f'<span class="pb-company">{E(it.get("school",""))}</span><span class="pb-role">{E(it.get("degree",""))}</span></div>'
            + f'<span class="pb-period">{E(it.get("period",""))}</span></div></article>'
        )
    return _section_open(b, "pb-education") + f'<h2 class="pb-sec-title">{title}</h2><div class="pb-items">{"".join(rows)}</div>' + _section_close()


def render_contact(b):
    c = b.get("content", {}) if isinstance(b.get("content"), dict) else {}
    title = E(b.get("title", "Contact"))
    items = []
    defs = [("email", "Email", "mailto:"), ("phone", "Phone", "tel:"), ("github", "GitHub", ""), ("linkedin", "LinkedIn", ""), ("wechat", "WeChat", "")]
    for key, label, prefix in defs:
        val = c.get(key)
        if not val:
            continue
        val = str(val)
        if key in ("github", "linkedin") and not val.startswith("http"):
            val = "https://" + val
        href = val if val.startswith("http") else prefix + val if prefix else ""
        if href:
            items.append(f'<div class="pb-cnt-item"><span class="pb-cnt-label">{label}</span><a href="{E(href)}" target="_blank" rel="noopener">{E(c.get(key))}</a></div>')
        else:
            items.append(f'<div class="pb-cnt-item"><span class="pb-cnt-label">{label}</span><span>{E(c.get(key))}</span></div>')
    return _section_open(b, "pb-contact pb-reveal") + f'<h2 class="pb-sec-title">{title}</h2><div class="pb-cnt-list">{"".join(items)}</div>' + _section_close()


def render_stats(b):
    items = _as_list(b.get("content", {}).get("items"))
    if not items:
        return ""
    html = []
    for i in items:
        if isinstance(i, dict):
            html.append(f'<div class="pb-stat-item pb-reveal"><div class="pb-stat-val">{E(i.get("value",""))}</div><div class="pb-stat-label">{E(i.get("label",""))}</div></div>')
    return _section_open(b, "pb-stats") + f'<div class="pb-stats-grid">{"".join(html)}</div>' + _section_close()


def render_services(b):
    items = _as_list(b.get("content", {}).get("items"))
    title = E(b.get("title", "Services"))
    if not items:
        return ""
    html = []
    for i in items:
        if isinstance(i, dict):
            html.append(f'<article class="pb-srv-card pb-reveal"><h3 class="pb-srv-title">{E(i.get("title",""))}</h3><p class="pb-srv-desc">{E(i.get("desc",""))}</p></article>')
    return _section_open(b, "pb-services") + f'<h2 class="pb-sec-title">{title}</h2><div class="pb-grid">{"".join(html)}</div>' + _section_close()


def render_testimonials(b):
    items = _as_list(b.get("content", {}).get("items"))
    title = E(b.get("title", "Testimonials"))
    if not items:
        return ""
    html = []
    for i in items:
        if isinstance(i, dict):
            html.append(
                '<article class="pb-tst-card pb-reveal">'
                + f'<p class="pb-tst-text">"{E(i.get("text",""))}"</p>'
                + f'<div class="pb-tst-author"><strong>{E(i.get("author",""))}</strong> · {E(i.get("role",""))}</div>'
                + "</article>"
            )
    return _section_open(b, "pb-testimonials") + f'<h2 class="pb-sec-title">{title}</h2><div class="pb-grid">{"".join(html)}</div>' + _section_close()


def render_cta(b):
    c = b.get("content", {}) if isinstance(b.get("content"), dict) else {}
    title = E(c.get("title", b.get("title", "Ready to build something great?")))
    desc = E(c.get("desc", "Let's collaborate on your next project."))
    btn_text = E(c.get("button_text", "Get in touch"))
    btn_url = E(c.get("button_url", "#"))
    return (
        _section_open(b, "pb-cta pb-reveal")
        + f'<div class="pb-cta-box"><h2 class="pb-sec-title">{title}</h2><p class="pb-subtitle">{desc}</p>'
        + f'<a href="{btn_url}" class="pb-btn pb-btn-primary">{btn_text}</a></div>'
        + _section_close()
    )


def render_footer(b):
    c = b.get("content", {}) if isinstance(b.get("content"), dict) else {}
    text = E(c.get("text", "© 2026 All Rights Reserved"))
    return f'<footer class="pb-footer" id="block-{E(b.get("id",""))}"><div class="pb-container"><p>{text}</p></div></footer>'


BLOCK_RENDERERS = {
    "hero": render_hero,
    "about": render_about,
    "projects": render_projects,
    "skills": render_skills,
    "experience": render_experience,
    "education": render_education,
    "contact": render_contact,
    "stats": render_stats,
    "services": render_services,
    "testimonials": render_testimonials,
    "cta": render_cta,
    "footer": render_footer,
}


def _base_css(theme, template_id):
    accent = theme.get("primaryColor", "#4f46e5")
    bg = theme.get("bgColor", "#0b1020" if template_id == "developer" else "#ffffff")
    text = theme.get("textColor", "#e5e7eb" if template_id == "developer" else "#121826")
    radius = theme.get("radius", "16px")

    return f"""
*{{box-sizing:border-box}}
html,body{{margin:0;padding:0}}
:root{{
  --pb-primary:{accent};
  --pb-bg:{bg};
  --pb-text:{text};
  --pb-muted: color-mix(in srgb, var(--pb-text) 62%, transparent);
  --pb-border: color-mix(in srgb, var(--pb-text) 12%, transparent);
  --pb-card: color-mix(in srgb, var(--pb-text) 6%, transparent);
  --pb-radius:{radius};
}}
body{{font-family:{_fonts()};background:var(--pb-bg);color:var(--pb-text);line-height:1.65;-webkit-font-smoothing:antialiased}}
a{{color:inherit;text-decoration:none}}
.pb-container{{width:100%;max-width:1120px;margin:0 auto;padding:0 22px}}
section{{position:relative;padding:64px 0;overflow:hidden}}
.pb-sec-title{{font-size:clamp(1.35rem,2.6vw,2.2rem);line-height:1.18;margin:0 0 18px;font-weight:800;letter-spacing:-.02em}}
.pb-subtitle{{margin:0;color:var(--pb-muted);font-size:clamp(1rem,1.6vw,1.2rem)}}
.pb-grid{{display:grid;grid-template-columns:repeat(12,minmax(0,1fr));gap:16px}}
.pb-reveal{{animation:pbReveal .6s ease both}}
@keyframes pbReveal{{from{{opacity:0;transform:translateY(10px)}}to{{opacity:1;transform:none}}}}
@keyframes pbBeam{{from{{transform:translateX(-120%)}}to{{transform:translateX(120%)}}}}
.pb-btn{{display:inline-flex;align-items:center;justify-content:center;padding:10px 18px;border-radius:12px;border:1px solid transparent;font-weight:700;transition:.25s transform,.25s box-shadow,.25s background,.25s border-color;cursor:pointer}}
.pb-btn:hover{{transform:translateY(-1px)}}
.pb-btn-primary{{background:var(--pb-primary);color:#fff;box-shadow:0 8px 20px color-mix(in srgb,var(--pb-primary) 35%,transparent)}}
.pb-btn-outline{{border-color:var(--pb-border);background:transparent}}
.pb-btn-sm{{padding:7px 12px;font-size:.86rem}}
.pb-tag{{display:inline-flex;align-items:center;padding:4px 10px;border-radius:999px;border:1px solid var(--pb-border);background:var(--pb-card);font-size:.78rem}}
.pb-tag-lg{{padding:7px 14px;font-size:.84rem}}
.pb-hero .pb-container{{position:relative}}
.pb-hero-grid{{display:grid;grid-template-columns:220px 1fr;gap:22px;align-items:center}}
.pb-avatar{{width:184px;height:184px;border-radius:24px;object-fit:cover;border:1px solid var(--pb-border);box-shadow:0 14px 30px color-mix(in srgb,var(--pb-primary) 22%,transparent)}}
.pb-avatar-fallback{{display:flex;align-items:center;justify-content:center;background:var(--pb-card);font-size:42px}}
.pb-title{{margin:0 0 10px;font-size:clamp(2rem,5vw,3.8rem);line-height:1.05;font-weight:900;letter-spacing:-.03em}}
.pb-hero-actions{{margin-top:18px;display:flex;gap:10px;flex-wrap:wrap}}
.pb-hero-links{{margin-top:14px;display:flex;gap:10px;flex-wrap:wrap}}
.pb-hero-links a{{font-size:.9rem;color:var(--pb-muted);border-bottom:1px dashed var(--pb-border)}}
.pb-hero-glow{{position:absolute;inset:auto -30% -140px auto;width:420px;height:420px;pointer-events:none;border-radius:50%;background:radial-gradient(circle,color-mix(in srgb,var(--pb-primary) 35%,transparent) 0%,transparent 70%);filter:blur(35px);opacity:.45}}
.pb-hero-line{{position:absolute;top:0;left:-30%;width:120%;height:1px;background:linear-gradient(90deg,transparent,color-mix(in srgb,var(--pb-primary) 75%,#fff),transparent);opacity:.4;animation:pbBeam 5.2s linear infinite}}
.pb-prose p{{margin:0 0 12px;color:var(--pb-muted)}}
.pb-proj-grid>.pb-proj-card{{grid-column:span 4}}
.pb-proj-card{{display:flex;flex-direction:column;border:1px solid var(--pb-border);border-radius:16px;background:var(--pb-card);overflow:hidden;transition:.3s transform,.3s box-shadow,.3s border-color}}
.pb-proj-card:hover{{transform:translateY(-4px);border-color:color-mix(in srgb,var(--pb-primary) 35%,var(--pb-border));box-shadow:0 16px 34px color-mix(in srgb,var(--pb-primary) 15%,transparent)}}
.pb-proj-cover{{width:100%;aspect-ratio:16/9;object-fit:cover}}
.pb-cover-fallback{{display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,var(--pb-card),color-mix(in srgb,var(--pb-primary) 14%,transparent));font-weight:700}}
.pb-proj-body{{padding:14px 14px 16px;display:flex;flex-direction:column;gap:10px}}
.pb-proj-title{{margin:0;font-size:1.06rem;font-weight:800}}
.pb-proj-desc{{margin:0;color:var(--pb-muted);font-size:.95rem}}
.pb-tags{{display:flex;gap:7px;flex-wrap:wrap}}
.pb-proj-links{{display:flex;gap:8px;flex-wrap:wrap;margin-top:2px}}
.pb-items{{display:flex;flex-direction:column;gap:14px}}
.pb-exp-item,.pb-edu-item{{border:1px solid var(--pb-border);background:var(--pb-card);padding:14px;border-radius:14px}}
.pb-exp-head{{display:flex;justify-content:space-between;gap:8px;align-items:flex-start;flex-wrap:wrap}}
.pb-company{{font-weight:800}}
.pb-role{{margin-left:8px;color:var(--pb-muted)}}
.pb-period{{font-size:.88rem;color:var(--pb-muted)}}
.pb-list{{margin:8px 0 0;padding-left:18px;color:var(--pb-muted)}}
.pb-list li{{margin-bottom:4px}}
.pb-tags-wrap{{display:flex;gap:10px;flex-wrap:wrap}}
.pb-stats-grid{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}}
.pb-stat-item{{padding:14px;border:1px solid var(--pb-border);background:var(--pb-card);border-radius:14px;text-align:center}}
.pb-stat-val{{font-size:1.5rem;font-weight:900;line-height:1.1}}
.pb-stat-label{{margin-top:4px;color:var(--pb-muted);font-size:.9rem}}
.pb-srv-card,.pb-tst-card{{grid-column:span 4;padding:14px;border:1px solid var(--pb-border);background:var(--pb-card);border-radius:14px;transition:.25s transform,.25s border-color}}
.pb-srv-card:hover,.pb-tst-card:hover{{transform:translateY(-2px);border-color:color-mix(in srgb,var(--pb-primary) 35%,var(--pb-border))}}
.pb-tst-text{{margin:0 0 10px;color:var(--pb-muted);font-style:italic}}
.pb-tst-author{{font-size:.9rem;color:var(--pb-muted)}}
.pb-cnt-list{{display:grid;grid-template-columns:1fr 1fr;gap:10px}}
.pb-cnt-item{{display:flex;gap:8px;align-items:center;padding:10px;border:1px solid var(--pb-border);border-radius:12px;background:var(--pb-card)}}
.pb-cnt-label{{color:var(--pb-muted);font-size:.88rem;min-width:74px}}
.pb-cnt-item a{{color:var(--pb-primary);text-decoration:underline dotted}}
.pb-cta-box{{padding:26px;border:1px solid var(--pb-border);background:linear-gradient(120deg,var(--pb-card),color-mix(in srgb,var(--pb-primary) 11%,transparent));border-radius:20px;text-align:center}}
.pb-footer{{padding:28px 0 38px;color:var(--pb-muted);text-align:center;font-size:.9rem}}

/* template skins */
body.pb-template-professional .pb-title{{letter-spacing:-.02em}}
body.pb-template-professional .pb-hero-line{{opacity:.28}}
body.pb-template-professional .pb-btn-primary{{border-radius:10px}}

body.pb-template-developer{{background:radial-gradient(circle at 10% -10%,#1e293b 0%,var(--pb-bg) 55%) fixed}}
body.pb-template-developer .pb-card,body.pb-template-developer .pb-proj-card,body.pb-template-developer .pb-exp-item,body.pb-template-developer .pb-edu-item,body.pb-template-developer .pb-cnt-item{{backdrop-filter:blur(8px)}}
body.pb-template-developer .pb-title{{font-family:ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,monospace}}
body.pb-template-developer .pb-btn-outline{{border-style:dashed}}

body.pb-template-creator .pb-title{{font-size:clamp(2.2rem,6vw,4.3rem)}}
body.pb-template-creator .pb-hero-glow{{opacity:.58}}
body.pb-template-creator .pb-proj-card,.pb-template-creator .pb-srv-card,.pb-template-creator .pb-tst-card{{border-radius:20px}}
body.pb-template-creator .pb-btn-primary{{background:linear-gradient(135deg,var(--pb-primary),color-mix(in srgb,var(--pb-primary) 50%,#fff))}}

body.pb-template-minimal .pb-hero-glow,body.pb-template-minimal .pb-hero-line{{display:none}}
body.pb-template-minimal .pb-card,body.pb-template-minimal .pb-proj-card,body.pb-template-minimal .pb-exp-item,body.pb-template-minimal .pb-edu-item,body.pb-template-minimal .pb-cnt-item{{background:transparent}}
body.pb-template-minimal .pb-btn-primary{{box-shadow:none}}
body.pb-template-minimal .pb-sec-title{{font-weight:700}}
body.pb-template-minimal .pb-proj-card:hover{{transform:none;box-shadow:none}}

@media (max-width:980px){{
  .pb-proj-grid>.pb-proj-card,.pb-srv-card,.pb-tst-card{{grid-column:span 6}}
  .pb-stats-grid{{grid-template-columns:repeat(2,minmax(0,1fr))}}
}}
@media (max-width:760px){{
  section{{padding:48px 0}}
  .pb-hero-grid{{grid-template-columns:1fr}}
  .pb-avatar{{width:124px;height:124px;border-radius:18px}}
  .pb-cnt-list{{grid-template-columns:1fr}}
  .pb-proj-grid>.pb-proj-card,.pb-srv-card,.pb-tst-card{{grid-column:span 12}}
}}
"""


def _normalize_template(site_data, site_config, style):
    template_id = ""
    if isinstance(site_data, dict):
        template_id = site_data.get("template_id") or ""
    if not template_id and isinstance(site_config, dict):
        template_id = site_config.get("template_id") or ""
    if not template_id and style:
        template_id = str(style)
    if template_id in ("professional", "developer", "creator", "minimal"):
        return template_id
    return "professional"


def render_personal_site(site_data, site_config=None, style=None):
    blocks = site_data.get("blocks", []) if isinstance(site_data, dict) else []
    theme = site_data.get("theme", {}) if isinstance(site_data, dict) else {}
    seo = site_data.get("seo", {}) if isinstance(site_data, dict) else {}
    template_id = _normalize_template(site_data or {}, site_config or {}, style)

    if not blocks:
        blocks = [
            {"id": "tmp1", "type": "hero", "visible": True, "content": {"name": "Personal Site", "subtitle": "Build your presence"}},
            {"id": "tmp2", "type": "about", "visible": True, "content": {"text": "No blocks to render yet."}},
        ]

    title = E(seo.get("title") or "Personal Site")
    desc = E(seo.get("description") or "Personal portfolio website")
    og_image = E(seo.get("og_image") or "")

    body = []
    for b in blocks:
        if not isinstance(b, dict):
            continue
        if b.get("visible", True) is False:
            continue
        renderer = BLOCK_RENDERERS.get(b.get("type"))
        if not renderer:
            continue
        try:
            body.append(renderer(b))
        except Exception as ex:
            body.append(f"<!-- block render error {E(b.get('id',''))}: {E(str(ex))} -->")

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
{f'<meta property="og:image" content="{og_image}">' if og_image else ''}
<style>{_base_css(theme, template_id)}</style>
</head>
<body class="pb-template-{template_id}">
{''.join(body)}
</body>
</html>"""


def list_styles():
    return [
        {"id": "professional", "name": "Professional Resume Site", "description": "稳重专业，求职导向", "emoji": "💼"},
        {"id": "developer", "name": "Developer Portfolio", "description": "技术感暗色，项目导向", "emoji": "💻"},
        {"id": "creator", "name": "Personal Brand Page", "description": "创作者品牌与视觉表达", "emoji": "✨"},
        {"id": "minimal", "name": "Minimal Landing Page", "description": "极简留白，信息密度克制", "emoji": "◻️"},
    ]
