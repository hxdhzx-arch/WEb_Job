"""
web_resume_renderer.py — 网页简历渲染引擎
4 套模板：minimal / card / timeline / sidebar
所有输出为纯静态 HTML，零外部依赖（无 Google Fonts / CDN）
"""
import html as _html

# ══════════════════════════════════════
#  工具函数
# ══════════════════════════════════════

def E(text):
    """HTML 转义"""
    if not text:
        return ""
    return _html.escape(str(text))


def _system_fonts():
    return "-apple-system,BlinkMacSystemFont,'PingFang SC','Hiragino Sans GB','Microsoft YaHei','Segoe UI',Roboto,sans-serif"


def _mono_fonts():
    return "'SF Mono','Menlo','Consolas','Courier New',monospace"


def _get_sections(data, config=None):
    """按 config 中定义的顺序和可见性返回 section 列表"""
    default_order = ["intro", "work", "education", "skills", "certs"]
    default_visible = {k: True for k in default_order}
    if config and config.get("sections"):
        order = config["sections"].get("order", default_order)
        visible = config["sections"].get("visible", default_visible)
    else:
        order = default_order
        visible = default_visible
    return [(k, visible.get(k, True)) for k in order]


def _get_theme(config=None):
    defaults = {
        "primaryColor": "#7C3AED",
        "bgColor": "#ffffff",
        "textColor": "#1f2937",
        "secondaryColor": "#6B7280",
        "darkMode": False,
    }
    if config and config.get("theme"):
        defaults.update(config["theme"])
    return defaults


def _contact_items(basic, intent=None):
    items = []
    if basic.get("phone"):
        items.append(E(basic["phone"]))
    if basic.get("email"):
        items.append(E(basic["email"]))
    if basic.get("city"):
        items.append(E(basic["city"]))
    if intent and intent.get("job"):
        items.append(E(intent["job"]))
    if basic.get("years"):
        items.append(E(basic["years"]) + "经验")
    return items


def _skills_list(skills_str):
    if not skills_str:
        return []
    import re
    return [s.strip() for s in re.split(r'[,，、\n]+', skills_str) if s.strip()]


# ══════════════════════════════════════
#  公共 CSS
# ══════════════════════════════════════

def _base_css(theme):
    return f"""
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
html{{font-size:16px;scroll-behavior:smooth}}
body{{
  font-family:{_system_fonts()};
  color:{theme['textColor']};
  background:{theme['bgColor']};
  line-height:1.7;
  -webkit-font-smoothing:antialiased;
  -moz-osx-font-smoothing:grayscale;
}}
a{{color:{theme['primaryColor']};text-decoration:none}}
a:hover{{text-decoration:underline}}
.wr-container{{max-width:780px;margin:0 auto;padding:40px 24px 60px}}
.wr-section{{margin-bottom:32px}}
.wr-section-title{{
  font-size:1.15rem;font-weight:700;
  color:{theme['primaryColor']};
  margin-bottom:14px;
  display:flex;align-items:center;gap:8px;
}}
.wr-text{{color:{theme['secondaryColor']};line-height:1.75}}
.wr-work-item{{margin-bottom:20px}}
.wr-work-header{{display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:4px}}
.wr-work-company{{font-size:1rem;font-weight:700;color:{theme['textColor']}}}
.wr-work-title{{font-size:.92rem;color:{theme['secondaryColor']};margin-left:8px}}
.wr-work-time{{font-size:.82rem;color:#9CA3AF;white-space:nowrap}}
.wr-duty-list{{margin:6px 0 0;padding-left:18px;color:{theme['secondaryColor']}}}
.wr-duty-list li{{margin-bottom:3px;line-height:1.65}}
.wr-edu-item{{margin-bottom:14px}}
.wr-edu-header{{display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap}}
.wr-edu-school{{font-weight:700;color:{theme['textColor']}}}
.wr-edu-detail{{font-size:.9rem;color:{theme['secondaryColor']};margin-top:2px}}
.wr-skill-tags{{display:flex;flex-wrap:wrap;gap:8px}}
.wr-skill-tag{{
  padding:5px 14px;border-radius:6px;font-size:.85rem;font-weight:500;
  background:{theme['primaryColor']}12;color:{theme['primaryColor']};
}}
.wr-footer{{
  margin-top:48px;padding-top:24px;border-top:1px solid #E5E7EB;
  text-align:center;font-size:.78rem;color:#9CA3AF;
}}
.wr-photo{{width:90px;height:108px;object-fit:cover;border-radius:8px;border:2px solid #F3F4F6}}
.wr-dark-toggle{{
  position:fixed;bottom:20px;right:20px;
  width:42px;height:42px;border-radius:50%;border:none;
  background:{theme['primaryColor']};color:#fff;font-size:1.1rem;
  cursor:pointer;box-shadow:0 4px 14px rgba(0,0,0,.15);
  display:flex;align-items:center;justify-content:center;
  transition:all .3s;z-index:100;
}}
.wr-dark-toggle:hover{{transform:scale(1.1)}}
@media(max-width:600px){{
  .wr-container{{padding:24px 16px 40px}}
  .wr-work-header{{flex-direction:column}}
  .wr-photo{{width:70px;height:84px}}
}}
@media print{{
  .wr-dark-toggle,.wr-footer{{display:none}}
  body{{background:#fff!important;color:#1f2937!important}}
}}
"""


