"""
DocMind Agent 测试脚本
======================
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 添加项目根目录到 sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
load_dotenv()


# 测试各个 Agent
async def test_langgraph_agent():
    """测试 LangGraph Agent（流程图式）"""
    from app.agent.langgraph_agent import init_agent, LangGraphAgent

    api_key = os.getenv("ZHIPU_API_KEY")
    if not api_key:
        print("> ZHIPU_API_KEY 未设置")
        return False

    print("=" * 50)
    print("测试 LangGraph Agent")
    print("=" * 50)

    # 初始化
    agent = init_agent(api_key)
    print(f"> Agent 初始化成功: {type(agent).__name__}")

    # 测试 1: 直接回答（无 URL）
    print("\n--- 测试 1: 直接回答 ---")
    result = await agent.process_message("你好，介绍一下你自己")
    print(f"输入: 你好，介绍一下你自己")
    print(f"输出: {result.get('response', '')[:200]}...")
    print(f"成功: {result.get('success')}")

    # 测试 2: 创建会话
    print("\n--- 测试 2: 会话管理 ---")
    session_id = agent.create_session()
    print(f"创建会话: {session_id}")

    result = await agent.process_message("我的名字是小明", session_id)
    print(f"> 消息处理成功")

    result = agent.get_session(session_id)
    print(f"获取会话: {result}")

    return True


async def test_react_agent():
    """测试 ReAct Agent（自主推理）"""
    from app.agent.react_agent import init_react_agent

    api_key = os.getenv("ZHIPU_API_KEY")
    print("\n" + "=" * 50)
    print("测试 ReAct Agent")
    print("=" * 50)

    agent = init_react_agent(api_key)
    print(f"> ReAct Agent 初始化成功")

    # 测试
    result = await agent.process_message("什么是 LangGraph？")
    print(f"输入: 什么是 LangGraph？")
    print(f"输出: {result.get('response', '')[:200]}...")
    print(f"成功: {result.get('success')}")

    return True


async def test_multi_agent():
    """测试 Multi-Agent（多智能体协作）"""
    from app.agent.multi_agent import init_multi_agent

    api_key = os.getenv("ZHIPU_API_KEY")
    print("\n" + "=" * 50)
    print("测试 Multi-Agent")
    print("=" * 50)

    agent = init_multi_agent(api_key)
    print(f"> Multi-Agent 初始化成功")

    # 测试
    result = await agent.process_message(
        "帮我总结这篇文档: https://python.langchain.com/docs/concepts/langchain/"
    )
    print(f"输入: 帮我总结这篇文档...")
    print(f"路由到: {result.get('current_agent', 'unknown')}")
    print(f"输出: {result.get('response', '')[:200]}...")
    print(f"成功: {result.get('success')}")

    return True


async def main():
    print("> DocMind Agent 测试开始\n")

    try:
        # 依次测试
        await test_langgraph_agent()
        await test_react_agent()
        await test_multi_agent()

        print("\n" + "=" * 50)
        print("> 所有测试完成!")
        print("=" * 50)

    except Exception as e:
        print(f"\n> 测试失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
