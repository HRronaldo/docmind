"""Tools for the Agent.

DocMind Agent 工具模块
=======================

本模块定义了 Agent 可以调用的工具（Tools）。
使用 LangChain 的 @tool 装饰器将函数转换为 Agent 可调用的工具。

工具列表：
- fetch_url_content: 抓取网页内容
- summarize_text: 文本摘要

这些工具会被绑定到 LLM，使 Agent 能够自主决定何时调用工具。
"""

import trafilatura
import requests
from typing import Optional
from langchain_core.tools import tool


@tool
def fetch_url_content(url: str) -> str:
    """
    抓取并提取网页主要内容。

    这是 DocMind 的核心工具之一，负责：
    1. 访问指定 URL
    2. 智能提取正文内容（去除广告、导航等噪音）
    3. 返回结构化的文本

    使用 trafilatura 库进行智能提取，支持：
    - 新闻文章
    - 博客帖子
    - 技术文档
    - 论坛帖子

    Args:
        url: 要抓取的网页 URL

    Returns:
        提取的正文内容，或错误信息
    """
    if not url:
        return "Error: URL cannot be empty"

    # URL 验证
    if not url.startswith(("http://", "https://")):
        return "Error: URL must start with http:// or https://"

    try:
        # ===== 方法1：使用 trafilatura（智能提取） =====
        # trafilatura 是一个专门用于提取网页正文的库
        # 它能智能识别并提取文章的主要内容
        downloaded = trafilatura.fetch_url(url)

        # ===== 方法2：备用方案（直接请求） =====
        if downloaded is None:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            downloaded = response.text

        # ===== 提取正文 =====
        result = trafilatura.extract(
            downloaded, include_links=True, include_images=True, output_format="json"
        )

        if result:
            import json

            data = json.loads(result)
            text = data.get("text", "")

            if text and len(text) > 100:
                # 返回包含标题的内容
                title = data.get("title", "Untitled")
                return f"## {title}\n\n{text}"
            else:
                return "Error: Could not extract meaningful content from this URL"
        else:
            return "Error: Could not extract content from this webpage"

    except requests.exceptions.Timeout:
        return "Error: Request timed out. Please try a different URL."
    except requests.exceptions.RequestException as e:
        return f"Error: Failed to fetch URL - {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def summarize_text(text: str, max_length: int = 500) -> str:
    """
    对给定文本进行摘要（基础版本）。

    注意：这个是一个简单的基于提取的摘要方法。
    实际的智能摘要由 GLM 大模型完成。

    Args:
        text: 要摘要的文本
        max_length: 摘要的最大字符数

    Returns:
        摘要后的文本
    """
    if not text:
        return "Error: No text provided"

    # 如果文本已经较短，直接返回
    if len(text) <= max_length:
        return text

    # 简单的句子提取摘要
    sentences = text.replace("\n", " ").split(". ")
    if len(sentences) <= 3:
        return text[:max_length] + "..."

    # 取前几句作为摘要
    summary = ". ".join(sentences[:3]) + "..."
    return summary


# ===== 可用工具列表 =====
# 这个列表会被绑定到 LLM，使 Agent 能够调用这些工具
AVAILABLE_TOOLS = [fetch_url_content, summarize_text]
