"""
app.py — Flask 主入口
"""
import time
import threading
from collections import defaultdict
from flask import Flask, render_template, request, jsonify
from config import PORT, DEBUG, RATE_LIMIT_PER_MINUTE
from services.resume_analyzer import analyze_resume
from services.jd_matcher import match_jd
from services.gemini_client import call_gemini
from services.privacy_mask import mask_resume_for_ai
from services import database as db

app = Flask(__name__)

# ── 限流（带自动清理） ──
_request_log = defaultdict(list)
_log_lock = threading.Lock()

def _cleanup_stale_ips():
    """每 120 秒清理不活跃的 IP 记录，防止内存泄漏"""
    while True:
        time.sleep(120)
        now = time.time()
        with _log_lock:
            stale = [ip for ip, ts in _request_log.items() if not ts or now - ts[-1] > 120]
            for ip in stale:
                del _request_log[ip]

_cleaner = threading.Thread(target=_cleanup_stale_ips, daemon=True)
_cleaner.start()

def _is_rate_limited(ip):
    now = time.time()
    with _log_lock:
        _request_log[ip] = [t for t in _request_log[ip] if now - t < 60]
        if len(_request_log[ip]) >= RATE_LIMIT_PER_MINUTE:
            return True
        _request_log[ip].append(now)
    return False

# ── 页面路由 ──
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/resume")
def resume_page():
    return render_template("resume.html")

@app.route("/jd")
def jd_page():
    return render_template("jd_match.html")

@app.route("/builder")
def builder_page():
    return render_template("resume_builder.html")

@app.route("/career-tools")
def career_tools_page():
    return render_template("career_tools.html")

@app.route("/privacy")
def privacy_page():
    return render_template("privacy.html")

@app.route("/terms")
def terms_page():
    return render_template("terms.html")

# ── API 路由 ──
@app.route("/api/analyze-resume", methods=["POST"])
def api_analyze_resume():
    if _is_rate_limited(request.remote_addr):
        return jsonify({"error": "请求过于频繁"}), 429
    data = request.get_json()
    if not data or not data.get("resume_text"):
        return jsonify({"error": "请输入简历内容"}), 400
    try:
        return jsonify(analyze_resume(data["resume_text"]))
    except Exception as e:
        return jsonify({"error": "分析失败: %s" % str(e)}), 500

@app.route("/api/match-jd", methods=["POST"])
def api_match_jd():
    if _is_rate_limited(request.remote_addr):
        return jsonify({"error": "请求过于频繁"}), 429
    data = request.get_json()
    if not data or not data.get("resume_text") or not data.get("jd_text"):
        return jsonify({"error": "请输入简历和职位描述"}), 400
    try:
        return jsonify(match_jd(data["resume_text"], data["jd_text"]))
    except Exception as e:
        return jsonify({"error": "分析失败: %s" % str(e)}), 500

@app.route("/api/career-advisor", methods=["POST"])
def api_career_advisor():
    """AI 职业顾问"""
    if _is_rate_limited(request.remote_addr):
        return jsonify({"error": "请求过于频繁"}), 429
    data = request.get_json()
    if not data or not data.get("user_query"):
        return jsonify({"error": "请描述你的情况"}), 400
    try:
        prompt = '''你是一位资深职业规划顾问。根据用户描述，给出职业方向和薪资建议。
你必须且只能输出以下JSON格式，不要输出任何其他文字：
{
  "salary_evaluation": "针对用户期望薪资的合理性评估（50字内）",
  "recommended_roles": [
    {"title": "推荐岗位1", "reason": "推荐理由（30字内）"},
    {"title": "推荐岗位2", "reason": "推荐理由（30字内）"},
    {"title": "推荐岗位3", "reason": "推荐理由（30字内）"}
  ],
  "best_match_jd": "根据用户特征生成的最匹配的一份详细岗位JD，包含岗位职责和任职要求，至少200字"
}

用户描述：
''' + data["user_query"]
        raw = call_gemini(prompt)
        import json as _json
        # Try parse JSON from response
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        result = _json.loads(text)
        return jsonify(result)
    except (ValueError, _json.JSONDecodeError):
        return jsonify({"error": "AI 返回格式异常，请重试"}), 500
    except Exception as e:
        return jsonify({"error": "咨询失败: %s" % str(e)}), 500

