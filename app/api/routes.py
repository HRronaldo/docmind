"""API routes for the summary service."""

from typing import Optional, Dict
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from app.services.chat_service import get_chat_service, ChatService

# Create router
router = APIRouter(prefix="/api/v1", tags=["chat"])


# Request/Response models
class ChatRequest(BaseModel):
    """Request model for chat endpoint."""

    message: str = Field(..., description="User message or URL")
    session_id: Optional[str] = Field(
        None, description="Session ID for conversation continuity"
    )


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""

    session_id: str
    response: str
    success: bool
    url_processed: Optional[str] = None
    error: Optional[str] = None


class InitRequest(BaseModel):
    """Request model for initializing the agent."""

    api_key: str = Field(..., description="ZhipuAI API Key")
    model: Optional[str] = Field("glm-4", description="Model name")
    temperature: Optional[float] = Field(0.7, description="Temperature")


class SessionResponse(BaseModel):
    """Response model for session operations."""

    session_id: str
    success: bool


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str
    version: str


# Dependencies
def get_service() -> ChatService:
    """Get chat service dependency."""
    return get_chat_service()


# Routes
@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(status="ok", version="0.7.0")


@router.post("/init", response_model=Dict)
async def initialize_agent(
    request: InitRequest, service: ChatService = Depends(get_service)
):
    """
    Initialize the agent with API key.

    This should be called once before starting to use the chat.
    """
    try:
        service.initialize(
            api_key=request.api_key,
            model=request.model,
            temperature=request.temperature,
        )
        return {"success": True, "message": "Agent initialized successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, service: ChatService = Depends(get_service)):
    """
    Send a message and get AI response.

    The message can be:
    - A regular text question
    - A URL (will automatically fetch and summarize)
    """
    try:
        result = await service.send_message(
            message=request.message, session_id=request.session_id
        )

        return ChatResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/session", response_model=SessionResponse)
async def create_session(service: ChatService = Depends(get_service)):
    """Create a new chat session."""
    try:
        session_id = service.create_session()
        return SessionResponse(session_id=session_id, success=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/session/{session_id}", response_model=SessionResponse)
async def delete_session(session_id: str, service: ChatService = Depends(get_service)):
    """Delete a chat session."""
    success = service.delete_session(session_id)

    if not success:
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionResponse(session_id=session_id, success=True)


@router.get("/session/{session_id}", response_model=Dict)
async def get_session(session_id: str, service: ChatService = Depends(get_service)):
    """Get session information."""
    session = service.get_session(session_id)

    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_id": session_id,
        "message_count": len(session.get("history", [])),
        "created_at": session.get("created_at"),
    }
