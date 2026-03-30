"""
backend/api/dashboard.py — 用户工作台大盘 API
提供跨“网页简历 (resume)”和“个人网站 (personal_site)”的统一聚合视图及管理操作。
"""
from flask import Blueprint, request, jsonify
from backend.extensions import db
from backend.models.resume import Resume
from backend.models.personal_site import PersonalSite
from backend.models.project_version import ProjectVersion
from backend.middleware.auth_required import jwt_required_custom as auth_required
import copy

def create_blueprint():
    bp = Blueprint("dashboard", __name__)

    @bp.route("/dashboard/projects", methods=["GET"])
    @auth_required()
    def list_projects(current_user):
        resumes = Resume.query.filter_by(user_id=current_user.id).order_by(Resume.updated_at.desc()).all()
        sites = PersonalSite.query.filter_by(user_id=current_user.id).order_by(PersonalSite.updated_at.desc()).all()
        
        projects = []
        for r in resumes:
            projects.append({
                "id": r.id,
                "project_type": "resume",
                "title": r.title,
                "is_published": r.is_published,
                "slug": r.slug,
                "view_count": r.view_count,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
                "editor_url": f"/builder?id={r.id}",
                "public_url": f"/r/{r.slug}" if r.is_published else None,
            })
        for s in sites:
            projects.append({
                "id": s.id,
                "project_type": "site",
                "title": s.title,
                "is_published": s.is_published,
                "slug": s.slug,
                "view_count": s.view_count,
                "updated_at": s.updated_at.isoformat() if s.updated_at else None,
                "editor_url": f"/personal-site?id={s.id}",
                "public_url": f"/site/{s.slug}" if s.is_published else None,
            })
        
        # Sort by updated_at descending
        projects.sort(key=lambda x: x["updated_at"] or "", reverse=True)
        
        return jsonify({"success": True, "data": projects})

    @bp.route("/dashboard/projects/duplicate", methods=["POST"])
    @auth_required()
    def duplicate_project(current_user):
        data = request.get_json()
        pid = data.get("id")
        ptype = data.get("type")
        if not pid or not ptype:
            return jsonify({"success": False, "message": "缺少参数"}), 400
            
        if ptype == "resume":
            orig = Resume.query.filter_by(id=pid, user_id=current_user.id).first()
            if not orig: return jsonify({"success": False, "message": "项目不存在"}), 404
            new_proj = Resume(
                user_id=current_user.id,
                title=f"{orig.title} (副本)",
                resume_data=copy.deepcopy(orig.resume_data),
                template_config=copy.deepcopy(orig.template_config),
            )
            db.session.add(new_proj)
            db.session.commit()
            return jsonify({"success": True})
            
        elif ptype == "site":
            orig = PersonalSite.query.filter_by(id=pid, user_id=current_user.id).first()
            if not orig: return jsonify({"success": False, "message": "项目不存在"}), 404
            new_proj = PersonalSite(
                user_id=current_user.id,
                title=f"{orig.title} (副本)",
                prompt=orig.prompt,
                site_data=copy.deepcopy(orig.site_data),
                site_config=copy.deepcopy(orig.site_config)
            )
            db.session.add(new_proj)
            db.session.commit()
            return jsonify({"success": True})
            
        return jsonify({"success": False, "message": "未知类型"}), 400

    @bp.route("/dashboard/projects/rename", methods=["POST"])
    @auth_required()
    def rename_project(current_user):
        data = request.get_json()
        pid = data.get("id")
        ptype = data.get("type")
        new_title = data.get("title", "").strip()
        if not pid or not ptype or not new_title:
            return jsonify({"success": False, "message": "参数不完整"}), 400
            
        model = Resume if ptype == "resume" else PersonalSite
        proj = model.query.filter_by(id=pid, user_id=current_user.id).first()
        if not proj:
            return jsonify({"success": False, "message": "项目不存在"}), 404
        proj.title = new_title
        db.session.commit()
        return jsonify({"success": True})
        
    @bp.route("/dashboard/projects/delete", methods=["POST"])
    @auth_required()
    def delete_project(current_user):
        data = request.get_json()
        pid = data.get("id")
        ptype = data.get("type")
        if not pid or not ptype:
            return jsonify({"success": False, "message": "参数不完整"}), 400
            
        model = Resume if ptype == "resume" else PersonalSite
        proj = model.query.filter_by(id=pid, user_id=current_user.id).first()
        if not proj:
            return jsonify({"success": False, "message": "项目不存在"}), 404
            
        db.session.delete(proj)
        db.session.commit()
        return jsonify({"success": True})

    @bp.route("/dashboard/versions/save", methods=["POST"])
    @auth_required()
    def save_version(current_user):
        data = request.get_json()
        pid = data.get("project_id")
        ptype = data.get("project_type")
        note = data.get("note", "自动存档")
        
        if not pid or not ptype:
            return jsonify({"success": False, "message": "缺少标识"}), 400
            
        model = Resume if ptype == "resume" else PersonalSite
        proj = model.query.filter_by(id=pid, user_id=current_user.id).first()
        if not proj:
            return jsonify({"success": False, "message": "项目不存在"}), 404
            
        snap_data = proj.resume_data if ptype == "resume" else proj.site_data
        snap_cfg = proj.template_config if ptype == "resume" else proj.site_config
        
        v = ProjectVersion(
            user_id=current_user.id,
            project_type=ptype,
            project_id=pid,
            version_note=note,
            data_snapshot=copy.deepcopy(snap_data),
            config_snapshot=copy.deepcopy(snap_cfg)
        )
        db.session.add(v)
        
        versions = ProjectVersion.query.filter_by(project_type=ptype, project_id=pid, user_id=current_user.id).order_by(ProjectVersion.created_at.desc()).all()
        if len(versions) >= 10:
            for old in versions[9:]:
                db.session.delete(old)
                
        db.session.commit()
        return jsonify({"success": True, "data": v.to_dict()})

    @bp.route("/dashboard/versions/list", methods=["GET"])
    @auth_required()
    def list_versions(current_user):
        pid = request.args.get("project_id")
        ptype = request.args.get("project_type")
        if not pid or not ptype:
            return jsonify({"success": False}), 400
        
        versions = ProjectVersion.query.filter_by(project_type=ptype, project_id=pid, user_id=current_user.id).order_by(ProjectVersion.created_at.desc()).all()
        return jsonify({"success": True, "data": [v.to_dict() for v in versions]})

    @bp.route("/dashboard/versions/restore", methods=["POST"])
    @auth_required()
    def restore_version(current_user):
        data = request.get_json()
        vid = data.get("version_id")
        if not vid:
            return jsonify({"success": False}), 400
            
        v = ProjectVersion.query.filter_by(id=vid, user_id=current_user.id).first()
        if not v:
            return jsonify({"success": False, "message": "版本不存在"}), 404
            
        model = Resume if v.project_type == "resume" else PersonalSite
        proj = model.query.filter_by(id=v.project_id, user_id=current_user.id).first()
        if not proj:
            return jsonify({"success": False, "message": "关联项目已删除"}), 404
            
        if v.project_type == "resume":
            proj.resume_data = v.data_snapshot
            proj.template_config = v.config_snapshot
        else:
            proj.site_data = v.data_snapshot
            proj.site_config = v.config_snapshot
            
        db.session.commit()
        return jsonify({"success": True})

    return bp
