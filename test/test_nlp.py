"""
DocMind NLP 模块测试
"""

import pytest
from pathlib import Path
import sys

_test_path = Path(__file__).resolve().parent.parent
if str(_test_path) not in sys.path:
    sys.path.insert(0, str(_test_path))


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