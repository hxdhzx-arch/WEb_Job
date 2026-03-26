"""
resume_analyzer.py — 简历诊断业务逻辑
"""

import json
import os

from services.gemini_client import call_gemini

# 加载提示词模板
_prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "resume_prompt.txt")
with open(_prompt_path, "r", encoding="utf-8") as f:
    RESUME_PROMPT_TEMPLATE = f.read()


def analyze_resume(resume_text: str) -> dict:
    """
    对简历进行全面诊断分析

    Args:
        resume_text: 用户输入的简历文本

    Returns:
        结构化的分析结果字典
    """
    if not resume_text or not resume_text.strip():
        raise ValueError("简历内容不能为空")

    # 填充模板
    prompt = RESUME_PROMPT_TEMPLATE.replace("{resume_text}", resume_text.strip())

    # 调用 AI
    raw_response = call_gemini(prompt)

    # 解析 JSON（兼容 AI 返回带 ```json 标记的情况）
    result = _parse_json(raw_response)

    return result


def _parse_json(text: str) -> dict:
    """从 AI 返回的文本中提取 JSON"""
    cleaned = text.strip()

    # 去除 Markdown 代码块标记
    if cleaned.startswith("```"):
        # 去掉第一行（```json）和最后一行（```）
        lines = cleaned.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\n".join(lines)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # JSON 解析失败，返回原始文本作为兜底
        return {
            "overall_score": 0,
            "dimensions": [],
            "highlights": [],
            "issues": ["AI 返回格式异常，请重试"],
            "suggestions": [],
            "rewritten_summary": "",
            "raw_response": text
        }