"""
verify.py — 验证码生成、校验、限流引擎
"""
import random
import time
import re

# ── 常量 ──
CODE_LENGTH = 6
CODE_TTL = 300          # 5 分钟过期
COOLDOWN = 60           # 同目标 60 秒冷却
HOURLY_CAP = 5          # 同目标 1 小时内最多发 5 次
MAX_ATTEMPTS = 5        # 错误尝试 5 次后作废

# 邮箱正则
_EMAIL_RE = re.compile(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$')
# 手机号正则（中国大陆）
_PHONE_RE = re.compile(r'^1[3-9]\d{9}$')


def validate_target(target: str) -> tuple:
    """
    校验目标格式，返回 (target_type, cleaned, error)
    target_type: 'email' | 'phone'
    """
    if not target or not target.strip():
        return None, None, "请输入邮箱或手机号"

    cleaned = target.strip().lower()

    if _EMAIL_RE.match(cleaned):
        return "email", cleaned, None

    # 去除手机号中的空格和横线
    phone_cleaned = re.sub(r'[\s\-]', '', target.strip())
    if _PHONE_RE.match(phone_cleaned):
        return "phone", phone_cleaned, None

    return None, None, "邮箱或手机号格式不正确"


def generate_code() -> str:
    """生成 6 位数字验证码"""
    return ''.join([str(random.randint(0, 9)) for _ in range(CODE_LENGTH)])


def can_send(db_conn, target: str, purpose: str = "bind") -> tuple:
    """
    检查是否可以发送验证码（限流）
    返回 (ok: bool, error_msg: str | None, wait_seconds: int)
    """
    now = time.time()
    c = db_conn

    # 检查 60 秒冷却
    last = c.execute(
        "SELECT created_at FROM verify_codes "
        "WHERE target=? AND purpose=? ORDER BY created_at DESC LIMIT 1",
        (target, purpose)
    ).fetchone()

    if last:
        elapsed = now - last["created_at"]
        if elapsed < COOLDOWN:
            wait = int(COOLDOWN - elapsed) + 1
            return False, "发送过于频繁，请 %d 秒后重试" % wait, wait

    # 检查 1 小时上限
    one_hour_ago = now - 3600
    count = c.execute(
        "SELECT COUNT(*) FROM verify_codes "
        "WHERE target=? AND created_at>?",
        (target, one_hour_ago)
    ).fetchone()[0]

    if count >= HOURLY_CAP:
        return False, "验证码发送次数过多，请 1 小时后重试", 3600

    return True, None, 0


def create_code(db_conn, target: str, purpose: str = "bind") -> str:
    """
    生成验证码并写入数据库
    返回 code 字符串
    """
    code = generate_code()
    now = time.time()

    # 将同 target+purpose 的旧未用验证码标记为已用（防止旧码仍可验证）
    db_conn.execute(
        "UPDATE verify_codes SET used=1 "
        "WHERE target=? AND purpose=? AND used=0",
        (target, purpose)
    )

    db_conn.execute(
        "INSERT INTO verify_codes(target, code, purpose, attempts, created_at, expires_at, used) "
        "VALUES(?, ?, ?, 0, ?, ?, 0)",
        (target, code, purpose, now, now + CODE_TTL)
    )
    db_conn.commit()
    return code


def verify_code(db_conn, target: str, code: str, purpose: str = "bind") -> tuple:
    """
    校验验证码
    返回 (valid: bool, error_msg: str | None)
    """
    if not code or len(code) != CODE_LENGTH:
        return False, "请输入 %d 位验证码" % CODE_LENGTH

    now = time.time()
    c = db_conn

    row = c.execute(
        "SELECT id, code, attempts, expires_at, used FROM verify_codes "
        "WHERE target=? AND purpose=? AND used=0 "
        "ORDER BY created_at DESC LIMIT 1",
        (target, purpose)
    ).fetchone()

    if not row:
        return False, "验证码不存在或已过期，请重新获取"

    # 已过期
    if now > row["expires_at"]:
        c.execute("UPDATE verify_codes SET used=1 WHERE id=?", (row["id"],))
        c.commit()
        return False, "验证码已过期，请重新获取"

    # 尝试次数过多
    if row["attempts"] >= MAX_ATTEMPTS:
        c.execute("UPDATE verify_codes SET used=1 WHERE id=?", (row["id"],))
        c.commit()
        return False, "错误次数过多，验证码已失效，请重新获取"

    # 验证码不匹配
    if row["code"] != code.strip():
        c.execute(
            "UPDATE verify_codes SET attempts=attempts+1 WHERE id=?",
            (row["id"],)
        )
        c.commit()
        remaining = MAX_ATTEMPTS - row["attempts"] - 1
        if remaining <= 0:
            return False, "验证码错误次数过多，请重新获取"
        return False, "验证码错误，还可尝试 %d 次" % remaining

    # 验证通过 → 标记已用
    c.execute("UPDATE verify_codes SET used=1 WHERE id=?", (row["id"],))
    c.commit()
    return True, None


def cleanup_expired(db_conn):
    """清理过期验证码（可定期调用）"""
    cutoff = time.time() - 3600  # 清理 1 小时前的
    db_conn.execute("DELETE FROM verify_codes WHERE created_at < ?", (cutoff,))
    db_conn.commit()