@app.route("/api/inject-keywords", methods=["POST"])
def api_inject_keywords():
    """AI 智能融合缺失关键词"""
    if _is_rate_limited(request.remote_addr):
        return jsonify({"error": "请求过于频繁"}), 429
    data = request.get_json()
    if not data or not data.get("resume_text") or not data.get("missing_keywords"):
        return jsonify({"error": "参数不完整"}), 400
    try:
        keywords = ", ".join(data["missing_keywords"])
        prompt = """你是一位专业的简历优化专家。请将以下缺失的关键词自然地融入简历中。
严格要求：
1. 不得捏造虚假经历或技能，只在合理的位置补充关键词
2. 优先融入自我评价、技能特长和工作职责描述中
3. 保持原文结构和真实信息不变
4. 融入后的表述必须通顺自然，不能生硬堆砌
5. 只输出修改后的完整简历文本，不要加任何解释

需要融入的关键词：""" + keywords + """

原始简历：
""" + data["resume_text"]
        result = call_gemini(prompt)
        return jsonify({"enhanced_resume": result.strip()})
    except Exception as e:
        return jsonify({"error": "融合失败: %s" % str(e)}), 500

@app.route("/api/parse-resume-pdf", methods=["POST"])
def api_parse_resume_pdf():
    """解析 PDF 简历并结构化为 JSON"""
    if _is_rate_limited(request.remote_addr):
        return jsonify({"error": "请求过于频繁"}), 429
    if "file" not in request.files:
        return jsonify({"error": "请上传文件"}), 400
    f = request.files["file"]
    if not f.filename:
        return jsonify({"error": "文件为空"}), 400
    try:
        import fitz
        pdf_bytes = f.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        if len(text.strip()) < 10:
            return jsonify({"error": "PDF 内容为空或无法识别"}), 400

        prompt = '''你是简历解析专家。请将以下简历纯文本严格解析为JSON格式。
你必须且只能输出JSON，不要输出任何其他文字、解释或markdown标记。

JSON格式要求：
{
  "basic": {"name":"姓名","age":"年龄","phone":"手机","email":"邮箱","city":"城市","years":"工作年限"},
  "intent": {"job":"目标职位","salary":"期望薪资"},
  "education": [{"school":"学校","major":"专业","degree":"学历","time":"时间"}],
  "work": [{"company":"公司","title":"职位","time":"时间","duties":["工作成就1","工作成就2"]}],
  "skills": "技能1、技能2、技能3",
  "intro": "自我评价",
  "certs": "证书"
}

注意：
- 如果某个字段在简历中找不到，填空字符串
- work.duties 必须是字符串数组，每条成就独立一项
- education 和 work 都是数组，支持多段
- skills 用顿号分隔

简历原文：
''' + text[:4000]
        raw = call_gemini(prompt)
        import json as _json
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        result = _json.loads(cleaned)
        # Ensure structure
        if "basic" not in result:
            result = {"basic": {}, "intent": {}, "education": [], "work": [], "skills": "", "intro": "", "certs": ""}
        return jsonify({"resumeData": result})
    except Exception as e:
        return jsonify({"error": "解析失败: %s" % str(e)}), 500

