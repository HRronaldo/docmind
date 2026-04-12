"""
NLP 模块
========

中文自然语言处理模块，提供：
- 分词（jieba）
- 关键词提取
- 术语识别

用法：
```python
from app.nlp import segment_text, extract_keywords

# 分词
words = segment_text("这是一个中文句子")
print(words)  # ['这是', '一个', '中文', '句子']

# 关键词提取
keywords = extract_keywords("深度学习是机器学习的分支...", top_k=5)
print(keywords)  # ['深度学习', '机器学习', ...]
```
"""

from app.nlp.segmenter import segment_text, Segmenter
from app.nlp.keywords import extract_keywords, KeywordExtractor
from app.nlp.terms import TermRecognizer

__all__ = [
    "segment_text",
    "Segmenter",
    "extract_keywords",
    "KeywordExtractor",
    "TermRecognizer",
]
