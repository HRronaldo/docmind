"""LangChain Agent chain definition."""

import secrets as secrets_module
from typing import List, Dict, Any, Optional
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_community.chat_models import ChatZhipuAI

from app.agent.tools import AVAILABLE_TOOLS, fetch_url_content
from app.agent.prompt import SYSTEM_PROMPT, create_chat_prompt
from app.core.config import ZHIPU_API_KEY, GLM_MODEL, GLM_TEMPERATURE, GLM_MAX_TOKENS


class SummaryAgent:
    """
    Document Summary Agent using LangChain + GLM.

    Features:
    - URL content extraction
    - Intelligent summarization
    - Conversational memory
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = GLM_MODEL,
        temperature: float = GLM_TEMPERATURE,
        max_tokens: int = GLM_MAX_TOKENS,
    ):
        """Initialize the agent with LLM and tools."""
        self.api_key = api_key or ZHIPU_API_KEY

        if not self.api_key:
            raise ValueError("ZHIPU_API_KEY is required")

        # Initialize GLM Chat Model
        self.llm = ChatZhipuAI(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=self.api_key,
        )

        # Bind tools to the LLM
        self.llm_with_tools = self.llm.bind_tools(AVAILABLE_TOOLS)

        # Create prompt
        self.prompt = create_chat_prompt()

        # Conversation history (in-memory for MVP)
        self.chat_history: List[BaseMessage] = []

        # Session management
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def create_session(self, session_id: Optional[str] = None) -> str:
        """Create a new chat session."""
        if session_id is None:
            session_id = secrets_module.token_urlsafe(16)

        self.sessions[session_id] = {"history": [], "created_at": "now"}

        return session_id

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID."""
        return self.sessions.get(session_id)

    def is_url(self, text: str) -> bool:
        """Check if text is a URL."""
        return text.strip().startswith(("http://", "https://"))

    async def process_message(
        self, message: str, session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a user message and return the response.

        Args:
            message: User's message (can be text or URL)
            session_id: Optional session ID for conversation continuity

        Returns:
            Dict with response and metadata
        """
        # Create or get session
        if session_id and session_id in self.sessions:
            chat_history = self.sessions[session_id]["history"]
        else:
            session_id = self.create_session(session_id)
            chat_history = []

        # Check if message contains a URL
        has_url = self.is_url(message)

        # Build the chain
        # For MVP, we'll use a simpler approach - direct LLM with tools

        if has_url:
            # Extract URL from message
            words = message.split()
            url = None
            for word in words:
                if self.is_url(word):
                    url = word
                    break

            if url:
                # First fetch the URL content
                try:
                    content_result = fetch_url_content.invoke(url)

                    # Create prompt with content
                    prompt = f"""根据以下内容，回答用户的问题。

内容：
{content_result}

用户问题：{message.replace(url, "").strip() or "请总结这篇文章的主要内容"}

请用中文回答，突出重点。"""

                    # Call LLM
                    response = self.llm.invoke(prompt)

                    # Save to history
                    chat_history.append(HumanMessage(content=message))
                    chat_history.append(response)
                    self.sessions[session_id]["history"] = chat_history

                    return {
                        "session_id": session_id,
                        "response": response.content,
                        "url_processed": url,
                        "success": True,
                    }

                except Exception as e:
                    return {
                        "session_id": session_id,
                        "response": f"处理URL时出错：{str(e)}",
                        "success": False,
                        "error": str(e),
                    }

        # Regular message - just use LLM
        try:
            # Build messages with history
            messages = []
            for msg in chat_history[-10:]:  # Keep last 10 messages
                messages.append(msg)
            messages.append(HumanMessage(content=message))

            # Invoke
            response = self.llm.invoke(messages)

            # Save to history
            chat_history.append(HumanMessage(content=message))
            chat_history.append(response)
            self.sessions[session_id]["history"] = chat_history

            return {
                "session_id": session_id,
                "response": response.content,
                "success": True,
            }

        except Exception as e:
            return {
                "session_id": session_id,
                "response": f"处理消息时出错：{str(e)}",
                "success": False,
                "error": str(e),
            }

    def clear_session(self, session_id: str) -> bool:
        """Clear a session's history."""
        if session_id in self.sessions:
            self.sessions[session_id]["history"] = []
            return True
        return False

    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False


# Singleton instance (will be initialized with API key)
_agent_instance: Optional[SummaryAgent] = None


def get_agent() -> SummaryAgent:
    """Get or create the global agent instance."""
    global _agent_instance

    if _agent_instance is None:
        _agent_instance = SummaryAgent()

    return _agent_instance


def init_agent(api_key: str, **kwargs) -> SummaryAgent:
    """Initialize the agent with API key."""
    global _agent_instance

    _agent_instance = SummaryAgent(api_key=api_key, **kwargs)
    return _agent_instance
