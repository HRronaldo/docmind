"""
笔记模板模块
============

生成结构化的笔记模板。

功能：
- 摘要模板
- 读书笔记模板
- 会议记录模板
- 教程笔记模板

Usage:
```python
from app.nlp.templates import generate_note_template

# 生成摘要模板
template = generate_note_template("summary", title="深度学习介绍", content="...")

# 生成读书笔记模板
template = generate_note_template("book", book_title="深度学习", author="Ian Goodfellow")
```
"""

from typing import Dict, Optional
from datetime import datetime


class NoteTemplate:
    """笔记模板生成器"""
    
    TEMPLATES = {
        "summary": """# {title}

> 来源：{source}
> 日期：{date}

## 核心要点
{key_points}

## 详细摘要
{summary}

## 关键词
{keywords}

## 相关术语
{terms}

---
*由 DocMind 自动生成*
""",
        
        "book": """# {book_title}

> 作者：{author}
> 日期：{date}

## 书籍信息
- ISBN：{isbn}
- 出版社：{publisher}
- 出版年：{year}

## 核心主题
{main_theme}

## 主要章节
{chapters}

## 读书笔记
{notes}

## 要点总结
{summary}

## 行动项
- [ ]

---
*由 DocMind 自动生成*
""",
        
        "meeting": """# {meeting_title}

> 日期：{date}
> 参会人：{attendees}

## 议程
{agenda}

## 讨论要点
{discussion_points}

## 决策
{decisions}

## 行动项
| 任务 | 负责人 | 截止日期 |
|------|--------|----------|
{action_items}

## 下次会议
{next_meeting}

---
*由 DocMind 自动生成*
""",
        
        "tutorial": """# {title}

> 难度：{difficulty}
> 预计时间：{estimated_time}
> 日期：{date}

## 前置要求
{prerequisites}

## 目标
{goals}

## 步骤
{steps}

## 代码示例
```python
{code_example}
```

## 练习
{practice}

## 常见问题
{faq}

## 总结
{summary}

---
*由 DocMind 自动生成*
""",
    }
    
    @classmethod
    def generate(cls, template_type: str, **kwargs) -> str:
        """
        生成笔记模板
        
        Args:
            template_type: 模板类型 (summary/book/meeting/tutorial)
            **kwargs: 模板变量
            
        Returns:
            填充后的模板
        """
        template = cls.TEMPLATES.get(template_type, cls.TEMPLATES["summary"])
        
        # 添加默认值
        kwargs.setdefault("date", datetime.now().strftime("%Y-%m-%d"))
        
        # 使用 replace 而不是 format（避免与大括号冲突）
        result = template
        for key, value in kwargs.items():
            result = result.replace("{" + key + "}", str(value))
        
        return result
    
    @classmethod
    def get_template_types(cls) -> list:
        """获取支持的模板类型"""
        return list(cls.TEMPLATES.keys())


def generate_note_template(template_type: str, **kwargs) -> str:
    """
    便捷函数：生成笔记模板
    
    Args:
        template_type: 模板类型
        **kwargs: 模板变量
        
    Returns:
        填充后的模板
    """
    return NoteTemplate.generate(template_type, **kwargs)


def generate_from_content(content: str, template_type: str = "summary") -> str:
    """
    从内容生成笔记模板
    
    Args:
        content: 文档内容
        template_type: 模板类型
        
    Returns:
        填充后的模板
    """
    # 简单实现：提取标题作为占位符
    lines = content.split("\n")
    title = lines[0][:50] if lines else "Untitled"
    key_points = "\n".join([f"- 要点{i+1}" for i in range(3)])
    
    return NoteTemplate.generate(
        template_type,
        title=title,
        key_points=key_points,
        summary=content[:500] + "...",
        keywords="关键词待提取",
        terms="术语待识别"
    )


# 高亮提取功能
def extract_highlights(content: str, max_highlights: int = 5) -> list:
    """
    提取内容中的高亮部分
    
    基于规则的高亮提取：
    - 包含数字的句子
    - 以动词开头的句子
    - 包含专业术语的句子
    
    Args:
        content: 文档内容
        max_highlights: 最大高亮数
        
    Returns:
        高亮列表
    """
    sentences = content.replace("\n", ".").split(".")
    highlights = []
    
    import re
    
    for i, sent in enumerate(sentences):
        sent = sent.strip()
        if not sent or len(sent) < 10:
            continue
            
        # 规则1：包含数字
        if re.search(r"\d+", sent):
            highlights.append(sent)
            continue
            
        # 规则2：包含术语
        tech_terms = ["深度学习", "机器学习", "神经网络", "Transformer", "BERT", "GPT"]
        if any(term in sent for term in tech_terms):
            highlights.append(sent)
            continue
            
        # 规则3：以特定动词开头
        verb_starters = ["首先", "其次", "最后", "重要", "关键", "主要"]
        if any(sent.startswith(v) for v in verb_starters):
            highlights.append(sent)
    
    return highlights[:max_highlights]