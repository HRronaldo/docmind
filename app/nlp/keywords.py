"""
关键词提取模块
==============

基于 TF-IDF 和 TextRank 的关键词提取算法。

支持：
- TF-IDF 算法（适合文档级关键词）
- TextRank 算法（适合单句/段落关键词）
- 组合两种算法的结果

Usage:
```python
from app.nlp.keywords import extract_keywords, KeywordExtractor

# 简单用法
keywords = extract_keywords("深度学习是机器学习的一个分支...", top_k=5)
print(keywords)  # ['深度学习', '机器学习', '神经网络', ...]

# 高级用法
extractor = KeywordExtractor(method='textrank')
keywords = extractor.extract("一段很长的文本...", top_k=10)
```
"""

from typing import List, Optional, Dict, Tuple
from collections import Counter
import re
from app.nlp.segmenter import segment_text, add_word
from app.core.logger import get_logger

logger = get_logger("docmind.nlp.keywords")

# 常用技术词汇（预先添加到词典）
TECH_WORDS = [
    "深度学习",
    "机器学习",
    "神经网络",
    "人工智能",
    "自然语言处理",
    "计算机视觉",
    "强化学习",
    "迁移学习",
    "对抗生成网络",
    "卷积神经网络",
    "循环神经网络",
    "长短期记忆网络",
    "Transformer",
    "注意力机制",
    "BERT",
    "GPT",
    "ChatGPT",
    "大语言模型",
    "LLM",
    "RAG",
    "LangChain",
    "LangGraph",
    "向量数据库",
    "Embedding",
    "Embedding层",
    "token",
    "tokenizer",
    "GPU",
    "TPU",
    "CUDA",
    "Python",
    "PyTorch",
    "TensorFlow",
    "JAX",
    "FastAPI",
    "FastChat",
    "vLLM",
    "Ollama",
    "LangSmith",
    "MCP",
    "Model Context Protocol",
    "Agent",
    "Agent",
    "Supervisor",
    "ReAct",
    "Tool",
    "PDF",
    "EPUB",
    "Markdown",
    "JSON",
    "API",
    "PDFplumber",
    "ebooklib",
    "trafilatura",
    "jieba",
    "TextRank",
    "TF-IDF",
    "关键词提取",
]


