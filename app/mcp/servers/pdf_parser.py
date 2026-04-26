"""
PDF 解析器

使用 pdfplumber 提取 PDF 文件的文本内容。
"""

import pdfplumber
from pathlib import Path
from typing import Optional


def extract_text_from_pdf(file_path: str, max_pages: Optional[int] = None, layout: bool = True) -> dict:
    """
    从 PDF 文件中提取文本。

    Args:
        file_path: PDF 文件路径
        max_pages: 最大提取页数（None = 全部）
        layout: 是否保留布局格式

    Returns:
        包含文本和元数据的字典
    """
    path = Path(file_path)

    if not path.exists():
        return {
            "success": False,
            "error": f"文件不存在: {file_path}"
        }

    if path.suffix.lower() != ".pdf":
        return {
            "success": False,
            "error": "文件必须是 PDF 格式"
        }

    try:
        with pdfplumber.open(path) as pdf:
            total_pages = len(pdf.pages)
            pages_to_extract = min(total_pages, max_pages) if max_pages else total_pages

            all_text = []
            for i, page in enumerate(pdf.pages[:pages_to_extract]):
                text = page.extract_text(layout=layout)
                if text:
                    all_text.append(f"[第 {i+1} 页]\n{text}")

            return {
                "success": True,
                "text": "\n\n".join(all_text),
                "metadata": {
                    "file_name": path.name,
                    "total_pages": total_pages,
                    "extracted_pages": pages_to_extract,
                    "char_count": sum(len(t) for t in all_text)
                }
            }

    except Exception as e:
        return {
            "success": False,
            "error": f"解析失败: {str(e)}"
        }


def extract_pdf_preview(file_path: str, max_chars: int = 2000) -> dict:
    """
    提取 PDF 预览（前几页的摘要）。

    Args:
        file_path: PDF 文件路径
        max_chars: 最大字符数

    Returns:
        预览文本
    """
    result = extract_text_from_pdf(file_path, max_pages=3)

    if result["success"]:
        text = result["text"]
        if len(text) > max_chars:
            text = text[:max_chars] + "\n\n... (内容已截断)"
        result["text"] = text
        result["preview"] = True
    else:
        result["preview"] = True

    return result
