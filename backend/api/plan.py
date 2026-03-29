"""
api/plan.py — 套餐查询
"""
from flask import Blueprint
from backend.models.plan import Plan
from backend.utils.response import success, error


def create_blueprint():
    bp = Blueprint("plan", __name__, url_prefix="/plans")

    @bp.route("/", methods=["GET"])
    def list_plans():
        plans = Plan.query.filter_by(is_active=True).order_by(Plan.sort_order).all()
        return success([p.to_dict() for p in plans])

    @bp.route("/<int:plan_id>", methods=["GET"])
    def get_plan(plan_id):
        plan = Plan.query.get(plan_id)
        if not plan or not plan.is_active:
            return error("套餐不存在", 404)
        return success(plan.to_dict())

    return bp
