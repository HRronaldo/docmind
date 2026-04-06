"""
ReAct Agent 实现
================

ReAct = Reasoning + Acting
核心思想：LLM 自主决定何时调用工具，形成"思考→行动→观察"的循环

TODO:
- [ ] 最终使用 bind_tools（当前方案 A 是手动循环）
- [ ] bind_tools 需要处理 Zhipu API 兼容性
- [ ] 工具定义可能需要调整格式

方案说明：
- 方案 A（当前）：手动实现 ReAct 循环，稳定可控
- 方案 B：使用 create_react_agent + bind_tools（Zhipu 兼容性待解决）
"""

from typing import Dict, Any, Optional, Sequence
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, BaseMessage
from langchain_core.tools import BaseTool
from langchain_community.chat_models import ChatZhipuAI
from pydantic import BaseModel

from app.agent.tools import fetch_url_content, summarize_text
from app.core.config import ZHIPU_API_KEY, GLM_MODEL, GLM_TEMPERATURE


# ===== 工具注册表 =====
# 手动管理工具映射（替代 bind_tools）
TOOL_REGISTRY: Dict[str, BaseTool] = {
    "fetch_url_content": fetch_url_content,
    "summarize_text": summarize_text,
}


# ===== LLM 初始化 =====
_llm: Optional[ChatZhipuAI] = None


def _get_llm() -> ChatZhipuAI:
    """获取 LLM 实例"""
    global _llm
    if _llm is None:
        _llm = ChatZhipuAI(
            model=GLM_MODEL,
            temperature=GLM_TEMPERATURE,
            api_key=ZHIPU_API_KEY,
        )
    return _llm


def _get_tools_schema() -> list[dict]:
    """
    获取工具 schema，用于 LLM 工具调用。

    替代 bind_tools，手动提供工具定义。
    这解决了 Zhipu API 与标准 OpenAI tool_call 格式的兼容性问题。
    """
    schemas = []
    for name, tool in TOOL_REGISTRY.items():
        # 获取参数 schema
        params = {"type": "object", "properties": {}}
        args_schema = getattr(tool, "args_schema", None)

        if args_schema is not None:
            # 如果是 Pydantic 模型，尝试获取 schema
            if isinstance(args_schema, type) and issubclass(args_schema, BaseModel):
                params = args_schema.model_json_schema()
            elif hasattr(args_schema, "model_json_schema"):
                # 已经是实例化的模型
                try:
                    params = args_schema.model_json_schema()
                except Exception:
                    pass  # 保持默认的空 schema

        schemas.append(
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": tool.description,
                    "parameters": params,
                },
            }
        )
    return schemas


# ===== ReAct 核心循环 =====
async def _react_loop(messages: list, max_iterations: int = 10) -> AIMessage:
    """
    ReAct 核心循环：思考 → 行动 → 观察

    流程：
    1. LLM 生成回复（可能包含工具调用）
    2. 如果没有工具调用，返回最终回复
    3. 执行工具，将结果添加入消息
    4. 重复直到 LLM 不再调用工具

    Args:
        messages: 对话历史
        max_iterations: 最大迭代次数（防止无限循环）

    Returns:
        最终的 AI 回复
    """
    llm = _get_llm()
    tools_schema = _get_tools_schema()

    iteration = 0

    while iteration < max_iterations:
        iteration += 1
        print(f"[ReAct] 迭代 {iteration}/{max_iterations}")

        # 1. LLM 生成回复（带上工具 schema）
        response = llm.bind(tools=tools_schema).invoke(messages)
        messages.append(response)

        # 2. 检查是否有工具调用
        if not hasattr(response, "tool_calls") or not response.tool_calls:
            # 没有工具调用，ReAct 循环结束
            print(f"[ReAct] 无工具调用，循环结束")
            return response

        # 3. 执行工具
        for tool_call in response.tool_calls:
            tool_name = tool_call.get("name") or tool_call.get("function", {}).get(
                "name", ""
            )
            # Zhipu 使用 "args"，标准 OpenAI 使用 "arguments"
            tool_args_raw = (
                tool_call.get("args")
                or tool_call.get("arguments")
                or tool_call.get("function", {}).get("arguments", {})
            )
            tool_call_id = tool_call.get("id", "")

            # 解析 arguments（可能是 dict 或 JSON string）
            import json

            tool_args = tool_args_raw
            if isinstance(tool_args_raw, str):
                try:
                    tool_args = json.loads(tool_args_raw)
                except:
                    tool_args = {}

            print(f"[ReAct] 调用工具: {tool_name}")
            print(f"[ReAct] 参数: {tool_args}")

            # 查找工具
            tool = TOOL_REGISTRY.get(tool_name)
            if not tool:
                error_msg = f"Error: Tool '{tool_name}' not found"
                messages.append(
                    ToolMessage(content=error_msg, tool_call_id=tool_call_id)
                )
                continue

            # 执行工具
            try:
                result = tool.invoke(tool_args)
                print(f"[ReAct] 工具结果长度: {len(str(result))} 字符")
            except Exception as e:
                result = f"Error executing tool: {str(e)}"
                print(f"[ReAct] 工具执行错误: {e}")

            # 4. 将工具结果添加入消息
            messages.append(ToolMessage(content=str(result), tool_call_id=tool_call_id))

    # 达到最大迭代次数
    return AIMessage(content="[ReAct] 达到最大迭代次数，停止执行")


# ===== Agent 封装类 =====
class ReActAgent:
    """
    ReAct Agent 封装类。

    使用手动实现的 ReAct 循环，支持：
    - fetch_url_content: 抓取网页内容
    - summarize_text: 文本摘要

    工作流程：
    用户消息 → ReAct 循环 → 自主决定是否调用工具 → 最终回复
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or ZHIPU_API_KEY

    async def process_message(self, message: str) -> Dict[str, Any]:
        """
        处理用户消息

        Args:
            message: 用户输入

        Returns:
            包含响应内容的字典
        """
        try:
            # 构建初始消息列表
            messages = [HumanMessage(content=message)]

            # 执行 ReAct 循环
            final_response = await _react_loop(messages)

            return {
                "response": final_response.content,
                "success": True,
                "iterations": len(
                    [
                        m
                        for m in messages
                        if isinstance(m, AIMessage) and getattr(m, "tool_calls", None)
                    ]
                ),
            }

        except Exception as e:
            import traceback

            print(f"[ReAct] 错误: {e}")
            traceback.print_exc()
            return {
                "response": f"处理消息时出错：{str(e)}",
                "success": False,
                "error": str(e),
            }


# ===== 全局实例 =====
_react_agent_instance: Optional[ReActAgent] = None


def get_react_agent() -> ReActAgent:
    """获取 ReAct Agent 实例"""
    global _react_agent_instance
    if _react_agent_instance is None:
        _react_agent_instance = ReActAgent()
    return _react_agent_instance


def init_react_agent(api_key: str) -> ReActAgent:
    """
    初始化 ReAct Agent。

    与 test_agent.py 的调用兼容。
    """
    global _llm, _react_agent_instance

    _llm = ChatZhipuAI(
        model=GLM_MODEL,
        temperature=GLM_TEMPERATURE,
        api_key=api_key,
    )
    _react_agent_instance = ReActAgent(api_key=api_key)
    return _react_agent_instance
