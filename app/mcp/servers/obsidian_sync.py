"""
Obsidian 同步器

将解析后的文档同步到 Obsidian vault。
"""

from pathlib import Path
from datetime import datetime
from typing import Optional


def sync_to_obsidian(
    content: str,
    title: str,
    vault_path: str,
    folder: str = "DocMind",
    tags: Optional[list[str]] = None,
) -> dict:
    """
    将内容同步到 Obsidian vault。

    Args:
        content: 文档内容（Markdown 格式）
        title: 文档标题
        vault_path: Obsidian vault 路径
        folder: 保存的子文件夹（默认 DocMind）
        tags: 可选的标签列表

    Returns:
        操作结果
    """
    # 验证 vault 路径
    vault = Path(vault_path)
    if not vault.exists():
        return {"success": False, "error": f"Obsidian vault 不存在: {vault_path}"}

    # 创建子文件夹
    target_folder = vault / folder
    target_folder.mkdir(parents=True, exist_ok=True)

    # 生成安全的文件名
    safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in title)
    safe_title = safe_title[:100]  # 限制长度

    # 添加时间戳
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{safe_title}.md"
    file_path = target_folder / filename

    # 生成 frontmatter
    frontmatter = f"""---
created: {datetime.now().isoformat()}
source: DocMind
tags: [{", ".join(tags) if tags else "docmind"}]
---

"""

    # 写入文件
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(frontmatter)
            f.write(f"# {title}\n\n")
            f.write(content)

        return {
            "success": True,
            "path": str(file_path),
            "relative_path": f"{folder}/{filename}",
        }
    except Exception as e:
        return {"success": False, "error": f"写入失败: {str(e)}"}


def sync_document_to_obsidian(
    document_result: dict,
    vault_path: str,
    folder: str = "DocMind",
    tags: Optional[list[str]] = None,
) -> dict:
    """
    将文档解析结果同步到 Obsidian。

    Args:
        document_result: extract_text_from_document() 的返回值
        vault_path: Obsidian vault 路径
        folder: 保存的子文件夹
        tags: 可选的标签

    Returns:
        同步结果
    """
    if not document_result.get("success"):
        return document_result

    metadata = document_result.get("metadata", {})
    text = document_result.get("text", "")

    # 生成标题
    title = metadata.get("title") or metadata.get("file_name", "Untitled")
    title = title.replace(".pdf", "").replace(".epub", "").replace(".mobi", "")

    # 添加文档信息
    content = text

    # 如果有页数信息，添加摘要
    if metadata.get("total_pages"):
        content = f"**文档**: {metadata.get('file_name')}\n"
        content += f"**页数**: {metadata.get('total_pages')}\n\n"
        if metadata.get("author"):
            content += f"**作者**: {metadata.get('author')}\n\n"
        content += "---\n\n"
        content += text

    # 同步到 Obsidian
    return sync_to_obsidian(
        content=content, title=title, vault_path=vault_path, folder=folder, tags=tags
    )
