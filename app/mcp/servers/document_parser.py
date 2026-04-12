"""
文档解析 MCP Server

支持 PDF 和 EPUB 格式的文档解析。
"""

from pathlib import Path
from typing import Optional

from .pdf_parser import extract_text_from_pdf, extract_pdf_preview
from .epub_parser import extract_text_from_epub, extract_epub_preview


def extract_text_from_document(file_path: str, max_chars: Optional[int] = None) -> dict:
    """
    从文档（PDF/EPUB）中提取文本。

    Args:
        file_path: 文档文件路径
        max_chars: 最大字符数（None = 不限制）

    Returns:
        包含文本和元数据的字典
    """
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        result = extract_text_from_pdf(file_path)
    elif suffix in [".epub", ".mobi"]:
        result = extract_text_from_epub(file_path)
    else:
        return {
            "success": False,
            "error": f"不支持的文件格式: {suffix}，支持: .pdf, .epub, .mobi",
        }

    # 截断文本
    if result["success"] and max_chars:
        if len(result["text"]) > max_chars:
            result["text"] = result["text"][:max_chars] + "\n\n... (内容已截断)"

    return result


def extract_document_preview(file_path: str, max_chars: int = 2000) -> dict:
    """
    提取文档预览（快速摘要）。

    Args:
        file_path: 文档文件路径
        max_chars: 最大字符数

    Returns:
        预览文本
    """
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        result = extract_pdf_preview(file_path, max_chars)
    elif suffix in [".epub", ".mobi"]:
        result = extract_epub_preview(file_path, max_chars)
    else:
        return {
            "success": False,
            "error": f"不支持的文件格式: {suffix}，支持: .pdf, .epub, .mobi",
        }

    if result.get("success"):
        result["preview"] = True

    return result
