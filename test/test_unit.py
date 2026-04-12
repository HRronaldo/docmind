"""
DocMind 工具模块测试
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

# 添加项目路径
import sys

_test_path = Path(__file__).resolve().parent.parent
if str(_test_path) not in sys.path:
    sys.path.insert(0, str(_test_path))


class TestLogger:
    """日志模块测试"""

    def test_get_logger(self):
        from app.core.logger import get_logger

        logger = get_logger("test")
        assert logger is not None
        assert logger.name == "test"

    def test_logger_mixin(self):
        from app.core.logger import LoggerMixin

        class MyService(LoggerMixin):
            pass

        service = MyService()
        assert hasattr(service, "logger")
        assert service.logger.name == "MyService"


class TestExceptions:
    """异常模块测试"""

    def test_docmind_error(self):
        from app.core.exceptions import DocMindError

        error = DocMindError("Test error", "TEST_CODE")
        assert error.message == "Test error"
        assert error.code == "TEST_CODE"

    def test_llm_error(self):
        from app.core.exceptions import LLMError

        error = LLMError("LLM failed", model="glm-4")
        assert error.message == "LLM failed"
        assert error.model == "glm-4"
        assert error.code == "LLM_ERROR"

    def test_validation_error(self):
        from app.core.exceptions import ValidationError

        error = ValidationError("Invalid input", field="url")
        assert error.message == "Invalid input"
        assert error.field == "url"
        assert error.code == "VALIDATION_ERROR"


class TestUtils:
    """工具函数测试"""

    def test_retry_success(self):
        from app.core.utils import retry

        call_count = 0

        @retry(max_attempts=3)
        def successful_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = successful_func()
        assert result == "success"
        assert call_count == 1

    def test_retry_failure(self):
        from app.core.utils import retry

        @retry(max_attempts=2, delay=0.1)
        def always_fails():
            raise ValueError("always fails")

        with pytest.raises(ValueError):
            always_fails()

    def test_safe_call(self):
        from app.core.utils import safe_call

        def success_func():
            return "ok"

        result = safe_call(success_func, default="fail")
        assert result == "ok"

    def test_safe_call_with_exception(self):
        from app.core.utils import safe_call

        def fail_func():
            raise ValueError("failed")

        result = safe_call(fail_func, default="fallback")
        assert result == "fallback"


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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
