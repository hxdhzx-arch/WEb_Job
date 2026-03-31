"""
api/personal_site.py — AI 个人网站生成/预览/发布 API
独立于 web_resume，使用 Gemini AI 从提示词生成结构化网站内容
"""
import json
import re
import traceback
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, make_response
from backend.extensions import db
from backend.models.personal_site import PersonalSite
from backend.middleware.auth_required import jwt_required_custom as auth_required
from backend.utils.personal_site_renderer import render_personal_site, list_styles

TEMPLATE_IDS = ("professional", "developer", "creator", "minimal")


GENERATION_PROMPT = '''你是一个顶尖的个人网站设计架构师。

用户给了你一段描述或一段简历原文。你需要将这些信息结构化为一个 Canva 风格的区块化(block-based)个人网站数据 JSON。

要求：
1. 你必须且只能输出 JSON，绝对不能输出任何其他文字、解释或 markdown 代码块。
2. 极其重要：如果用户只给了非常宽泛的要求（比如：“帮我生成一个模板”或完全没给真实信息），你绝对【不能】输出空数据！你必须自动生成一份极其专业、内容丰富、耀眼的**完整虚拟简历数据**（包含优秀的假名、一流工作经历、2-3个出色项目、顶级学府学历、满屏技能等）来填满这个 JSON，模拟真实且高级的 landing page！
3. 你的输出必须是 `{"blocks": [ ... ]}` 的格式。
4. 你可以根据用户的侧重点自由决定选用以下哪些区块（支持任意组合，至少包含 5 个区块）：
   - hero (封面/基本信息：必须包含 name, subtitle, 可以有 cta: {text, url})
   - about (个人简介)
   - stats (数据里程碑，如 "3+ Years", "50+ Projects")
   - experience (工作经历)
   - projects (项目经验，支持 tags, cover, link, github)
   - skills (技能堆栈)
   - education (教育背景)
   - testimonials (他人评价/推荐信)
   - services (提供的服务/接单业务)
   - contact (联系方式，邮箱电话和社交媒体)
   - footer (页脚)

JSON 数据结构示例（不要完美复制，要根据用户输入动态调整数量和内容）：
{
  "blocks": [
    {
      "id": "hero-1",
      "type": "hero",
      "visible": true,
      "style": { "layout": "left", "variant": "card" },
      "content": {
        "name": "姓名",
        "subtitle": "一句话定位，例如：全栈工程师",
        "cta": { "text": "下载简历", "url": "#" }
      }
    },
    {
      "id": "about-1",
      "type": "about",
      "visible": true,
      "style": { "layout": "center", "variant": "minimal" },
      "content": { "text": "我是...专注于..." }
    },
    {
      "id": "services-1",
      "type": "services",
      "title": "我的服务",
      "visible": true,
      "style": { "layout": "grid", "variant": "card" },
      "content": {
        "items": [
          { "title": "Web App 开发", "desc": "为您打造高性能的现代 Web 应用。" },
          { "title": "UI/UX 设计", "desc": "创造让人愉悦的交互体验。" }
        ]
      }
    },
    {
      "id": "stats-1",
      "type": "stats",
      "visible": true,
      "style": { "layout": "grid", "variant": "solid" },
      "content": {
        "items": [
          { "value": "5+", "label": "行业经验(年)" },
          { "value": "50+", "label": "成功项目" }
        ]
      }
    },
    {
      "id": "projects-1",
      "type": "projects",
      "title": "精选项目",
      "visible": true,
      "style": { "layout": "grid", "variant": "card" },
      "content": {
        "items": [
          { "title": "项目名", "desc": "描述", "tags": ["React", "Python"], "link": "", "github": "", "cover": "" }
        ]
      }
    },
    {
      "id": "exp-1",
      "type": "experience",
      "title": "工作经历",
      "visible": true,
      "style": { "layout": "left", "variant": "minimal" },
      "content": {
        "items": [
          { "company": "公司", "role": "职位", "period": "2020-至今", "desc": ["成就1", "成就2"] }
        ]
      }
    },
    {
      "id": "testimonials-1",
      "type": "testimonials",
      "title": "同行评价",
      "visible": true,
      "style": { "layout": "grid", "variant": "card" },
      "content": {
        "items": [
          { "author": "张总", "role": "CEO", "text": "非常出色的开发者..." }
        ]
      }
    },
    {
      "id": "contact-1",
      "type": "contact",
      "title": "联系我",
      "visible": true,
      "style": { "layout": "center", "variant": "card" },
      "content": {
        "email": "hello@example.com", "phone": "13800000000", "wechat": "", "github": "https://github.com", "linkedin": ""
      }
    }
  ]
}

用户提示词：{prompt}

{resume_text_section}
'''


