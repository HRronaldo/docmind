"""测试 multi_agent"""

import sys
from pathlib import Path

# 添加项目根目录到 sys.path
# test_multi_agent.py 在 docmind/test/ 下
# parent = docmind/test
# parent.parent = docmind
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

import asyncio
from app.agent.multi_agent import get_multi_agent


async def test():
    print("=" * 50)
    print("测试 Multi-Agent (Supervisor + Workers)")
    print("=" * 50)

    agent = get_multi_agent()

    # 测试1: 单 URL
    print("\n--- 测试1: 单 URL ---")
    result = await agent.process_message("帮我总结 https://example.com")
    print(f"策略: {result.get('strategy')}")
    print(f"回复: {result.get('response', '')[:200]}...")

    # 测试2: 多 URL
    print("\n--- 测试2: 多 URL ---")
    result = await agent.process_message(
        "帮我总结 https://example.com 和 https://httpbin.org/html"
    )
    print(f"策略: {result.get('strategy')}")
    print(f"任务数: {result.get('tasks_count')}")
    print(f"回复: {result.get('response', '')[:200]}...")

    # 测试3: 无 URL
    print("\n--- 测试3: 无 URL ---")
    result = await agent.process_message("什么是 LangGraph？")
    print(f"策略: {result.get('strategy')}")
    print(f"回复: {result.get('response', '')[:200]}...")


asyncio.run(test())
