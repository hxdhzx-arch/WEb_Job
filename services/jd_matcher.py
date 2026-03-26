"""
jd_matcher.py — JD 匹配分析业务逻辑
"""

import json
import re
import os

from services.gemini_client import call_gemini
from services.privacy_mask import mask_resume_for_ai

# 加载提示词模板
_prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "jd_prompt.txt")
with open(_prompt_path, "r", encoding="utf-8") as f:
    JD_PROMPT_TEMPLATE = f.read()


def match_jd(resume_text: str, jd_text: str) -> dict:
    """
    简历与 JD 匹配度分析
    """
    if not resume_text or not resume_text.strip():
        raise ValueError("简历内容不能为空")
    if not jd_text or not jd_text.strip():
        raise ValueError("职位描述不能为空")

    # PII 脱敏后再发给 AI（JD 不含隐私，不需脱敏）
    safe_resume = mask_resume_for_ai(resume_text.strip())
    prompt = JD_PROMPT_TEMPLATE.replace(
        "{resume_text}", safe_resume
    ).replace(
        "{jd_text}", jd_text.strip()
    )

    raw_response = call_gemini(prompt)
    result = _parse_json(raw_response)
    return result


def _parse_json(text: str) -> dict:
    """从 AI 返回的文本中提取 JSON（增强版）"""
    cleaned = text.strip()

    # 方法1：尝试直接解析
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # 方法2：去除 Markdown 代码块标记
    code_block = re.search(r'```(?:json)?\s*\n?(.*?)\n?\s*```', cleaned, re.DOTALL)
    if code_block:
        try:
            return json.loads(code_block.group(1).strip())
        except json.JSONDecodeError:
            pass

    # 方法3：找到第一个 { 和最后一个 } 之间的内容
    first_brace = cleaned.find('{')
    last_brace = cleaned.rfind('}')
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        try:
            return json.loads(cleaned[first_brace:last_brace + 1])
        except json.JSONDecodeError:
            pass

    # 全部失败，返回兜底
    return {
        "match_score": 0,
        "sub_scores": {},
        "matched_keywords": [],
        "missing_keywords": [],
        "strengths": [],
        "gaps": ["AI 返回格式异常，请重试"],
        "suggestions": [],
        "tailored_summary": "",
        "raw_response": text
    }
