"""
DocMind MCP Server

基于 FastMCP 实现的 MCP Server，提供文档摘要能力。
支持 Claude Desktop、OpenCode、Cursor 等 MCP 客户端。
"""

import os
import trafilatura
import requests
from typing import Optional
from fastmcp import FastMCP

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
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            downloaded = response.text

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

                    client = ZhipuAI(api_key=ZHIPU_API_KEY)
                    response = client.chat.completions.create(
                        model=GLM_MODEL, messages=[{"role": "user", "content": prompt}]
                    )
                    return response.choices[0].message.content
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


@mcp.resource("docmind://status")
def get_status() -> dict:
    """获取 DocMind 服务状态"""
    return {
        "name": "DocMind",
        "version": "0.1.0",
        "status": "running",
        "features": [
            "summarize_url - URL 摘要生成",
            "extract_article_content - 仅提取正文",
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
