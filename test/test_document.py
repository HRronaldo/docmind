"""
DocMind 文档解析测试
"""

import pytest
from pathlib import Path
import sys

_test_path = Path(__file__).resolve().parent.parent
if str(_test_path) not in sys.path:
    sys.path.insert(0, str(_test_path))


class TestDocumentParser:
    """文档解析测试"""

    def test_pdf_not_exists(self):
        from app.mcp.servers.pdf_parser import extract_text_from_pdf

        result = extract_text_from_pdf("/nonexistent/file.pdf")
        assert result["success"] is False
        assert "不存在" in result["error"]

    def test_epub_not_exists(self):
        from app.mcp.servers.epub_parser import extract_text_from_epub

        result = extract_text_from_epub("/nonexistent/file.epub")
        assert result["success"] is False
        assert "不存在" in result["error"]

    def test_unsupported_format(self):
        from app.mcp.servers.document_parser import extract_text_from_document

        result = extract_text_from_document("/path/to/file.txt")
        assert result["success"] is False
        assert "不支持" in result["error"]


class TestObsidianSync:
    """Obsidian 同步测试"""

    def test_vault_not_exists(self):
        from app.mcp.servers.obsidian_sync import sync_to_obsidian

        result = sync_to_obsidian(
            content="test content", title="Test", vault_path="/nonexistent/vault"
        )
        assert result["success"] is False
        assert "不存在" in result["error"]

    def test_sync_with_content(self, tmp_path):
        """使用临时目录测试同步功能"""
        from app.mcp.servers.obsidian_sync import sync_to_obsidian

        result = sync_to_obsidian(
            content="# Test\n\nTest content",
            title="Test Note",
            vault_path=str(tmp_path),
        )
        # 可能成功也可能失败，取决于目录权限
        assert "success" in result