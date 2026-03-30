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


# ── AI 生成提示词 ──────────────────────────────
GENERATION_PROMPT = '''你是一个个人网站内容生成专家。

用户给了你一段描述或一段简历原文。你需要将这些信息结构化为一个个人网站数据 JSON。

要求：
1. 你必须且只能输出 JSON，不要输出任何其他文字、解释或 markdown 代码块。
2. 极其重要：如果用户仅仅给出了非常宽泛的要求（比如：“帮我生成一个模板”或完全没有提供真实信息），你绝对【不能】输出空数据或省略字段！你必须根据用户描述的侧重点，自动生成一份极其专业、内容丰富、耀眼的**完整虚拟简历数据**（包含优秀的假名、假邮箱、2-3段一流工作经历、2-3个出色项目、顶级学府学历、满屏技能等）来填满这个 JSON。这样在没有任何简历的情况下，用户能直接看到一张如同 Canva 完美演示样板那样的炫酷个人网站。
3. 如果用户提供了真实的简历，就必须严格提取和美化真实信息。
4. projects.tags 和 skills 可以被处理为字符串数组。experience.description 用纯文本的换行符 \n 分隔多条成就。

JSON 格式：
{
  "hero": {
    "name": "姓名",
    "tagline": "一句话介绍（职位/个人定位）"
  },
  "about": "个人简介（2-4句话描述，专业、有吸引力）",
  "experience": [
    {
      "company": "公司名",
      "role": "职位",
      "period": "时间段",
      "description": "成就1\\n成就2\\n成就3"
    }
  ],
  "projects": [
    {
      "name": "项目名",
      "description": "项目描述（1-2句话）",
      "tags": ["技术标签1", "技术标签2"],
      "link": ""
    }
  ],
  "education": [
    {
      "school": "学校",
      "degree": "学历",
      "major": "专业",
      "period": "时间段"
    }
  ],
  "skills": [
    {
      "category": "分类名",
      "items": ["技能1", "技能2", "技能3"]
    }
  ],
  "contact": {
    "email": "",
    "phone": "",
    "github": "",
    "linkedin": "",
    "website": "",
    "wechat": ""
  }
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


def _fallback_from_text(text, prompt=""):
    """当 AI 失败时，从纯文本构建最基础的 site_data"""
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
        "hero": {"name": name, "tagline": prompt[:60] if prompt else ""},
        "about": "\n".join(lines[1:4]) if len(lines) > 1 else "",
        "experience": [],
        "projects": [],
        "education": [],
        "skills": [],
        "contact": {"email": email, "phone": phone},
    }


def _convert_resume_data(resume_data):
    """将编辑器格式 resumeData 转换为 site_data"""
    basic = resume_data.get("basic", {})
    intent = resume_data.get("intent", {})
    experience = []
    for w in resume_data.get("work", []):
        if w.get("company") or w.get("title"):
            experience.append({
                "company": w.get("company", ""),
                "role": w.get("title", ""),
                "period": w.get("time", ""),
                "description": "\n".join(w.get("duties", [])),
            })
    education = []
    for ed in resume_data.get("education", []):
        if ed.get("school"):
            education.append({
                "school": ed["school"],
                "degree": ed.get("degree", ""),
                "major": ed.get("major", ""),
                "period": ed.get("time", ""),
            })
    skills_raw = resume_data.get("skills", "")
    skills = []
    if skills_raw:
        items = [s.strip() for s in re.split(r'[,，、\n]+', skills_raw) if s.strip()]
        if items:
            skills = items  # 简单列表

    return {
        "hero": {
            "name": basic.get("name", ""),
            "tagline": intent.get("job", ""),
        },
        "about": resume_data.get("intro", ""),
        "experience": experience,
        "projects": [],
        "education": education,
        "skills": skills,
        "contact": {
            "email": basic.get("email", ""),
            "phone": basic.get("phone", ""),
        },
    }


def create_personal_site_bp():
    bp = Blueprint("personal_site", __name__)

    # ── 风格列表 ──
    @bp.route("/personal-site/styles", methods=["GET"])
    def get_styles():
        return jsonify({"success": True, "data": list_styles()})

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
            if resume_json:
                try:
                    rd = json.loads(resume_json)
                    site_data = _convert_resume_data(rd.get("resumeData", rd))
                    if avatar_b64:
                        site_data["hero"]["avatar"] = avatar_b64
                    return jsonify({"success": True, "data": {"site_data": site_data, "source": "resume_convert"}})
                except Exception:
                    pass
        else:
            data = request.get_json() or {}
            prompt = data.get("prompt", "")
            resume_text = data.get("resume_text", "")
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
            if not site_data or "hero" not in site_data:
                raise ValueError("AI 返回格式不正确")
            # 注入头像
            if avatar_b64:
                site_data.setdefault("hero", {})["avatar"] = avatar_b64
            return jsonify({"success": True, "data": {"site_data": site_data, "source": "ai"}})
        except Exception as e:
            print(f"[personal-site] AI 生成失败: {e}")
            traceback.print_exc()
            # 回退方案
            if resume_text:
                site_data = _fallback_from_text(resume_text, prompt)
            else:
                site_data = {
                    "hero": {"name": "张科技", "tagline": "资深全栈工程师 / 独立开发者"},
                    "about": "这是一个AI备用演示模板。因为服务发生了一些中断，我们为您自动填充了这些占位符内容，您可以随后在左栏手动更改结构。",
                    "experience": [
                        {"company": "字节跳动", "role": "高级研发工程师", "period": "2021.06 - 至今", "description": "主导了千万级并发微服务架构设计与落地。\\n将核心接口响应时长降低了 40%。"}
                    ],
                    "projects": [
                        {"name": "开源 Vue 组件库", "description": "在 Github 上获得了 15.2k Stars，帮助上千企业快速构建后台。", "tags": ["Vue3", "TypeScript"]}
                    ],
                    "education": [{"school": "清华大学", "major": "计算机科学与技术", "degree": "硕士", "period": "2018 - 2021"}],
                    "skills": ["Python", "Golang", "React", "Docker", "Kubernetes"],
                    "contact": {"email": "hello@example.com", "github": "https://github.com/example"},
                }
            if avatar_b64:
                site_data.setdefault("hero", {})["avatar"] = avatar_b64
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
                name = site_data.get("hero", {}).get("name", "")
            except (AttributeError, TypeError):
                pass
            site = PersonalSite(
                user_id=current_user.id,
                title=f"{name or '未命名'}的个人网站",
                prompt=prompt,
                site_data=site_data,
                site_config=site_config,
            )
            # 保存头像
            avatar = site_data.get("hero", {}).get("avatar", "")
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
            name = data["site_data"].get("hero", {}).get("name", "site") or "site"
        except (AttributeError, TypeError):
            pass

        resp = make_response(html)
        resp.headers["Content-Type"] = "text/html; charset=utf-8"
        resp.headers["Content-Disposition"] = f'attachment; filename="{name}_site.html"'
        return resp

    return bp
