"""
NLP 模块
========

中文自然语言处理模块，提供：
- 分词（jieba）
- 关键词提取
- 术语识别
- 知识图谱

用法：
```python
from app.nlp import segment_text, extract_keywords, KnowledgeGraph

# 分词
words = segment_text("这是一个中文句子")
print(words)  # ['这是', '一个', '中文', '句子']

# 关键词提取
keywords = extract_keywords("深度学习是机器学习的分支...", top_k=5)
print(keywords)  # ['深度学习', '机器学习', ...]

# 知识图谱
from app.nlp.kg import extract_entities_relations
result = extract_entities_relations("深度学习由神经网络组成，PyTorch是Facebook开发的框架")
print(result['entities'])
```
"""

from app.nlp.segmenter import segment_text, Segmenter
from app.nlp.keywords import extract_keywords, KeywordExtractor
from app.nlp.terms import TermRecognizer
from app.nlp.kg import KnowledgeGraph, extract_entities_relations, build_graph_from_texts
from app.nlp.templates import generate_note_template, generate_from_content, extract_highlights, NoteTemplate

__all__ = [
    "segment_text",
    "Segmenter",
    "extract_keywords",
    "KeywordExtractor",
    "TermRecognizer",
    "KnowledgeGraph",
    "extract_entities_relations",
    "build_graph_from_texts",
    "generate_note_template",
    "generate_from_content",
    "extract_highlights",
    "NoteTemplate",
]