def _dark_mode_css():
    return """
body.dark{background:#0B0F19;color:#E2E8F0}
body.dark .wr-work-company,body.dark .wr-edu-school{color:#F1F5F9}
body.dark .wr-text,body.dark .wr-work-title,body.dark .wr-duty-list,
body.dark .wr-edu-detail{color:#94A3B8}
body.dark .wr-work-time{color:#64748B}
body.dark .wr-skill-tag{background:rgba(139,92,246,.15)}
body.dark .wr-footer{border-color:#1E293B;color:#475569}
body.dark .wr-photo{border-color:#334155}
"""


def _interaction_js():
    return """
(function(){
  var toggle=document.getElementById('wr-dark-toggle');
  if(!toggle)return;
  var dark=localStorage.getItem('wr-dark')==='1';
  if(dark)document.body.classList.add('dark');
  toggle.textContent=dark?'☀':'🌙';
  toggle.addEventListener('click',function(){
    dark=!dark;
    document.body.classList.toggle('dark',dark);
    toggle.textContent=dark?'☀':'🌙';
    localStorage.setItem('wr-dark',dark?'1':'0');
  });
})();
"""


# ══════════════════════════════════════
#  Section 渲染器
# ══════════════════════════════════════

def _render_intro(data, theme):
    intro = data.get("intro", "")
    if not intro:
        return ""
    return f'''<section class="wr-section">
<div class="wr-section-title">个人简介</div>
<div class="wr-text">{E(intro)}</div>
</section>'''


def _render_work(data, theme):
    work_list = data.get("work", [])
    items = ""
    for w in work_list:
        if not w.get("company") and not w.get("title"):
            continue
        duties_html = ""
        duties = w.get("duties", [])
        if duties:
            valid = [d for d in duties if d and d.strip()]
            if valid:
                duties_html = '<ul class="wr-duty-list">' + "".join(
                    f"<li>{E(d)}</li>" for d in valid
                ) + '</ul>'
        items += f'''<div class="wr-work-item">
<div class="wr-work-header">
<div><span class="wr-work-company">{E(w.get("company",""))}</span>
<span class="wr-work-title">{E(w.get("title",""))}</span></div>
<span class="wr-work-time">{E(w.get("time",""))}</span>
</div>{duties_html}</div>'''
    if not items:
        return ""
    return f'''<section class="wr-section">
<div class="wr-section-title">工作经历</div>
{items}</section>'''


def _render_education(data, theme):
    edu_list = data.get("education", [])
    items = ""
    for ed in edu_list:
        if not ed.get("school"):
            continue
        detail_parts = [ed.get("major", ""), ed.get("degree", "")]
        detail = " · ".join(p for p in detail_parts if p)
        items += f'''<div class="wr-edu-item">
<div class="wr-edu-header">
<span class="wr-edu-school">{E(ed["school"])}</span>
<span class="wr-work-time">{E(ed.get("time",""))}</span>
</div>
{f'<div class="wr-edu-detail">{E(detail)}</div>' if detail else ""}
</div>'''
    if not items:
        return ""
    return f'''<section class="wr-section">
<div class="wr-section-title">教育背景</div>
{items}</section>'''


