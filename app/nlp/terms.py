"""
术语识别模块
============

识别文本中的专业术语和技术词汇。

功能：
- 内置常用技术术语词典
- 支持自定义术语库
- 术语边界识别
- 术语分类（技术、人名、机构名等）

Usage:
```python
from app.nlp.terms import TermRecognizer, recognize_terms

# 简单用法
terms = recognize_terms("我正在学习 PyTorch 和深度学习")
print(terms)  # [{'term': 'PyTorch', 'type': 'tech', 'start': 9, 'end': 15}, ...]

# 高级用法
recognizer = TermRecognizer()
terms = recognizer.recognize("BERT 是 Google 提出的预训练模型", categories=['tech', 'org'])
```
"""

import re
from typing import List, Dict, Optional, Set, Tuple
from app.nlp.segmenter import add_word
from app.core.logger import get_logger

logger = get_logger("docmind.nlp.terms")

# 内置术语词典
TECH_TERMS: Dict[str, str] = {
    # AI/ML
    "深度学习": "tech",
    "机器学习": "tech",
    "神经网络": "tech",
    "人工智能": "tech",
    "自然语言处理": "tech",
    "计算机视觉": "tech",
    "强化学习": "tech",
    "迁移学习": "tech",
    "卷积神经网络": "tech",
    "循环神经网络": "tech",
    "长短期记忆网络": "tech",
    "LSTM": "tech",
    "RNN": "tech",
    "CNN": "tech",
    "Transformer": "tech",
    "注意力机制": "tech",
    "BERT": "tech",
    "GPT": "tech",
    "ChatGPT": "tech",
    "大语言模型": "tech",
    "LLM": "tech",
    "多模态": "tech",
    "Agent": "tech",
    "多Agent": "tech",
    "RAG": "tech",
    "LangChain": "tech",
    "LangGraph": "tech",
    "ReAct": "tech",
    "Supervisor": "tech",
    "Tool": "tech",
    "MCP": "tech",
    "Model Context Protocol": "tech",
    "Embedding": "tech",
    "向量数据库": "tech",
    # 框架/工具
    "PyTorch": "framework",
    "TensorFlow": "framework",
    "JAX": "framework",
    "FastAPI": "framework",
    "FastChat": "framework",
    "vLLM": "framework",
    "Ollama": "framework",
    "LangSmith": "framework",
    "sklearn": "framework",
    "pandas": "framework",
    "NumPy": "framework",
    "jieba": "framework",
    "trafilatura": "framework",
    "pdfplumber": "framework",
    "ebooklib": "framework",
    "PDFplumber": "framework",
    "EbookLib": "framework",
    # 算法/模型
    "TextRank": "algo",
    "TF-IDF": "algo",
    "BM25": "algo",
    "Word2Vec": "algo",
    "GloVe": "algo",
    "CLIP": "model",
    "CLIP": "model",
    "ResNet": "model",
    "VGG": "model",
    "YOLO": "model",
    "AlphaGo": "model",
    # 公司/组织
    "Google": "org",
    "OpenAI": "org",
    "Microsoft": "org",
    "Meta": "org",
    "Anthropic": "org",
    "智谱AI": "org",
    "智谱": "org",
    "百度": "org",
    "阿里": "org",
    "腾讯": "org",
    "字节跳动": "org",
    "清华大学": "org",
    "北京大学": "org",
    "MIT": "org",
    "Stanford": "org",
    # 产品
    "Obsidian": "product",
    "Notion": "product",
    "Roam Research": "product",
    "Logseq": "product",
    "flomo": "product",
    "简悦": "product",
    "Readwise": "product",
    "Product Hunt": "product",
    # 文件格式
    "PDF": "format",
    "EPUB": "format",
    "Markdown": "format",
    "JSON": "format",
    "YAML": "format",
    "XML": "format",
    "HTML": "format",
    "CSV": "format",
}


