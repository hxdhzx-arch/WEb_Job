"""
database.py — SQLite 算力追踪 + 风控 + 评价系统
"""
import sqlite3, os, threading, time

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "resume_ai.db")
_local = threading.local()

INITIAL_CREDITS = 300
COST_PER_AI_CALL = 100
REWARD_PER_REVIEW = 100
MAX_UIDS_PER_DEVICE = 2
MAX_UIDS_PER_IP = 3

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
        created_at    REAL NOT NULL,
        updated_at    REAL NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_u_device ON users(device_hash);
    CREATE INDEX IF NOT EXISTS idx_u_ip ON users(ip_address);
    CREATE INDEX IF NOT EXISTS idx_u_email ON users(bind_email);

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
    """)
    c.commit()

def get_or_create_user(user_id, device_hash, ip):
    """返回 (user_dict, is_new, error_msg)"""
    c = _conn(); now = time.time()
    row = c.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
    if row:
        c.execute("UPDATE users SET device_hash=?,ip_address=?,updated_at=? WHERE user_id=?",
                  (device_hash, ip, now, user_id))
        c.commit()
        return dict(row), False, None
    # Anti-abuse: device check
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

def bind_account(uid, email=None, phone=None):
    c = _conn(); now = time.time()
    val = email or phone
    field = "bind_email" if email else "bind_phone"
    if not val: return None, "请输入邮箱或手机号"
    cur = c.execute("SELECT * FROM users WHERE user_id=?", (uid,)).fetchone()
    if not cur: return None, "用户不存在"
    existing = c.execute("SELECT * FROM users WHERE {}=? AND user_id!=?".format(field), (val, uid)).fetchone()
    if existing:
        guest_cr = cur["credits_left"]
        c.execute("UPDATE users SET credits_left=credits_left+?,updated_at=? WHERE user_id=?",
                  (guest_cr, now, existing["user_id"]))
        c.execute("DELETE FROM users WHERE user_id=?", (uid,))
        c.commit()
        merged = c.execute("SELECT * FROM users WHERE user_id=?", (existing["user_id"],)).fetchone()
        return {"merged":True,"new_user_id":existing["user_id"],"credits":merged["credits_left"],
                "message":"已将算力合并到已绑定账号"}, None
    c.execute("UPDATE users SET {}=?,updated_at=? WHERE user_id=?".format(field), (val, now, uid))
    c.commit()
    return {"merged":False,"credits":cur["credits_left"],"message":"绑定成功！算力与数据已永久保存"}, None

init_db()