def _render_skills(data, theme):
    skills = _skills_list(data.get("skills", ""))
    if not skills:
        return ""
    tags = "".join(f'<span class="wr-skill-tag">{E(s)}</span>' for s in skills)
    return f'''<section class="wr-section">
<div class="wr-section-title">技能特长</div>
<div class="wr-skill-tags">{tags}</div>
</section>'''


def _render_certs(data, theme):
    certs = data.get("certs", "")
    if not certs:
        return ""
    return f'''<section class="wr-section">
<div class="wr-section-title">证书资质</div>
<div class="wr-text">{E(certs)}</div>
</section>'''


SECTION_RENDERERS = {
    "intro": _render_intro,
    "work": _render_work,
    "education": _render_education,
    "skills": _render_skills,
    "certs": _render_certs,
}


def _render_sections(data, config, theme):
    html = ""
    for key, visible in _get_sections(data, config):
        if not visible:
            continue
        renderer = SECTION_RENDERERS.get(key)
        if renderer:
            html += renderer(data, theme)
    return html


# ══════════════════════════════════════
#  模板 1: minimal — 极简白
# ══════════════════════════════════════

def _template_minimal(data, config, theme):
    basic = data.get("basic", {})
    intent = data.get("intent", {})
    contacts = _contact_items(basic, intent)
    photo = ""
    if basic.get("photo"):
        photo = f'<img class="wr-photo" src="{basic["photo"]}" alt="头像">'

    header = f'''<header style="text-align:center;margin-bottom:36px">
{photo}
<h1 style="font-size:2rem;font-weight:800;margin:12px 0 4px;letter-spacing:-.01em">{E(basic.get("name",""))}</h1>
{f'<div style="font-size:1rem;color:{theme["secondaryColor"]};margin-bottom:8px">{E(intent.get("job",""))}</div>' if intent.get("job") else ""}
{f'<div style="font-size:.85rem;color:#9CA3AF">{" · ".join(contacts)}</div>' if contacts else ""}
</header>'''

    css = _base_css(theme) + _dark_mode_css() + """
.wr-section-title{padding-bottom:8px;border-bottom:2px solid """ + theme['primaryColor'] + """;}
"""
    return _wrap_page(data, config, theme, css, header + _render_sections(data, config, theme))


# ══════════════════════════════════════
#  模板 2: card — 卡片式
# ══════════════════════════════════════

def _template_card(data, config, theme):
    basic = data.get("basic", {})
    intent = data.get("intent", {})
    contacts = _contact_items(basic, intent)
    photo = ""
    if basic.get("photo"):
        photo = f'<img class="wr-photo" style="border-radius:50%;width:80px;height:80px" src="{basic["photo"]}" alt="头像">'

    header = f'''<header style="
  background:linear-gradient(135deg,{theme['primaryColor']},#2563EB);
  color:#fff;padding:32px;border-radius:16px;margin-bottom:28px;
  display:flex;align-items:center;gap:20px">
{photo}
<div>
<h1 style="font-size:1.6rem;font-weight:800;margin-bottom:4px">{E(basic.get("name",""))}</h1>
{f'<div style="font-size:.95rem;opacity:.85">{E(intent.get("job",""))}</div>' if intent.get("job") else ""}
{f'<div style="font-size:.82rem;opacity:.65;margin-top:6px">{" | ".join(contacts)}</div>' if contacts else ""}
</div>
</header>'''

    card_css = f"""
.wr-section{{
  background:#fff;border-radius:12px;padding:24px;
  box-shadow:0 1px 6px rgba(0,0,0,.06);border:1px solid #F3F4F6;
}}
body.dark .wr-section{{background:#111827;border-color:#1E293B;box-shadow:0 1px 6px rgba(0,0,0,.2)}}
.wr-section-title{{margin-bottom:16px}}
"""
    css = _base_css(theme) + _dark_mode_css() + card_css
    return _wrap_page(data, config, theme, css, header + _render_sections(data, config, theme))


# ══════════════════════════════════════
#  模板 3: timeline — 时间轴
# ══════════════════════════════════════

