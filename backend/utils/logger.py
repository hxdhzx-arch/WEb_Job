"""
utils/logger.py — 结构化运营脱敏日志
"""
import logging
import json
import traceback
from datetime import datetime, timezone
from flask import request, has_request_context
from backend.models.error_log import log_error
from backend.extensions import db

class SafeStructuredLogger:
    def __init__(self, name="SaaS_App"):
        self.logger = logging.getLogger(name)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
            # 避免重复打印到 werkzeug 级别的标准输出
            self.logger.propagate = False

    def _sanitize(self, data):
        """过滤核心敏感字段防泄密"""
        if not isinstance(data, dict):
            return data
        safe_data = data.copy()
        sensitive_keys = ['password', 'token', 'secret', 'code', 'session', 'card', 'cvv']
        for k in safe_data.keys():
            if any(s in k.lower() for s in sensitive_keys):
                safe_data[k] = "***MASKED***"
            elif isinstance(safe_data[k], dict):
                safe_data[k] = self._sanitize(safe_data[k])
        return safe_data

    def _get_context_info(self):
        ctx = {"ip": None, "endpoint": None, "method": None, "user_id": None}
        if has_request_context():
            ctx["ip"] = request.remote_addr
            ctx["endpoint"] = request.path
            ctx["method"] = request.method
            try:
                from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
                verify_jwt_in_request(optional=True)
                uid = get_jwt_identity()
                if uid:
                    ctx["user_id"] = int(uid)
            except Exception:
                pass
        return ctx

    def _log(self, level, module, event, data=None, exc_info=None, save_db=False):
        safe_data = self._sanitize(data) if data else {}
        ctx = self._get_context_info()
        
        log_payload = {
            "module": module,
            "event": event,
            "ctx": ctx,
            "data": safe_data,
        }
        
        log_str = json.dumps(log_payload, ensure_ascii=False)
        
        if level == "INFO":
            self.logger.info(log_str)
        elif level == "WARNING":
            self.logger.warning(log_str)
        elif level in ["ERROR", "CRITICAL"]:
            if level == "CRITICAL":
                self.logger.critical(log_str, exc_info=exc_info)
            else:
                self.logger.error(log_str, exc_info=exc_info)
                
            if save_db:
                tb_str = traceback.format_exc() if exc_info else None
                try:
                    log_error(
                        message=event + (" | " + json.dumps(safe_data) if safe_data else ""),
                        module=module,
                        traceback_str=tb_str,
                        user_id=ctx["user_id"],
                        ip=ctx["ip"],
                        endpoint=ctx["endpoint"],
                        method=ctx["method"],
                        level=level.lower()
                    )
                except Exception:
                    pass

    def info(self, module, event, data=None):
        self._log("INFO", module, event, data)
        
    def warning(self, module, event, data=None):
        self._log("WARNING", module, event, data)
        
    def error(self, module, event, data=None, exc_info=None, save_db=True):
        self._log("ERROR", module, event, data, exc_info, save_db)
        
    def critical(self, module, event, data=None, exc_info=None, save_db=True):
        self._log("CRITICAL", module, event, data, exc_info, save_db)

sys_logger = SafeStructuredLogger()
