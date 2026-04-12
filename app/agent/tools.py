"""Tools for the Agent.

DocMind Agent 工具模块
=======================

本模块定义了 Agent 可以调用的工具（Tools）。
使用 LangChain 的 @tool 装饰器将函数转换为 Agent 可调用的工具。

工具列表：
- fetch_url_content: 抓取网页内容
- summarize_text: 文本摘要
- parse_pdf: 解析 PDF 文档
- parse_epub: 解析 EPUB 文档
- sync_to_obsidian: 同步到 Obsidian

这些工具会被绑定到 LLM，使 Agent 能够自主决定何时调用工具。
"""

import trafilatura
import requests
from typing import Optional
from langchain_core.tools import tool
from pathlib import Path

# 导入文档解析功能
from app.mcp.servers.pdf_parser import extract_text_from_pdf
from app.mcp.servers.epub_parser import extract_text_from_epub
from app.mcp.servers.obsidian_sync import sync_document_to_obsidian


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


@tool
def parse_pdf(file_path: str, max_chars: int = 50000) -> str:
    """
    解析 PDF 文档并提取文本内容。

    适用于：
    - 技术文档
    - 论文
    - 电子书
    - 简历

    Args:
        file_path: PDF 文件的绝对路径
        max_chars: 最大提取字符数（默认 50000）

    Returns:
        提取的文本内容及元数据
    """
    if not file_path:
        return "Error: 文件路径不能为空"

    # 转换为 Path 对象
    path = Path(file_path)

    # 验证文件存在
    if not path.exists():
        return f"Error: 文件不存在: {file_path}"

    # 验证文件格式
    if path.suffix.lower() != ".pdf":
        return "Error: 文件必须是 PDF 格式"

    try:
        result = extract_text_from_pdf(file_path, max_chars=max_chars)

        if result.get("success"):
            metadata = result.get("metadata", {})
            text = result.get("text", "")

            header = f"""【PDF 解析结果】
文件名: {metadata.get("file_name", "Unknown")}
页数: {metadata.get("total_pages", "N/A")}
字符数: {metadata.get("char_count", len(text))}

---
"""
            return header + text
        else:
            return f"Error: {result.get('error', '解析失败')}"

    except Exception as e:
        return f"Error: {str(e)}"


@tool
def parse_epub(file_path: str, max_chars: int = 50000) -> str:
    """
    解析 EPUB 电子书并提取文本内容。

    适用于：
    - 电子书
    - 技术书籍
    - 小说

    Args:
        file_path: EPUB 文件的绝对路径
        max_chars: 最大提取字符数（默认 50000）

    Returns:
        提取的文本内容及元数据
    """
    if not file_path:
        return "Error: 文件路径不能为空"

    path = Path(file_path)

    if not path.exists():
        return f"Error: 文件不存在: {file_path}"

    if path.suffix.lower() not in [".epub", ".mobi"]:
        return "Error: 文件必须是 EPUB 或 MOBI 格式"

    try:
        result = extract_text_from_epub(file_path, max_chars=max_chars)

        if result.get("success"):
            metadata = result.get("metadata", {})
            text = result.get("text", "")

            header = f"""【EPUB 解析结果】
文件名: {metadata.get("file_name", "Unknown")}
标题: {metadata.get("title", "N/A")}
作者: {metadata.get("author", "N/A")}
字符数: {metadata.get("char_count", len(text))}

---
"""
            return header + text
        else:
            return f"Error: {result.get('error', '解析失败')}"

    except Exception as e:
        return f"Error: {str(e)}"


@tool
def sync_to_obsidian(
    content: str, title: str, vault_path: str, folder: str = "DocMind"
) -> str:
    """
    将内容同步到 Obsidian vault。

    自动创建 Markdown 文件，包含 YAML frontmatter 元数据。

    Args:
        content: 要保存的内容（Markdown 格式）
        title: 文档标题
        vault_path: Obsidian vault 的路径（文件夹路径）
        folder: 保存的子文件夹（默认 DocMind）

    Returns:
        操作结果，包含文件路径
    """
    if not content:
        return "Error: 内容不能为空"
    if not title:
        return "Error: 标题不能为空"
    if not vault_path:
        return "Error: Obsidian vault 路径不能为空"

    try:
        result = sync_document_to_obsidian(
            document_result={
                "success": True,
                "text": content,
                "metadata": {"title": title, "file_name": f"{title}.md"},
            },
            vault_path=vault_path,
            folder=folder,
            tags=["docmind"],
        )

        if result.get("success"):
            return f"""✅ 已同步到 Obsidian

文件路径: {result.get("path", "N/A")}
相对路径: {result.get("relative_path", "N/A")}"""
        else:
            return f"Error: {result.get('error', '同步失败')}"

    except Exception as e:
        return f"Error: {str(e)}"


# ===== 可用工具列表 =====
# 这个列表会被绑定到 LLM，使 Agent 能够调用这些工具
AVAILABLE_TOOLS = [
    fetch_url_content,
    summarize_text,
    parse_pdf,
    parse_epub,
    sync_to_obsidian,
]
