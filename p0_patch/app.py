"""
app.py — Flask 主入口
新增路由：验证码发送/登录、云端简历 CRUD
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
from services import verify as vfy
from services.email_sender import send_verify_code

app = Flask(__name__)

# ── 限流（带自动清理） ──
_request_log = defaultdict(list)
_log_lock = threading.Lock()

def _cleanup_stale_ips():
    while True:
        time.sleep(120)
        now = time.time()
        with _log_lock:
            stale = [ip for ip, ts in _request_log.items() if not ts or now - ts[-1] > 120]
            for ip in stale:
                del _request_log[ip]

_cleaner = threading.Thread(target=_cleanup_stale_ips, daemon=True)
_cleaner.start()

# 定期清理过期验证码
def _cleanup_verify_codes():
    while True:
        time.sleep(600)
        try:
            vfy.cleanup_expired(db._conn())
        except Exception:
            pass

_vc_cleaner = threading.Thread(target=_cleanup_verify_codes, daemon=True)
_vc_cleaner.start()

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

@app.route("/privacy")
def privacy_page():
    return render_template("privacy.html")

@app.route("/terms")
def terms_page():
    return render_template("terms.html")

# ── 辅助函数 ──
def _uid_info():
    d = request.get_json(silent=True) or {}
    uid = d.get("user_id") or request.headers.get("X-User-Id", "")
    did = d.get("device_hash") or request.headers.get("X-Device-Hash", "")
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    if ip and "," in ip:
        ip = ip.split(",")[0].strip()
    return uid, did, ip


# ═══════════════════════════════════════
# 验证码 API
# ═══════════════════════════════════════

@app.route("/api/verify/send", methods=["POST"])
def api_verify_send():
    """发送验证码"""
    if _is_rate_limited(request.remote_addr):
        return jsonify({"error": "请求过于频繁"}), 429

    data = request.get_json()
    if not data:
        return jsonify({"error": "参数缺失"}), 400

    target = data.get("target", "").strip()
    purpose = data.get("purpose", "bind")

    if purpose not in ("bind", "login"):
        return jsonify({"error": "无效的 purpose"}), 400

    # 格式校验
    target_type, cleaned, err = vfy.validate_target(target)
    if err:
        return jsonify({"error": err}), 400

    # 如果是登录用途，检查该邮箱/手机号是否已绑定
    if purpose == "login":
        user = db.find_user_by_contact(
            email=cleaned if target_type == "email" else None,
            phone=cleaned if target_type == "phone" else None
        )
        if not user:
            return jsonify({"error": "该账号未注册，请先使用并绑定"}), 404

    # 限流检查
    conn = db._conn()
    ok, err, wait = vfy.can_send(conn, cleaned, purpose)
    if not ok:
        return jsonify({"error": err, "wait_seconds": wait}), 429

    # 生成并存储验证码
    code = vfy.create_code(conn, cleaned, purpose)

    # 发送邮件（手机号暂不支持，预留接口）
    if target_type == "email":
        success, mail_err = send_verify_code(cleaned, code, purpose)
        if not success:
            return jsonify({"error": mail_err or "发送失败"}), 500
    else:
        # TODO: 接入短信服务商（阿里云/腾讯云短信 API）
        print("[短信] 验证码 %s → %s（短信服务未接入，仅打印）" % (code, cleaned))

    return jsonify({
        "message": "验证码已发送至 %s" % _mask_contact(cleaned, target_type),
        "expires_in": vfy.CODE_TTL
    })


@app.route("/api/auth/login", methods=["POST"])
def api_auth_login():
    """验证码登录（已绑定用户换设备恢复）"""
    if _is_rate_limited(request.remote_addr):
        return jsonify({"error": "请求过于频繁"}), 429

    data = request.get_json()
    if not data:
        return jsonify({"error": "参数缺失"}), 400

    target = data.get("target", "").strip()
    code = data.get("code", "").strip()

    target_type, cleaned, err = vfy.validate_target(target)
    if err:
        return jsonify({"error": err}), 400

    # 校验验证码
    conn = db._conn()
    valid, verify_err = vfy.verify_code(conn, cleaned, code, "login")
    if not valid:
        return jsonify({"error": verify_err}), 400

    # 查找用户
    user = db.find_user_by_contact(
        email=cleaned if target_type == "email" else None,
        phone=cleaned if target_type == "phone" else None
    )
    if not user:
        return jsonify({"error": "账号不存在"}), 404

    # 记录登录
    db.record_login(user["user_id"])

    # 加载默认简历
    default_resume = db.load_default_resume(user["user_id"])

    return jsonify({
        "user_id": user["user_id"],
        "credits": user["credits_left"],
        "bound": True,
        "default_resume": default_resume,  # 可能为 None
        "resumes_count": len(db.list_resumes(user["user_id"]))
    })


def _mask_contact(value, contact_type):
    """对展示用的邮箱/手机号做部分遮罩"""
    if contact_type == "email":
        parts = value.split("@")
        if len(parts) == 2:
            name = parts[0]
            masked = name[0] + "***" + (name[-1] if len(name) > 1 else "")
            return masked + "@" + parts[1]
    elif contact_type == "phone":
        if len(value) >= 7:
            return value[:3] + "****" + value[-4:]
    return value


# ═══════════════════════════════════════
# 账号绑定（改造：需要验证码）
# ═══════════════════════════════════════

@app.route("/api/bind-account", methods=["POST"])
def api_bind_account():
    uid, _, _ = _uid_info()
    data = request.get_json() or {}
    if not uid:
        return jsonify({"error": "缺少 user_id"}), 400

    email = (data.get("email") or "").strip()
    phone = (data.get("phone") or "").strip()
    code = (data.get("code") or "").strip()

    if not email and not phone:
        return jsonify({"error": "请输入邮箱或手机号"}), 400

    if not code:
        return jsonify({"error": "请输入验证码"}), 400

    target = email or phone
    target_type, cleaned, fmt_err = vfy.validate_target(target)
    if fmt_err:
        return jsonify({"error": fmt_err}), 400

    # 校验验证码
    conn = db._conn()
    valid, verify_err = vfy.verify_code(conn, cleaned, code, "bind")
    if not valid:
        return jsonify({"error": verify_err}), 400

    # 验证通过，执行绑定
    if target_type == "email":
        result, err = db.bind_account(uid, email=cleaned)
    else:
        result, err = db.bind_account(uid, phone=cleaned)

    if err:
        return jsonify({"error": err}), 400
    return jsonify(result)


# ═══════════════════════════════════════
# 云端简历 API
# ═══════════════════════════════════════

@app.route("/api/resumes/save", methods=["POST"])
def api_resumes_save():
    """保存简历到云端"""
    uid, _, _ = _uid_info()
    if not uid:
        return jsonify({"error": "缺少 user_id"}), 400

    data = request.get_json()
    if not data or not data.get("resume_data"):
        return jsonify({"error": "缺少简历内容"}), 400

    # 检查用户是否已绑定（只允许已绑定用户保存到云端）
    user = db._conn().execute(
        "SELECT bind_email, bind_phone FROM users WHERE user_id=?", (uid,)
    ).fetchone()
    if not user:
        return jsonify({"error": "用户不存在"}), 404
    if not user["bind_email"] and not user["bind_phone"]:
        return jsonify({"error": "请先绑定邮箱或手机号，再保存到云端", "need_bind": True}), 403

    import json as _json
    try:
        resume_data_json = _json.dumps(data["resume_data"], ensure_ascii=False)
        template_config_json = _json.dumps(
            data.get("template_config", {}), ensure_ascii=False
        )
    except (TypeError, ValueError):
        return jsonify({"error": "数据格式错误"}), 400

    resume_id, err = db.save_resume(
        uid=uid,
        resume_data_json=resume_data_json,
        template_config_json=template_config_json,
        title=data.get("title", "未命名简历"),
        resume_id=data.get("resume_id"),
        is_default=data.get("is_default", False)
    )

    if err:
        return jsonify({"error": err}), 400

    return jsonify({
        "resume_id": resume_id,
        "message": "保存成功"
    })


@app.route("/api/resumes/list", methods=["GET"])
def api_resumes_list():
    """列出用户所有简历"""
    uid = request.args.get("user_id", "")
    if not uid:
        return jsonify({"error": "缺少 user_id"}), 400

    resumes = db.list_resumes(uid)
    return jsonify({"resumes": resumes})


@app.route("/api/resumes/load", methods=["GET"])
def api_resumes_load():
    """加载一份简历"""
    uid = request.args.get("user_id", "")
    resume_id = request.args.get("resume_id", "")
    if not uid or not resume_id:
        return jsonify({"error": "参数不完整"}), 400

    try:
        resume_id = int(resume_id)
    except ValueError:
        return jsonify({"error": "无效的 resume_id"}), 400

    result, err = db.load_resume(uid, resume_id)
    if err:
        return jsonify({"error": err}), 404
    return jsonify(result)


@app.route("/api/resumes/delete", methods=["POST"])
def api_resumes_delete():
    """删除一份简历"""
    uid, _, _ = _uid_info()
    data = request.get_json() or {}
    if not uid:
        return jsonify({"error": "缺少 user_id"}), 400

    resume_id = data.get("resume_id")
    if not resume_id:
        return jsonify({"error": "缺少 resume_id"}), 400

    ok, err = db.delete_resume(uid, int(resume_id))
    if not ok:
        return jsonify({"error": err}), 404
    return jsonify({"message": "已删除"})


# ═══════════════════════════════════════
# 原有 API 路由（保持不变）
# ═══════════════════════════════════════

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
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        result = _json.loads(text)
        return jsonify(result)
    except (ValueError, Exception) as e:
        if "JSON" in str(type(e).__name__):
            return jsonify({"error": "AI 返回格式异常，请重试"}), 500
        return jsonify({"error": "咨询失败: %s" % str(e)}), 500

@app.route("/api/inject-keywords", methods=["POST"])
def api_inject_keywords():
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
        if "basic" not in result:
            result = {"basic": {}, "intent": {}, "education": [], "work": [], "skills": "", "intro": "", "certs": ""}
        return jsonify({"resumeData": result})
    except Exception as e:
        return jsonify({"error": "解析失败: %s" % str(e)}), 500

@app.route("/api/auto-fill", methods=["POST"])
def api_auto_fill():
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
@app.route("/api/credits/init", methods=["POST"])
def api_credits_init():
    uid, did, ip = _uid_info()
    if not uid: return jsonify({"error": "缺少 user_id"}), 400
    user, is_new, err = db.get_or_create_user(uid, did, ip)
    if err: return jsonify({"error": err, "credits": 0, "need_bind": True}), 403
    return jsonify({"credits": user["credits_left"], "is_new": is_new,
                    "bound": bool(user.get("bind_email") or user.get("bind_phone"))})

@app.route("/api/credits/check", methods=["POST"])
def api_credits_check():
    uid, _, _ = _uid_info()
    if not uid: return jsonify({"error": "缺少 user_id"}), 400
    return jsonify({"credits": db.get_credits(uid)})

@app.route("/api/credits/consume", methods=["POST"])
def api_credits_consume():
    uid, _, _ = _uid_info()
    if not uid: return jsonify({"error": "缺少 user_id"}), 400
    ok, rem, err = db.consume(uid)
    if not ok: return jsonify({"error": err, "credits": rem, "need_bind": rem == 0}), 403
    return jsonify({"credits": rem})

@app.route("/api/submit-review", methods=["POST"])
def api_submit_review():
    uid, _, _ = _uid_info()
    data = request.get_json() or {}
    if not uid: return jsonify({"error": "缺少 user_id"}), 400
    rating = data.get("rating")
    if not rating or not isinstance(rating, int) or rating < 1 or rating > 5:
        return jsonify({"error": "请选择 1-5 星评分"}), 400
    content = data.get("content", "")
    is_anon = 1 if data.get("is_anonymous") else 0
    display = "匿名用户" if is_anon else data.get("display_name", "用户")
    feature = data.get("feature", "general")
    new_cr, err = db.add_review(uid, feature, rating, content, is_anon, display)
    if err: return jsonify({"error": err}), 400
    return jsonify({"credits": new_cr, "message": "评价成功，已奖励 ⚡ 100 算力！", "show_bind": True})

@app.route("/api/get-reviews", methods=["GET"])
def api_get_reviews():
    reviews = db.get_public_reviews(limit=20)
    return jsonify({"reviews": reviews})


if __name__ == "__main__":
    print("服务启动于: http://localhost:%d" % PORT)
    app.run(host="0.0.0.0", port=PORT, debug=DEBUG)
