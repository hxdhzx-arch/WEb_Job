"""
api/web_resume.py — 网页简历发布/预览/导出 API
"""
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, make_response
from backend.extensions import db
from backend.models.resume import Resume
from backend.middleware.auth_required import jwt_required_custom as auth_required
from backend.utils.web_resume_renderer import render_resume, list_templates


def create_web_resume_bp():
    bp = Blueprint("web_resume", __name__)

    # ── 模板列表 ──
    @bp.route("/resume/web-templates", methods=["GET"])
    @auth_required()
    def get_templates(current_user):
        return jsonify({"success": True, "data": list_templates()})

    # ── 获取单份简历数据 (Load Resume) ──
    @bp.route("/resume/<int:resume_id>", methods=["GET"])
    @auth_required()
    def get_resume(current_user, resume_id):
        resume = Resume.query.filter_by(id=resume_id, user_id=current_user.id).first()
        if not resume:
            return jsonify({"success": False, "message": "简历不存在"}), 404
            
        return jsonify({
            "success": True,
            "data": {
                "id": resume.id,
                "title": resume.title,
                "resume_data": resume.resume_data,
                "web_config": resume.web_config,
                "template_config": resume.template_config,
                "is_published": resume.is_published,
                "slug": resume.slug
            }
        })

    # ── 预览渲染 ──
    @bp.route("/resume/render-preview", methods=["POST"])
    @auth_required()
    def render_preview(current_user):
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "缺少数据"}), 400

        resume_data = data.get("resume_data", {})
        web_config = data.get("web_config", {})
        template = data.get("template", None)

        try:
            html = render_resume(resume_data, web_config, template)
            return jsonify({"success": True, "data": {"html": html}})
        except Exception as e:
            return jsonify({"success": False, "message": f"渲染失败: {str(e)}"}), 500

    # ── 发布 ──
    @bp.route("/resume/publish", methods=["POST"])
    @auth_required()
    def publish_resume(current_user):
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "缺少数据"}), 400

        resume_id = data.get("resume_id")
        web_config = data.get("web_config", {})
        password = data.get("password", "")

        # 尝试读取名字（旧版从 basic.name，新版从 hero block）
        name = ""
        resume_data = data.get("resume_data", {})
        try:
            if "blocks" in resume_data:
                for b in resume_data["blocks"]:
                    if b.get("type") == "hero":
                        name = b.get("content", {}).get("name", "")
                        break
            else:
                name = resume_data.get("basic", {}).get("name", "")
        except Exception:
            pass

        # 如果提供了 resume_id，从数据库加载并更细
        if resume_id:
            resume = Resume.query.filter_by(id=resume_id, user_id=current_user.id).first()
            if not resume:
                return jsonify({"success": False, "message": "简历不存在"}), 404
            resume.web_config = web_config
            if resume_data:
                resume.resume_data = resume_data
            if name:
                resume.title = f"{name}的网页简历"
        else:
            # 从请求体创建新简历记录
            if not resume_data:
                return jsonify({"success": False, "message": "缺少简历数据"}), 400

            resume = Resume(
                user_id=current_user.id,
                title=f"{name or '未命名'}的网页简历",
                resume_data=resume_data,
                web_config=web_config,
            )
            db.session.add(resume)
            db.session.flush()  # 获取 ID

        # 生成 slug
        if not resume.slug:
            resume.generate_slug()

        resume.is_published = True
        resume.published_at = datetime.now(timezone.utc)

        # 设置密码
        if password:
            resume.set_password(password)
        elif data.get("remove_password"):
            resume.set_password(None)

        if "seo_title" in data:
            resume.seo_title = data["seo_title"]
        if "seo_description" in data:
            resume.seo_description = data["seo_description"]

        db.session.commit()

        return jsonify({
            "success": True,
            "data": {
                "resume_id": resume.id,
                "slug": resume.slug,
                "url": f"/r/{resume.slug}",
                "published_at": resume.published_at.isoformat(),
            }
        })

    # ── 自动保存 (Auto Save) ──
    @bp.route("/resume/auto-save", methods=["POST"])
    @auth_required()
    def auto_save_resume(current_user):
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "缺少数据"}), 400

        resume_id = data.get("resume_id")
        if resume_id:
            resume = Resume.query.filter_by(id=resume_id, user_id=current_user.id).first()
            if not resume:
                return jsonify({"success": False, "message": "简历不存在"}), 404
        else:
            resume = Resume(user_id=current_user.id)
            db.session.add(resume)
            
        name = "未命名"
        resume_data = data.get("resume_data", {})
        try:
            if "blocks" in resume_data:
                for b in resume_data["blocks"]:
                    if b.get("type") == "hero":
                        name = b.get("content", {}).get("name", "未命名")
                        break
            else:
                name = resume_data.get("basic", {}).get("name", "未命名")
        except Exception:
            pass
            
        resume.title = data.get("title") or f"{name}的简历"
        
        if "resume_data" in data:
            resume.resume_data = data["resume_data"]
        if "web_config" in data:
            resume.web_config = data["web_config"]
        if "template_config" in data:
            resume.template_config = data["template_config"]
        if "seo_title" in data:
            resume.seo_title = data["seo_title"]
        if "seo_description" in data:
            resume.seo_description = data["seo_description"]

        db.session.commit()
        return jsonify({"success": True, "data": {"resume_id": resume.id}})

    # ── 获取发布状态 ──
    @bp.route("/resume/publish/<int:resume_id>", methods=["GET"])
    @auth_required()
    def get_publish_status(current_user, resume_id):
        resume = Resume.query.filter_by(id=resume_id, user_id=current_user.id).first()
        if not resume:
            return jsonify({"success": False, "message": "简历不存在"}), 404

        return jsonify({
            "success": True,
            "data": {
                "resume_id": resume.id,
                "is_published": resume.is_published,
                "slug": resume.slug,
                "url": f"/r/{resume.slug}" if resume.slug else None,
                "has_password": bool(resume.password_hash),
                "view_count": resume.view_count,
                "web_config": resume.web_config or {},
                "published_at": resume.published_at.isoformat() if resume.published_at else None,
            }
        })

    # ── 取消发布 ──
    @bp.route("/resume/unpublish/<int:resume_id>", methods=["DELETE"])
    @auth_required()
    def unpublish_resume(current_user, resume_id):
        resume = Resume.query.filter_by(id=resume_id, user_id=current_user.id).first()
        if not resume:
            return jsonify({"success": False, "message": "简历不存在"}), 404

        resume.is_published = False
        db.session.commit()

        return jsonify({"success": True, "message": "已取消发布"})

    # ── 更新网页配置 ──
    @bp.route("/resume/web-config/<int:resume_id>", methods=["PUT"])
    @auth_required()
    def update_web_config(current_user, resume_id):
        resume = Resume.query.filter_by(id=resume_id, user_id=current_user.id).first()
        if not resume:
            return jsonify({"success": False, "message": "简历不存在"}), 404

        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "缺少数据"}), 400

        resume.web_config = data.get("web_config", resume.web_config)
        if "password" in data:
            resume.set_password(data["password"] or None)

        db.session.commit()
        return jsonify({"success": True, "message": "已更新"})

    # ── 导出单文件 HTML ──
    @bp.route("/resume/export-html", methods=["POST"])
    @auth_required()
    def export_html(current_user):
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "缺少数据"}), 400

        resume_data = data.get("resume_data", {})
        web_config = data.get("web_config", {})
        template = data.get("template", None)

        try:
            html = render_resume(resume_data, web_config, template)
        except Exception as e:
            return jsonify({"success": False, "message": f"渲染失败: {str(e)}"}), 500

        name = "resume"
        try:
            name = resume_data.get("basic", {}).get("name", "resume") or "resume"
        except (AttributeError, TypeError):
            pass

        resp = make_response(html)
        resp.headers["Content-Type"] = "text/html; charset=utf-8"
        resp.headers["Content-Disposition"] = f'attachment; filename="{name}_resume.html"'
        return resp

    return bp
