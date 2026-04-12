# 创建测试文件 test_chat.py

import sys
from pathlib import Path

# 添加项目根目录到 sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from app.agent.langgraph_agent import init_agent, get_agent
from app.core.config import ZHIPU_API_KEY


async def test():
    # 初始化 Agent
    init_agent(ZHIPU_API_KEY)
    agent = get_agent()

    # 测试 chat
    result = await agent.process_message("你好，请介绍一下 LangGraph")
    print("结果:", result)


asyncio.run(test())