class KeywordExtractor:
    """
    关键词提取器

    支持两种算法：
    - tfidf: TF-IDF 算法，基于词频统计
    - textrank: TextRank 算法，基于图排序
    - combined: 组合两种算法的结果
    """

    def __init__(
        self, method: str = "combined", top_k: int = 10, min_word_len: int = 2
    ):
        """
        初始化关键词提取器

        Args:
            method: 提取方法 ('tfidf', 'textrank', 'combined')
            top_k: 返回的关键词数量
            min_word_len: 最小词长度
        """
        self.method = method
        self.top_k = top_k
        self.min_word_len = min_word_len

        # 预先添加技术词汇到 jieba
        for word in TECH_WORDS:
            add_word(word, freq=100)

        logger.debug(f"KeywordExtractor initialized with method={method}")

    def extract(
        self, text: str, top_k: Optional[int] = None
    ) -> List[Tuple[str, float]]:
        """
        提取关键词

        Args:
            text: 输入文本
            top_k: 返回数量（覆盖默认值）

        Returns:
            [(关键词, 得分), ...]
        """
        if not text:
            return []

        top_k = top_k or self.top_k

        # 预处理
        clean_text = self._preprocess(text)

        # 根据方法选择算法
        if self.method == "tfidf":
            return self._tfidf_extract(clean_text, top_k)
        elif self.method == "textrank":
            return self._textrank_extract(clean_text, top_k)
        else:  # combined
            tfidf_results = self._tfidf_extract(clean_text, top_k * 2)
            textrank_results = self._textrank_extract(clean_text, top_k * 2)
            return self._combine_results(tfidf_results, textrank_results, top_k)

    def _preprocess(self, text: str) -> str:
        """文本预处理"""
        # 移除特殊字符，保留中文、英文、数字
        text = re.sub(r"[^\u4e00-\u9fa5a-zA-Z0-9]", " ", text)
        return text

    def _tfidf_extract(self, text: str, top_k: int) -> List[Tuple[str, float]]:
        """TF-IDF 算法提取关键词"""
        words = segment_text(text, mode="precise", remove_stop_words=True)

        # 过滤短词
        words = [w for w in words if len(w) >= self.min_word_len]

        # 词频统计
        word_freq = Counter(words)
        total = len(words)

        # 计算 TF-IDF（简化版，假设 IDF 已知）
        # 实际生产环境应该使用 sklearn 的 TfidfVectorizer
        idf_scores = self._get_idf_scores()
        scores = {}
        for word, freq in word_freq.items():
            tf = freq / total
            idf = idf_scores.get(word, 1.0)
            scores[word] = tf * idf

        # 归一化并排序
        max_score = max(scores.values()) if scores else 1
        results = [
            (w, s / max_score) for w, s in sorted(scores.items(), key=lambda x: -x[1])
        ]
        return results[:top_k]

    def _textrank_extract(self, text: str, top_k: int) -> List[Tuple[str, float]]:
        """TextRank 算法提取关键词"""
        # 分词
        words = segment_text(text, mode="precise", remove_stop_words=True)
        words = [w for w in words if len(w) >= self.min_word_len]

        # 构建词共现图
        window_size = 5
        cooccur = {}

        for i, word in enumerate(words):
            for j in range(i + 1, min(i + window_size, len(words))):
                next_word = words[j]
                if word != next_word:
                    if word not in cooccur:
                        cooccur[word] = Counter()
                    if next_word not in cooccur:
                        cooccur[next_word] = Counter()
                    cooccur[word][next_word] += 1
                    cooccur[next_word][word] += 1

        # 简化的 TextRank
        scores = {}
        damping = 0.85
        max_iter = 50

        # 初始化
        for word in cooccur:
            scores[word] = 1.0

        # 迭代计算
        for _ in range(max_iter):
            new_scores = {}
            for word in cooccur:
                total_weight = sum(cooccur[word].values())
                if total_weight > 0:
                    rank_sum = sum(
                        scores[w] * cooccur[word][w] / sum(cooccur[w].values())
                        for w in cooccur[word]
                    )
                    new_scores[word] = (1 - damping) + damping * rank_sum
                else:
                    new_scores[word] = scores[word]
            scores = new_scores

        # 归一化并排序
        max_score = max(scores.values()) if scores else 1
        results = [
            (w, s / max_score) for w, s in sorted(scores.items(), key=lambda x: -x[1])
        ]
        return results[:top_k]

    def _combine_results(
        self,
        tfidf_results: List[Tuple[str, float]],
        textrank_results: List[Tuple[str, float]],
        top_k: int,
    ) -> List[Tuple[str, float]]:
        """组合 TF-IDF 和 TextRank 结果"""
        combined = {}

        for word, score in tfidf_results:
            combined[word] = combined.get(word, 0) + score * 0.5

        for word, score in textrank_results:
            combined[word] = combined.get(word, 0) + score * 0.5

        # 归一化
        max_score = max(combined.values()) if combined else 1
        results = [
            (w, s / max_score) for w, s in sorted(combined.items(), key=lambda x: -x[1])
        ]
        return results[:top_k]

    @staticmethod
    def _get_idf_scores() -> Dict[str, float]:
        """简化的 IDF 值（实际应基于大规模语料库计算）"""
        # 常见词的 IDF 值
        high_idf = {
            "深度学习": 8.5,
            "机器学习": 8.2,
            "神经网络": 8.0,
            "人工智能": 7.5,
            "Transformer": 9.0,
            "BERT": 9.0,
            "GPT": 8.8,
            "大语言模型": 9.2,
            "LangChain": 9.5,
            "LangGraph": 9.5,
            "Agent": 5.0,
            "RAG": 9.0,
            "PyTorch": 9.0,
            "TensorFlow": 8.8,
            "FastAPI": 9.0,
        }
        return high_idf


def extract_keywords(text: str, top_k: int = 10, method: str = "combined") -> List[str]:
    """
    便捷函数：提取关键词

    Args:
        text: 输入文本
        top_k: 返回数量
        method: 方法 ('tfidf', 'textrank', 'combined')

    Returns:
        关键词列表

    Examples:
        >>> extract_keywords("深度学习是机器学习的一个分支...", top_k=5)
        ['深度学习', '机器学习', '神经网络', '人工智能', '分支']
    """
    extractor = KeywordExtractor(method=method)
    results = extractor.extract(text, top_k=top_k)
    return [word for word, _ in results]


def extract_keywords_with_scores(
    text: str, top_k: int = 10, method: str = "combined"
) -> List[Tuple[str, float]]:
    """
    提取关键词及其得分

    Args:
        text: 输入文本
        top_k: 返回数量
        method: 方法

    Returns:
        [(关键词, 得分), ...]

    Examples:
        >>> extract_keywords_with_scores("深度学习是机器学习...", top_k=3)
        [('深度学习', 0.95), ('机器学习', 0.88), ('神经网络', 0.75)]
    """
    extractor = KeywordExtractor(method=method)
    return extractor.extract(text, top_k=top_k)