def _parse_ai_response(raw_text):
    """从 AI 输出中提取 JSON"""
    cleaned = raw_text.strip()
    # 去除 markdown 代码块
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # 尝试提取第一个 JSON 对象
        match = re.search(r'\{[\s\S]+\}', cleaned)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
    return None


import uuid

def _get_uuid():
    return uuid.uuid4().hex[:8]

def _fallback_from_text(text, prompt=""):
    """当 AI 失败时，从纯文本构建最基础的 blocks"""
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    name = lines[0] if lines else "未命名"
    # 简单提取邮箱/电话
    email = ""
    phone = ""
    for l in lines:
        if not email:
            m = re.search(r'[\w.-]+@[\w.-]+\.\w+', l)
            if m:
                email = m.group()
        if not phone:
            m = re.search(r'1[3-9]\d{9}', l)
            if m:
                phone = m.group()

    return {
        "blocks": [
            {
                "id": _get_uuid(), "type": "hero", "visible": True, "style": {"layout":"left", "variant":"card"},
                "content": {"name": name, "subtitle": prompt[:60] if prompt else "期待在新舞台发光"}
            },
            {
                "id": _get_uuid(), "type": "about", "visible": True, "style": {"layout":"center", "variant":"minimal"},
                "content": {"text": "\n".join(lines[1:4]) if len(lines) > 1 else "这是一段默认的简介文本..."}
            },
            {
                "id": _get_uuid(), "type": "contact", "visible": True, "style": {"layout":"center", "variant":"card"},
                "content": {"email": email, "phone": phone}
            },
            {
                "id": _get_uuid(), "type": "cta", "visible": True, "style": {"layout":"center", "variant":"solid"},
                "content": {"title": "欢迎联系合作", "desc": "若您在寻找靠谱伙伴，我很乐意交流。", "button_text": "发送邮件", "button_url": f"mailto:{email}" if email else "#"}
            },
            {"id": _get_uuid(), "type": "footer", "visible": True, "style": {"layout":"center", "variant":"minimal"}, "content": {"text": "© 2026 Personal Site"}}
        ],
        "template_id": "professional"
    }


def _convert_resume_data(resume_data):
    """将编辑器格式 resumeData 转换为 blocks"""
    basic = resume_data.get("basic", {})
    intent = resume_data.get("intent", {})
    
    blocks = []
    
    # Hero
    blocks.append({
        "id": _get_uuid(), "type": "hero", "visible": True, "style": {"layout":"left", "variant":"card"},
        "content": {"name": basic.get("name", "Name"), "subtitle": intent.get("job", "")}
    })
    
    # Intro
    if resume_data.get("intro"):
        blocks.append({
            "id": _get_uuid(), "type": "about", "visible": True, "style": {"layout":"center", "variant":"minimal"},
            "content": {"text": resume_data.get("intro", "")}
        })
        
    # Work
    work = resume_data.get("work", [])
    if work:
        items = []
        for w in work:
            if w.get("company") or w.get("title"):
                items.append({
                    "company": w.get("company", ""),
                    "role": w.get("title", ""),
                    "period": w.get("time", ""),
                    "desc": w.get("duties", [])
                })
        if items:
            blocks.append({
                "id": _get_uuid(), "type": "experience", "title": "工作经历", "visible": True,
                "style": {"layout":"left", "variant":"card"},
                "content": {"items": items}
            })

    # Education
    edu = resume_data.get("education", [])
    if edu:
        items = []
        for ed in edu:
            if ed.get("school"):
                items.append({
                    "school": ed["school"],
                    "degree": " · ".join(filter(None, [ed.get("degree"), ed.get("major")])),
                    "period": ed.get("time", ""),
                })
        if items:
            blocks.append({
                "id": _get_uuid(), "type": "education", "title": "教育背景", "visible": True,
                "style": {"layout":"left", "variant":"minimal"},
                "content": {"items": items}
            })
            
    # Skills
    skills_raw = resume_data.get("skills", "")
    if skills_raw:
        items = [s.strip() for s in re.split(r'[,，、\n]+', skills_raw) if s.strip()]
        if items:
            blocks.append({
                "id": _get_uuid(), "type": "skills", "title": "技能专长", "visible": True,
                "style": {"layout":"left", "variant":"card"},
                "content": {"items": items}
            })
            
    # Contact
    if basic.get("email") or basic.get("phone"):
        blocks.append({
            "id": _get_uuid(), "type": "contact", "title": "联系方式", "visible": True,
            "style": {"layout":"center", "variant":"card"},
            "content": {"email": basic.get("email", ""), "phone": basic.get("phone", "")}
        })

    if not any((b.get("type") == "cta" for b in blocks)):
        blocks.append({
            "id": _get_uuid(), "type": "cta", "visible": True, "style": {"layout": "center", "variant": "solid"},
            "content": {"title": "期待进一步沟通", "desc": "欢迎联系我获取完整简历与项目细节。", "button_text": "立即联系", "button_url": "#"}
        })
    if not any((b.get("type") == "footer" for b in blocks)):
        blocks.append({
            "id": _get_uuid(), "type": "footer", "visible": True, "style": {"layout": "center", "variant": "minimal"},
            "content": {"text": "© 2026 Personal Site"}
        })
    return {"blocks": blocks, "template_id": "professional"}


