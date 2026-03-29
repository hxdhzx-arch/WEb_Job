"""
api/contact.py — 联系表单 / 线索收集
"""
from datetime import datetime, timezone
from flask import Blueprint, request
from backend.extensions import db, limiter
from backend.models.contact_lead import ContactLead
from backend.utils.response import success, error
from backend.utils.validators import validate_email


def create_blueprint():
    bp = Blueprint("contact", __name__, url_prefix="/contact")

    @bp.route("/submit", methods=["POST"])
    @limiter.limit("10 per hour")
    def submit_contact():
        data = request.get_json()
        if not data:
            return error("请提供联系信息")
        name = (data.get("name") or "").strip()[:100]
        email = (data.get("email") or "").strip().lower()
        phone = (data.get("phone") or "").strip()[:20]
        company = (data.get("company") or "").strip()[:200]
        message = (data.get("message") or "").strip()[:2000]
        source = (data.get("source") or "contact_form").strip()[:50]
        if not email and not phone:
            return error("请提供邮箱或手机号")
        if email and not validate_email(email):
            return error("邮箱格式不正确")
        lead = ContactLead(
            name=name, email=email or None, phone=phone or None,
            company=company or None, message=message or None,
            source=source, ip_address=request.remote_addr,
            user_agent=(request.headers.get("User-Agent") or "")[:500],
        )
        db.session.add(lead)
        db.session.commit()
        return success(message="感谢您的留言，我们会尽快联系您！")

    return bp