@app.route("/api/auto-fill", methods=["POST"])
def api_auto_fill():
    """AI 智能扩写"""
    if _is_rate_limited(request.remote_addr):
        return jsonify({"error": "请求过于频繁"}), 429
    data = request.get_json()
    if not data or not data.get("text"):
        return jsonify({"error": "请输入内容"}), 400
    try:
        context = data.get("context", "")
        prompt = """你是一位世界500强企业的HRBP和简历撰写专家。
请将用户的白话文/短句用STAR法则（情境Situation、任务Task、行动Action、结果Result）进行专业扩写。
要求：
1. 主动使用专业动词（主导、统筹、推动、优化、搭建、落地）
2. 补充合理的量化数据（提升X%、降低X%、覆盖X+用户）
3. 每条成就独立一行，不要编号，不要加任何前缀符号
4. 输出3-5条扩写后的成就描述
5. 只输出扩写结果，不要加任何解释文字

""" + ("岗位背景：" + context + "\n\n" if context else "") + "用户原文：\n" + mask_resume_for_ai(data["text"])
        result = call_gemini(prompt)
        return jsonify({"expanded": result.strip()})
    except Exception as e:
        return jsonify({"error": "扩写失败: %s" % str(e)}), 500

def _calc_progressive_tax(monthly_taxable):
    """按中国大陆常见个税月度速算表计算税额"""
    brackets = [
        (3000, 0.03, 0),
        (12000, 0.10, 210),
        (25000, 0.20, 1410),
        (35000, 0.25, 2660),
        (55000, 0.30, 4410),
        (80000, 0.35, 7160),
        (float("inf"), 0.45, 15160),
    ]
    for limit, rate, deduction in brackets:
        if monthly_taxable <= limit:
            return max(0, monthly_taxable * rate - deduction), rate
    return 0, 0

@app.route("/api/calculate-net-salary", methods=["POST"])
def api_calculate_net_salary():
    """税后薪资 + 五险一金估算器"""
    data = request.get_json() or {}
    try:
        gross_salary = float(data.get("gross_salary", 0))
        city = (data.get("city") or "全国默认").strip()
        fund_rate = float(data.get("fund_rate", 12))
        insurance_base = float(data.get("insurance_base", gross_salary))
        special_deduction = float(data.get("special_deduction", 0))
    except (TypeError, ValueError):
        return jsonify({"error": "输入参数格式错误"}), 400

    if gross_salary <= 0:
        return jsonify({"error": "税前月薪必须大于 0"}), 400
    if fund_rate < 5 or fund_rate > 12:
        return jsonify({"error": "公积金比例建议在 5-12 之间"}), 400

    # 常见个人缴纳比例（简化版）
    pension = insurance_base * 0.08
    medical = insurance_base * 0.02 + 3
    unemployment = insurance_base * 0.005
    housing_fund = insurance_base * (fund_rate / 100)
    social_total = pension + medical + unemployment + housing_fund

    taxable_income = gross_salary - social_total - 5000 - special_deduction
    tax, tax_rate = _calc_progressive_tax(taxable_income)
    net_salary = gross_salary - social_total - tax

    return jsonify({
        "city": city,
        "gross_salary": round(gross_salary, 2),
        "insurance_base": round(insurance_base, 2),
        "fund_rate": fund_rate,
        "breakdown": {
            "pension": round(pension, 2),
            "medical": round(medical, 2),
            "unemployment": round(unemployment, 2),
            "housing_fund": round(housing_fund, 2),
            "social_total": round(social_total, 2),
            "taxable_income": round(max(0, taxable_income), 2),
            "tax_rate": f"{int(tax_rate * 100)}%",
            "income_tax": round(tax, 2),
        },
        "net_salary": round(net_salary, 2),
        "annual_net_salary": round(net_salary * 12, 2),
        "notice": "为产品内估算模型，实际缴纳请以当地社保公积金与个税政策为准。",
    })

