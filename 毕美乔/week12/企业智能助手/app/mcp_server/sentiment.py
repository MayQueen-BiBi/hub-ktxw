from typing import Annotated
from fastmcp import FastMCP
import requests
from app.config import API_KEY

mcp = FastMCP(
    name="Sentiment-Analysis-Tool",
    instructions="""
    This MCP server provides sentiment analysis capability.
    It calls Alibaba Cloud Bailian (Model Studio) model capability API.
    """
)


@mcp.tool
def sentiment_classify(
    text: Annotated[str, "Text to analyze sentiment"]
):
    """
    Perform sentiment analysis using DashScope API.
    """

    url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = f"""
请判断以下文本的情感倾向，只返回 JSON：
{{
  "label": "positive | negative | neutral",
  "score": 0-1
}}

文本：
{text}
"""

    payload = {
        "model": "qwen-turbo",
        "input": {
            "prompt": prompt
        },
        "parameters": {
            "temperature": 0.0
        }
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        resp.raise_for_status()

        # ⚠️ 简化解析（demo）
        content = resp.json()["output"]["text"]
        return content

    except Exception as e:
        return {
            "label": "neutral",
            "score": 0.0,
            "error": str(e)
        }
