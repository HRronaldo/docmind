"""
EPUB 解析器

使用 ebooklib 提取 EPUB 文件的文本内容。
"""

import ebooklib
from ebooklib import epub
from pathlib import Path
from typing import Optional


def extract_text_from_epub(file_path: str, max_chapters: Optional[int] = None) -> dict:
    """
    从 EPUB 文件中提取文本。

    Args:
        file_path: EPUB 文件路径
        max_chapters: 最大提取章节数（None = 全部）

    Returns:
        包含文本和元数据的字典
    """
    path = Path(file_path)

    if not path.exists():
        return {
            "success": False,
            "error": f"文件不存在: {file_path}"
        }

    if path.suffix.lower() not in [".epub", ".mobi"]:
        return {
            "success": False,
            "error": "文件必须是 EPUB 或 MOBI 格式"
        }

    try:
        book = epub.read_epub(path)

        # 获取元数据
        metadata = {
            "file_name": path.name,
            "title": None,
            "author": None,
            "language": None,
        }

        for meta in book.get_metadata("DC", "title"):
            if meta:
                metadata["title"] = meta[0][0]

        for meta in book.get_metadata("DC", "creator"):
            if meta:
                metadata["author"] = meta[0][0]

        for meta in book.get_metadata("DC", "language"):
            if meta:
                metadata["language"] = meta[0][0]

        # 提取文本
        all_text = []
        chapter_count = 0

        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                content = item.get_content()

                # 简单提取标签内文本
                import re
                text = re.sub(r'<[^>]+>', ' ', content)
                text = re.sub(r'\s+', ' ', text).strip()

                if text and len(text) > 50:  # 过滤短内容
                    all_text.append(text)
                    chapter_count += 1

                    if max_chapters and chapter_count >= max_chapters:
                        break

        full_text = "\n\n".join(all_text)

        return {
            "success": True,
            "text": full_text,
            "metadata": {
                **metadata,
                "extracted_chapters": chapter_count,
                "char_count": len(full_text)
            }
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"解析失败: {str(e)}"
        }


def extract_epub_preview(file_path: str, max_chars: int = 2000) -> dict:
    """
    提取 EPUB 预览（前几章的摘要）。

    Args:
        file_path: EPUB 文件路径
        max_chars: 最大字符数

    Returns:
        预览文本
    """
    result = extract_text_from_epub(file_path, max_chapters=5)

    if result["success"]:
        text = result["text"]
        if len(text) > max_chars:
            text = text[:max_chars] + "\n\n... (内容已截断)"
        result["text"] = text
        result["preview"] = True
    else:
        result["preview"] = True

    return result
