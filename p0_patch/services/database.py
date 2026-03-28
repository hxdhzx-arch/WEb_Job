"""
database.py — SQLite 算力追踪 + 风控 + 评价 + 云端简历 + 验证码
"""
import sqlite3, os, threading, time, json

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "resume_ai.db")
_local = threading.local()

INITIAL_CREDITS = 300
COST_PER_AI_CALL = 100
REWARD_PER_REVIEW = 100
MAX_UIDS_PER_DEVICE = 2
MAX_UIDS_PER_IP = 3
MAX_RESUMES_PER_USER = 10
MAX_RESUME_SIZE = 512 * 1024  # 500KB per resume JSON

def _conn():
    if not hasattr(_local, "c") or _local.c is None:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        _local.c = sqlite3.connect(DB_PATH)
        _local.c.row_factory = sqlite3.Row
        _local.c.execute("PRAGMA journal_mode=WAL")
    return _local.c

def init_db():
    c = _conn()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        user_id       TEXT PRIMARY KEY,
        device_hash   TEXT NOT NULL DEFAULT '',
        ip_address    TEXT NOT NULL DEFAULT '',
        credits_left  INTEGER NOT NULL DEFAULT 0,
        total_used    INTEGER NOT NULL DEFAULT 0,
        bind_email    TEXT DEFAULT NULL,
        bind_phone    TEXT DEFAULT NULL,
        last_login_at REAL DEFAULT NULL,
        login_count   INTEGER NOT NULL DEFAULT 0,
        created_at    REAL NOT NULL,
        updated_at    REAL NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_u_device ON users(device_hash);
    CREATE INDEX IF NOT EXISTS idx_u_ip ON users(ip_address);
    CREATE INDEX IF NOT EXISTS idx_u_email ON users(bind_email);
    CREATE INDEX IF NOT EXISTS idx_u_phone ON users(bind_phone);

    CREATE TABLE IF NOT EXISTS reviews (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id       TEXT NOT NULL,
        feature       TEXT NOT NULL DEFAULT 'general',
        rating        INTEGER NOT NULL,
        content       TEXT DEFAULT '',
        is_anonymous  INTEGER NOT NULL DEFAULT 0,
        display_name  TEXT DEFAULT '匿名用户',
        credits_awarded INTEGER NOT NULL DEFAULT 0,
        created_at    REAL NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_rv_user ON reviews(user_id);

    CREATE TABLE IF NOT EXISTS verify_codes (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        target      TEXT NOT NULL,
        code        TEXT NOT NULL,
        purpose     TEXT NOT NULL DEFAULT 'bind',
        attempts    INTEGER NOT NULL DEFAULT 0,
        created_at  REAL NOT NULL,
        expires_at  REAL NOT NULL,
        used        INTEGER NOT NULL DEFAULT 0
    );
    CREATE INDEX IF NOT EXISTS idx_vc_target ON verify_codes(target, purpose);

    CREATE TABLE IF NOT EXISTS resumes (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id         TEXT NOT NULL,
        title           TEXT NOT NULL DEFAULT '未命名简历',
        resume_data     TEXT NOT NULL,
        template_config TEXT NOT NULL DEFAULT '{}',
        is_default      INTEGER NOT NULL DEFAULT 0,
        created_at      REAL NOT NULL,
        updated_at      REAL NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_res_user ON resumes(user_id);
    """)
    c.commit()

    # 兼容升级：给旧表加新字段（忽略已存在的错误）
    for stmt in [
        "ALTER TABLE users ADD COLUMN last_login_at REAL DEFAULT NULL",
        "ALTER TABLE users ADD COLUMN login_count INTEGER NOT NULL DEFAULT 0",
    ]:
        try:
            c.execute(stmt)
            c.commit()
        except sqlite3.OperationalError:
            pass  # 字段已存在，跳过


# ═══════════════════════════════════════
# 用户相关（保留原有逻辑）
# ═══════════════════════════════════════

def get_or_create_user(user_id, device_hash, ip):
    """返回 (user_dict, is_new, error_msg)"""
    c = _conn(); now = time.time()
    row = c.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
    if row:
        c.execute("UPDATE users SET device_hash=?,ip_address=?,updated_at=? WHERE user_id=?",
                  (device_hash, ip, now, user_id))
        c.commit()
        return dict(row), False, None
    if device_hash:
        cnt = c.execute("SELECT COUNT(DISTINCT user_id) FROM users WHERE device_hash=?",
                        (device_hash,)).fetchone()[0]
        if cnt >= MAX_UIDS_PER_DEVICE:
            return None, False, "检测到该设备已领取过新手算力，请绑定账号继续使用"
    if ip:
        cnt = c.execute("SELECT COUNT(DISTINCT user_id) FROM users WHERE ip_address=?",
                        (ip,)).fetchone()[0]
        if cnt >= MAX_UIDS_PER_IP:
            return None, False, "当前网络环境已有多个账号，请绑定账号继续使用"
    c.execute("INSERT INTO users(user_id,device_hash,ip_address,credits_left,total_used,created_at,updated_at) VALUES(?,?,?,?,0,?,?)",
              (user_id, device_hash, ip, INITIAL_CREDITS, now, now))
    c.commit()
    row = c.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
    return dict(row), True, None

def get_credits(uid):
    row = _conn().execute("SELECT credits_left FROM users WHERE user_id=?", (uid,)).fetchone()
    return row["credits_left"] if row else 0

def consume(uid):
    """消耗算力，返回 (ok, remaining, error)"""
    c = _conn()
    row = c.execute("SELECT credits_left FROM users WHERE user_id=?", (uid,)).fetchone()
    if not row: return False, 0, "用户不存在"
    if row["credits_left"] < COST_PER_AI_CALL:
        return False, row["credits_left"], "算力不足，请评价获取算力或绑定账号"
    c.execute("UPDATE users SET credits_left=credits_left-?,total_used=total_used+?,updated_at=? WHERE user_id=?",
              (COST_PER_AI_CALL, COST_PER_AI_CALL, time.time(), uid))
    c.commit()
    return True, row["credits_left"] - COST_PER_AI_CALL, None


# ═══════════════════════════════════════
# 评价相关（保留原有逻辑）
# ═══════════════════════════════════════

def add_review(uid, feature, rating, content="", is_anonymous=0, display_name="匿名用户"):
    c = _conn(); now = time.time()
    existing = c.execute("SELECT id FROM reviews WHERE user_id=? AND feature=?", (uid, feature)).fetchone()
    if existing: return None, "您已评价过该功能"
    c.execute("INSERT INTO reviews(user_id,feature,rating,content,is_anonymous,display_name,credits_awarded,created_at) VALUES(?,?,?,?,?,?,?,?)",
              (uid, feature, rating, content, is_anonymous, display_name, REWARD_PER_REVIEW, now))
    c.execute("UPDATE users SET credits_left=credits_left+?,updated_at=? WHERE user_id=?",
              (REWARD_PER_REVIEW, now, uid))
    c.commit()
    return get_credits(uid), None

def get_public_reviews(limit=20):
    rows = _conn().execute(
        "SELECT rating, content, display_name, feature, created_at FROM reviews WHERE content!='' ORDER BY created_at DESC LIMIT ?",
        (limit,)
    ).fetchall()
    return [dict(r) for r in rows]


# ═══════════════════════════════════════
# 账号绑定（已修复 SQL 注入 + 增加验证码要求）
# ═══════════════════════════════════════

def bind_account(uid, email=None, phone=None):
    """
    绑定邮箱或手机号到用户账号（调用前必须已通过验证码校验）
    修复：不再使用 .format() 拼接字段名，改为显式分支
    """
    c = _conn(); now = time.time()

    if not email and not phone:
        return None, "请输入邮箱或手机号"

    cur = c.execute("SELECT * FROM users WHERE user_id=?", (uid,)).fetchone()
    if not cur:
        return None, "用户不存在"

    if email:
        # 检查是否已有其他用户绑定了该邮箱
        existing = c.execute(
            "SELECT * FROM users WHERE bind_email=? AND user_id!=?",
            (email, uid)
        ).fetchone()

        if existing:
            # 合并：将当前游客算力转移到已绑定账号
            guest_cr = cur["credits_left"]
            c.execute("UPDATE users SET credits_left=credits_left+?,updated_at=? WHERE user_id=?",
                      (guest_cr, now, existing["user_id"]))
            c.execute("DELETE FROM users WHERE user_id=?", (uid,))
            c.commit()
            merged = c.execute("SELECT * FROM users WHERE user_id=?",
                               (existing["user_id"],)).fetchone()
            return {
                "merged": True,
                "new_user_id": existing["user_id"],
                "credits": merged["credits_left"],
                "message": "已将算力合并到已绑定账号"
            }, None

        c.execute("UPDATE users SET bind_email=?,updated_at=? WHERE user_id=?",
                  (email, now, uid))
        c.commit()
        return {
            "merged": False,
            "credits": cur["credits_left"],
            "message": "绑定成功！算力与数据已永久保存"
        }, None

    else:  # phone
        existing = c.execute(
            "SELECT * FROM users WHERE bind_phone=? AND user_id!=?",
            (phone, uid)
        ).fetchone()

        if existing:
            guest_cr = cur["credits_left"]
            c.execute("UPDATE users SET credits_left=credits_left+?,updated_at=? WHERE user_id=?",
                      (guest_cr, now, existing["user_id"]))
            c.execute("DELETE FROM users WHERE user_id=?", (uid,))
            c.commit()
            merged = c.execute("SELECT * FROM users WHERE user_id=?",
                               (existing["user_id"],)).fetchone()
            return {
                "merged": True,
                "new_user_id": existing["user_id"],
                "credits": merged["credits_left"],
                "message": "已将算力合并到已绑定账号"
            }, None

        c.execute("UPDATE users SET bind_phone=?,updated_at=? WHERE user_id=?",
                  (phone, now, uid))
        c.commit()
        return {
            "merged": False,
            "credits": cur["credits_left"],
            "message": "绑定成功！算力与数据已永久保存"
        }, None


def find_user_by_contact(email=None, phone=None):
    """通过邮箱或手机号查找已绑定用户（用于验证码登录）"""
    c = _conn()
    if email:
        row = c.execute("SELECT * FROM users WHERE bind_email=?", (email,)).fetchone()
    elif phone:
        row = c.execute("SELECT * FROM users WHERE bind_phone=?", (phone,)).fetchone()
    else:
        return None
    return dict(row) if row else None


def record_login(uid):
    """记录登录时间"""
    c = _conn()
    c.execute(
        "UPDATE users SET last_login_at=?, login_count=login_count+1, updated_at=? WHERE user_id=?",
        (time.time(), time.time(), uid)
    )
    c.commit()


# ═══════════════════════════════════════
# 云端简历 CRUD
# ═══════════════════════════════════════

def save_resume(uid, resume_data_json, template_config_json,
                title="未命名简历", resume_id=None, is_default=False):
    """
    保存简历到云端
    resume_id=None → 新建; resume_id=数字 → 更新
    返回 (resume_id, error)
    """
    c = _conn(); now = time.time()

    # 验证用户存在
    user = c.execute("SELECT user_id FROM users WHERE user_id=?", (uid,)).fetchone()
    if not user:
        return None, "用户不存在"

    # 检查大小
    if len(resume_data_json) > MAX_RESUME_SIZE:
        return None, "简历内容过大（最大 500KB）"

    if resume_id:
        # 更新已有简历
        row = c.execute(
            "SELECT id FROM resumes WHERE id=? AND user_id=?",
            (resume_id, uid)
        ).fetchone()
        if not row:
            return None, "简历不存在或无权限"

        c.execute(
            "UPDATE resumes SET title=?, resume_data=?, template_config=?, "
            "is_default=?, updated_at=? WHERE id=? AND user_id=?",
            (title, resume_data_json, template_config_json,
             1 if is_default else 0, now, resume_id, uid)
        )
    else:
        # 新建简历
        count = c.execute(
            "SELECT COUNT(*) FROM resumes WHERE user_id=?", (uid,)
        ).fetchone()[0]
        if count >= MAX_RESUMES_PER_USER:
            return None, "最多保存 %d 份简历，请删除旧简历后再试" % MAX_RESUMES_PER_USER

        c.execute(
            "INSERT INTO resumes(user_id, title, resume_data, template_config, "
            "is_default, created_at, updated_at) VALUES(?,?,?,?,?,?,?)",
            (uid, title, resume_data_json, template_config_json,
             1 if is_default else 0, now, now)
        )
        resume_id = c.execute("SELECT last_insert_rowid()").fetchone()[0]

    # 如果设为默认，取消其他默认标记
    if is_default:
        c.execute(
            "UPDATE resumes SET is_default=0 WHERE user_id=? AND id!=?",
            (uid, resume_id)
        )

    c.commit()
    return resume_id, None


def list_resumes(uid):
    """列出用户所有简历（不含内容，用于列表展示）"""
    c = _conn()
    rows = c.execute(
        "SELECT id, title, is_default, created_at, updated_at, resume_data "
        "FROM resumes WHERE user_id=? ORDER BY updated_at DESC",
        (uid,)
    ).fetchall()

    result = []
    for r in rows:
        # 从 resume_data 中提取姓名作为预览
        preview_name = ""
        try:
            data = json.loads(r["resume_data"])
            preview_name = data.get("basic", {}).get("name", "")
        except (json.JSONDecodeError, AttributeError):
            pass

        result.append({
            "id": r["id"],
            "title": r["title"],
            "is_default": bool(r["is_default"]),
            "preview_name": preview_name,
            "created_at": r["created_at"],
            "updated_at": r["updated_at"],
        })
    return result


def load_resume(uid, resume_id):
    """加载一份简历的完整内容"""
    c = _conn()
    row = c.execute(
        "SELECT id, title, resume_data, template_config, is_default "
        "FROM resumes WHERE id=? AND user_id=?",
        (resume_id, uid)
    ).fetchone()

    if not row:
        return None, "简历不存在"

    return {
        "id": row["id"],
        "title": row["title"],
        "resume_data": json.loads(row["resume_data"]),
        "template_config": json.loads(row["template_config"]),
        "is_default": bool(row["is_default"]),
    }, None


def load_default_resume(uid):
    """加载用户的默认简历（用于登录后自动恢复）"""
    c = _conn()
    row = c.execute(
        "SELECT id, title, resume_data, template_config "
        "FROM resumes WHERE user_id=? AND is_default=1 LIMIT 1",
        (uid,)
    ).fetchone()

    if not row:
        # 没有默认简历，尝试取最近更新的
        row = c.execute(
            "SELECT id, title, resume_data, template_config "
            "FROM resumes WHERE user_id=? ORDER BY updated_at DESC LIMIT 1",
            (uid,)
        ).fetchone()

    if not row:
        return None

    return {
        "id": row["id"],
        "title": row["title"],
        "resume_data": json.loads(row["resume_data"]),
        "template_config": json.loads(row["template_config"]),
    }


def delete_resume(uid, resume_id):
    """删除一份简历"""
    c = _conn()
    row = c.execute(
        "SELECT id FROM resumes WHERE id=? AND user_id=?",
        (resume_id, uid)
    ).fetchone()
    if not row:
        return False, "简历不存在"

    c.execute("DELETE FROM resumes WHERE id=? AND user_id=?", (resume_id, uid))
    c.commit()
    return True, None


# ═══════════════════════════════════════
# 初始化
# ═══════════════════════════════════════
init_db()
