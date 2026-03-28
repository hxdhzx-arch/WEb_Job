"""
email_sender.py — 验证码邮件发送 (SMTP)
支持 QQ邮箱 / Gmail / 企业邮箱 等任意 SMTP 服务
"""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_FROM


def send_verify_code(to_email: str, code: str, purpose: str = "bind") -> tuple:
    """
    发送验证码邮件
    返回 (success: bool, error_msg: str | None)
    """
    if not SMTP_HOST or not SMTP_USER:
        print("[邮件] SMTP 未配置，验证码: %s → %s" % (code, to_email))
        # 开发模式：SMTP 未配置时不报错，打印到控制台
        return True, None

    subject_map = {
        "bind": "简历 AI — 绑定账号验证码",
        "login": "简历 AI — 登录验证码",
    }
    subject = subject_map.get(purpose, "简历 AI — 验证码")

    html_body = _build_email_html(code, purpose)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SMTP_FROM or SMTP_USER
    msg["To"] = to_email

    # 纯文本后备
    plain = "您的验证码是：%s，5 分钟内有效。如非本人操作，请忽略。" % code
    msg.attach(MIMEText(plain, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        if SMTP_PORT == 465:
            # SSL 直连（QQ 邮箱默认）
            ctx = ssl.create_default_context()
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ctx, timeout=10) as server:
                server.login(SMTP_USER, SMTP_PASS)
                server.sendmail(SMTP_USER, to_email, msg.as_string())
        else:
            # STARTTLS（Gmail / 企业邮箱常用 587 端口）
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
                server.ehlo()
                server.starttls(context=ssl.create_default_context())
                server.ehlo()
                server.login(SMTP_USER, SMTP_PASS)
                server.sendmail(SMTP_USER, to_email, msg.as_string())

        print("[邮件] 验证码已发送 → %s" % to_email)
        return True, None

    except smtplib.SMTPAuthenticationError:
        print("[邮件] SMTP 认证失败，请检查 SMTP_USER / SMTP_PASS")
        return False, "邮件服务配置异常，请联系管理员"
    except smtplib.SMTPRecipientsRefused:
        return False, "邮箱地址无效或被拒收"
    except Exception as e:
        print("[邮件] 发送失败: %s" % e)
        return False, "邮件发送失败，请稍后重试"


def _build_email_html(code: str, purpose: str) -> str:
    """生成美观的验证码邮件 HTML"""
    action = "绑定账号" if purpose == "bind" else "登录"
    return """
<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#f2f2f7;font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Noto Sans SC',sans-serif">
<table width="100%%" cellpadding="0" cellspacing="0" style="padding:40px 20px">
<tr><td align="center">
<table width="420" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:16px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,.06)">
  <tr><td style="padding:32px 36px 0;text-align:center">
    <div style="font-size:18px;font-weight:700;color:#1d1d1f;margin-bottom:6px">简历 AI</div>
    <div style="font-size:13px;color:#86868b">%(action)s验证码</div>
  </td></tr>
  <tr><td style="padding:28px 36px;text-align:center">
    <div style="font-size:36px;font-weight:800;letter-spacing:8px;color:#007AFF;background:#EEF2FF;border-radius:12px;padding:18px 0;margin:0 auto;max-width:240px">%(code)s</div>
    <div style="margin-top:16px;font-size:13px;color:#86868b;line-height:1.6">
      此验证码用于%(action)s操作，<strong style="color:#1d1d1f">5 分钟内有效</strong>。<br>
      如非本人操作，请忽略此邮件。
    </div>
  </td></tr>
  <tr><td style="padding:0 36px 28px;text-align:center">
    <div style="border-top:1px solid #f2f2f7;padding-top:16px;font-size:11px;color:#c7c7cc">
      此邮件由系统自动发送，请勿回复
    </div>
  </td></tr>
</table>
</td></tr></table>
</body></html>
""" % {"code": code, "action": action}