def _default_theme(template_id):
    mapping = {
        "professional": {"primaryColor": "#2563eb", "bgColor": "#f8fafc", "textColor": "#0f172a", "radius": "14px"},
        "developer": {"primaryColor": "#22d3ee", "bgColor": "#0b1020", "textColor": "#e5e7eb", "radius": "14px"},
        "creator": {"primaryColor": "#a855f7", "bgColor": "#fff7ff", "textColor": "#1f1630", "radius": "18px"},
        "minimal": {"primaryColor": "#111827", "bgColor": "#ffffff", "textColor": "#111827", "radius": "10px"},
    }
    return mapping.get(template_id, mapping["professional"])


def _preset_site_data(template_id):
    tid = template_id if template_id in TEMPLATE_IDS else "professional"
    if tid == "developer":
        return {
            "template_id": tid,
            "theme": _default_theme(tid),
            "seo": {"title": "Dev Portfolio", "description": "Developer portfolio and engineering work"},
            "blocks": [
                {"id": _get_uuid(), "type": "hero", "visible": True, "style": {"layout": "left", "variant": "card"}, "content": {"name": "Alex Chen", "subtitle": "Full-stack Engineer | Building reliable products", "cta": {"text": "View Projects", "url": "#block-projects"}, "github": "https://github.com/example", "linkedin": "https://linkedin.com/in/example"}},
                {"id": _get_uuid(), "type": "about", "visible": True, "title": "About", "style": {"layout": "left", "variant": "minimal"}, "content": {"text": "I design and ship product-grade systems across frontend, backend and cloud.\nI care about maintainability, measurable impact and engineering excellence."}},
                {"id": _get_uuid(), "type": "projects", "visible": True, "title": "Featured Projects", "style": {"layout": "grid", "variant": "card"}, "content": {"items": [
                    {"title": "Realtime Analytics Platform", "desc": "Built streaming dashboards with sub-second updates for 2k+ concurrent users.", "tags": ["TypeScript", "Flask", "Redis"], "link": "https://example.com", "github": "https://github.com/example/realtime", "cover": ""},
                    {"title": "Infra Cost Optimizer", "desc": "Cut cloud spend by 31% with autoscaling policy engine and workload profiling.", "tags": ["Python", "K8s", "AWS"], "link": "", "github": "https://github.com/example/optimizer", "cover": ""},
                    {"title": "Design System Toolkit", "desc": "Unified product UI primitives and reduced feature delivery time by 40%.", "tags": ["Vanilla JS", "CSS"], "link": "", "github": "https://github.com/example/design-system", "cover": ""}
                ]}},
                {"id": _get_uuid(), "type": "skills", "visible": True, "title": "Tech Stack", "style": {"layout": "left", "variant": "card"}, "content": {"items": ["Python", "Flask", "JavaScript", "SQL", "PostgreSQL", "Redis", "Docker", "CI/CD"]}},
                {"id": _get_uuid(), "type": "experience", "visible": True, "title": "Experience", "style": {"layout": "left", "variant": "card"}, "content": {"items": [
                    {"company": "Nova Labs", "role": "Senior Engineer", "period": "2022 - Now", "desc": ["Led architecture refactor for mission-critical B2B platform.", "Reduced p95 API latency from 820ms to 280ms."]},
                    {"company": "Blue Orbit", "role": "Backend Engineer", "period": "2020 - 2022", "desc": ["Built multi-tenant API services and observability stack.", "Shipped role-based permission system for enterprise clients."]}
                ]}},
                {"id": _get_uuid(), "type": "education", "visible": True, "title": "Education", "style": {"layout": "left", "variant": "minimal"}, "content": {"items": [{"school": "Zhejiang University", "degree": "B.Eng. Software Engineering", "period": "2016 - 2020"}]}},
                {"id": _get_uuid(), "type": "contact", "visible": True, "title": "Contact", "style": {"layout": "left", "variant": "card"}, "content": {"email": "alex@example.com", "github": "github.com/example", "linkedin": "linkedin.com/in/example"}},
                {"id": _get_uuid(), "type": "cta", "visible": True, "style": {"layout": "center", "variant": "solid"}, "content": {"title": "Need an engineer who ships?", "desc": "Let's discuss your product roadmap and delivery plan.", "button_text": "Start a Conversation", "button_url": "mailto:alex@example.com"}},
                {"id": _get_uuid(), "type": "footer", "visible": True, "style": {"layout": "center", "variant": "minimal"}, "content": {"text": "© 2026 Alex Chen. Built with intention."}},
            ],
        }
    if tid == "creator":
        return {
            "template_id": tid,
            "theme": _default_theme(tid),
            "seo": {"title": "Creator Brand Page", "description": "Personal brand and creator profile"},
            "blocks": [
                {"id": _get_uuid(), "type": "hero", "visible": True, "style": {"layout": "center", "variant": "card"}, "content": {"name": "Mia Lin", "subtitle": "Content Creator · Visual Storyteller · Brand Strategist", "cta": {"text": "See My Work", "url": "#block-projects"}}},
                {"id": _get_uuid(), "type": "about", "visible": True, "title": "My Story", "style": {"layout": "center", "variant": "minimal"}, "content": {"text": "I create narrative-driven digital content for tech, lifestyle and education brands.\nFrom concept to campaign, I focus on authentic storytelling and conversion impact."}},
                {"id": _get_uuid(), "type": "projects", "visible": True, "title": "Campaign Highlights", "style": {"layout": "grid", "variant": "card"}, "content": {"items": [
                    {"title": "Brand Film: Future Home", "desc": "Directed short-form campaign that reached 2.1M views and 8.9% engagement.", "tags": ["Branding", "Video", "Motion"], "link": "https://example.com", "github": "", "cover": ""},
                    {"title": "Creator Collab Series", "desc": "Built cross-platform creator collaboration with 12 partners in 6 weeks.", "tags": ["Social", "Strategy"], "link": "https://example.com", "github": "", "cover": ""},
                    {"title": "Community Challenge", "desc": "User-generated challenge campaign with 14k submissions.", "tags": ["Community", "Growth"], "link": "", "github": "", "cover": ""}
                ]}},
                {"id": _get_uuid(), "type": "services", "visible": True, "title": "What I Offer", "style": {"layout": "grid", "variant": "card"}, "content": {"items": [
                    {"title": "Creative Direction", "desc": "Campaign concepts with strong narrative architecture."},
                    {"title": "Content Production", "desc": "Script, shooting and post for short-form channels."},
                    {"title": "Brand Strategy", "desc": "Positioning and message systems for long-term growth."}
                ]}},
                {"id": _get_uuid(), "type": "testimonials", "visible": True, "title": "Client Voices", "style": {"layout": "grid", "variant": "card"}, "content": {"items": [
                    {"author": "Lena", "role": "Marketing Director", "text": "Mia transformed our campaign from generic to memorable."},
                    {"author": "Kevin", "role": "Startup Founder", "text": "Sharp storytelling and disciplined execution."}
                ]}},
                {"id": _get_uuid(), "type": "contact", "visible": True, "title": "Let's Collaborate", "style": {"layout": "center", "variant": "card"}, "content": {"email": "mia@example.com", "linkedin": "linkedin.com/in/mia", "wechat": "MiaStudio"}},
                {"id": _get_uuid(), "type": "cta", "visible": True, "style": {"layout": "center", "variant": "solid"}, "content": {"title": "Ready to elevate your brand?", "desc": "Tell me your campaign goal and timeline.", "button_text": "Book a Briefing", "button_url": "mailto:mia@example.com"}},
                {"id": _get_uuid(), "type": "footer", "visible": True, "style": {"layout": "center", "variant": "minimal"}, "content": {"text": "© 2026 Mia Lin Brand Studio"}},
            ],
        }
    if tid == "minimal":
        return {
            "template_id": tid,
            "theme": _default_theme(tid),
            "seo": {"title": "Minimal Landing", "description": "Minimal single-page personal site"},
            "blocks": [
                {"id": _get_uuid(), "type": "hero", "visible": True, "style": {"layout": "left", "variant": "minimal"}, "content": {"name": "Jordan Wu", "subtitle": "Product Designer & Frontend Partner", "cta": {"text": "Contact Me", "url": "mailto:jordan@example.com"}}},
                {"id": _get_uuid(), "type": "about", "visible": True, "title": "Focus", "style": {"layout": "left", "variant": "minimal"}, "content": {"text": "Designing clean interfaces and building practical web products.\nI work best with teams who value clarity, speed and quality."}},
                {"id": _get_uuid(), "type": "projects", "visible": True, "title": "Selected Work", "style": {"layout": "grid", "variant": "minimal"}, "content": {"items": [
                    {"title": "Fintech Onboarding", "desc": "Redesigned onboarding flow and improved activation by 22%.", "tags": ["UX", "Experiment"], "link": "", "github": "", "cover": ""},
                    {"title": "Internal Ops Portal", "desc": "Shipped lightweight operational dashboard for distributed teams.", "tags": ["Design", "Frontend"], "link": "", "github": "", "cover": ""}
                ]}},
                {"id": _get_uuid(), "type": "contact", "visible": True, "title": "Contact", "style": {"layout": "left", "variant": "minimal"}, "content": {"email": "jordan@example.com", "linkedin": "linkedin.com/in/jordan"}},
                {"id": _get_uuid(), "type": "cta", "visible": True, "style": {"layout": "center", "variant": "minimal"}, "content": {"title": "Open for selected projects", "desc": "Available for freelance and product design collaboration.", "button_text": "Send Email", "button_url": "mailto:jordan@example.com"}},
                {"id": _get_uuid(), "type": "footer", "visible": True, "style": {"layout": "center", "variant": "minimal"}, "content": {"text": "© 2026 Jordan Wu"}},
            ],
        }
    # professional
    return {
        "template_id": "professional",
        "theme": _default_theme("professional"),
        "seo": {"title": "Professional Resume Site", "description": "Professional profile for job opportunities"},
        "blocks": [
            {"id": _get_uuid(), "type": "hero", "visible": True, "style": {"layout": "left", "variant": "card"}, "content": {"name": "Ethan Zhang", "subtitle": "Senior Product Manager | AI & SaaS", "cta": {"text": "View Resume", "url": "#block-experience"}, "linkedin": "https://linkedin.com/in/example"}},
            {"id": _get_uuid(), "type": "about", "visible": True, "title": "Professional Summary", "style": {"layout": "left", "variant": "minimal"}, "content": {"text": "8+ years in B2B SaaS and AI products.\nSkilled at zero-to-one execution, cross-functional alignment and growth-driven roadmap design."}},
            {"id": _get_uuid(), "type": "experience", "visible": True, "title": "Experience", "style": {"layout": "left", "variant": "card"}, "content": {"items": [
                {"company": "Nebula Tech", "role": "Senior Product Manager", "period": "2021 - Present", "desc": ["Led AI workflow suite from 0 to $2.4M ARR in 14 months.", "Improved enterprise retention by 18% through onboarding redesign."]},
                {"company": "Orbit Cloud", "role": "Product Manager", "period": "2018 - 2021", "desc": ["Owned analytics platform roadmap for 300+ clients.", "Launched pricing revamp and lifted expansion revenue by 27%."]}
            ]}},
            {"id": _get_uuid(), "type": "projects", "visible": True, "title": "Selected Cases", "style": {"layout": "grid", "variant": "card"}, "content": {"items": [
                {"title": "AI Copilot for Sales Teams", "desc": "Designed AI-assisted sales workspace with task automation and insights.", "tags": ["AI", "Product"], "link": "https://example.com", "github": "", "cover": ""},
                {"title": "Metrics Command Center", "desc": "Built executive dashboard system for KPI governance and decision speed.", "tags": ["Analytics", "SaaS"], "link": "", "github": "", "cover": ""}
            ]}},
            {"id": _get_uuid(), "type": "skills", "visible": True, "title": "Core Skills", "style": {"layout": "left", "variant": "card"}, "content": {"items": ["Product Strategy", "Roadmapping", "Data Analysis", "A/B Testing", "Stakeholder Management", "AI Product Design"]}},
            {"id": _get_uuid(), "type": "education", "visible": True, "title": "Education", "style": {"layout": "left", "variant": "minimal"}, "content": {"items": [{"school": "Fudan University", "degree": "MSc Management", "period": "2015 - 2018"}]}},
            {"id": _get_uuid(), "type": "contact", "visible": True, "title": "Contact", "style": {"layout": "left", "variant": "card"}, "content": {"email": "ethan@example.com", "linkedin": "linkedin.com/in/example"}},
            {"id": _get_uuid(), "type": "cta", "visible": True, "style": {"layout": "center", "variant": "solid"}, "content": {"title": "Open to leadership opportunities", "desc": "Let's discuss how I can contribute to your product goals.", "button_text": "Contact Me", "button_url": "mailto:ethan@example.com"}},
            {"id": _get_uuid(), "type": "footer", "visible": True, "style": {"layout": "center", "variant": "minimal"}, "content": {"text": "© 2026 Ethan Zhang"}},
        ],
    }


