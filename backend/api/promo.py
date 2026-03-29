"""
api/promo.py — 优惠码验证
"""
from flask import Blueprint, request
from backend.models.promo import PromoCode, PromoUsage
from backend.middleware.auth_required import jwt_required_custom
from backend.utils.response import success, error


def create_blueprint():
    bp = Blueprint("promo", __name__, url_prefix="/promo")

    @bp.route("/verify", methods=["POST"])
    @jwt_required_custom()
    def verify_promo(**kwargs):
        current_user = kwargs["current_user"]
        data = request.get_json()
        code = (data.get("code") or "").strip().upper() if data else ""
        if not code:
            return error("请输入优惠码")
        promo = PromoCode.query.filter_by(code=code).first()
        if not promo:
            return error("优惠码不存在")
        if not promo.is_valid:
            return error("优惠码已失效或已用完")
        used = PromoUsage.query.filter_by(promo_code_id=promo.id, user_id=current_user.id).first()
        if used:
            return error("您已使用过该优惠码")
        return success(promo.to_dict(), "优惠码有效")

    return bp
