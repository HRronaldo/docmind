"""Main application entry point."""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.api.routes import router
from app.core.config import HOST, PORT, DEBUG, ALLOWED_ORIGINS
from app.services.chat_service import get_chat_service

# Load environment variables
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print("Starting Agent Summary Service...")

    # Try to initialize with API key from env if available
    api_key = os.getenv("ZHIPU_API_KEY")
    if api_key:
        try:
            service = get_chat_service()
            service.initialize(api_key=api_key)
            print("Agent initialized with environment API key")
        except Exception as e:
            print(f"Warning: Could not initialize agent: {e}")
    else:
        print("Warning: ZHIPU_API_KEY not set. Call /api/v1/init to initialize.")

    yield

    # Shutdown
    print("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Agent Summary API",
    description="AI-powered document summarization service with URL extraction",
    version="1.0.0",
    lifespan=lifespan,
    debug=DEBUG,
)

# Add CORS middleware
origins = ALLOWED_ORIGINS.split(",") if isinstance(ALLOWED_ORIGINS, str) else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Agent Summary Service",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "health": "/api/v1/health",
            "init": "/api/v1/init",
            "chat": "/api/v1/chat",
            "session": "/api/v1/session",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=HOST,
        port=PORT,
        reload=DEBUG,
    )