def _template_timeline(data, config, theme):
    basic = data.get("basic", {})
    intent = data.get("intent", {})
    contacts = _contact_items(basic, intent)

    header = f'''<header style="margin-bottom:36px;padding-bottom:24px;border-bottom:1px solid #E5E7EB">
<div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:16px">
<div>
<h1 style="font-size:2rem;font-weight:800">{E(basic.get("name",""))}</h1>
{f'<div style="font-size:1rem;color:{theme["primaryColor"]};font-weight:600;margin-top:4px">{E(intent.get("job",""))}</div>' if intent.get("job") else ""}
{f'<div style="font-size:.85rem;color:#9CA3AF;margin-top:8px">{" · ".join(contacts)}</div>' if contacts else ""}
</div>
{f'<img class="wr-photo" src="{basic["photo"]}" alt="头像">' if basic.get("photo") else ""}
</div></header>'''

    tl_css = f"""
.wr-section-title{{position:relative;padding-left:20px}}
.wr-section-title::before{{
  content:'';position:absolute;left:0;top:50%;transform:translateY(-50%);
  width:10px;height:10px;border-radius:50%;
  background:{theme['primaryColor']};
}}
.wr-work-item,.wr-edu-item{{
  position:relative;padding-left:24px;
  border-left:2px solid #E5E7EB;margin-left:4px;
}}
.wr-work-item::before,.wr-edu-item::before{{
  content:'';position:absolute;left:-5px;top:6px;
  width:8px;height:8px;border-radius:50%;
  background:{theme['primaryColor']};
}}
body.dark .wr-work-item,body.dark .wr-edu-item{{border-color:#334155}}
"""
    css = _base_css(theme) + _dark_mode_css() + tl_css
    return _wrap_page(data, config, theme, css, header + _render_sections(data, config, theme))


# ══════════════════════════════════════
#  模板 4: sidebar — 侧边栏
# ══════════════════════════════════════

def _template_sidebar(data, config, theme):
    basic = data.get("basic", {})
    intent = data.get("intent", {})
    skills = _skills_list(data.get("skills", ""))

    # 侧边栏内容
    sidebar_items = ""
    if basic.get("photo"):
        sidebar_items += f'<img src="{basic["photo"]}" style="width:80px;height:80px;border-radius:50%;object-fit:cover;border:2px solid rgba(255,255,255,.2);margin-bottom:16px" alt="头像">'
    sidebar_items += f'<h1 style="font-size:1.3rem;font-weight:800;margin-bottom:4px">{E(basic.get("name",""))}</h1>'
    if intent.get("job"):
        sidebar_items += f'<div style="font-size:.85rem;opacity:.7;margin-bottom:20px">{E(intent["job"])}</div>'

    # 联系方式
    contact_block = ""
    for label, key in [("手机", "phone"), ("邮箱", "email"), ("城市", "city")]:
        if basic.get(key):
            contact_block += f'<div style="margin-bottom:8px"><div style="font-size:.7rem;opacity:.4;text-transform:uppercase;letter-spacing:.08em">{label}</div><div style="font-size:.85rem;opacity:.85">{E(basic[key])}</div></div>'
    if contact_block:
        sidebar_items += f'<div style="margin-bottom:24px;padding-top:16px;border-top:1px solid rgba(255,255,255,.1)">{contact_block}</div>'

    # 技能
    if skills:
        skills_html = "".join(
            f'<div style="font-size:.82rem;opacity:.85;padding:5px 0;border-bottom:1px solid rgba(255,255,255,.06)">{E(s)}</div>'
            for s in skills
        )
        sidebar_items += f'<div><div style="font-size:.7rem;opacity:.4;text-transform:uppercase;letter-spacing:.08em;margin-bottom:8px">技能</div>{skills_html}</div>'

    # 证书
    if data.get("certs"):
        sidebar_items += f'<div style="margin-top:20px"><div style="font-size:.7rem;opacity:.4;text-transform:uppercase;letter-spacing:.08em;margin-bottom:6px">证书</div><div style="font-size:.82rem;opacity:.85">{E(data["certs"])}</div></div>'

    sb_css = f"""
.wr-container{{max-width:100%;padding:0;display:flex;min-height:100vh}}
.wr-sidebar{{
  width:260px;flex-shrink:0;background:{theme['primaryColor']};
  color:#fff;padding:36px 24px;
}}
.wr-main{{flex:1;padding:36px 32px;max-width:640px}}
.wr-section-title{{padding-left:14px;border-left:3px solid {theme['primaryColor']}}}
body.dark .wr-sidebar{{background:#1E293B}}
@media(max-width:700px){{
  .wr-container{{flex-direction:column}}
  .wr-sidebar{{width:100%}}
  .wr-main{{max-width:100%;padding:24px 16px}}
}}
"""
    # sidebar 模板跳过 skills 和 certs（已在侧边栏显示）
    sections_html = ""
    for key, visible in _get_sections(data, config):
        if not visible or key in ("skills", "certs"):
            continue
        renderer = SECTION_RENDERERS.get(key)
        if renderer:
            sections_html += renderer(data, theme)

    body = f'''<div class="wr-container">
<aside class="wr-sidebar">{sidebar_items}</aside>
<main class="wr-main">{sections_html}</main>
</div>'''

    css = _base_css(theme) + _dark_mode_css() + sb_css
    return _wrap_page(data, config, theme, css, body, use_container=False)


