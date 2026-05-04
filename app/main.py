"""Main application entry point.

DocMind - 智能文档摘要服务
===========================

本文件是 DocMind 应用的入口点，负责：
1. 初始化 FastAPI 应用
2. 配置 CORS 中间件
3. 注册路由
4. 挂载 MCP Server (SSE 模式)
5. 管理应用生命周期（启动/关闭）

使用方法：
    uv run python -m app.main
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from fastmcp.utilities.lifespan import combine_lifespans

from app.api.routes import router
from app.core.config import HOST, PORT, DEBUG, ALLOWED_ORIGINS, ensure_port_available
from app.services.chat_service import get_chat_service
from app.mcp.server import mcp

# 加载 .env 文件中的环境变量
load_dotenv()

# ===== 启动前检查端口 =====
# 如果端口被占用，尝试自动清理
if not ensure_port_available(PORT):
    print(f"\n[X] Port {PORT} is not available, please close the process")
    exit(1)

# ===== 创建 MCP ASGI 应用 =====
mcp_app = mcp.http_app(path="/")


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    """
    DocMind 应用生命周期管理。
    """
    # ===== 启动阶段 =====
    print("Starting DocMind Service...")

    # 尝试使用环境变量中的 API Key 初始化服务
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

    # ===== 关闭阶段 =====
    print("Shutting down...")


# ===== 创建 FastAPI 应用 =====
app = FastAPI(
    title="DocMind API",
    description="基于 LangChain + GLM 的智能文档摘要服务，支持 RESTful API 和 MCP 协议",
    version="1.0.0",
    lifespan=combine_lifespans(app_lifespan, mcp_app.lifespan),
    debug=DEBUG,
)

# ===== 配置 CORS 中间件 =====
# 允许跨域请求，便于前端调用
origins = ALLOWED_ORIGINS.split(",") if isinstance(ALLOWED_ORIGINS, str) else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== 注册路由 =====
app.include_router(router)

# ===== 挂载 MCP Server =====
app.mount("/sse", mcp_app)


# ===== 根路由 =====
@app.get("/")
async def root():
    """
    根路由，返回服务基本信息。

    Returns:
        dict: 服务名称、版本、可用端点
    """
    return {
        "name": "DocMind - 智能文档摘要服务",
        "version": "0.7.0",
        "description": "基于 LangChain + GLM 的智能文档摘要服务",
        "docs": "/docs",
        "endpoints": {
            "health": "/api/v1/health",
            "init": "/api/v1/init",
            "chat": "/api/v1/chat",
            "session": "/api/v1/session",
        },
    }


# ===== 启动入口 =====
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=HOST,
        port=PORT,
        reload=DEBUG,
    )
