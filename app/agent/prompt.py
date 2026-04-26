"""Prompt templates for the Agent.

中文优化版本
============

针对中文文档的优化：
- 中文术语保留（不翻译）
- 中文标点符号
- 中文习惯的表达方式
- 结构化的中文输出
"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# System prompt - defines the agent's personality and capabilities
SYSTEM_PROMPT = """你是一个智能文档摘要助手，专门帮助用户理解和总结各种文档内容。

【核心能力】
1. **智能理解**：准确把握用户意图
2. **内容抓取**：从 URL 抓取网页内容
3. **深度摘要**：提炼核心要点
4. **术语识别**：识别并标注专业术语

【回答规范】
- ✅ 使用中文标点（，。：；？！""）
- ✅ 保留中文术语（LangGraph、PyTorch 等不翻译）
- ✅ 结构化输出（标题、列表、表格）
- ✅ 突出关键信息，层次分明
- ✅ 技术文档要专业准确
- ✅ 新闻文章要客观简洁
- ✅ 教程类要步骤清晰

【输出格式】
```
## 核心要点
- 要点1
- 要点2

## 关键术语
- **术语名**：解释

## 详细解读
...
```

如需更多信息，请明确告知用户。"""

# 中文优化摘要 Prompt
CHINESE_SUMMARY_PROMPT = """请对以下内容进行中文摘要：

---
{content}
---

【摘要要求】
1. **核心要点**：提炼 3-5 个核心观点
2. **关键术语**：识别并解释专业术语
3. **结构清晰**：使用标题、列表等结构
4. **长度控制**：摘要不超过原文的 20%
5. **中文表达**：使用地道的中文表达方式

【输出格式】
```
## 核心要点
1. 要点1
2. 要点2
3. 要点3

## 关键术语
- **术语名**：简要解释

## 重要细节
...
```"""

# 中文优化问答 Prompt
CHINESE_QA_PROMPT = """基于以下内容，回答用户的问题。

【用户问题】
{question}

---
{context}
---

【回答要求】
1. **直接回答**：先给出明确答案
2. **引用来源**：标注信息来源
3. **术语解释**：解释专业术语
4. **如有不确定**：坦诚说明，不要编造

【输出格式】
```
## 回答
...

## 引用来源
- 来源1
- 来源2

## 相关术语
- **术语**：解释
```"""

# Prompt for handling URLs
URL_HANDLING_PROMPT = """用户想要处理这个URL：{url}

请先抓取URL内容，然后根据用户的问题：{question}

抓取内容后，进行总结和回答。"""

# Prompt for general questions
GENERAL_QUESTION_PROMPT = """用户的问题是：{question}

请直接回答。如果需要更多信息，请礼貌地询问用户。"""


def create_chat_prompt() -> ChatPromptTemplate:
    """Create the chat prompt template with conversation history."""
    return ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{question}"),
            MessagesPlaceholder(variable_name="agent_scratchpad", optional=True),
        ]
    )


def create_url_prompt(url: str, question: str) -> str:
    """Create a prompt for URL handling."""
    return URL_HANDLING_PROMPT.format(url=url, question=question)


def create_general_prompt(question: str) -> str:
    """Create a prompt for general questions."""
    return GENERAL_QUESTION_PROMPT.format(question=question)


def create_chinese_summary_prompt(content: str) -> str:
    """
    创建中文摘要 Prompt

    Args:
        content: 要摘要的内容

    Returns:
        格式化的 Prompt
    """
    return CHINESE_SUMMARY_PROMPT.format(content=content)


def create_chinese_qa_prompt(question: str, context: str) -> str:
    """
    创建中文问答 Prompt

    Args:
        question: 用户问题
        context: 上下文内容

    Returns:
        格式化的 Prompt
    """
    return CHINESE_QA_PROMPT.format(question=question, context=context)
