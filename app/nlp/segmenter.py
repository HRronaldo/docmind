"""
中文分词模块
============

基于 jieba 的中文分词，支持：
- 精确模式分词
- 全模式分词
- 搜索引擎模式分词
- 词性标注

Usage:
```python
from app.nlp.segmenter import segment_text, Segmenter

# 简单用法
words = segment_text("我爱自然语言处理")
print(words)  # ['我爱', '自然语言', '处理']

# 高级用法
segmenter = Segmenter(mode='search')
words = segmenter.segment("深度学习框架 PyTorch")
print(words)
```
"""

import jieba
import jieba.posseg as pseg
from typing import List, Optional, Set
from app.core.logger import get_logger

logger = get_logger("docmind.nlp.segmenter")

# 初始化 jieba（加载默认词典）
jieba.initialize()


class Segmenter:
    """
    中文分词器

    支持三种分词模式：
    - precise: 精确模式（默认），适合文本分析
    - full: 全模式，把所有可能的词都切分出来
    - search: 搜索引擎模式，适合搜索场景
    """

    MODES = {"precise": "precise", "full": "full", "search": "search"}

    def __init__(self, mode: str = "precise", stop_words: Optional[Set[str]] = None):
        """
        初始化分词器

        Args:
            mode: 分词模式 ('precise', 'full', 'search')
            stop_words: 停用词集合
        """
        self.mode = mode
        self.stop_words = stop_words or self._default_stop_words()
        logger.debug(f"Segmenter initialized with mode={mode}")

    @staticmethod
    def _default_stop_words() -> Set[str]:
        """默认停用词"""
        return {
            "的",
            "了",
            "和",
            "是",
            "在",
            "我",
            "有",
            "个",
            "人",
            "这",
            "你",
            "他",
            "它",
            "们",
            "那",
            "就",
            "也",
            "都",
            "而",
            "及",
            "与",
            "着",
            "或",
            "一个",
            "没有",
            "我们",
            "你们",
            "他们",
            "这个",
            "那个",
            "什么",
            "怎么",
            "如何",
            "为什么",
            "可以",
            "因为",
            "所以",
            "但是",
            "如果",
            "虽然",
            "然而",
            "不过",
            "只是",
            "就是",
            "而且",
            "或者",
            "以及",
            "关于",
            "对于",
            "根据",
            "通过",
            "按照",
            "随着",
            "由于",
            "为了",
            "以便",
            "只要",
            "除非",
            "即使",
            "尽管",
        }

    def segment(self, text: str, remove_stop_words: bool = True) -> List[str]:
        """
        分词

        Args:
            text: 输入文本
            remove_stop_words: 是否移除停用词

        Returns:
            分词结果列表
        """
        if not text:
            return []

        # 根据模式选择分词方法
        if self.mode == "full":
            words = list(jieba.cut(text, cut_all=True))
        elif self.mode == "search":
            words = list(jieba.cut_for_search(text))
        else:  # precise
            words = list(jieba.cut(text))

        # 移除停用词
        if remove_stop_words:
            words = [w for w in words if w.strip() and w not in self.stop_words]

        return words

    def segment_with_pos(self, text: str) -> List[tuple]:
        """
        分词并标注词性

        Args:
            text: 输入文本

        Returns:
            [(词, 词性), ...]
        """
        if not text:
            return []

        words = pseg.cut(text)
        return [(word, flag) for word, flag in words]


def segment_text(
    text: str, mode: str = "precise", remove_stop_words: bool = True
) -> List[str]:
    """
    便捷函数：对文本进行分词

    Args:
        text: 输入文本
        mode: 分词模式 ('precise', 'full', 'search')
        remove_stop_words: 是否移除停用词

    Returns:
        分词结果列表

    Examples:
        >>> segment_text("深度学习是机器学习的分支")
        ['深度学习', '机器学习', '分支']
    """
    segmenter = Segmenter(mode=mode)
    return segmenter.segment(text, remove_stop_words=remove_stop_words)


def add_word(word: str, freq: int = None, tag: str = None):
    """
    添加自定义词到 jieba 词典

    Args:
        word: 自定义词
        freq: 词频（越高越容易被识别）
        tag: 词性标注

    Examples:
        >>> add_word("PyTorch", freq=100)
        >>> add_word("大语言模型", freq=50)
    """
    if freq is not None and tag is not None:
        jieba.add_word(word, freq, tag)
    elif freq is not None:
        jieba.add_word(word, freq)
    else:
        jieba.add_word(word)
    logger.debug(f"Added custom word: {word}")


def load_user_dict(dict_path: str):
    """
    加载自定义词典

    Args:
        dict_path: 词典文件路径

    词典格式：每行一个词，可选跟随词频和词性
        深度学习 100 n
        PyTorch 50 eng
    """
    jieba.load_userdict(dict_path)
    logger.info(f"Loaded user dictionary: {dict_path}")
