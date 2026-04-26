"""
笔记模板模块
============

生成结构化的笔记模板。

功能：
- 摘要模板
- 读书笔记模板
- 会议记录模板
- 教程笔记模板
- 复习笔记模板（间隔重复）

Usage:
```python
from app.nlp.templates import generate_note_template

# 生成摘要模板
template = generate_note_template("summary", title="深度学习介绍", content="...")

# 生成读书笔记模板
template = generate_note_template("book", book_title="深度学习", author="Ian Goodfellow")

# 生成复习笔记模板
template = generate_note_template("review", title="深度学习", review_date="2026-05-01")
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

        "review": """# {title} - 复习笔记

> 首次学习：{first_date}
> 复习周期：{interval}
> 建议复习日期：{review_date}

## 核心概念
{concepts}

## 关键知识点
{key_points}

## 我的理解
{understanding}

## 遗忘点
- [ ]

## 复习总结
{summary}

## 下次复习
- 1天后：检查遗忘点
- 3天后：尝试默写
- 7天后：应用实践
- 30天后：复盘总结

---
*由 DocMind 自动生成 - 间隔重复笔记*
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


# 复习计划生成功能
def generate_review_schedule(
    content: str, 
    first_date: str = None,
    intervals: list = None
) -> dict:
    """
    生成复计划（简化版 - 不需要数据库）
    
    根据首次学习日期，生成建议的复习日期。
    用户需要手动将这些日期记录到笔记中。
    
    Args:
        content: 文档内容
        first_date: 首次学习日期 (YYYY-MM-DD)，默认今天
        intervals: 复习间隔天数列表
        
    Returns:
        复习计划词典
    """
    from datetime import datetime, timedelta
    
    if first_date is None:
        first_date = datetime.now().strftime("%Y-%m-%d")
    
    if intervals is None:
        intervals = [1, 3, 7, 14, 30]  # 默认间隔：1天、3天、7天、14天、30天
    
    # 解析首次日期
    try:
        first = datetime.strptime(first_date, "%Y-%m-%d")
    except ValueError:
        first = datetime.now()
    
    # 生成复习日期
    schedule = {
        "first_date": first_date,
        "intervals": intervals,
        "reviews": []
    }
    
    for days in intervals:
        review_date = first + timedelta(days=days)
        schedule["reviews"].append({
            "day": days,
            "date": review_date.strftime("%Y-%m-%d"),
            "type": _get_review_type(days)
        })
    
    return schedule


def _get_review_type(days: int) -> str:
    """根据间隔天数返回复习类型"""
    if days == 1:
        return "快速回顾"
    elif days == 3:
        return "记忆巩固"
    elif days == 7:
        return "理解深化"
    elif days == 14:
        return "知识串联"
    elif days == 30:
        return "长期记忆"
    else:
        return "复习巩固"