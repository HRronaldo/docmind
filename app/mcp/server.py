"""
DocMind MCP Server

基于 FastMCP 实现的 MCP Server，提供文档摘要能力。
支持 Claude Desktop、OpenCode、Cursor 等 MCP 客户端。
"""

import os
import trafilatura
import requests
from dotenv import load_dotenv
from typing import Optional
from fastmcp import FastMCP

from app.agent.multi_agent import get_multi_agent
from app.mcp.servers import (
    extract_text_from_document,
    extract_document_preview,
    sync_document_to_obsidian,
)

# 自动加载项目根目录的 .env 文件
load_dotenv()

# 初始化 MCP Server
mcp = FastMCP("DocMind")

# 获取环境变量中的 API Key
ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY", "")
GLM_MODEL = os.getenv("GLM_MODEL", "glm-4")


@mcp.tool()
def summarize_url(url: str, question: Optional[str] = None) -> str:
    """
    抓取网页内容并生成摘要。

    Args:
        url: 要抓取的网页 URL
        question: 可选的问题，用于定制化摘要

    Returns:
        摘要文本
    """
    if not url:
        return "Error: URL 不能为空"

    if not url.startswith(("http://", "https://")):
        return "Error: URL 必须以 http:// 或 https:// 开头"

    try:
        # 抓取网页
        downloaded = trafilatura.fetch_url(url)

        if downloaded is None:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            http_response = requests.get(url, headers=headers, timeout=30)
            http_response.raise_for_status()
            downloaded = http_response.text

        # 提取内容
        result = trafilatura.extract(
            downloaded, include_links=True, include_images=True, output_format="json"
        )

        if result:
            import json

            data = json.loads(result)
            text = data.get("text", "")
            title = data.get("title", "Untitled")

            if text and len(text) > 100:
                # 构建问题
                if question:
                    prompt = (
                        f"根据以下内容，回答问题：'{question}'\n\n内容：{text[:10000]}"
                    )
                else:
                    prompt = (
                        f"请总结以下文章的主要内容，要求简洁准确：\n\n{text[:10000]}"
                    )

                # 调用 GLM API
                if ZHIPU_API_KEY:
                    from zhipuai import ZhipuAI
                    from typing import Any

                    client = ZhipuAI(api_key=ZHIPU_API_KEY)
                    # 非流式响应
                    response: Any = client.chat.completions.create(
                        model=GLM_MODEL,
                        messages=[{"role": "user", "content": prompt}],
                        stream=False,
                    )
                    # 提取内容
                    if response and hasattr(response, "choices") and response.choices:
                        content = response.choices[0].message.content
                    else:
                        content = None
                    return content if content else "Error: 未能获取有效响应"
                else:
                    # 没有 API Key，返回提取的文本
                    return f"## {title}\n\n{text[:2000]}...\n\n⚠️ 未配置 ZHIPU_API_KEY，无法生成智能摘要。"
            else:
                return "Error: 无法从该网页提取有意义的内容"
        else:
            return "Error: 无法提取网页内容"

    except requests.exceptions.Timeout:
        return "Error: 请求超时，请尝试其他 URL"
    except requests.exceptions.RequestException as e:
        return f"Error: 请求失败 - {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
def extract_article_content(url: str) -> str:
    """
    仅提取网页正文内容，不进行摘要。

    Args:
        url: 要抓取的网页 URL

    Returns:
        提取的正文内容
    """
    if not url:
        return "Error: URL 不能为空"

    if not url.startswith(("http://", "https://")):
        return "Error: URL 必须以 http:// 或 https:// 开头"

    try:
        downloaded = trafilatura.fetch_url(url)

        if downloaded is None:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            downloaded = response.text

        result = trafilatura.extract(
            downloaded, include_links=True, output_format="json"
        )

        if result:
            import json

            data = json.loads(result)
            text = data.get("text", "")
            title = data.get("title", "Untitled")

            if text:
                return f"# {title}\n\n{text}"
            else:
                return "Error: 无法提取内容"
        else:
            return "Error: 无法提取网页内容"

    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
async def chat(message: str) -> str:
    """
    处理用户对话。

    Args:
        message: 用户消息

    Returns:
        Agent 响应
    """
    agent = get_multi_agent()
    result = await agent.process_message(message)
    return result.get("response", "")


