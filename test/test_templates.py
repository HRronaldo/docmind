"""
DocMind 笔记模板测试
"""

import pytest
from pathlib import Path
import sys

_test_path = Path(__file__).resolve().parent.parent
if str(_test_path) not in sys.path:
    sys.path.insert(0, str(_test_path))


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

    def test_review_template(self):
        """测试复习模板"""
        from app.nlp.templates import generate_note_template, generate_review_schedule
        
        # Test review template
        template = generate_note_template(
            "review", 
            title="深度学习",
            first_date="2026-04-26"
        )
        assert "复习笔记" in template
        assert "深度学习" in template
        
        # Test review schedule
        schedule = generate_review_schedule("test", first_date="2026-04-26")
        assert "reviews" in schedule
        assert len(schedule["reviews"]) == 5

    def test_review_schedule_intervals(self):
        """测试复习间隔"""
        from app.nlp.templates import generate_review_schedule
        
        schedule = generate_review_schedule("test", first_date="2026-04-26")
        intervals = schedule["intervals"]
        
        # 默认间隔: 1, 3, 7, 14, 30
        assert intervals == [1, 3, 7, 14, 30]
        
        # 第一天复习日期
        assert schedule["reviews"][0]["day"] == 1
        assert schedule["reviews"][0]["date"] == "2026-04-27"