@app.route("/api/compare-offers", methods=["POST"])
def api_compare_offers():
    """Offer 对比器：按综合得分排序"""
    data = request.get_json() or {}
    offers = data.get("offers") or []
    if not isinstance(offers, list) or len(offers) < 2:
        return jsonify({"error": "请至少提供 2 个 offer"}), 400

    evaluated = []
    for idx, offer in enumerate(offers):
        try:
            name = (offer.get("name") or f"Offer {idx+1}").strip()
            monthly_salary = float(offer.get("monthly_salary", 0))
            months = float(offer.get("months", 12))
            bonus = float(offer.get("bonus", 0))
            stock = float(offer.get("stock", 0))
            commute = float(offer.get("commute", 5))
            growth = float(offer.get("growth", 5))
            stability = float(offer.get("stability", 5))
            wlb = float(offer.get("wlb", 5))
        except (TypeError, ValueError):
            return jsonify({"error": f"第 {idx+1} 个 offer 数据格式错误"}), 400

        annual_cash = monthly_salary * months + bonus
        total_package = annual_cash + stock
        soft_score = growth * 0.35 + stability * 0.25 + wlb * 0.25 + (10 - min(commute, 10)) * 0.15
        final_score = total_package / 10000 * 0.65 + soft_score * 0.35

        evaluated.append({
            "name": name,
            "annual_cash": round(annual_cash, 2),
            "total_package": round(total_package, 2),
            "soft_score": round(soft_score, 2),
            "final_score": round(final_score, 2),
            "inputs": {
                "monthly_salary": monthly_salary,
                "months": months,
                "bonus": bonus,
                "stock": stock,
                "commute": commute,
                "growth": growth,
                "stability": stability,
                "wlb": wlb,
            },
        })

    ranked = sorted(evaluated, key=lambda x: x["final_score"], reverse=True)
    return jsonify({
        "ranking": ranked,
        "winner": ranked[0]["name"],
        "summary": f"综合评分最高的是 {ranked[0]['name']}，建议优先推进谈薪与入职流程。",
    })

@app.route("/api/parse-jd-customize-resume", methods=["POST"])
def api_parse_jd_customize_resume():
    """JD 解析 + 简历定制建议"""
    if _is_rate_limited(request.remote_addr):
        return jsonify({"error": "请求过于频繁"}), 429
    data = request.get_json() or {}
    jd_text = (data.get("jd_text") or "").strip()
    resume_text = (data.get("resume_text") or "").strip()
    if len(jd_text) < 30:
        return jsonify({"error": "请输入完整岗位 JD（至少 30 字）"}), 400
    try:
        prompt = """你是资深招聘专家。请解析岗位JD并输出严格JSON，字段如下：
{
  "job_title": "岗位名称",
  "level": "初级/中级/高级",
  "keywords": ["关键词1","关键词2","关键词3","关键词4","关键词5"],
  "must_have": ["硬性要求1","硬性要求2","硬性要求3"],
  "bonus_points": ["加分项1","加分项2"],
  "resume_tailoring": ["简历改写建议1","简历改写建议2","简历改写建议3","简历改写建议4"],
  "self_intro": "一段 120 字内的面试自我介绍"
}
要求：只输出JSON，不要markdown。
"""
        if resume_text:
            prompt += "\n候选人简历：\n" + mask_resume_for_ai(resume_text[:2500]) + "\n"
        prompt += "\n岗位JD：\n" + jd_text[:2500]

        raw = call_gemini(prompt)
        import json as _json
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        result = _json.loads(cleaned)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": "JD 解析失败: %s" % str(e)}), 500

@app.route("/api/doc-tools-catalog", methods=["GET"])
def api_doc_tools_catalog():
    """文档工具导航：已上线/规划中能力"""
    return jsonify({
        "online": [
            "简历 PDF 解析并自动识别教育经历/工作经历/技能模块",
            "AI 扩写与简历润色",
        ],
        "coming_soon": [
            "简历 PDF 转可编辑 Word（结构化版）",
            "Word 转 PDF",
            "PDF 压缩 / 合并 / 拆分 / 提取文字",
        ],
    })