@mcp.tool()
def parse_document(file_path: str, max_chars: int = 50000) -> str:
    """
    解析 PDF 或 EPUB 文档并提取文本内容。

    Args:
        file_path: 文档文件路径（支持 .pdf, .epub, .mobi）
        max_chars: 最大提取字符数（默认 50000）

    Returns:
        提取的文本内容
    """
    if not file_path:
        return "Error: 文件路径不能为空"

    result = extract_text_from_document(file_path, max_chars=max_chars)

    if result["success"]:
        metadata = result.get("metadata", {})
        text = result.get("text", "")

        header = f"""## 文档解析结果

**文件名**: {metadata.get("file_name", "Unknown")}
**标题**: {metadata.get("title", "N/A")}
**作者**: {metadata.get("author", "N/A")}

"""

        if metadata.get("total_pages"):
            header += f"**页数**: {metadata.get('total_pages')}\n"
        if metadata.get("extracted_chapters"):
            header += f"**章节数**: {metadata.get('extracted_chapters')}\n"
        header += f"**字符数**: {metadata.get('char_count', len(text))}\n\n"

        return header + text
    else:
        return f"Error: {result.get('error', '未知错误')}"


@mcp.tool()
def parse_document_preview(file_path: str, max_chars: int = 2000) -> str:
    """
    解析文档并生成预览（快速摘要）。

    Args:
        file_path: 文档文件路径
        max_chars: 最大字符数（默认 2000）

    Returns:
        文档预览文本
    """
    if not file_path:
        return "Error: 文件路径不能为空"

    result = extract_document_preview(file_path, max_chars=max_chars)

    if result["success"]:
        metadata = result.get("metadata", {})
        text = result.get("text", "")

        header = f"""## 文档预览

**文件名**: {metadata.get("file_name", "Unknown")}
**字符数**: {metadata.get("char_count", len(text))}

---

"""

        return header + text
    else:
        return f"Error: {result.get('error', '未知错误')}"


@mcp.tool()
def sync_document_to_obsidian_tool(
    document_path: str,
    vault_path: str,
    folder: str = "DocMind",
    tags: Optional[str] = None,
) -> str:
    """
    解析文档并同步到 Obsidian vault。

    Args:
        document_path: 文档文件路径（PDF/EPUB）
        vault_path: Obsidian vault 路径
        folder: 保存的子文件夹（默认 DocMind）
        tags: 标签，逗号分隔（可选）

    Returns:
        同步结果
    """
    if not document_path:
        return "Error: 文档路径不能为空"

    if not vault_path:
        return "Error: Obsidian vault 路径不能为空"

    # 解析文档
    doc_result = extract_text_from_document(document_path)

    if not doc_result.get("success"):
        return f"Error: {doc_result.get('error', '解析失败')}"

    # 解析标签
    tag_list = [t.strip() for t in tags.split(",")] if tags else None

    # 同步到 Obsidian
    sync_result = sync_document_to_obsidian(
        document_result=doc_result, vault_path=vault_path, folder=folder, tags=tag_list
    )

    if sync_result.get("success"):
        return f"""✅ 文档已同步到 Obsidian

**路径**: {sync_result.get("relative_path")}
**文件**: {sync_result.get("path")}

文档已保存到 Obsidian vault 中的 {folder} 文件夹。"""
    else:
        return f"Error: {sync_result.get('error', '同步失败')}"


@mcp.resource("docmind://status")
def get_status() -> dict:
    """获取 DocMind 服务状态"""
    return {
        "name": "DocMind",
        "version": "0.3.0",
        "status": "running",
        "architecture": "Supervisor + Workers + Aggregator",
        "features": [
            "chat - Multi-Agent 对话（Supervisor 决策）",
            "summarize_url - URL 摘要生成",
            "extract_article_content - 仅提取正文",
            "parse_document - PDF/EPUB 文档解析",
            "parse_document_preview - 文档预览",
            "sync_document_to_obsidian - 同步到 Obsidian",
        ],
    }


if __name__ == "__main__":
    import sys

    # 支持不同的传输模式
    if len(sys.argv) > 1:
        transport = sys.argv[1]
        if transport == "sse":
            # SSE 模式（HTTP 长连接）
            mcp.run(transport="sse")
        elif transport == "stdio":
            # STDIO 模式（本地运行）
            mcp.run(transport="stdio")
        else:
            mcp.run()
    else:
        # 默认 STDIO 模式
        mcp.run()
