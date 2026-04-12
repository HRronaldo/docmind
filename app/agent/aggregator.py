"""
Aggregator - 结果汇总器
====================

职责：
1. 收集 Worker 的执行结果
2. 根据 need_qa 决定回答方式
3. 生成最终回复
"""

import sys
from pathlib import Path

# 添加项目根目录
_docmind = Path(__file__).resolve().parent.parent
if str(_docmind) not in sys.path:
    sys.path.insert(0, str(_docmind))

from typing import TypedDict, List, Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_community.chat_models import ChatZhipuAI
from app.core.config import GLM_MODEL, GLM_TEMPERATURE, ZHIPU_API_KEY


class AggregatorState(TypedDict):
    """Aggregator 状态"""

    user_input: str
    worker_results: List[Dict]  # [{"url": "...", "content": "...", "type": "..."}]
    need_qa: bool
    final_response: str


def _get_llm():
    """获取 LLM 实例"""
    return ChatZhipuAI(
        model=GLM_MODEL,
        temperature=GLM_TEMPERATURE,
        api_key=ZHIPU_API_KEY,
    )


def aggregator_node(state: AggregatorState) -> dict:
    """
    汇总 Worker 结果，生成最终回复。

    流程：
    1. 收集 worker_results
    2. 根据 need_qa 决定回答方式
       - need_qa=True: 基于内容回答用户问题
       - need_qa=False: 仅生成摘要
    3. 返回 final_response
    """
    llm = _get_llm()
    user_input = state.get("user_input", "")
    worker_results = state.get("worker_results", [])
    need_qa = state.get("need_qa", True)

    print(f"[Aggregator] 收到 {len(worker_results)} 个 Worker 结果, need_qa={need_qa}")

    # 没有结果时
    if not worker_results:
        # 直接回答问题（无外部内容）
        if need_qa:
            prompt = f"""你是一个问答助手。请回答用户的问题。

用户问题：{user_input}

请给出简洁、准确的回答。"""
        else:
            prompt = f"""你是一个摘要助手。请简洁地回答用户。

用户请求：{user_input}

请给出简洁的回答。"""

        response = llm.invoke([HumanMessage(content=prompt)])
        return {"final_response": str(response.content)}

    # 有结果时，构建上下文
    context_parts = []
    for i, result in enumerate(worker_results):
        source = result.get("url", result.get("type", f"来源{i + 1}"))
        content = result.get("content", "")
        if content:
            context_parts.append(f"【{source}】\n{content}")

    context = "\n\n".join(context_parts)

    # 根据 need_qa 生成回答
    if need_qa:
        # 问答模式：基于内容回答问题
        prompt = f"""基于以下内容，回答用户的问题。

用户问题：{user_input}

---
{context}
---

请给出：
1. 直接回答问题
2. 引用相关来源
3. 如有不确定，明确说明"""
    else:
        # 摘要模式：仅生成摘要
        prompt = f"""请总结以下内容：

---
{context}
---

要求：
1. 简洁明了，不超过 500 字
2. 保留关键信息
3. 按逻辑顺序组织"""

    print(f"[Aggregator] 生成回复中...")
    response = llm.invoke([HumanMessage(content=prompt)])

    return {"final_response": str(response.content)}


# ===== 测试 =====
if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()

    # 测试1: 有结果 + 问答
    state1 = AggregatorState(
        user_input="这两个网站的主要区别是什么？",
        worker_results=[
            {"url": "https://example.com", "content": "Example 是一个示例网站。"},
            {"url": "https://test.com", "content": "Test 是一个测试网站。"},
        ],
        need_qa=True,
        final_response="",
    )

    print("=" * 50)
    print("测试1: 有结果 + 问答")
    print("=" * 50)
    result1 = aggregator_node(state1)
    print(f"结果: {result1['final_response'][:200]}...")

    # 测试2: 无结果
    state2 = AggregatorState(
        user_input="什么是 LangGraph？",
        worker_results=[],
        need_qa=True,
        final_response="",
    )

    print("\n" + "=" * 50)
    print("测试2: 无结果")
    print("=" * 50)
    result2 = aggregator_node(state2)
    print(f"结果: {result2['final_response'][:200]}...")
