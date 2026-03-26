"""
jd_matcher.py — JD 匹配分析业务逻辑
"""

import json
import os

from services.gemini_client import call_gemini

# 加载提示词模板
_prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "jd_prompt.txt")
with open(_prompt_path, "r", encoding="utf-8") as f:
    JD_PROMPT_TEMPLATE = f.read()


def match_jd(resume_text: str, jd_text: str) -> dict:
    """
    简历与 JD 匹配度分析

    Args:
        resume_text: 用户输入的简历文本
        jd_text: 目标岗位的职位描述

    Returns:
        结构化的匹配分析结果字典
    """
    if not resume_text or not resume_text.strip():
        raise ValueError("简历内容不能为空")
    if not jd_text or not jd_text.strip():
        raise ValueError("职位描述不能为空")

    # 填充模板
    prompt = JD_PROMPT_TEMPLATE.replace(
        "{resume_text}", resume_text.strip()
    ).replace(
        "{jd_text}", jd_text.strip()
    )

    # 调用 AI
    raw_response = call_gemini(prompt)

    # 解析 JSON
    result = _parse_json(raw_response)

    return result


def _parse_json(text: str) -> dict:
    """从 AI 返回的文本中提取 JSON"""
    cleaned = text.strip()

    # 去除 Markdown 代码块标记
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\n".join(lines)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
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