@app.route("/api/polish-resume", methods=["POST"])
def api_polish_resume():
    if _is_rate_limited(request.remote_addr):
        return jsonify({"error": "请求过于频繁"}), 429
    data = request.get_json()
    if not data or not data.get("resume_text"):
        return jsonify({"error": "请输入简历内容"}), 400
    try:
        prompt = "你是专业简历润色专家。请润色以下简历，要求：保持信息不变但优化表达，用STAR法则改写工作经历，突出量化成果，技能描述专业化，自我评价精炼有力。只输出润色后的完整简历文本，不要加任何解释。\n\n原始简历：\n" + mask_resume_for_ai(data["resume_text"])
        result = call_gemini(prompt)
        return jsonify({"polished_text": result})
    except Exception as e:
        return jsonify({"error": "润色失败: %s" % str(e)}), 500

# ── 算力系统 API ──
def _uid_info():
    d = request.get_json(silent=True) or {}
    uid = d.get("user_id") or request.headers.get("X-User-Id","")
    did = d.get("device_hash") or request.headers.get("X-Device-Hash","")
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    if ip and "," in ip: ip = ip.split(",")[0].strip()
    return uid, did, ip

@app.route("/api/credits/init", methods=["POST"])
def api_credits_init():
    uid, did, ip = _uid_info()
    if not uid: return jsonify({"error":"缺少 user_id"}), 400
    user, is_new, err = db.get_or_create_user(uid, did, ip)
    if err: return jsonify({"error":err,"credits":0,"need_bind":True}), 403
    return jsonify({"credits":user["credits_left"],"is_new":is_new,
                    "bound":bool(user.get("bind_email") or user.get("bind_phone"))})

@app.route("/api/credits/check", methods=["POST"])
def api_credits_check():
    uid,_,_ = _uid_info()
    if not uid: return jsonify({"error":"缺少 user_id"}), 400
    return jsonify({"credits":db.get_credits(uid)})

@app.route("/api/credits/consume", methods=["POST"])
def api_credits_consume():
    uid,_,_ = _uid_info()
    if not uid: return jsonify({"error":"缺少 user_id"}), 400
    ok, rem, err = db.consume(uid)
    if not ok: return jsonify({"error":err,"credits":rem,"need_bind":rem==0}), 403
    return jsonify({"credits":rem})

@app.route("/api/submit-review", methods=["POST"])
def api_submit_review():
    uid,_,_ = _uid_info()
    data = request.get_json() or {}
    if not uid: return jsonify({"error":"缺少 user_id"}), 400
    rating = data.get("rating")
    if not rating or not isinstance(rating, int) or rating<1 or rating>5:
        return jsonify({"error":"请选择 1-5 星评分"}), 400
    content = data.get("content","")
    is_anon = 1 if data.get("is_anonymous") else 0
    display = "匿名用户" if is_anon else data.get("display_name","用户")
    feature = data.get("feature","general")
    new_cr, err = db.add_review(uid, feature, rating, content, is_anon, display)
    if err: return jsonify({"error":err}), 400
    return jsonify({"credits":new_cr,"message":"评价成功，已奖励 ⚡ 100 算力！","show_bind":True})

@app.route("/api/get-reviews", methods=["GET"])
def api_get_reviews():
    reviews = db.get_public_reviews(limit=20)
    return jsonify({"reviews":reviews})

@app.route("/api/bind-account", methods=["POST"])
def api_bind_account():
    uid,_,_ = _uid_info()
    data = request.get_json() or {}
    if not uid: return jsonify({"error":"缺少 user_id"}), 400
    email = (data.get("email") or "").strip()
    phone = (data.get("phone") or "").strip()
    if not email and not phone: return jsonify({"error":"请输入邮箱或手机号"}), 400
    result, err = db.bind_account(uid, email=email or None, phone=phone or None)
    if err: return jsonify({"error":err}), 400
    return jsonify(result)

if __name__ == "__main__":
    print("服务启动于: http://localhost:%d" % PORT)
    app.run(host="0.0.0.0", port=PORT, debug=DEBUG)
