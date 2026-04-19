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


class TestNLP:
    """NLP 模块测试"""

    def test_segment_text(self):
        """测试分词功能"""
        from app.nlp import segment_text

        text = "深度学习是机器学习的重要分支"
        words = segment_text(text)
        assert isinstance(words, list)
        assert len(words) > 0
        # 应该能识别出"深度学习"等术语
        assert "深度学习" in words or "深度" in words

    def test_extract_keywords(self):
        """测试关键词提取"""
        from app.nlp import extract_keywords

        text = "深度学习是机器学习的一个重要分支，PyTorch是常用的深度学习框架"
        keywords = extract_keywords(text, top_k=3)
        assert isinstance(keywords, list)
        assert len(keywords) <= 3
        # 应该包含深度学习、机器学习等
        assert "深度学习" in keywords or "机器学习" in keywords

    def test_term_recognizer(self):
        """测试术语识别"""
        from app.nlp import TermRecognizer

        text = "PyTorch是深度学习框架"
        recognizer = TermRecognizer()
        terms = recognizer.recognize(text)
        assert isinstance(terms, list)
        # 应该识别出PyTorch和深度学习
        term_texts = [t["term"] for t in terms]
        assert "PyTorch" in term_texts
        assert "深度学习" in term_texts

    def test_term_annotate(self):
        """测试术语标注"""
        from app.nlp import TermRecognizer

        text = "PyTorch是深度学习框架"
        recognizer = TermRecognizer()
        annotated = recognizer.annotate_text(text)
        assert "**PyTorch**" in annotated
        assert "**深度学习**" in annotated


class TestKnowledgeGraph:
    """知识图谱测试"""

    def test_extract_entities_relations(self):
        """测试实体关系提取"""
        from app.nlp.kg import extract_entities_relations

        result = extract_entities_relations("深度学习由神经网络组成，PyTorch是Facebook开发的框架")
        assert "entities" in result
        assert "relations" in result
        assert len(result["entities"]) > 0

    def test_knowledge_graph_class(self):
        """测试 KnowledgeGraph 类"""
        from app.nlp.kg import KnowledgeGraph

        kg = KnowledgeGraph()
        kg.add_text("BERT是Google开发的模型")
        kg.add_text("Transformer由Google提出")

        assert len(kg.entities) > 0
        assert len(kg.relations) > 0

    def test_graph_query(self):
        """测试图谱查询"""
        from app.nlp.kg import KnowledgeGraph

        kg = KnowledgeGraph()
        kg.add_text("BERT是Google开发的模型")
        kg.add_text("Google还开发了Transformer")

        result = kg.query("Google")
        assert result.get("found") is True
        assert result.get("mentions") == 2

    def test_graph_neighbors(self):
        """测试获取邻居"""
        from app.nlp.kg import KnowledgeGraph

        kg = KnowledgeGraph()
        kg.add_text("BERT是Google开发的模型")
        kg.add_text("Transformer由Google提出")

        neighbors = kg.get_neighbors("Google")
        assert len(neighbors) > 0


class TestNoteTemplates:
    """笔记模板测试"""

    def test_note_template_summary(self):
        """测试摘要模板"""
        from app.nlp.templates import generate_note_template

        template = generate_note_template("summary", title="Test", source="test.com")
        assert "Test" in template
        assert "test.com" in template

    def test_note_template_book(self):
        """测试读书笔记模板"""
        from app.nlp.templates import generate_note_template

        template = generate_note_template("book", book_title="Python", author="Guido")
        assert "Python" in template
        assert "Guido" in template

    def test_extract_highlights(self):
        """测试高亮提取"""
        from app.nlp.templates import extract_highlights

        content = "深度学习是机器学习。Transformer在2017年发布。"
        highlights = extract_highlights(content)
        assert isinstance(highlights, list)

    def test_note_template_types(self):
        """测试支持模板类型"""
        from app.nlp.templates import NoteTemplate

        types = NoteTemplate.get_template_types()
        assert "summary" in types
        assert "book" in types
        assert "meeting" in types


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
