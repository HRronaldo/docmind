"""Chat service - business logic for chat operations."""

from typing import Dict, Any, Optional
from app.agent.langgraph_agent import LangGraphAgent, get_agent, init_agent


class ChatService:
    """Service for handling chat operations."""

    def __init__(self):
        self.agent: Optional[LangGraphAgent] = None

    def initialize(self, api_key: str, **kwargs):
        """Initialize the agent with API key."""
        self.agent = init_agent(api_key, **kwargs)

    async def send_message(
        self, message: str, session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send a message and get response."""
        if self.agent is None:
            return {
                "success": False,
                "error": "Agent not initialized. Please provide API key.",
            }

        return await self.agent.process_message(message, session_id)

    def create_session(self, session_id: Optional[str] = None) -> str:
        """Create a new chat session."""
        if self.agent is None:
            raise RuntimeError("Agent not initialized")

        return self.agent.create_session(session_id)

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session info."""
        if self.agent is None:
            return None

        return self.agent.get_session(session_id)

    def clear_session(self, session_id: str) -> bool:
        """Clear session history."""
        if self.agent is None:
            return False

        return self.agent.clear_session(session_id)

    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        if self.agent is None:
            return False

        return self.agent.delete_session(session_id)


# Singleton instance
_chat_service: Optional[ChatService] = None


def get_chat_service() -> ChatService:
    """Get or create the chat service singleton."""
    global _chat_service

    if _chat_service is None:
        _chat_service = ChatService()

    return _chat_service