class TermRecognizer:
    """
    术语识别器

    功能：
    - 内置术语库匹配
    - 自定义术语添加
    - 术语分类过滤
    - 术语位置标注
    """

    def __init__(self, custom_terms: Optional[Dict[str, str]] = None):
        """
        初始化术语识别器

        Args:
            custom_terms: 自定义术语库，格式 {'术语': '类型'}
        """
        self.terms: Dict[str, str] = TECH_TERMS.copy()

        # 添加自定义术语
        if custom_terms:
            self.terms.update(custom_terms)

        # 将术语添加到 jieba 词典（提高分词准确性）
        for term in self.terms:
            add_word(term, freq=100)

        # 构建正则模式（按长度排序，优先匹配长词）
        self._build_pattern()

        logger.debug(f"TermRecognizer initialized with {len(self.terms)} terms")

    def _build_pattern(self):
        """构建正则匹配模式"""
        # 按长度降序排序
        sorted_terms = sorted(self.terms.keys(), key=len, reverse=True)
        # 转义特殊字符并构建模式
        escaped_terms = [re.escape(t) for t in sorted_terms]
        pattern = "|".join(escaped_terms)
        self.pattern = re.compile(pattern)

    def add_term(self, term: str, term_type: str = "custom"):
        """
        添加术语

        Args:
            term: 术语
            term_type: 类型 ('tech', 'framework', 'org', 'product', 'custom')
        """
        self.terms[term] = term_type
        add_word(term, freq=100)
        self._build_pattern()
        logger.debug(f"Added term: {term} ({term_type})")

    def add_terms(self, terms: Dict[str, str]):
        """
        批量添加术语

        Args:
            terms: 术语字典 {'术语': '类型'}
        """
        for term, term_type in terms.items():
            self.add_term(term, term_type)

    def recognize(
        self,
        text: str,
        categories: Optional[List[str]] = None,
    ) -> List[Dict]:
        """
        识别文本中的术语

        Args:
            text: 输入文本
            categories: 要识别的类别列表（如 ['tech', 'org']），None 表示全部

        Returns:
            术语列表，每个元素包含:
            - term: 术语文本
            - type: 术语类型
            - start: 起始位置
            - end: 结束位置

        Examples:
            >>> recognizer = TermRecognizer()
            >>> recognizer.recognize("PyTorch 是 Facebook 开发的框架")
            [
                {'term': 'PyTorch', 'type': 'framework', 'start': 0, 'end': 7},
                {'term': 'Facebook', 'type': 'org', 'start': 11, 'end': 19}
            ]
        """
        if not text:
            return []

        results = []
        seen_positions = set()  # 避免重叠

        for match in self.pattern.finditer(text):
            start, end = match.start(), match.end()
            term = match.group()

            # 检查是否与已匹配的术语重叠
            if any(s < start < e or s < end < e for s, e in seen_positions):
                continue

            term_type = self.terms.get(term, "unknown")

            # 类别过滤
            if categories and term_type not in categories:
                continue

            results.append(
                {
                    "term": term,
                    "type": term_type,
                    "start": start,
                    "end": end,
                }
            )
            seen_positions.add((start, end))

        # 按位置排序
        results.sort(key=lambda x: x["start"])
        return results

    def recognize_unique(
        self,
        text: str,
        categories: Optional[List[str]] = None,
    ) -> List[str]:
        """
        识别并返回不重复的术语列表

        Args:
            text: 输入文本
            categories: 类别过滤

        Returns:
            术语列表（去重）
        """
        terms = self.recognize(text, categories)
        return list(dict.fromkeys(t["term"] for t in terms))

    def annotate_text(self, text: str, categories: Optional[List[str]] = None) -> str:
        """
        标注文本中的术语（Markdown 格式）

        Args:
            text: 输入文本
            categories: 类别过滤

        Returns:
            标注后的文本，术语用 **术语** 格式

        Examples:
            >>> recognizer = TermRecognizer()
            >>> recognizer.annotate_text("PyTorch 是深度学习框架")
            '**PyTorch** 是 **深度学习** 框架'
        """
        terms = self.recognize(text, categories)
        if not terms:
            return text

        # 从后向前替换（避免位置偏移）
        result = text
        offset = 0
        for term_info in terms:
            start = term_info["start"] + offset
            end = term_info["end"] + offset
            result = result[:start] + f"**{term_info['term']}**" + result[end:]
            offset += 4  # ** 的长度

        return result


def recognize_terms(
    text: str,
    categories: Optional[List[str]] = None,
) -> List[Dict]:
    """
    便捷函数：识别术语

    Args:
        text: 输入文本
        categories: 类别过滤

    Returns:
        术语列表
    """
    recognizer = TermRecognizer()
    return recognizer.recognize(text, categories)


def annotate_terms(
    text: str,
    categories: Optional[List[str]] = None,
) -> str:
    """
    便捷函数：标注术语

    Args:
        text: 输入文本
        categories: 类别过滤

    Returns:
        标注后的文本
    """
    recognizer = TermRecognizer()
    return recognizer.annotate_text(text, categories)