# ══════════════════════════════════════
#  页面包装器
# ══════════════════════════════════════

def _wrap_page(data, config, theme, css, body_content, use_container=True):
    basic = data.get("basic", {})
    name = E(basic.get("name", "简历"))
    job = E(data.get("intent", {}).get("job", ""))
    intro = E((data.get("intro", "") or "")[:160])
    title = f"{name}" + (f" — {job}" if job else "") + " 简历"

    show_brand = True
    if config and config.get("meta"):
        show_brand = config["meta"].get("showFooterBrand", True)
        custom_title = config["meta"].get("pageTitle", "")
        if custom_title:
            title = custom_title

    footer = ""
    if show_brand:
        footer = '<footer class="wr-footer">由 <strong>简历 AI</strong> 生成 · 在线简历</footer>'

    main_body = body_content
    if use_container:
        main_body = f'<div class="wr-container">{body_content}{footer}</div>'
    else:
        main_body = body_content + (f'<div style="text-align:center;padding:20px;font-size:.78rem;color:#9CA3AF">{footer}</div>' if footer else "")

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{intro}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{intro}">
<meta name="robots" content="noindex,nofollow">
<style>{css}</style>
</head>
<body>
{main_body}
<button class="wr-dark-toggle" id="wr-dark-toggle" title="切换暗色模式">🌙</button>
<script>{_interaction_js()}</script>
</body>
</html>'''


# ══════════════════════════════════════
#  公开 API
# ══════════════════════════════════════

TEMPLATES = {
    "minimal": _template_minimal,
    "card": _template_card,
    "timeline": _template_timeline,
    "sidebar": _template_sidebar,
}

DEFAULT_TEMPLATE = "card"


def render_resume(resume_data, web_config=None, template=None):
    """
    渲染网页简历 HTML。

    Args:
        resume_data: 简历数据 dict（同编辑器 resumeData 结构）
        web_config: 网页配置 dict（模板/主题/section 顺序）
        template: 模板名 (minimal/card/timeline/sidebar)

    Returns:
        完整 HTML 字符串
    """
    if resume_data and "blocks" in resume_data:
        return _render_blocks_engine(resume_data, web_config)
        
    if not template:
        template = (web_config or {}).get("template", DEFAULT_TEMPLATE)
    if template not in TEMPLATES:
        template = DEFAULT_TEMPLATE

    theme = _get_theme(web_config)
    renderer = TEMPLATES[template]
    return renderer(resume_data, web_config, theme)

# ══════════════════════════════════════
#  NEW BLOCK ENGINE (Canva Style Editor)
# ══════════════════════════════════════
def _render_blocks_engine(resume_data, web_config):
    blocks = resume_data.get("blocks", [])
    theme = (web_config or {}).get("theme", {})
    
    primary = theme.get("primaryColor", "#8B5CF6")
    bg = theme.get("bgColor", "#ffffff")
    text = theme.get("textColor", "#1f2937")
    radius = theme.get("radius", "16px")
    
    css = f"""
    *, *::before, *::after {{ box-sizing: border-box; }}
    :root {{
        --primary: {primary};
        --bg: {bg};
        --text: {text};
        --radius: {radius};
    }}
    body {{ margin:0; padding:0; font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Microsoft YaHei',sans-serif; background:var(--bg); color:var(--text); line-height:1.7; -webkit-font-smoothing:antialiased; }}
    .wr2-container {{ max-width: 860px; margin: 0 auto; padding: 40px 24px 80px; display: flex; flex-direction: column; gap: 24px; }}
    .wr2-block {{ padding: 32px; border-radius: var(--radius); transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1); }}
    .wr2-block-title {{ font-size: 1.35rem; font-weight: 800; color: var(--primary); margin-bottom: 24px; display:flex; align-items:center; letter-spacing: -0.01em; }}
    
    /* Layouts */
    .wr2-layout-center {{ text-align: center; }}
    .wr2-layout-left {{ text-align: left; }}
    .wr2-layout-right {{ text-align: right; }}
    .wr2-layout-center .wr2-item-header {{ justify-content: center; text-align: center; }}
    .wr2-layout-center .wr2-skill-tags {{ justify-content: center; }}
    
    /* Variants */
    .wr2-style-card {{ background: #ffffff; box-shadow: 0 8px 30px rgba(0,0,0,0.04); border: 1px solid rgba(0,0,0,0.05); }}
    .wr2-style-minimal {{ background: transparent; padding-left: 0; padding-right: 0; border-bottom: 1px solid rgba(0,0,0,0.06); border-radius: 0; }}
    .wr2-style-outline {{ background: transparent; border: 2px solid var(--primary); }}
    .wr2-style-solid {{ background: var(--primary); color: #fff; }}
    .wr2-style-solid .wr2-block-title {{ color: #fff; opacity: 0.9; }}
    .wr2-style-solid .wr2-skill-tag {{ background: rgba(0,0,0,0.2); color: #fff; }}
    .wr2-style-solid .wr2-item-subtitle, .wr2-style-solid .wr2-item-time {{ opacity: 0.8; color: #fff; }}
    
    /* Elements */
    .wr2-hero-avatar {{ width: 110px; height: 110px; border-radius: 50%; object-fit: cover; margin-bottom: 20px; border: 4px solid var(--primary); box-shadow: 0 4px 14px rgba(0,0,0,0.1); }}
    .wr2-hero-name {{ font-size: 2.8rem; font-weight: 900; margin-bottom: 8px; line-height: 1.2; letter-spacing: -0.02em; }}
    .wr2-hero-job {{ font-size: 1.15rem; font-weight: 600; opacity: 0.85; margin-bottom: 16px; }}
    .wr2-hero-meta {{ display: flex; gap: 16px; flex-wrap: wrap; font-size: 0.95rem; opacity: 0.7; font-weight: 500; }}
    .wr2-layout-center .wr2-hero-meta {{ justify-content: center; }}
    .wr2-layout-right .wr2-hero-meta {{ justify-content: flex-end; }}
    
    .wr2-item {{ margin-bottom: 24px; }}
    .wr2-item:last-child {{ margin-bottom: 0; }}
    .wr2-item-header {{ display: flex; justify-content: space-between; align-items: baseline; flex-wrap: wrap; margin-bottom: 10px; gap: 8px; }}
    .wr2-item-title {{ font-weight: 800; font-size: 1.1rem; }}
    .wr2-item-subtitle {{ font-size: 0.95rem; font-weight: 600; margin-left:8px; opacity: 0.8; }}
    .wr2-item-time {{ font-size: 0.85rem; font-weight: 600; opacity: 0.5; }}
    .wr2-item-desc {{ list-style-position: outside; margin-left: 20px; padding-left:0; margin-top:0; }}
    .wr2-item-desc li {{ margin-bottom: 6px; font-size: 0.95rem; opacity: 0.85; line-height:1.6; }}
    
    .wr2-skill-tags {{ display: flex; flex-wrap: wrap; gap: 10px; }}
    .wr2-skill-tag {{ padding: 8px 16px; background: rgba(0,0,0,0.04); border-radius: 8px; font-size: 0.9rem; font-weight: 600; color: var(--text); }}
    
    .wr2-intro-text {{ font-size: 1.05rem; line-height: 1.8; opacity: 0.85; white-space: pre-wrap; }}
    
    @media (max-width: 600px) {{
        .wr2-item-header {{ flex-direction: column; align-items: flex-start; gap: 4px; }}
        .wr2-item-subtitle {{ margin-left: 0; display: block; }}
        .wr2-container {{ padding: 20px 16px; gap: 16px; }}
        .wr2-block {{ padding: 24px 20px; }}
        .wr2-hero-name {{ font-size: 2.2rem; }}
    }}
    
    /* Custom Scoped Overrides generated dynamically */
    """
    
    def render_block(b):
        if not b.get("visible", True): return ""
        b_type = b.get("type", "")
        style = b.get("style", {})
        layout = style.get("layout", "left")
        variant = style.get("variant", "minimal")
        c = b.get("content", {})
        title = b.get("title", "")
        
        classes = f"wr2-block wr2-layout-{layout} wr2-style-{variant}"
        title_html = f'<div class="wr2-block-title">{_html.escape(title)}</div>' if title else ""
        content_html = ""
        
        if b_type == "hero":
            avatar_html = f'<img src="{_html.escape(c.get("avatar",""))}" class="wr2-hero-avatar">' if c.get('avatar') else ""
            meta_items = c.get("meta", [])
            meta_html = f'<div class="wr2-hero-meta">' + "".join(f"<span>{_html.escape(m)}</span>" for m in meta_items if m) + "</div>"
            content_html = f'''
                {avatar_html}
                <div class="wr2-hero-name">{_html.escape(c.get("name",""))}</div>
                <div class="wr2-hero-job">{_html.escape(c.get("job",""))}</div>
                {meta_html}
            '''
        elif b_type == "intro":
            content_html = f'{title_html}<div class="wr2-intro-text">{_html.escape(c.get("text",""))}</div>'
            
        elif b_type in ["list_work", "list_edu", "list_projects"]:
            items = c.get("items", [])
            items_html = ""
            for item in items:
                desc_html = ""
                if item.get("desc"):
                    desc_html = '<ul class="wr2-item-desc">' + "".join(f"<li>{_html.escape(d)}</li>" for d in item["desc"] if d) + '</ul>'
                
                items_html += f'''
                <div class="wr2-item">
                    <div class="wr2-item-header">
                        <div>
                            <span class="wr2-item-title">{_html.escape(item.get("title",""))}</span>
                            <span class="wr2-item-subtitle">{_html.escape(item.get("subtitle",""))}</span>
                        </div>
                        <span class="wr2-item-time">{_html.escape(item.get("time",""))}</span>
                    </div>
                    {desc_html}
                </div>
                '''
            content_html = title_html + items_html
            
        elif b_type == "skills":
            tags = c.get("tags", [])
            tags_html = '<div class="wr2-skill-tags">' + "".join(f'<span class="wr2-skill-tag">{_html.escape(t)}</span>' for t in tags if t) + '</div>'
            content_html = title_html + tags_html
            
        elif b_type == "certs":
             content_html = f'{title_html}<div class="wr2-intro-text">{_html.escape(c.get("text",""))}</div>'

        return f'<div class="{classes}" id="wr2-block-{_html.escape(b.get("id",""))}">{content_html}</div>'

    body_html = '<div class="wr2-container">' + "".join(render_block(b) for b in blocks) + '</div>'
    
    page_title = (web_config or {}).get("meta", {}).get("pageTitle", "简历")
    if not page_title:
        # try to find hero block name
        for b in blocks:
            if b.get("type") == "hero" and b.get("content", {}).get("name"):
                page_title = f"{b['content']['name']} 的简历"
                break
    
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{_html.escape(page_title or '网页简历')}</title>
<style>{css}</style>
</head>
<body>
{body_html}
</body>
</html>'''


def list_templates():
    """返回可用模板列表"""
    return [
        {"id": "minimal", "name": "极简白", "description": "大留白、无色块、专注内容"},
        {"id": "card", "name": "卡片式", "description": "圆角卡片、微阴影、分区清晰"},
        {"id": "timeline", "name": "时间轴", "description": "左侧时间线 + 右侧内容"},
        {"id": "sidebar", "name": "侧边栏", "description": "深色侧边信息 + 白色主区"},
    ]