def create_personal_site_bp():
    bp = Blueprint("personal_site", __name__)

    # ── 风格列表 ──
    @bp.route("/personal-site/styles", methods=["GET"])
    def get_styles():
        return jsonify({"success": True, "data": list_styles()})

    @bp.route("/personal-site/presets", methods=["GET"])
    def get_presets():
        presets = []
        for tid in TEMPLATE_IDS:
            d = _preset_site_data(tid)
            presets.append({"id": tid, "name": [s["name"] for s in list_styles() if s["id"] == tid][0], "site_data": d})
        return jsonify({"success": True, "data": presets})

    # ── AI 生成 ──
    @bp.route("/personal-site/generate", methods=["POST"])
    def generate_site():
        """从提示词 + 可选上传内容生成个人网站数据"""
        prompt = ""
        resume_text = ""
        avatar_b64 = ""

        # 支持 JSON 和 FormData 两种提交
        if request.content_type and "multipart" in request.content_type:
            prompt = request.form.get("prompt", "")
            resume_text = request.form.get("resume_text", "")
            # PDF 上传
            pdf_file = request.files.get("pdf")
            if pdf_file:
                try:
                    import fitz
                    pdf_bytes = pdf_file.read()
                    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                    for page in doc:
                        resume_text += page.get_text()
                    doc.close()
                except Exception as e:
                    print(f"[personal-site] PDF 解析失败: {e}")
            # 头像上传
            avatar_file = request.files.get("avatar")
            if avatar_file:
                import base64
                raw = avatar_file.read()
                mime = avatar_file.content_type or "image/jpeg"
                avatar_b64 = f"data:{mime};base64,{base64.b64encode(raw).decode()}"
            # resume JSON
            resume_json = request.form.get("resume_json", "")
            preset_id = request.form.get("preset_id", "").strip()
            if preset_id in TEMPLATE_IDS:
                return jsonify({"success": True, "data": {"site_data": _preset_site_data(preset_id), "source": "preset"}})
            if resume_json:
                try:
                    rd = json.loads(resume_json)
                    site_data = _convert_resume_data(rd.get("resumeData", rd))
                    if avatar_b64:
                        for b in site_data.get("blocks", []):
                            if b.get("type") == "hero":
                                b.setdefault("content", {})["avatar"] = avatar_b64
                                break
                    return jsonify({"success": True, "data": {"site_data": site_data, "source": "resume_convert"}})
                except Exception:
                    pass
        else:
            data = request.get_json() or {}
            prompt = data.get("prompt", "")
            resume_text = data.get("resume_text", "")
            preset_id = str(data.get("preset_id", "")).strip()
            if preset_id in TEMPLATE_IDS:
                return jsonify({"success": True, "data": {"site_data": _preset_site_data(preset_id), "source": "preset"}})
            # 如果前端传来已有的 resumeData，直接转换
            resume_data = data.get("resume_data")
            if resume_data:
                site_data = _convert_resume_data(resume_data)
                return jsonify({"success": True, "data": {"site_data": site_data, "source": "resume_convert"}})

        if not prompt and not resume_text:
            return jsonify({"success": False, "message": "请输入提示词或上传简历"}), 400

        # 构建 AI prompt
        resume_section = ""
        if resume_text:
            resume_section = f"简历原文（请从中提取信息）：\n{resume_text[:5000]}"

        full_prompt = GENERATION_PROMPT.replace("{prompt}", prompt or "生成一个专业个人网站").replace("{resume_text_section}", resume_section)

        try:
            from services.gemini_client import call_gemini
            raw = call_gemini(full_prompt)
            site_data = _parse_ai_response(raw)
            if not site_data or "blocks" not in site_data:
                raise ValueError("AI 返回格式不正确")
            if site_data.get("template_id") not in TEMPLATE_IDS:
                site_data["template_id"] = "professional"
            site_data.setdefault("theme", _default_theme(site_data["template_id"]))
            site_data.setdefault("seo", {})
            # 注入头像
            if avatar_b64:
                for b in site_data["blocks"]:
                    if b.get("type") == "hero":
                        b.setdefault("content", {})["avatar"] = avatar_b64
                        break
            return jsonify({"success": True, "data": {"site_data": site_data, "source": "ai"}})
        except Exception as e:
            print(f"[personal-site] AI 生成失败: {e}")
            traceback.print_exc()
            # 回退方案
            if resume_text:
                site_data = _fallback_from_text(resume_text, prompt)
            else:
                site_data = _preset_site_data("professional")
            if avatar_b64:
                for b in site_data["blocks"]:
                    if b.get("type") == "hero":
                        b.setdefault("content", {})["avatar"] = avatar_b64
                        break
            return jsonify({
                "success": True,
                "data": {"site_data": site_data, "source": "fallback"},
                "warning": f"AI 生成失败，已使用默认模板: {str(e)[:100]}"
            })

    # ── 预览（无需登录） ──
    @bp.route("/personal-site/preview", methods=["POST"])
    def preview_site():
        data = request.get_json()
        if not data or not data.get("site_data"):
            return jsonify({"success": False, "message": "缺少数据"}), 400
        try:
            html = render_personal_site(
                data["site_data"],
                data.get("site_config"),
                data.get("style"),
            )
            return jsonify({"success": True, "data": {"html": html}})
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

    # ── 发布 ──
    @bp.route("/personal-site/publish", methods=["POST"])
    @auth_required()
    def publish_site(current_user):
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "缺少数据"}), 400

        site_id = data.get("site_id")
        site_data = data.get("site_data", {})
        site_config = data.get("site_config", {})
        prompt = data.get("prompt", "")

        if site_id:
            site = PersonalSite.query.filter_by(id=site_id, user_id=current_user.id).first()
            if not site:
                return jsonify({"success": False, "message": "网站不存在"}), 404
            site.site_data = site_data
            site.site_config = site_config
            if prompt:
                site.prompt = prompt
        else:
            name = ""
            try:
                for b in site_data.get("blocks", []):
                    if b.get("type") == "hero":
                        name = b.get("content", {}).get("name", "")
                        break
            except Exception:
                pass
            site = PersonalSite(
                user_id=current_user.id,
                title=f"{name or '未命名'}的个人网站",
                prompt=prompt,
                site_data=site_data,
                site_config=site_config,
            )
            # 保存头像
            avatar = ""
            try:
                for b in site_data.get("blocks", []):
                    if b.get("type") == "hero":
                        avatar = b.get("content", {}).get("avatar", "")
                        break
            except Exception:
                pass
            if avatar and avatar.startswith("data:"):
                site.avatar_data = avatar
            db.session.add(site)
            db.session.flush()

        if "slug" in data and data["slug"]:
            site.slug = data["slug"]
        elif not site.slug:
            site.generate_slug()

        if "seo_title" in data:
            site.seo_title = data["seo_title"]
        if "seo_description" in data:
            site.seo_description = data["seo_description"]

        site.is_published = True
        site.published_at = datetime.now(timezone.utc)
        db.session.commit()

        return jsonify({
            "success": True,
            "data": {
                "site_id": site.id,
                "slug": site.slug,
                "url": f"/site/{site.slug}",
                "published_at": site.published_at.isoformat(),
            }
        })

    # ── 获取已保存的站点 ──
    @bp.route("/personal-site/<int:site_id>", methods=["GET"])
    @auth_required()
    def get_site(current_user, site_id):
        site = PersonalSite.query.filter_by(id=site_id, user_id=current_user.id).first()
        if not site:
            return jsonify({"success": False, "message": "不存在"}), 404
        return jsonify({"success": True, "data": site.to_dict(include_content=True)})

    # ── 自动保存 (Auto Save) ──
    @bp.route("/personal-site/auto-save", methods=["POST"])
    @auth_required()
    def auto_save_site(current_user):
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "缺少数据"}), 400

        site_id = data.get("site_id")
        site_data = data.get("site_data", {})
        
        name = "未命名"
        try:
            for b in site_data.get("blocks", []):
                if b.get("type") == "hero":
                    name = b.get("content", {}).get("name", "未命名")
                    break
        except Exception:
            pass

        if site_id:
            site = PersonalSite.query.filter_by(id=site_id, user_id=current_user.id).first()
            if not site:
                return jsonify({"success": False, "message": "网站不存在"}), 404
        else:
            site = PersonalSite(user_id=current_user.id)
            db.session.add(site)

        site.title = f"{name}的个人网站"
        site.prompt = data.get("prompt", "")
        if "site_data" in data:
            site.site_data = site_data
        if "site_config" in data:
            site.site_config = data.get("site_config")
        avatar = ""
        try:
            for b in site_data.get("blocks", []):
                if b.get("type") == "hero":
                    avatar = b.get("content", {}).get("avatar", "")
                    break
        except Exception:
            pass
        if avatar and avatar.startswith("data:"):
            site.avatar_data = avatar
            
        db.session.commit()
        return jsonify({"success": True, "data": {"site_id": site.id}})

    # ── 更新 ──
    @bp.route("/personal-site/<int:site_id>", methods=["PUT"])
    @auth_required()
    def update_site(current_user, site_id):
        site = PersonalSite.query.filter_by(id=site_id, user_id=current_user.id).first()
        if not site:
            return jsonify({"success": False, "message": "不存在"}), 404
        data = request.get_json() or {}
        if "site_data" in data:
            site.site_data = data["site_data"]
        if "site_config" in data:
            site.site_config = data["site_config"]
        if "title" in data:
            site.title = data["title"]
        db.session.commit()
        return jsonify({"success": True, "message": "已更新"})

    # ── 取消发布 ──
    @bp.route("/personal-site/unpublish/<int:site_id>", methods=["DELETE"])
    @auth_required()
    def unpublish_site(current_user, site_id):
        site = PersonalSite.query.filter_by(id=site_id, user_id=current_user.id).first()
        if not site:
            return jsonify({"success": False, "message": "不存在"}), 404
        site.is_published = False
        db.session.commit()
        return jsonify({"success": True, "message": "已取消发布"})

    # ── 导出 HTML ──
    @bp.route("/personal-site/export-html", methods=["POST"])
    def export_html():
        data = request.get_json()
        if not data or not data.get("site_data"):
            return jsonify({"success": False, "message": "缺少数据"}), 400
        try:
            html = render_personal_site(data["site_data"], data.get("site_config"), data.get("style"))
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500

        name = "personal_site"
        try:
            for b in data.get("site_data", {}).get("blocks", []):
                if b.get("type") == "hero":
                    name = b.get("content", {}).get("name", "site")
                    break
        except Exception:
            pass

        resp = make_response(html)
        resp.headers["Content-Type"] = "text/html; charset=utf-8"
        resp.headers["Content-Disposition"] = f'attachment; filename="{name}_site.html"'
        return resp

    return bp
