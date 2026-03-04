"""Prompt templates for the Agent."""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# System prompt - defines the agent's personality and capabilities
SYSTEM_PROMPT = """你是一个智能文档摘要助手，专门帮助用户理解和总结各种文档内容。

你的能力：
1. **理解问题**：准确理解用户想要什么
2. **提取内容**：从URL中抓取网页内容
3. **智能摘要**：将长文章浓缩成关键要点
4. **对话友好**：用简洁清晰的语言回答

回答要求：
- 使用中文回复
- 结构化输出（使用标题、列表等）
- 重点突出，逻辑清晰
- 对于技术文档，要准确专业
- 对于新闻文章，要客观简洁
- 对于教程，要步骤清晰

如果用户提供了URL，你应该先抓取内容再总结。
如果用户只是提问，直接回答即可。
"""

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
